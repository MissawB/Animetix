"""Core API views, split by domain.

Star re-exports preserve the public surface of the former monolithic
``core.py`` (``api_views`` star-imports this package, and URLs resolve the
view classes through it). Tests patch the domain submodules directly.
"""

from .accounts import *  # noqa: F401, F403
from .config import *  # noqa: F401, F403
from .manga import *  # noqa: F401, F403
from .media import *  # noqa: F401, F403
from .suwayomi import *  # noqa: F401, F403
