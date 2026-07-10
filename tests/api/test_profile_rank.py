"""Regression locks for ``Profile.rank`` (2026-07-10 finding).

The rank ladder lived only on the domain entity (``UserProfile.rank_label``,
zero consumers) while the Django ``Profile`` had no ``rank`` attribute at all:
``ProfileSerializer.rank`` silently serialized to nothing and the
authenticated ``/api/v1/config/`` crashed with an AttributeError (500).
"""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("points", "label"),
    [
        (0, "Bronze 🥉"),
        (499, "Bronze 🥉"),
        (500, "Argent 🥈"),
        (1500, "Or 🥇"),
        (3000, "Platine 💎"),
        (6000, "Diamant 💠"),
        (10000, "Maître de la Data 👑"),
    ],
)
def test_profile_rank_property_follows_domain_ladder(points, label):
    user = User.objects.create_user(username=f"rank_{points}")
    profile = user.profile
    profile.ranked_points = points
    assert profile.rank == label


def test_profile_serializer_exposes_rank():
    from animetix.serializers import ProfileSerializer

    user = User.objects.create_user(username="rank_serializer")
    data = ProfileSerializer(user.profile).data
    assert data["rank"] == "Bronze 🥉"


def test_config_endpoint_authenticated_returns_rank():
    """Regression: this endpoint 500'd (AttributeError) for every
    authenticated user because ``request.user.profile.rank`` did not exist."""
    user = User.objects.create_user(username="rank_config")
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/v1/config/")
    assert resp.status_code == 200
    assert resp.data["user"]["rank"] == "Bronze 🥉"
