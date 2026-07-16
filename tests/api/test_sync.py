import json

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_sync_offline_data_unauthenticated(api_client):
    url = reverse("sync_offline_data")
    response = api_client.post(url, data={}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"error": "Authentication required"}


@pytest.mark.django_db
def test_sync_offline_data_invalid_method(api_client):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_login(user)
    url = reverse("sync_offline_data")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_sync_offline_data_invalid_json(api_client):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_login(user)
    url = reverse("sync_offline_data")
    # Send malformed raw data
    response = api_client.post(
        url, data="malformed{json", content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "Invalid JSON"


@pytest.mark.django_db
def test_sync_offline_data_validation_error(api_client):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_login(user)
    url = reverse("sync_offline_data")

    # Invalid game_mode ("unknown_game_mode")
    payload = [
        {
            "game_mode": "unknown_game_mode",
            "media_type": "Anime",
            "score": 100,
            "attempts": 1,
        }
    ]
    response = api_client.post(
        url, data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.django_db
def test_sync_offline_data_success(api_client):
    user = User.objects.create_user(username="testuser", password="password")
    user.profile.xp = 100
    user.profile.save()

    api_client.force_login(user)
    url = reverse("sync_offline_data")

    # We send 2 games: 1 classic (score 100) and 1 emoji (score 50)
    payload = [
        {"game_mode": "classic", "media_type": "Anime", "score": 100, "attempts": 2},
        {"game_mode": "emoji", "media_type": "Manga", "score": 50, "attempts": 1},
    ]

    # Clear cache before running
    import datetime

    today = datetime.date.today().isoformat()
    cache.delete(f"offline_xp_limit_{user.id}_{today}")

    response = api_client.post(
        url, data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert data["synced_items"] == 1
    assert data["xp_gained"] == 10
    assert data["daily_total"] == 10

    # Check user XP got updated
    user.profile.refresh_from_db()
    assert user.profile.xp == 160


@pytest.mark.django_db
def test_sync_offline_data_daily_cap(api_client):
    user = User.objects.create_user(username="testuser2", password="password")
    user.profile.xp = 100
    user.profile.save()

    api_client.force_login(user)
    url = reverse("sync_offline_data")

    # Force daily limit already reached in cache
    import datetime

    today = datetime.date.today().isoformat()
    cache_key = f"offline_xp_limit_{user.id}_{today}"
    cache.set(cache_key, 200, 3600)

    payload = [
        {"game_mode": "classic", "media_type": "Anime", "score": 100, "attempts": 1}
    ]

    response = api_client.post(
        url, data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        response.json().get("error")
        == "Daily offline XP limit reached. Play online for more!"
    )
