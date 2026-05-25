from celery import shared_task
def get_container():
    from .containers import get_container as _get_container
    return _get_container()
from .creative_tasks import generate_fusion_image
import logging

logger = logging.getLogger('animetix.tasks')

@shared_task
def generate_fusion_scenario_task(media_type, item1, item2, language, chaos_level=50, universe_balance=50, art_style="Cyberpunk"):
    """Génère le synopsis de fusion."""
    try:
        container = get_container()
        return container.llm_service.generate_fusion_scenario(
            media_type, item1, item2, language, 
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style
        )
    except Exception as e:
        logger.error(f"Task Error in generate_fusion_scenario: {e}")
        return "Erreur lors de la génération du scénario."

@shared_task
def generate_fusion_image_task(fusion_data, item1, item2, art_style="Cyberpunk"):
    """Génère l'image de fusion à partir du résultat du synopsis."""
    try:
        # Si fusion_data est une string, on en fait un dict
        if isinstance(fusion_data, str):
            fusion_data = {'scenario': fusion_data}
            
        image_url = generate_fusion_image(item1, item2, art_style=art_style)
        
        # Enrichir le résultat avec l'image
        fusion_data['fusion_image'] = image_url
        return fusion_data
    except Exception as e:
        logger.error(f"Task Error in generate_fusion_image: {e}")
        return fusion_data

@shared_task
def process_video_chunk_task(chunk_data_b64, chunk_index, total_chunks, query=None):
    """Analyse un segment vidéo spécifique via VLM."""
    import base64
    container = get_container()
    video_bytes = base64.b64decode(chunk_data_b64)
    
    logger.info(f"🎬 [Video-RAG] Processing chunk {chunk_index}/{total_chunks}")
    
    # Appel au service de domaine pour l'analyse de segment
    if query:
        result = container.video_quest_service.find_precise_moment(video_bytes, query)
    else:
        result = container.video_quest_service.process_segment(video_bytes)
        
    return {
        "index": chunk_index,
        "data": result,
        "timestamp_start": chunk_index * 30 # Hypothèse 30s par chunk
    }

@shared_task
def aggregate_video_results_task(results, original_query=None):
    """Agrège les résultats de tous les segments pour produire une synthèse globale."""
    container = get_container()
    logger.info(f"📊 [Video-RAG] Aggregating {len(results)} segment results")
    
    # Tri par index pour conserver la chronologie
    sorted_results = sorted(results, key=lambda x: x['index'])
    
    # Synthèse finale
    summary = container.video_quest_service.query_long_video(sorted_results, original_query or "Résumé global")
    
    return {
        "summary": summary,
        "timeline": sorted_results,
        "total_segments": len(results)
    }

@shared_task
def run_star_training_cycle_task():
    """Tâche périodique pour cristalliser les traces STaR via Fine-Tuning."""
    container = get_container()
    logger.info("🛠️ [STaR Task] Starting automated training cycle...")
    
    # 1. Préparation des données
    new_entries = container.star_mlops_service.prepare_star_dataset()
    if new_entries < 1: # On peut monter le seuil en prod
        return "Insufficient new traces for training."
        
    # 2. Déclenchement du Fine-Tuning
    result = container.star_mlops_service.trigger_finetuning()
    return f"STaR cycle triggered. Entries: {new_entries}. Status: {result['status']}"

@shared_task(bind=True, max_retries=3)
def sync_media_item_task(self, media_type, item_id, data):
    """Synchronise un item avec les bases Graphes et Vecteurs de manière asynchrone."""
    try:
        container = get_container()
        container.sync_service.handle_media_update(media_type, item_id, data)
        return f"Successfully synced {media_type} {item_id}"
    except Exception as e:
        logger.error(f"Sync failed for {media_type} {item_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@shared_task
def answer_complex_query_task(query: str, media_type: str):
    """Tâche asynchrone pour traiter une question complexe."""
    container = get_container()
    return container.rag_service.generate_advanced_answer(query, media_type)


@shared_task
def scheduled_dpo_optimization():
    """
    Tâche périodique pour optimiser les prompts à partir des feedbacks négatifs accumulés.
    Identifie les catégories avec suffisamment d'échecs et déclenche l'ingénierie Meta-Prompt.
    """
    from animetix.models import AIFeedback
    from django.db.models import Count
    from django.core.cache import cache
    
    lock_id = "scheduled_dpo_optimization_lock"
    # Acquire lock for 1 hour (max task duration)
    # cache.add is atomic in django-redis
    if not cache.add(lock_id, "true", 3600):
        logger.warning("🤖 [DPO Task] Already running. Skipping.")
        return "Task already running."
    
    try:
        container = get_container()
        dpo_loop = container.dpo_feedback_loop
        prompt_manager = container.prompt_manager
        
        logger.info("🤖 [DPO Task] Starting automated prompt optimization cycle...")
    
        # 1. Identifier les catégories (feedback_type) ayant suffisamment de feedbacks 'Rejected'
        # On cherche au moins 5 feedbacks négatifs récents pour justifier une optimisation
        MIN_REJECTED_THRESHOLD = 5
        
        stats = AIFeedback.objects.filter(is_positive=False).values('feedback_type').annotate(
            rejected_count=Count('id')
        ).filter(rejected_count__gte=MIN_REJECTED_THRESHOLD)
        
        optimized_categories = []
        
        for stat in stats:
            prompt_key = stat['feedback_type']
            # Vérifier si c'est une clé de prompt valide gérée par le PromptManager
            if prompt_key in prompt_manager.prompts:
                logger.info(f"✨ [DPO Task] Optimizing prompt '{prompt_key}' (Rejected count: {stat['rejected_count']})")
                
                try:
                    new_prompt = dpo_loop.optimize_prompt_from_feedback(prompt_key, limit=50)
                    if new_prompt:
                        logger.info(f"✅ [DPO Task] Success: Prompt '{prompt_key}' has been updated.")
                        logger.info(f"📝 [DPO Task] New prompt for '{prompt_key}':\n{new_prompt}")
                        optimized_categories.append(prompt_key)
                    else:
                        logger.warning(f"⚠️ [DPO Task] Optimization failed or no changes for '{prompt_key}'.")
                except Exception as e:
                    logger.error(f"❌ [DPO Task] Error optimizing '{prompt_key}': {e}")
            else:
                logger.debug(f"ℹ️ [DPO Task] Category '{prompt_key}' found in feedback but not in PromptManager. Skipping.")
    
        if not optimized_categories:
            return "No prompts needed optimization today."
            
        return f"Optimization cycle complete. Categories updated: {', '.join(optimized_categories)}"
    finally:
        cache.delete(lock_id)


@shared_task
def cleanup_duel_resources_task(room_code: str):
    """Nettoie les ressources liées à un salon de duel."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"duel_{room_code}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {"type": "duel.cleanup", "message": "Room closed by system."}
            )
    except ImportError:
        pass 
    return f"Cleanup triggered for {room_code}"


@shared_task
def log_dpo_preference_task(query, chosen, rejected, project_root):
    """Journalisation asynchrone des paires de préférence DPO via Celery."""
    import json
    import os
    try:
        datasets_dir = os.path.join(project_root, "data", "mlops", "datasets")
        os.makedirs(datasets_dir, exist_ok=True)
        path = os.path.join(datasets_dir, "ai_feedback.jsonl")

        pair_chosen = {
            "context": query,
            "output": chosen,
            "is_positive": True
        }
        pair_rejected = {
            "context": query,
            "output": rejected,
            "is_positive": False
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(pair_chosen, ensure_ascii=False) + "\n")
            f.write(json.dumps(pair_rejected, ensure_ascii=False) + "\n")
        
        logger.info(f"💾 [Celery DPO] Logged preference pair for query='{query[:30]}...'")
        return True
    except Exception as e:
        logger.error(f"Failed to log DPO feedback in Celery: {e}")
        return False
