import json

from .base import BaseConsumer


class NotificationConsumer(BaseConsumer):
    async def connect(self):
        # 1. Groupe Global (tous les utilisateurs connectés)
        await self.channel_layer.group_add("global_notifications", self.channel_name)

        # 2. Groupe Privé (uniquement pour l'utilisateur)
        if not self.scope["user"].is_anonymous:
            self.user_id = self.scope["user"].id
            self.group_name = f"user_notifications_{self.user_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "global_notifications", self.channel_name
        )
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """
        Handler pour les événements de type 'send_notification' envoyés par le channel layer.
        """
        await self.send(text_data=json.dumps(event["data"]))
