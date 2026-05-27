import logging
import warnings
from .containers import get_container

logger = logging.getLogger('animetix')

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    'Anime': {'Easy': 1000, 'Normal': 500, 'Hard': 200, 'Impossible': 50},
    'Manga': {'Easy': 800, 'Normal': 400, 'Hard': 150, 'Impossible': 30},
    'Character': {'Easy': 500, 'Normal': 250, 'Hard': 100, 'Impossible': 20}
}

def send_notification(user, title, message, notification_type='info', link=None):
    """
    Deprecated bridge for sending notifications.
    Use container.notification_port().send(...) instead.
    """
    warnings.warn("send_notification is deprecated, use container.notification_port()", DeprecationWarning)
    container = get_container()
    return container.notification_port().send(
        user_id=user.id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )

def check_achievements(user, action_type, context=None):
    """
    Deprecated bridge for checking achievements.
    Use container.achievement_service().check_and_unlock(...) instead.
    """
    warnings.warn("check_achievements is deprecated, use achievement_service()", DeprecationWarning)
    from core.domain.entities.achievement import GameEvent
    
    container = get_container()
    context = context or {}
    event = GameEvent(
        user_id=user.id, game_mode=context.get('game_mode', 'unknown'), media_type=context.get('media_type', 'unknown'),
        was_won=(action_type == 'win'), is_daily=context.get('is_daily', False), is_ranked=context.get('is_ranked', False),
        attempts=context.get('attempts', 0), streak=getattr(user.profile, 'current_streak', 0),
        total_wins=getattr(user.profile, 'total_wins', 0), total_games=getattr(user.profile, 'total_games', 0), 
        item_rarity=context.get('item_rarity', 'Common')
    )
    
    return container.achievement_service().check_and_unlock(event)

class AnimetixService:
    """
    DEPRECATED Legacy Service Bridge.
    Directly use the DI Container (get_container()) for all domain services.
    """
    def __init__(self):
        warnings.warn("AnimetixService is deprecated, use get_container() directly", DeprecationWarning)
        self._container = get_container()

    @property
    def catalog_service(self): return self._container.catalog_service
    
    def load_data(self, media_type): return self.catalog_service().load_data(media_type)
    
    @property
    def blind_test_service(self): return self._container.blind_test_service()
    @property
    def cover_test_service(self): return self._container.cover_test_service()
    @property
    def vision_quest_service(self): return self._container.vision_quest_service()
    @property
    def emoji_service(self): return self._container.emoji_service()
    @property
    def paradox_service(self): return self._container.paradox_service()
    @property
    def animinator_service(self): return self._container.animinator_service()
    @property
    def akinetix_service(self): return self._container.akinetix_service()
    @property
    def game_service(self): return self._container.game_service()
    @property
    def llm_service(self): return self._container.llm_service()
    @property
    def fusion_service(self): return self._container.fusion_service()
    @property
    def studio_transform_service(self): return self._container.studio_transform_service()
    @property
    def manga_flow_service(self): return self._container.manga_flow_service()
    @property
    def soundscape_service(self): return self._container.soundscape_service()
    @property
    def spatial_computing_service(self): return self._container.spatial_computing_service()
    @property
    def vision_service(self): return self._container.vision_service()
    @property
    def video_quest_service(self): return self._container.video_quest_service()
    @property
    def rag_service(self): return self._container.rag_service()
    @property
    def voice_cloning_service(self): return self._container.voice_cloning_service()
    @property
    def notification_port(self): return self._container.notification_port()
    @property
    def achievement_service(self): return self._container.achievement_service()
