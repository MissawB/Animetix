from celery import shared_task
from animetix_project.logging_config import get_logger
from animetix.tasks_registry import register_task

def get_container():
    from ..containers import get_container as _get_container
    return _get_container()

logger = get_logger('animetix.' + __name__)

def generate_fusion_image(item1, item2, art_style='Cyberpunk'):
    container = get_container()
    return container.core.fusion_service.generate_fusion_image(item1, item2, art_style=art_style)

@shared_task
@register_task("generate_fusion_scenario_task")
def generate_fusion_scenario_task(media_type, item1, item2, language, chaos_level=50, universe_balance=50, art_style='Cyberpunk'):
    try:
        container = get_container()
        return container.llm_service.generate_fusion_scenario(media_type, item1, item2, language, chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style)
    except Exception as e:
        logger.error(f'Task Error in generate_fusion_scenario: {e}')
        return 'Erreur lors de la génération du scénario.'

@shared_task
@register_task("generate_fusion_image_task")
def generate_fusion_image_task(fusion_data, item1, item2, art_style='Cyberpunk'):
    try:
        if isinstance(fusion_data, str): fusion_data = {'scenario': fusion_data}
        image_url = generate_fusion_image(item1, item2, art_style=art_style)
        fusion_data['fusion_image'] = image_url
        return fusion_data
    except Exception as e:
        logger.error(f'Task Error in generate_fusion_image: {e}')
        return fusion_data

@register_task("generate_fusion_flow_task")
def generate_fusion_flow_task(media_type, item1, item2, language, chaos_level=50, universe_balance=50, art_style='Cyberpunk'):
    scenario = generate_fusion_scenario_task(media_type, item1, item2, language, chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style)
    result = generate_fusion_image_task(scenario, item1, item2, art_style=art_style)
    return result

@shared_task
@register_task("process_video_chunk_task")
def process_video_chunk_task(chunk_data_b64, chunk_index, total_chunks, query=None):
    import base64
    container = get_container()
    video_bytes = base64.b64decode(chunk_data_b64)
    if query: result = container.video_rag_service.find_precise_moment(video_bytes, query)
    else: result = container.video_rag_service.process_segment(video_bytes)
    return {'index': chunk_index, 'data': result, 'timestamp_start': chunk_index * 30}

@shared_task
@register_task("aggregate_video_results_task")
def aggregate_video_results_task(results, original_query=None):
    container = get_container()
    sorted_results = sorted(results, key=lambda x: x['index'])
    summary = container.video_rag_service.query_long_video(sorted_results, original_query or 'Résumé global')
    return {'summary': summary, 'timeline': sorted_results}

@shared_task
@register_task("run_star_training_cycle_task")
def run_star_training_cycle_task():
    container = get_container()
    new_entries = container.star_mlops_service.prepare_star_dataset()
    if new_entries < 1: return 'Insufficient new traces.'
    result = container.star_mlops_service.trigger_finetuning()
    return f"STaR cycle triggered: {result['status']}"


@shared_task(bind=True, max_retries=3)
@register_task("sync_media_item_task")
def sync_media_item_task(self, media_type, item_id, data):
    try:
        container = get_container()
        container.sync_service.handle_media_update(media_type, item_id, data)
    except Exception as e: raise self.retry(exc=e, countdown=60)

@shared_task
@register_task("trigger_club_event")
def trigger_club_event(club_id, event_id):
    """
    Signals all members of a club via WebSocket that an event has started.
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.error("No channel layer found for club event trigger.")
        return

    group_name = f'club_{club_id}'
    
    # Broadcast to the club's WebSocket group
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'event_start',
            'event_id': event_id,
            'message': "L'événement du club commence maintenant !"
        }
    )
    logger.info(f"Triggered event {event_id} for club {club_id}")


from . import telemetry_tasks



