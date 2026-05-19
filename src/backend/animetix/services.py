import logging
from django.conf import settings
from .containers import get_container
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger('animetix')

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    'Anime': {'Easy': 1000, 'Normal': 500, 'Hard': 200, 'Impossible': 50},
    'Manga': {'Easy': 800, 'Normal': 400, 'Hard': 150, 'Impossible': 30},
    'Character': {'Easy': 500, 'Normal': 250, 'Hard': 100, 'Impossible': 20}
}

def send_notification(user, title, message, notification_type='info', link=None):
    """
    Crée une notification en base de données et l'envoie en temps réel via WebSockets.
    """
    from .models import Notification
    
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
                # Pour le toast de succès spécifique
                "achievement": {
                    "name": title.replace("Succès Débloqué !", "").strip() or title,
                    "icon": "🏆",
                    "xp": 100 # Valeur par défaut
                }
            }
        }
    )
    return notification

def check_achievements(user, action_type, context=None):
    """
    Infrastructure helper to check for achievements and notify user via WebSockets.
    Bridge between Core Domain and Django Channels.
    """
    from core.domain.entities.achievement import GameEvent
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    container = get_container()
    context = context or {}
    event = GameEvent(
        user_id=user.id, game_mode=context.get('game_mode', 'unknown'), media_type=context.get('media_type', 'unknown'),
        was_won=(action_type == 'win'), is_daily=context.get('is_daily', False), is_ranked=context.get('is_ranked', False),
        attempts=context.get('attempts', 0), streak=user.profile.current_streak,
        total_wins=user.profile.total_wins, total_games=user.profile.total_games, item_rarity=context.get('item_rarity', 'Common')
    )
    
    newly_unlocked = container.achievement_listener.on_game_finished(event)
    
    # --- NOTIFICATION TEMPS RÉEL (WebSockets) ---
    if newly_unlocked:
        for ach in newly_unlocked:
            send_notification(
                user=user,
                title="Succès Débloqué !",
                message=f"Félicitations ! Vous avez débloqué le succès '{ach.name}' (+{ach.xp_reward} XP).",
                notification_type='achievement',
                link='/achievements/'
            )
            
    return newly_unlocked

class AnimetixService:
    """
    Legacy Service Bridge.
    Uses the DI Container internally to provide access to all domain services.
    Maintains structural integrity for code not yet fully migrated to Hexagonal Architecture.
    """
    def __init__(self):
        self._container = get_container()

    @property
    def catalog_service(self): return self._container.catalog_service
    
    def load_data(self, media_type): return self.catalog_service.load_data(media_type)
    
    @property
    def blind_test_service(self): return self._container.blind_test_service
    @property
    def cover_test_service(self): return self._container.cover_test_service
    @property
    def vision_quest_service(self): return self._container.vision_quest_service
    @property
    def emoji_service(self): return self._container.emoji_service
    @property
    def paradox_service(self): return self._container.paradox_service
    @property
    def animinator_service(self): return self._container.animinator_service
    @property
    def akinetix_service(self): return self._container.akinetix_service
    @property
    def game_service(self): return self._container.game_service
    @property
    def llm_service(self): return self._container.llm_service
    @property
    def fusion_service(self): return self._container.fusion_service
    @property
    def studio_transform_service(self): return self._container.studio_transform_service
    @property
    def manga_flow_service(self): return self._container.manga_flow_service
    @property
    def soundscape_service(self): return self._container.soundscape_service
    @property
    def spatial_computing_service(self): return self._container.spatial_computing_service
    @property
    def vision_service(self): return self._container.vision_service
    @property
    def video_quest_service(self): return self._container.video_quest_service
    @property
    def rag_service(self): return self._container.rag_service

