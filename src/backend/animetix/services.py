import logging
from django.conf import settings
from .containers import get_container

logger = logging.getLogger('animetix')

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    'Anime': {'Easy': 1000, 'Normal': 500, 'Hard': 200, 'Impossible': 50},
    'Manga': {'Easy': 800, 'Normal': 400, 'Hard': 150, 'Impossible': 30},
    'Character': {'Easy': 500, 'Normal': 250, 'Hard': 100, 'Impossible': 20}
}

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
        channel_layer = get_channel_layer()
        for ach in newly_unlocked:
            async_to_sync(channel_layer.group_send)(
                f"user_notifications_{user.id}",
                {
                    "type": "send_notification",
                    "data": {
                        "type": "achievement_unlocked",
                        "achievement": {
                            "name": ach.name,
                            "icon": ach.icon,
                            "xp": ach.xp_reward
                        }
                    }
                }
            )
            
    return newly_unlocked

# Legacy class for structural integrity during transition (optional, could be removed)
# class AnimetixService: ...
