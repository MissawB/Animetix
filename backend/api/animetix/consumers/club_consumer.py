import json
import logging
from channels.db import database_sync_to_async
from .base import BaseConsumer
from ..models import ClubMembership

logger = logging.getLogger(__name__)

class ClubConsumer(BaseConsumer):
    """
    Consumer for real-time club chat and synchronization.
    """
    async def connect(self):
        self.club_id = self.scope['url_route']['kwargs']['club_id']
        self.club_group_name = f'club_{self.club_id}'
        self.user = self.scope['user']

        if self.user.is_authenticated:
            # Check if user is a member of the club
            is_member = await self.check_membership(self.user, self.club_id)
            if is_member:
                # Join club group
                await self.channel_layer.group_add(
                    self.club_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                await self.close()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave club group
        if hasattr(self, 'club_group_name'):
            await self.channel_layer.group_discard(
                self.club_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            
            if not message:
                return

            # Broadcast message to club group
            await self.channel_layer.group_send(
                self.club_group_name,
                {
                    'type': 'send_msg',
                    'message': {
                        'text': message,
                        'username': self.user.username,
                        'type': 'chat',
                        'club_id': self.club_id
                    }
                }
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Consumer JSON decode failed: {e}")

    async def event_start(self, event):
        """Handler for 'event_start' group message."""
        await self.send(text_data=json.dumps(event))

    async def next_question(self, event):
        """Handler for 'next_question' group message."""
        await self.send(text_data=json.dumps(event))

    async def score_update(self, event):
        """Handler for 'score_update' group message."""
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def check_membership(self, user, club_id):
        return ClubMembership.objects.filter(user=user, club_id=club_id).exists()
