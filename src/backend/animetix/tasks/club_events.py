from celery import shared_task
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger('animetix.tasks.clubs')

@shared_task
def trigger_club_event(club_id, event_id):
    """
    Signals all members of a club via WebSocket that an event has started.
    """
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
            'message': 'L''événement du club commence maintenant !'
        }
    )
    logger.info(f"Triggered event {event_id} for club {club_id}")
