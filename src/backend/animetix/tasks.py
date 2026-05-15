from celery import shared_task
from .services import LangChainService

@shared_task
def generate_fusion_scenario_task(media_type, item1, item2, language):
    """Génère le synopsis de fusion."""
    langchain_service = LangChainService()
    return langchain_service.generate_scenario_advanced(media_type, item1, item2, language)

@shared_task
def generate_fusion_image_task(fusion_data, item1, item2):
    """Génère l'image de fusion à partir du résultat du synopsis."""
    langchain_service = LangChainService()
    # Si fusion_data est une string (erreur de chaîne précédente), on en fait un dict
    if isinstance(fusion_data, str):
        fusion_data = {'scenario': fusion_data}
        
    scenario_text = fusion_data.get('scenario', '')
    title_A = item1.get('title') or item1.get('name')
    title_B = item2.get('title') or item2.get('name')
    vis_prompt = f"Fusion of {title_A} and {title_B}: {scenario_text[:200]}"
    image_url = langchain_service.generate_fusion_image(vis_prompt)
    
    # Enrichir le résultat avec l'image
    fusion_data['fusion_image'] = image_url
    return fusion_data

@shared_task
def answer_complex_query_task(query: str, media_type: str):
    """Tâche asynchrone pour traiter une question complexe."""
    from animetix.services import AnimetixService
    rag_service = AnimetixService().rag_service
    return rag_service.generate_advanced_answer(query, media_type)

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
