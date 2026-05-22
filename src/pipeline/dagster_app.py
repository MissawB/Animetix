from dagster import asset, Definitions, ScheduleDefinition, AssetSelection, define_asset_job, sensor, RunRequest, DefaultScheduleStatus, RetryPolicy
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Chemins de base dynamiques
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent.parent
SRC_DIR = PIPELINE_DIR.parent
BACKEND_DIR = SRC_DIR / "backend"

# Chargement du .env
load_dotenv(PROJECT_ROOT / ".env")

# Ajout des dossiers au path pour les imports
for path in [str(PIPELINE_DIR), str(SRC_DIR), str(BACKEND_DIR)]:
    if path not in sys.path:
        sys.path.append(path)

# --- CONFIGURATION DJANGO ---
import django
from django.apps import apps
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
if not apps.ready:
    django.setup()

# --- IMPORTS PIPELINE ---
from characters import ingest_characters, refine_characters, filter_characters, train_vibe_characters, vectorize_characters, combat_data, vectorize_combat
from anime import ingest_anime, filter_anime, train_vibe_anime, vectorize_anime, fetch_themes, reconcile_drift
from manga import ingest_manga, filter_manga, train_vibe_manga, vectorize_manga, fetch_covers
from games import ingest_games, filter_games, vectorize_games
from actors import ingest_actors, filter_actors, vectorize_actors, cross_media_mapping
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

# --- 🎭 PIPELINE : ACTORS ---
@asset(group_name="actors")
def raw_actors(): return ingest_actors.run_ingestion()

@asset(deps=[raw_actors], group_name="actors")
def filtered_actors(): return filter_actors.run_filtering()

@asset(deps=[filtered_actors], group_name="actors")
def actor_artifacts(chroma: ChromaResource): 
    return vectorize_actors.run_vectorization(chroma_res=chroma)

@asset(deps=[actor_artifacts, character_artifacts], group_name="actors")
def actor_mapping(chroma: ChromaResource): 
    return cross_media_mapping.run_mapping(chroma_res=chroma)

# --- ⚔️ PIPELINE : COMBAT (VS Battle) ---
@asset(deps=[filtered_characters], group_name="combat")
def raw_combat_data(): return combat_data.run_combat_data_ingestion(limit=20)

@asset(deps=[raw_combat_data], group_name="combat")
def combat_artifacts(chroma: ChromaResource): 
    return vectorize_combat.run_combat_vectorization(chroma_res=chroma)

# --- 🎮 PIPELINE : GAMES ---
@asset(group_name="games")
def raw_games(): return ingest_games.run_ingestion()

@asset(deps=[raw_games], group_name="games")
def filtered_games(): return filter_games.run_filtering()

@asset(deps=[filtered_games], group_name="games")
def game_artifacts(chroma: ChromaResource): 
    return vectorize_games.run_vectorization(chroma_res=chroma)

# --- 📺 PIPELINE : ANIME ---
@asset(group_name="anime")
def raw_anime(): return ingest_anime.run_ingestion()

@asset(deps=[raw_anime], group_name="anime")
def reconciled_anime(): 
    """Asset de réconciliation automatique basé sur le drift détecté."""
    return reconcile_drift.run_reconciliation()

@asset(deps=[reconciled_anime], group_name="anime")
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

# --- 🧪 PIPELINE : MLOPS ---
@asset(group_name="mlops")
def self_healing_graph_agent(): 
    from core.domain.services.graph_healer_service import GraphHealerService
    return GraphHealerService().perform_healing()

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

@asset(group_name="mlops", deps=[trl_ready_dataset])
def trigger_model_retraining(): return rlhf_pipeline.trigger_model_retraining()

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

@asset(group_name="graph", deps=[game_artifacts])
def sync_games_to_graph(): return neo4j_sync.run_sync_type_to_graph("Game")

@asset(group_name="graph", deps=[sync_anime_to_graph, sync_manga_to_graph, sync_characters_to_graph, sync_games_to_graph])
def global_knowledge_graph(): return True

# --- JOBS ---
# Job complet pour rafraîchissement total
full_pipeline_job = define_asset_job(name="full_pipeline_job", selection=AssetSelection.all())

# Job d'ingestion (Anime, Manga, Characters, Games, Actors, Combat)
ingestion_job = define_asset_job(
    name="ingestion_job", 
    selection=AssetSelection.groups("characters") | AssetSelection.groups("anime") | AssetSelection.groups("manga") | AssetSelection.groups("games") | AssetSelection.groups("actors") | AssetSelection.groups("combat")
)

# Job de maintenance (Drift check, Graph healer, Knowledge graph)
maintenance_job = define_asset_job(
    name="maintenance_job",
    selection=AssetSelection.groups("mlops") | AssetSelection.groups("graph")
)

# Job de monitoring de santé (uniquement les assets critiques de monitoring)
health_monitoring_job = define_asset_job(
    name="health_monitoring_job",
    selection=AssetSelection.assets(monitor_inference_health, ai_regression_test, knowledge_drift_check)
)

# Job MLOps pour le capteur (sensor)
mlops_job = define_asset_job(name="mlops_job", selection=AssetSelection.groups("mlops"))

# --- SENSORS ---
@sensor(job=mlops_job)
def auto_lora_sensor(context):
    return auto_lora_trigger.check_gold_dataset_sensor(context)

# --- SCHEDULES ---
# Ingestion quotidienne à 03:00 du matin
daily_ingestion_schedule = ScheduleDefinition(
    job=ingestion_job, 
    cron_schedule="0 3 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING
)

# Maintenance et Sync Graph à 05:00 du matin (après l'ingestion)
daily_maintenance_schedule = ScheduleDefinition(
    job=maintenance_job,
    cron_schedule="0 5 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING
)

# Monitoring de santé toutes les heures
hourly_monitoring_schedule = ScheduleDefinition(
    job=health_monitoring_job,
    cron_schedule="0 * * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING
)

# --- DEFINITIONS ---
defs = Definitions(
    assets=[
        raw_characters, refined_characters, filtered_characters, trained_characters_model, character_artifacts,
        raw_anime, reconciled_anime, filtered_anime, anime_themes, trained_anime_model, anime_artifacts,
        raw_manga, filtered_manga, manga_covers, trained_manga_model, manga_artifacts,
        raw_games, filtered_games, game_artifacts,
        raw_actors, filtered_actors, actor_artifacts, actor_mapping,
        raw_combat_data, combat_artifacts,
        monitor_inference_health, exported_user_feedback, trl_ready_dataset, trigger_model_retraining,
        ragas_performance_comparison, legacy_retrieval_metrics, finetuning_dataset_asset, otaku_model_training,
        latent_space_data_asset, global_knowledge_graph, speculative_draft_distillation, knowledge_drift_check, 
        ai_regression_test, self_healing_graph_agent, continuous_pretraining_draft,
        sync_anime_to_graph, sync_manga_to_graph, sync_characters_to_graph, sync_games_to_graph
    ],
    jobs=[full_pipeline_job, ingestion_job, maintenance_job, health_monitoring_job, mlops_job],
    schedules=[daily_ingestion_schedule, daily_maintenance_schedule, hourly_monitoring_schedule],
    sensors=[auto_lora_sensor],
    resources={
        "chroma": ChromaResource(persist_path=str(PROJECT_ROOT / "data" / "chroma_db")),
        "neo4j": Neo4jResource(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            user=os.getenv("NEO4J_USER", "neo4j"), 
            password=os.getenv("NEO4J_PASSWORD", "secretpassword")
        )
    }
)
