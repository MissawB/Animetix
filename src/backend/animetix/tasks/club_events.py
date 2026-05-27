from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task(name="animetix.social.trigger_club_event")
def trigger_club_event(club_id, event_id):
    """
    Triggers a club-wide event by broadcasting to the WebSocket group.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"club_{club_id}",
        {
            "type": "event_start",
            "event_id": event_id,
            "club_id": club_id,
        }
    )
