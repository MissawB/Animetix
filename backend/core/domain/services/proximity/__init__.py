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
from .service import HOT, WARM, ProximityService  # noqa: F401
