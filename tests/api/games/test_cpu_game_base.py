# -*- coding: utf-8 -*-
"""Contrat de la base CpuGameAPIView (dedup audit dette 2026-07-19).

Les ~33 vues de jeux CPU héritaient chacune du couple AllowAny +
CpuGameThrottle recopié ; elles héritent désormais de CpuGameAPIView. On
verrouille (a) le contrat de la base et (b) qu'une vue migrée en hérite bien —
et que les vues Bx/GPU (IsAuthenticated) ne l'ont PAS adopté par erreur.
"""

from animetix.api.games.base import CpuGameAPIView
from animetix.api.throttles import CpuGameThrottle
from rest_framework import permissions
from rest_framework.views import APIView


def test_base_carries_allowany_and_cpu_throttle():
    assert issubclass(CpuGameAPIView, APIView)
    assert CpuGameAPIView.permission_classes == [permissions.AllowAny]
    assert CpuGameAPIView.throttle_classes == [CpuGameThrottle]


def test_a_migrated_cpu_view_inherits_the_contract():
    from animetix.api.games.classic import ClassicGameStateView

    assert issubclass(ClassicGameStateView, CpuGameAPIView)
    # Inherited, not redeclared.
    assert "permission_classes" not in vars(ClassicGameStateView)
    assert "throttle_classes" not in vars(ClassicGameStateView)
    view = ClassicGameStateView()
    assert [type(p) for p in view.get_permissions()] == [permissions.AllowAny]
    assert [type(t) for t in view.get_throttles()] == [CpuGameThrottle]


def test_auth_required_world_boss_view_did_not_adopt_the_cpu_base():
    # WorldBossAnswerView is IsAuthenticated (Bx run) — must stay off the base.
    from animetix.api.games.world_boss import WorldBossAnswerView

    assert not issubclass(WorldBossAnswerView, CpuGameAPIView)
    assert WorldBossAnswerView.permission_classes == [permissions.IsAuthenticated]
