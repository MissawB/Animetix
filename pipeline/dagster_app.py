from dagster import asset, Definitions, ScheduleDefinition, AssetSelection, define_asset_job
from pathlib import Path
import os
import sys

# Chemins de base dynamiques
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent

# Ajout du dossier pipeline au path pour les imports locaux
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))

# --- IMPORTS DES MODULES REFACTORISÉS ---
from characters import ingest_characters, refine_characters, filter_characters, train_vibe_characters, vectorize_characters
from anime import ingest_anime, filter_anime, train_vibe_anime, vectorize_anime, fetch_themes
from manga import ingest_manga, filter_manga, train_vibe_manga, vectorize_manga, fetch_covers
from mlops import finetuning_dataset, train_expert_model, rlhf_pipeline, evaluation_metrics, latent_space_viz

# --- 🎭 PIPELINE : CHARACTERS ---
@asset(group_name="characters")
def raw_characters(): return ingest_characters.run_ingestion()

@asset(deps=[raw_characters], group_name="characters")
def refined_characters(): return refine_characters.run_refinement()

@asset(deps=[refined_characters], group_name="characters")
def filtered_characters(): return filter_characters.run_filtering()

@asset(deps=[filtered_characters], group_name="characters")
def trained_characters_model(): return train_vibe_characters.run_training()

@asset(deps=[trained_characters_model], group_name="characters")
def character_artifacts(): return vectorize_characters.run_vectorization()

# --- 📺 PIPELINE : ANIME ---
@asset(group_name="anime")
def raw_anime(): return ingest_anime.run_ingestion()

@asset(deps=[raw_anime], group_name="anime")
def filtered_anime(): return filter_anime.run_filtering()

@asset(deps=[filtered_anime], group_name="anime")
def anime_themes(): return fetch_themes.run_fetching(limit=100)

@asset(deps=[filtered_anime], group_name="anime")
def trained_anime_model(): return train_vibe_anime.run_training()

@asset(deps=[trained_anime_model], group_name="anime")
def anime_artifacts(): return vectorize_anime.run_vectorization()

# --- 📖 PIPELINE : MANGA ---
@asset(group_name="manga")
def raw_manga(): return ingest_manga.run_ingestion()

@asset(deps=[raw_manga], group_name="manga")
def filtered_manga(): return filter_manga.run_filtering()

@asset(deps=[filtered_manga], group_name="manga")
def manga_covers(): return fetch_covers.run_fetching(limit=100)

@asset(deps=[filtered_manga], group_name="manga")
def trained_manga_model(): return train_vibe_manga.run_training()

@asset(deps=[trained_manga_model], group_name="manga")
def manga_artifacts(): return vectorize_manga.run_vectorization()

# --- 🧪 PIPELINE : MLOPS (Fine-Tuning, Eval & Viz) ---

@asset(group_name="mlops", deps=[anime_artifacts, manga_artifacts, character_artifacts])
def finetuning_dataset_asset():
    """Génère le dataset d'instructions multi-médias pour le Fine-Tuning."""
    return finetuning_dataset.run_generate_instruction_dataset()

@asset(group_name="mlops", deps=[finetuning_dataset_asset])
def otaku_model_training():
    """Lance l'entraînement QLoRA (nécessite un GPU)."""
    return train_expert_model.run_expert_training()

@asset(group_name="mlops", deps=[anime_artifacts])
def latent_space_data_asset():
    """Projette les embeddings en 3D via UMAP."""
    return latent_space_viz.run_visualization()

# --- 🔄 RLHF PIPELINE ---
@asset(group_name="mlops")
def monitor_inference_health(): return rlhf_pipeline.monitor_inference_health()

@asset(group_name="mlops", compute_kind="django_db")
def exported_user_feedback(): return rlhf_pipeline.exported_user_feedback()

@asset(group_name="mlops", deps=[exported_user_feedback])
def trl_ready_dataset(exported_user_feedback): return rlhf_pipeline.trl_ready_dataset(exported_user_feedback)

@asset(group_name="mlops", deps=[trl_ready_dataset])
def trigger_model_retraining(): return rlhf_pipeline.trigger_model_retraining()

# --- 📊 EVALUATION ---
@asset(group_name="mlops")
def ragas_performance_comparison(): return evaluation_metrics.ragas_performance_comparison()

@asset(group_name="mlops")
def legacy_retrieval_metrics(): return evaluation_metrics.legacy_retrieval_metrics()

# --- JOBS & SCHEDULES ---
all_assets_job = define_asset_job(name="all_assets_job", selection=AssetSelection.all())
mlops_job = define_asset_job(name="mlops_job", selection=AssetSelection.groups("mlops"))

daily_refresh_schedule = ScheduleDefinition(job=all_assets_job, cron_schedule="0 0 * * *")
hourly_health_check = ScheduleDefinition(job=mlops_job, cron_schedule="0 * * * *")

# --- DEFINITIONS ---
defs = Definitions(
    assets=[
        raw_characters, refined_characters, filtered_characters, trained_characters_model, character_artifacts,
        raw_anime, filtered_anime, anime_themes, trained_anime_model, anime_artifacts,
        raw_manga, filtered_manga, manga_covers, trained_manga_model, manga_artifacts,
        monitor_inference_health, exported_user_feedback, trl_ready_dataset, trigger_model_retraining,
        ragas_performance_comparison, legacy_retrieval_metrics, finetuning_dataset_asset, otaku_model_training,
        latent_space_data_asset
    ],
    jobs=[all_assets_job, mlops_job],
    schedules=[daily_refresh_schedule, hourly_health_check]
)
