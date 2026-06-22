import logging
from typing import Optional

from core.ports.user_context_port import UserContextPort

logger = logging.getLogger("animetix.adapters.user_context")


class MiddlewareUserContextAdapter(UserContextPort):
    """Resolves the ambient user from the Django request middleware thread-locals.

    Implements :class:`UserContextPort` so the domain layer never imports
    ``animetix.middleware`` directly. The import stays lazy + guarded so the adapter
    is harmless outside a Django request (returns the unauthenticated defaults).
    """

    def get_current_user_id(self) -> Optional[int]:
        try:
            from animetix.middleware import get_current_user_id

            return get_current_user_id()
        except (
            ImportError
        ) as e:  # pragma: no cover - animetix unavailable (pure-core ctx)
            logger.warning(f"User context unavailable: {e}")
            return None

    def get_current_user_tier(self) -> str:
        try:
            from animetix.middleware import get_current_user_tier

            return get_current_user_tier()
        except (
            ImportError
        ) as e:  # pragma: no cover - animetix unavailable (pure-core ctx)
            logger.warning(f"User context unavailable: {e}")
            return "free"
