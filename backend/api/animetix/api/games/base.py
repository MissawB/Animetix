"""Base commune aux vues de jeux CPU.

Les jeux CPU (Akinetix classique, Cover Quest, Blindtest, Emoji, Qui-est-ce…)
sont AllowAny (jouables sans compte, aucune conso Bx/GPU) mais throttlés par
minute via CpuGameThrottle. Ce couple `permission_classes` + `throttle_classes`
était recopié sur ~33 vues ; il vit désormais ici (audit dette 2026-07-19).

NB : réservé aux jeux CPU. Les vues Bx/GPU (paradox, vs_battle, akinetix_rl…)
gardent leur propre `permission_classes = [IsAuthenticated]` — ne PAS les faire
hériter de cette base.
"""

from rest_framework import permissions
from rest_framework.views import APIView

from animetix.api.throttles import CpuGameThrottle


class CpuGameAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [CpuGameThrottle]
