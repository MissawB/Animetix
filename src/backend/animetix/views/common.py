import logging
from ..containers import get_container
from ..utils import handle_win_achievements

logger = logging.getLogger('animetix')

container = get_container()

# Expose services through the container for all views
# This maintains backward compatibility while using the DI Container
animetix_service = container.catalog_service
blindtest_service = container.blind_test_service
covertest_service = container.cover_test_service
vision_service = container.vision_quest_service
emoji_service = container.emoji_service
paradox_service = container.paradox_service
animinator_service = container.animinator_service
akinetix_service = container.akinetix_service
game_service = container.game_service

# Placeholder for LangChainService logic (now largely moved to domain)
# If a view specifically needs the legacy langchain_service, we point to llm_service
langchain_service = container.llm_service 
