import logging
from typing import Optional, Any
from core.ports.notification_port import NotificationPort

logger = logging.getLogger("animetix.adapters.notification")

class DjangoNotificationAdapter(NotificationPort):
    """
    Adapter implementing notification delivery via Django models and Channels (WebSockets).
    """
    def send(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        notification_type: str = 'info', 
        link: Optional[str] = None,
        **kwargs
    ) -> Any:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from django.contrib.auth import get_user_model
        from animetix.models import Notification

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            
            # 1. Sauvegarde en base
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link
            )
            
            # 2. Envoi via WebSocket
            channel_layer = get_channel_layer()
            if channel_layer:
                # Mapping type pour le frontend
                ws_type = notification_type
                if notification_type == 'achievement':
                    ws_type = 'achievement_unlocked'
                
                async_to_sync(channel_layer.group_send)(
                    f"user_notifications_{user.id}",
                    {
                        "type": "send_notification",
                        "data": {
                            "id": notification.id,
                            "type": ws_type,
                            "title": title,
                            "message": message,
                            "link": link,
                            "created_at": notification.created_at.strftime("%H:%M"),
                            "achievement": kwargs.get("achievement", {
                                "name": title.replace("Succès Débloqué !", "").strip() or title,
                                "icon": "🏆",
                                "xp": 100
                            })
                        }
                    }
                )
            return notification
        except Exception as e:
            logger.error(f"❌ Failed to send Django notification to user {user_id}: {e}")
            return None
