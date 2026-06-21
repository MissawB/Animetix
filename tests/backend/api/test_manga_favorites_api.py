from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from animetix.models import FavoriteManga, MediaItem
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    client = APIClient()
    user = User.objects.create_user(username="testuser", password="password")
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def mock_suwayomi_adapter():
    mock = MagicMock()
    container = get_container()

    # Override DI singleton
    container.persistence.suwayomi_adapter.override(mock)
    yield mock
    # Reset override after test
    container.persistence.suwayomi_adapter.reset_override()


@pytest.mark.django_db
def test_favorite_toggle_get_unauthenticated(api_client):
    url = reverse("api_manga_favorite_toggle", kwargs={"media_id": "suwayomi:1:123"})
    res = api_client.get(url)
    assert res.status_code == 403


@pytest.mark.django_db
def test_favorite_toggle_get_authenticated(authenticated_client):
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:123", media_type="Manga", title="One Piece"
    )
    url = reverse("api_manga_favorite_toggle", kwargs={"media_id": "suwayomi:1:123"})

    # 1. Not favorited yet
    res = authenticated_client.get(url)
    assert res.status_code == 200
    assert res.data["is_favorite"] is False

    # 2. Favorited
    user = User.objects.get(username="testuser")
    FavoriteManga.objects.create(user=user, manga=manga)
    res = authenticated_client.get(url)
    assert res.status_code == 200
    assert res.data["is_favorite"] is True


@pytest.mark.django_db
def test_favorite_toggle_post_auto_import(authenticated_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.get_manga_details.return_value = {
        "id": 123,
        "title": "One Piece",
        "description": "Pirates!",
        "thumbnailUrl": "http://localhost:4567/thumb.png",
        "author": "Oda",
        "artist": "Oda",
        "status": "Ongoing",
    }

    mock_service = MagicMock()
    container = get_container()
    container.core.manga_service.override(mock_service)

    try:
        url = reverse(
            "api_manga_favorite_toggle", kwargs={"media_id": "suwayomi:1:123"}
        )
        res = authenticated_client.post(
            url, {"source_id": "1", "suwayomi_manga_id": "123"}, format="json"
        )

        assert res.status_code == 200
        assert res.data["is_favorite"] is True

        # Verify DB item and favorite association
        assert MediaItem.objects.filter(external_id="suwayomi:1:123").exists()
        assert FavoriteManga.objects.filter(
            manga__external_id="suwayomi:1:123"
        ).exists()
    finally:
        container.core.manga_service.reset_override()


@pytest.mark.django_db
def test_favorite_toggle_post_toggle_off(authenticated_client):
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:123", media_type="Manga", title="One Piece"
    )

    url = reverse("api_manga_favorite_toggle", kwargs={"media_id": "suwayomi:1:123"})

    # Toggle ON
    res = authenticated_client.post(url)
    assert res.status_code == 200
    assert res.data["is_favorite"] is True

    # Toggle OFF
    res = authenticated_client.post(url)
    assert res.status_code == 200
    assert res.data["is_favorite"] is False
    assert not FavoriteManga.objects.filter(manga=manga).exists()


@pytest.mark.django_db
def test_favorite_list_view(authenticated_client):
    manga1 = MediaItem.objects.create(
        external_id="manga1", media_type="Manga", title="Manga One"
    )
    MediaItem.objects.create(
        external_id="manga2", media_type="Manga", title="Manga Two"
    )

    user = User.objects.get(username="testuser")
    FavoriteManga.objects.create(user=user, manga=manga1)

    url = reverse("api_favorite_manga_list")
    res = authenticated_client.get(url)

    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["id"] == "manga1"
    assert res.data[0]["title"] == "Manga One"
