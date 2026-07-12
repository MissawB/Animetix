"""The leaderboard ranks by the deepest climb, not by total damage: damage follows
from the climb, and ranking on damage alone would reward grinding tier 1."""

import importlib
import types
from datetime import timedelta

import pytest
from animetix.models import BossParticipation, GlobalBoss
from animetix.serializers import BossParticipationSerializer
from django.contrib.auth.models import User
from django.utils import timezone

_migration = importlib.import_module(
    "animetix.migrations.0051_bossparticipation_best_tier_and_more"
)


@pytest.mark.django_db
def test_a_participation_starts_at_tier_zero():
    boss = GlobalBoss.objects.create(
        title="RAID OMEGA",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now(),
    )
    user = User.objects.create_user("kenji")

    participation = BossParticipation.objects.create(user=user, boss=boss)

    assert participation.best_tier == 0
    assert participation.limiter_breaks == 0


@pytest.mark.django_db
def test_the_serializer_exposes_the_climb():
    boss = GlobalBoss.objects.create(
        title="RAID OMEGA",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now(),
    )
    user = User.objects.create_user("kenji")
    participation = BossParticipation.objects.create(
        user=user, boss=boss, points_contributed=4095, best_tier=12, limiter_breaks=1
    )

    data = BossParticipationSerializer(participation).data

    assert data["best_tier"] == 12
    assert data["limiter_breaks"] == 1
    assert data["username"] == "kenji"


@pytest.mark.django_db
def test_retiring_the_legacy_raid_also_expires_it_so_a_new_one_can_spawn():
    """A retired boss must stop satisfying the respawn guard.

    The guard in world_boss.py only skips spawning a fresh boss when a row with
    a future end_date exists -- it never checks is_active. Deactivating a
    legacy boss without also expiring its end_date would leave it blocking the
    weekly spawn for up to a week, with no active boss to fight in the
    meantime.
    """
    legacy_boss = GlobalBoss.objects.create(
        title="OLD RAID",
        secret_title="",
        media_type="Anime",
        total_hp=10000,
        current_hp=10000,
        is_active=True,
        end_date=timezone.now() + timedelta(days=7),
    )
    modern_boss = GlobalBoss.objects.create(
        title="RAID OMEGA",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        is_active=True,
        end_date=timezone.now() + timedelta(days=7),
    )
    apps = types.SimpleNamespace(get_model=lambda app, model: GlobalBoss)

    _migration.retire_the_legacy_raid(apps, None)

    legacy_boss.refresh_from_db()
    modern_boss.refresh_from_db()
    assert legacy_boss.is_active is False
    assert legacy_boss.end_date <= timezone.now()
    assert modern_boss.is_active is True
    assert modern_boss.end_date > timezone.now()
