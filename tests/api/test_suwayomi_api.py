import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix.containers import get_container
from animetix.models import MediaItem
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


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
    container.persistence.suwayomi_adapter.reset_last_overriding()


@pytest.mark.django_db
def test_suwayomi_sources_view(api_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.get_sources.return_value = [
        {"id": "1", "name": "MangaDex", "lang": "en"}
    ]
    url = reverse("api_suwayomi_sources")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data == [{"id": "1", "name": "MangaDex", "lang": "en"}]
    mock_suwayomi_adapter.get_sources.assert_called_once()


@pytest.mark.django_db
def test_suwayomi_search_view(api_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.search_manga.return_value = [
        {"id": "123", "title": "One Piece", "thumbnailUrl": "thumb"}
    ]
    url = reverse("api_suwayomi_search")
    response = api_client.get(url, {"source_id": "1", "q": "One Piece"})
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["title"] == "One Piece"
    mock_suwayomi_adapter.search_manga.assert_called_once_with("1", "One Piece")


@pytest.mark.django_db
def test_suwayomi_import_view(authenticated_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.get_manga_details.return_value = {
        "id": 123,
        "title": "One Piece",
        "description": "Pirates!",
        "thumbnailUrl": "http://localhost:4567/thumb.png",
        "author": "Oda",
        "artist": "Oda",
        "status": "Ongoing",
    }

    # mock get_chapters as well to avoid calling real suwayomi during import's chapter sync
    mock_suwayomi_adapter.get_chapters.return_value = []

    url = reverse("api_suwayomi_import")
    response = authenticated_client.post(
        url, {"source_id": "1", "suwayomi_manga_id": "123"}
    )
    assert response.status_code == 200
    assert response.data["success"] is True

    # Verify DB item was created
    media_item = MediaItem.objects.get(external_id="suwayomi:1:123")
    assert media_item.title == "One Piece"
    assert media_item.metadata["author"] == "Oda"
    assert "/api/v1/media/Manga/suwayomi-image/?page_url=" in media_item.image_url


@pytest.mark.django_db
@patch("animetix.api.core.suwayomi.safe_http_request")
def test_suwayomi_image_proxy(mock_safe_req, api_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_image_bytes"
    mock_response.headers = {"Content-Type": "image/png"}
    mock_safe_req.return_value = mock_response

    encoded_url = base64.b64encode(b"http://127.0.0.1:4567/thumb.png").decode("utf-8")
    url = f"{reverse('api_suwayomi_image_proxy')}?page_url={encoded_url}"
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.content == b"fake_image_bytes"
    assert response["Content-Type"] == "image/png"
    # Ensure safe_http_request was called with correct target URL
    mock_safe_req.assert_called_once_with(
        "GET", "http://127.0.0.1:4567/thumb.png", headers={}, timeout=15
    )


@pytest.mark.django_db
def test_suwayomi_extensions_list_view(authenticated_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.get_extensions.return_value = [
        {
            "pkgName": "com.mangadex",
            "name": "MangaDex",
            "versionName": "1.4.15",
            "isInstalled": True,
            "hasUpdate": False,
            "lang": "en",
        }
    ]
    url = reverse("api_suwayomi_extensions")
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data[0]["pkgName"] == "com.mangadex"
    assert response.data[0]["name"] == "MangaDex"
    mock_suwayomi_adapter.get_extensions.assert_called_once()


@pytest.mark.django_db
def test_suwayomi_extensions_list_view_unauthenticated(
    api_client, mock_suwayomi_adapter
):
    """Listing extensions is a read-only GET on a public page (/explore/tachidesk/),
    so anonymous users must be able to load it — like sources and search. Only
    the mutating action/import endpoints require authentication."""
    mock_suwayomi_adapter.get_extensions.return_value = [
        {"pkgName": "com.mangadex", "name": "MangaDex", "isInstalled": True}
    ]
    url = reverse("api_suwayomi_extensions")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data[0]["pkgName"] == "com.mangadex"
    mock_suwayomi_adapter.get_extensions.assert_called_once()


@pytest.mark.django_db
def test_suwayomi_extensions_action_view(authenticated_client, mock_suwayomi_adapter):
    mock_suwayomi_adapter.update_extensions.return_value = [
        {
            "pkgName": "com.mangadex",
            "name": "MangaDex",
            "isInstalled": True,
            "hasUpdate": False,
        }
    ]
    url = reverse("api_suwayomi_extensions_action")

    # 1. Success case: install
    response = authenticated_client.post(
        url, {"ids": ["com.mangadex"], "action": "install"}, format="json"
    )
    assert response.status_code == 200
    assert response.data[0]["pkgName"] == "com.mangadex"
    mock_suwayomi_adapter.update_extensions.assert_called_once_with(
        ["com.mangadex"], "install"
    )

    # 2. Missing parameter case
    response = authenticated_client.post(url, {"ids": ["com.mangadex"]}, format="json")
    assert response.status_code == 400

    # 3. Invalid action case
    response = authenticated_client.post(
        url, {"ids": ["com.mangadex"], "action": "invalid"}, format="json"
    )
    assert response.status_code == 400
