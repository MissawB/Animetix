import json

from adapters.persistence.django_cache_state_adapter import DjangoCacheStateAdapter
from channels.generic.websocket import AsyncWebsocketConsumer

state_adapter = DjangoCacheStateAdapter()


class BaseConsumer(AsyncWebsocketConsumer):
    """
    Base class for Animetix consumers providing common utilities.
    """

    async def send_msg(self, event):
        """Standard handler for sending messages to the client."""
        await self.send(text_data=json.dumps(event["message"]))
