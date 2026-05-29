from animetix_project.logging_config import get_logger
from ..containers import get_container
from animetix.api.dependencies import get_session_service

logger = get_logger('animetix.' + __name__)

def handle_win_achievements(request, unlocked_achievements):
    """Wrapper for GameSessionService.handle_win_achievements."""
    get_session_service(request).handle_win_achievements(unlocked_achievements)

class LazyServiceProxy:
    """Proxy évaluant dynamiquement le singleton du conteneur à chaque appel de méthode ou propriété."""
    def __init__(self, provider_name: str):
        self._provider_name = provider_name

    def _resolve(self):
        container = get_container()
        provider = getattr(container, self._provider_name)
        return provider() # Évalue et renvoie le singleton instancié

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)

container = get_container()

# Expose services through lazy proxies to maintain dynamic dependency resolution at runtime.
# This prevents eager loading of heavy adapters/models during Django view imports.
blindtest_service = LazyServiceProxy('blind_test_service')
covertest_service = LazyServiceProxy('cover_test_service')
vision_service = LazyServiceProxy('vision_service')
emoji_service = LazyServiceProxy('emoji_service')
paradox_service = LazyServiceProxy('paradox_service')
animinator_service = LazyServiceProxy('animinator_service')
akinetix_service = LazyServiceProxy('akinetix_service')
vs_battle_service = LazyServiceProxy('vs_battle_service')
game_service = LazyServiceProxy('game_service')
langchain_service = LazyServiceProxy('llm_service')

