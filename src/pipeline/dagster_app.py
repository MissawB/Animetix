from dagster import asset, Definitions, ScheduleDefinition, AssetSelection, define_asset_job, RetryPolicy
from pathlib import Path
import os
import sys

# Chemins de base dynamiques
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent.parent
SRC_DIR = PIPELINE_DIR.parent
BACKEND_DIR = SRC_DIR / "backend"

# Ajout des dossiers au path pour les imports
for path in [str(PIPELINE_DIR), str(SRC_DIR), str(BACKEND_DIR)]:
    if path not in sys.path:
        sys.path.append(path)

# --- CONFIGURATION DJANGO (Nécessaire pour les modèles) ---
import django
from django.apps import apps
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
if not apps.ready:
    django.setup()

# --- IMPORTS ---
from characters import ingest_characters, refine_characters, filter_characters, train_vibe_characters, vectorize_characters
from anime import ingest_anime, filter_anime, train_vibe_anime, vectorize_anime, fetch_themes
from manga import ingest_manga, filter_manga, train_vibe_manga, vectorize_manga, fetch_covers
from mlops import finetuning_dataset, train_expert_model, rlhf_pipeline, evaluation_metrics, latent_space_viz, distillation, auto_lora_trigger, graph_healer, continuous_pretraining
from evaluation import drift_detection, regression_benchmark
import neo4j_sync
from resources import ChromaResource, Neo4jResource

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
def anime_artifacts(chroma: ChromaResource, neo4j: Neo4jResource): 
    return vectorize_anime.run_vectorization(chroma_res=chroma, neo4j_res=neo4j)

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
@asset(group_name="mlops")
def self_healing_graph_agent(): return graph_healer.run_graph_healer()

@asset(group_name="mlops", deps=[raw_anime])
def continuous_pretraining_draft(): return continuous_pretraining.run_cpt()

@asset(group_name="mlops", deps=[anime_artifacts, manga_artifacts, character_artifacts])
def finetuning_dataset_asset(): return finetuning_dataset.run_generate_instruction_dataset()

@asset(group_name="mlops", deps=[finetuning_dataset_asset], retry_policy=RetryPolicy(max_retries=3, delay=60))
def otaku_model_training(): return train_expert_model.run_expert_training()

@asset(group_name="mlops", deps=[anime_artifacts])
def latent_space_data_asset(): return latent_space_viz.run_visualization()

@asset(group_name="mlops")
def monitor_inference_health(): return rlhf_pipeline.monitor_inference_health()

@asset(group_name="mlops", compute_kind="django_db")
def exported_user_feedback(): return rlhf_pipeline.exported_user_feedback()

@asset(group_name="mlops", deps=[exported_user_feedback])
def trl_ready_dataset(exported_user_feedback): return rlhf_pipeline.trl_ready_dataset(exported_user_feedback)

@asset(group_name="mlops", deps=[trl_ready_dataset, knowledge_drift_check])
def trigger_model_retraining(trl_ready_dataset, knowledge_drift_check): return rlhf_pipeline.trigger_model_retraining(trl_ready_dataset, knowledge_drift_check)

@asset(group_name="mlops", deps=[trl_ready_dataset])
def speculative_draft_distillation(): return distillation.run_distillation()

@asset(group_name="mlops")
def ragas_performance_comparison(): return evaluation_metrics.ragas_performance_comparison()

@asset(group_name="mlops")
def legacy_retrieval_metrics(): return evaluation_metrics.legacy_retrieval_metrics()

@asset(group_name="mlops")
def knowledge_drift_check(): return drift_detection.run_drift_detection()

@asset(group_name="mlops")
def ai_regression_test(): return regression_benchmark.run_regression_test()

# --- 🕸️ PIPELINE : GRAPH (Neo4j) ---
@asset(group_name="graph", deps=[anime_artifacts])
def sync_anime_to_graph(): return neo4j_sync.run_sync_type_to_graph("Anime")

@asset(group_name="graph", deps=[manga_artifacts])
def sync_manga_to_graph(): return neo4j_sync.run_sync_type_to_graph("Manga")

@asset(group_name="graph", deps=[character_artifacts])
def sync_characters_to_graph(): return neo4j_sync.run_sync_type_to_graph("Character")

@asset(group_name="graph", deps=[sync_anime_to_graph, sync_manga_to_graph, sync_characters_to_graph])
def global_knowledge_graph(): return True

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
        latent_space_data_asset, global_knowledge_graph, speculative_draft_distillation, knowledge_drift_check, 
        ai_regression_test, self_healing_graph_agent, continuous_pretraining_draft,
        sync_anime_to_graph, sync_manga_to_graph, sync_characters_to_graph
    ],
    jobs=[all_assets_job, mlops_job],
    schedules=[daily_refresh_schedule, hourly_health_check],
    sensors=[auto_lora_trigger.check_gold_dataset_sensor],
    resources={
        "chroma": ChromaResource(persist_path=str(PROJECT_ROOT / "data" / "chroma_db")),
        "neo4j": Neo4jResource(uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"), user=os.getenv("NEO4J_USER", "neo4j"), password=os.getenv("NEO4J_PASSWORD", "password"))
    }
)
