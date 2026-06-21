from datetime import timedelta

import pytest
from animetix.models import GlobalBoss
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def active_boss(db):
    return GlobalBoss.objects.create(
        title="Test Boss",
        secret_title="One Piece",
        media_type="anime",
        total_hp=1000,
        current_hp=1000,
        end_date=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db
def test_active_boss_view(api_client, active_boss):
    url = reverse("api_world_boss_active")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["title"] == "Test Boss"


@pytest.mark.django_db
def test_boss_attack_correct(api_client, user, active_boss):
    api_client.force_authenticate(user=user)
    url = reverse("api_world_boss_attack")
    data = {"boss_id": active_boss.id, "guess": "One Piece"}
    response = api_client.post(url, data)
    assert response.status_code == 200
    assert response.data["is_correct"] is True
    assert response.data["damage_dealt"] == 100

    active_boss.refresh_from_db()
    assert active_boss.current_hp == 900


@pytest.mark.django_db
def test_boss_attack_incorrect(api_client, user, active_boss):
    api_client.force_authenticate(user=user)
    url = reverse("api_world_boss_attack")
    data = {"boss_id": active_boss.id, "guess": "Naruto"}
    response = api_client.post(url, data)
    assert response.status_code == 200
    assert response.data["is_correct"] is False
    assert response.data["damage_dealt"] == 0
