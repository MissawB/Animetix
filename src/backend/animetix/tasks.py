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
