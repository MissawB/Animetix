from celery import shared_task
from .containers import get_container
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
