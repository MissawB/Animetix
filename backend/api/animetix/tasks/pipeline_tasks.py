# -*- coding: utf-8 -*-
"""
Celery Pipeline Tasks for Animetix.
Migrated from Dagster pipelines to achieve a lightweight orchestration engine.
"""

import os
import sys
from pathlib import Path
from animetix_project.logging_config import get_logger
from animetix.tasks_registry import register_task
from animetix.tasks_client import enqueue_task

logger = get_logger('animetix.' + __name__)

# Setup python path to import pipeline modules cleanly
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PIPELINE_DIR = BASE_DIR / "pipeline"

for path in [str(PIPELINE_DIR), str(PIPELINE_DIR / "mlops"), str(PIPELINE_DIR / "anime"), str(PIPELINE_DIR / "manga"), str(PIPELINE_DIR / "games"), str(PIPELINE_DIR / "actors"), str(PIPELINE_DIR / "characters")]:
    if path not in sys.path:
        sys.path.insert(0, path)

@register_task("run_daily_ingestion_workflow")
def run_daily_ingestion_workflow():
    """
    Orchestration globale de l'ingestion quotidienne de données (3h00).
    """
    logger.info("🚀 Starting Daily Ingestion Workflow...")
    
    # 1. Characters Ingestion & Vectorization
    try:
        from characters import ingest_characters, refine_characters, filter_characters, train_vibe_characters, vectorize_characters
        logger.info("Ingesting raw characters...")
        ingest_characters.run_ingestion()
        logger.info("Refining characters...")
        refine_characters.run_refinement()
        logger.info("Filtering characters...")
        filter_characters.run_filtering()
        logger.info("Training characters vibe model...")
        train_vibe_characters.run_training()
        logger.info("Vectorizing characters...")
        vectorize_characters.run_vectorization()
        logger.info("✅ Characters Ingestion & Vectorization Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Characters Ingestion: {e}", exc_info=True)
        
    # 2. Actors Ingestion & Mapping
    try:
        from actors import ingest_actors, filter_actors, vectorize_actors, cross_media_mapping
        logger.info("Ingesting raw actors...")
        ingest_actors.run_ingestion()
        logger.info("Filtering actors...")
        filter_actors.run_filtering()
        logger.info("Vectorizing actors...")
        vectorize_actors.run_vectorization()
        logger.info("Mapping actors to characters...")
        cross_media_mapping.run_mapping()
        logger.info("✅ Actors Ingestion & Mapping Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Actors Ingestion: {e}", exc_info=True)
        
    # 3. Combat Data Ingestion
    try:
        from characters import combat_data, vectorize_combat
        logger.info("Ingesting raw combat data...")
        combat_data.run_combat_data_ingestion(limit=20)
        logger.info("Vectorizing combat data...")
        vectorize_combat.run_combat_vectorization()
        logger.info("✅ Combat Ingestion Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Combat Ingestion: {e}", exc_info=True)
        
    # 4. Games Ingestion
    try:
        from games import ingest_games, filter_games, vectorize_games
        logger.info("Ingesting games...")
        ingest_games.run_ingestion()
        logger.info("Filtering games...")
        filter_games.run_filtering()
        logger.info("Vectorizing games...")
        vectorize_games.run_vectorization()
        logger.info("✅ Games Ingestion Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Games Ingestion: {e}", exc_info=True)

    # 5. Anime Ingestion & Reconciliation
    try:
        from anime import ingest_anime, reconcile_drift, filter_anime, fetch_themes, train_vibe_anime, vectorize_anime
        logger.info("Ingesting anime...")
        ingest_anime.run_ingestion()
        logger.info("Reconciling anime drift...")
        reconcile_drift.run_reconciliation()
        logger.info("Filtering anime...")
        filter_anime.run_filtering()
        logger.info("Fetching anime themes...")
        fetch_themes.run_fetching(limit=100)
        logger.info("Training anime vibe model...")
        train_vibe_anime.run_training()
        logger.info("Vectorizing anime...")
        vectorize_anime.run_vectorization()
        logger.info("✅ Anime Ingestion Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Anime Ingestion: {e}", exc_info=True)

    # 6. Manga Ingestion
    try:
        from manga import ingest_manga, filter_manga, fetch_covers, train_vibe_manga, vectorize_manga
        logger.info("Ingesting manga...")
        ingest_manga.run_ingestion()
        logger.info("Filtering manga...")
        filter_manga.run_filtering()
        logger.info("Fetching manga covers...")
        fetch_covers.run_fetching(limit=100)
        logger.info("Training manga vibe model...")
        train_vibe_manga.run_training()
        logger.info("Vectorizing manga...")
        vectorize_manga.run_vectorization()
        logger.info("✅ Manga Ingestion Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Manga Ingestion: {e}", exc_info=True)

    # 7. Enrichment Scrapers
    try:
        import enrich_db_scraper
        import specialized_scrapers
        import advanced_scrapers
        import expert_scrapers
        
        logger.info("Running general semantic enrichment...")
        enrich_db_scraper.run_enrichment(limit=10)
        logger.info("Running specialized scrapers (Casting VO/VF)...")
        specialized_scrapers.run_tripartite_enrichment(limit=5)
        logger.info("Running advanced scrapers (Arcs, fillers, IGDB)...")
        advanced_scrapers.run_tripartite_enrichment(limit=5)
        logger.info("Running expert scrapers (Streaming, pilgrimage)...")
        expert_scrapers.run_tripartite_enrichment(limit=5)
        logger.info("✅ Enrichment Scrapers Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Enrichment Scrapers: {e}", exc_info=True)

    # 8. Sync Neo4j Graph
    try:
        import neo4j_sync
        logger.info("Syncing Anime to Graph DB...")
        neo4j_sync.run_sync_type_to_graph("Anime")
        logger.info("Syncing Manga to Graph DB...")
        neo4j_sync.run_sync_type_to_graph("Manga")
        logger.info("Syncing Characters to Graph DB...")
        neo4j_sync.run_sync_type_to_graph("Character")
        logger.info("Syncing Games to Graph DB...")
        neo4j_sync.run_sync_type_to_graph("Game")
        logger.info("✅ Neo4j Sync Complete.")
    except Exception as e:
        logger.error(f"❌ Error in Neo4j Sync: {e}", exc_info=True)

    logger.info("🎉 Daily Ingestion Workflow Finished.")
    return "SUCCESS"

@register_task("run_daily_maintenance_workflow")
def run_daily_maintenance_workflow():
    """
    Orchestration globale de la maintenance MLOps quotidienne (5h00).
    """
    logger.info("🚀 Starting Daily Maintenance & MLOps Workflow...")
    
    # 1. Graph Healer Agent
    try:
        from mlops import graph_healer
        logger.info("Running self-healing graph healer...")
        graph_healer.run_graph_healer()
    except Exception as e:
        logger.error(f"❌ Error in Graph Healer: {e}", exc_info=True)

    # 2. Continuous Pre-training (CPT)
    try:
        from mlops import continuous_pretraining
        logger.info("Running continuous pre-training...")
        continuous_pretraining.run_cpt()
    except Exception as e:
        logger.error(f"❌ Error in Continuous Pretraining: {e}", exc_info=True)

    # 3. Fine-tuning Instruction Dataset generation & Expert training
    try:
        from mlops import finetuning_dataset, train_expert_model
        logger.info("Generating fine-tuning instruction dataset...")
        finetuning_dataset.run_generate_instruction_dataset()
        logger.info("Triggering expert model training...")
        train_expert_model.run_expert_training()
    except Exception as e:
        logger.error(f"❌ Error in Expert Model Training: {e}", exc_info=True)

    # 4. Latent Space Visualisation
    try:
        from mlops import latent_space_viz
        logger.info("Running latent space visualization sync...")
        latent_space_viz.run_visualization()
    except Exception as e:
        logger.error(f"❌ Error in Latent Space Viz: {e}", exc_info=True)

    # 5. Speculative Draft Distillation
    try:
        from mlops import distillation
        logger.info("Running speculative draft model distillation...")
        distillation.run_distillation()
    except Exception as e:
        logger.error(f"❌ Error in Distillation: {e}", exc_info=True)

    # 6. Evaluation metrics (RAGAS / custom judge, Legacy Retrieval)
    try:
        from mlops import evaluation_metrics
        logger.info("Running RAGAS and custom judge performance comparison...")
        evaluation_metrics.ragas_performance_comparison()
        logger.info("Running legacy retrieval metrics...")
        evaluation_metrics.legacy_retrieval_metrics()
    except Exception as e:
        logger.error(f"❌ Error in Evaluation Metrics: {e}", exc_info=True)

    # 7. Regression Benchmark
    try:
        from evaluation import regression_benchmark
        logger.info("Running AI regression benchmarks...")
        regression_benchmark.run_regression_test()
    except Exception as e:
        logger.error(f"❌ Error in Regression Benchmark: {e}", exc_info=True)

    logger.info("🎉 Daily Maintenance Workflow Finished.")
    return "SUCCESS"

@register_task("run_hourly_monitoring_workflow")
def run_hourly_monitoring_workflow():
    """
    Monitoring de santé et détection de dérive (Toutes les heures).
    """
    logger.info("🚀 Starting Hourly Monitoring Workflow...")
    
    # 0. Global Alert & Health Check
    try:
        from animetix.containers import get_container
        from django.contrib.auth import get_user_model
        
        container = get_container()
        alert_service = container.core.alert_service()
        
        # On récupère le premier administrateur pour envoyer les alertes
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            logger.info(f"Running global health check for admin {admin.username}...")
            alert_service.check_and_alert(admin_user_id=admin.id)
        else:
            logger.warning("No superuser found to receive alerts.")
    except Exception as e:
        logger.error(f"❌ Error in Global Alert Check: {e}", exc_info=True)

    # 1. Monitor Inference Health
    try:
        from mlops import rlhf_pipeline
        logger.info("Monitoring inference API health...")
        rlhf_pipeline.monitor_inference_health()
    except Exception as e:
        logger.error(f"❌ Error in Monitor Inference Health: {e}", exc_info=True)

    # 2. Knowledge Drift Check
    try:
        from evaluation import drift_detection
        logger.info("Checking knowledge drift...")
        drift_detection.run_drift_detection()
    except Exception as e:
        logger.error(f"❌ Error in Drift Detection: {e}", exc_info=True)

    # 3. AI Regression Test
    try:
        from evaluation import regression_benchmark
        logger.info("Running AI regression test...")
        regression_benchmark.run_regression_test()
    except Exception as e:
        logger.error(f"❌ Error in Regression Benchmark: {e}", exc_info=True)

    logger.info("🎉 Hourly Monitoring Workflow Finished.")
    return "SUCCESS"

@register_task("check_gold_dataset_sensor_task")
def check_gold_dataset_sensor_task():
    """
    Sensor périodique qui vérifie s'il y a 100+ nouvelles entrées GoldDataset validées.
    Enregistre l'état en cache pour éviter les doublons.
    """
    logger.info("🔍 Running Gold Dataset Sensor...")
    from django.core.cache import cache
    from animetix.models import GoldDatasetEntry
    
    validated_count = GoldDatasetEntry.objects.filter(is_validated=True).count()
    last_count = cache.get("auto_lora_last_count", 0)
    
    if validated_count >= last_count + 100:
        logger.info(f"🚀 LoRA Trigger condition met: {validated_count} validated, last count was {last_count}.")
        cache.set("auto_lora_last_count", validated_count)
        
        # Déclenche l'entraînement
        try:
            enqueue_task("run_star_training_cycle_task")
            logger.info("✅ LoRA training task queued via Cloud Tasks.")
        except Exception as e:
            logger.error(f"❌ Error triggering training from sensor: {e}")
        return "TRIGGERED"
        
    logger.info(f"ℹ️ Gold Dataset Sensor finished. Count={validated_count}, Last={last_count}. Threshold (100) not met.")
    return "NO_TRIGGER"

@register_task("check_dpo_feedback_sensor_task")
def check_dpo_feedback_sensor_task():
    """
    Sensor périodique qui vérifie s'il y a 100+ nouvelles entrées DPO.
    Enregistre l'état en cache pour éviter les doublons.
    """
    logger.info("🔍 Running DPO Feedback Sensor...")
    from django.core.cache import cache
    from animetix.models import AIFeedback
    
    try:
        total_feedbacks = AIFeedback.objects.count()
    except Exception as e:
        total_feedbacks = 0
        
    last_count = cache.get("auto_dpo_last_count", 0)
    
    if total_feedbacks >= last_count + 100:
        logger.info(f"🚀 DPO Trigger condition met: {total_feedbacks} feedbacks, last count was {last_count}.")
        cache.set("auto_dpo_last_count", total_feedbacks)
        
        # Déclenche l'entraînement
        try:
            from pipeline.mlops.trl_ops import trl_ready_dataset, trigger_lora_training
            dataset_path = trl_ready_dataset(config=None)
            trigger_lora_training(dataset_path=dataset_path)
            logger.info("✅ DPO training triggered successfully.")
        except Exception as e:
            logger.error(f"❌ Error triggering DPO training from sensor: {e}")
        return "TRIGGERED"
        
    logger.info(f"ℹ️ DPO Feedback Sensor finished. Count={total_feedbacks}, Last={last_count}. Threshold (100) not met.")
    return "NO_TRIGGER"
