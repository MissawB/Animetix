"""The leaderboard ranks by the deepest climb, not by total damage: damage follows
from the climb, and ranking on damage alone would reward grinding tier 1."""

import pytest
from animetix.models import BossParticipation, GlobalBoss
from animetix.serializers import BossParticipationSerializer
from django.contrib.auth.models import User
from django.utils import timezone


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
