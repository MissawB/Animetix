"""Throttles à deux vitesses.

Historique : les seuls rates étaient des caps journaliers (anon 100/day,
user 1000/day) — inefficaces contre les rafales, et si agressifs sur les jeux
CPU qu'ils étaient désactivés (`throttle_classes = []`), supprimant TOUTE
protection. On ajoute des limites par minute et un throttle dédié aux jeux CPU.
"""

from rest_framework.throttling import (
    AnonRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)


class BurstAnonRateThrottle(AnonRateThrottle):
    """Plafond anti-rafale par minute pour les anonymes (en plus du cap /day)."""

    scope = "anon_burst"


class BurstUserRateThrottle(UserRateThrottle):
    """Plafond anti-rafale par minute pour les authentifiés (en plus du /day)."""

    scope = "user_burst"


class CpuGameThrottle(SimpleRateThrottle):
    """Throttle par minute pour les jeux CPU AllowAny.

    Hérite de SimpleRateThrottle (pas ScopedRateThrottle) : ce dernier réécrit
    self.scope depuis view.throttle_scope à chaque requête, ce qui annulerait le
    throttle sur des vues qui ne déclarent pas throttle_scope. On fixe donc le
    scope ici et on identifie par utilisateur (si authentifié) ou par IP.
    """

    scope = "cpu_game"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
