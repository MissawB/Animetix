from abc import ABC, abstractmethod
from typing import Optional


class UserContextPort(ABC):
    """Port exposing the *ambient* request-scoped user identity to the domain.

    The hexagonal core must not reach into the Django request/middleware layer to
    discover "who is calling". When an explicit ``user_id``/``tier`` is not threaded
    through a call, a service may consult this port to obtain the current request's
    user. The concrete adapter (infra) is responsible for resolving it (e.g. from a
    middleware thread-local); the core only depends on this abstraction.
    """

    @abstractmethod
    def get_current_user_id(self) -> Optional[int]:
        """Return the current request's user id, or ``None`` if unauthenticated/out of request scope."""

    @abstractmethod
    def get_current_user_tier(self) -> str:
        """Return the current request's tier (e.g. ``"free"``, ``"pro"``); defaults to ``"free"``."""
