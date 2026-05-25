import logging
from ..containers import get_container
from animetix.api.dependencies import get_session_service
from ..services import AnimetixService

logger = logging.getLogger('animetix')

def handle_win_achievements(request, unlocked_achievements):
    """Wrapper for GameSessionService.handle_win_achievements."""
    get_session_service(request).handle_win_achievements(unlocked_achievements)

container = get_container()

# Expose services through the container for all views
# This maintains backward compatibility and fixed naming mismatches
animetix_service = AnimetixService()
blindtest_service = container.blind_test_service()
covertest_service = container.cover_test_service()
vision_service = container.vision_service()
emoji_service = container.emoji_service()
paradox_service = container.paradox_service()
animinator_service = container.animinator_service()
akinetix_service = container.akinetix_service()
vs_battle_service = container.vs_battle_service()
game_service = container.game_service()
langchain_service = container.llm_service()
