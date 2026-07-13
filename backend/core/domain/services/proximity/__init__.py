"""Proximité entre œuvres : le graphe de recommandations, pas l'embedding du synopsis."""

from .components import (  # noqa: F401
    BONUS_CAP,
    W_CO_RECO,
    W_DIRECT,
    W_TAGS,
    Components,
    ProximityIndex,
    build_index,
    score,
)
from .service import (  # noqa: F401
    HOT,
    HOT_FLOOR,
    WARM,
    WARM_FLOOR,
    ProximityService,
)
