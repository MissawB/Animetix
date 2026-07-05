"""Throttles à deux vitesses.

Historique : les seuls rates étaient des caps journaliers (anon 100/day,
user 1000/day) — inefficaces contre les rafales, et si agressifs sur les jeux
CPU qu'ils étaient désactivés (`throttle_classes = []`), supprimant TOUTE
protection. On ajoute des limites par minute et un throttle dédié aux jeux CPU.
"""

from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)


class BurstAnonRateThrottle(AnonRateThrottle):
    """Plafond anti-rafale par minute pour les anonymes (en plus du cap /day)."""

    scope = "anon_burst"


class BurstUserRateThrottle(UserRateThrottle):
    """Plafond anti-rafale par minute pour les authentifiés (en plus du /day)."""

    scope = "user_burst"


class CpuGameThrottle(ScopedRateThrottle):
    """Throttle par minute pour les jeux CPU AllowAny.

    Protège du flood sans jamais appliquer le cap journalier global (qui coupait
    des parties en cours). Utilise l'IP pour les anonymes, l'utilisateur sinon.
    """

    scope = "cpu_game"

    def __init__(self):
        # ScopedRateThrottle lit self.scope depuis view.throttle_scope ; ici on
        # fixe le scope sur la classe pour l'utiliser sans view.throttle_scope.
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
