"""Labs API views, split by domain.

Star re-exports preserve the public surface of the former monolithic
``labs.py`` (``api_views`` star-imports this package, and URLs resolve the
view classes through it). Tests patch the domain submodules directly.
"""

from .audio import *  # noqa: F401, F403
from .dashboards import *  # noqa: F401, F403
from .manga import *  # noqa: F401, F403
from .singularity import *  # noqa: F401, F403
from .spatial import *  # noqa: F401, F403
from .video import *  # noqa: F401, F403
