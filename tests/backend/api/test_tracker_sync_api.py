import pytest
from animetix.models import MediaItem, TrackerConnection
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


@pytest.mark.django_db
def test_tracker_list_empty(authenticated_client):
    url = reverse("api_tracker_connections")
    res = authenticated_client.get(url)
    assert res.status_code == 200
    assert len(res.data) == 0


@pytest.mark.django_db
def test_tracker_link_and_list(authenticated_client):
    link_url = reverse("api_tracker_link")
    list_url = reverse("api_tracker_connections")

    # Link MAL
    res = authenticated_client.post(
        link_url,
        {"tracker": "myanimelist", "username": "mal_user", "token": "mal-token"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["success"] is True

    # Link AniList
    res = authenticated_client.post(
        link_url,
        {"tracker": "anilist", "username": "anilist_user", "token": "anilist-token"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["success"] is True

    # List connections
    res = authenticated_client.get(list_url)
    assert res.status_code == 200
    assert len(res.data) == 2
    trackers = {item["tracker"]: item["username"] for item in res.data}
    assert trackers["myanimelist"] == "mal_user"
    assert trackers["anilist"] == "anilist_user"


@pytest.mark.django_db
def test_tracker_unlink(authenticated_client):
    link_url = reverse("api_tracker_link")
    unlink_url = reverse("api_tracker_unlink")
    list_url = reverse("api_tracker_connections")

    # Link MAL
    authenticated_client.post(
        link_url,
        {"tracker": "myanimelist", "username": "mal_user", "token": "mal-token"},
        format="json",
    )

    # Unlink MAL
    res = authenticated_client.post(
        unlink_url, {"tracker": "myanimelist"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["success"] is True

    # List connections (should be empty)
    res = authenticated_client.get(list_url)
    assert len(res.data) == 0


@pytest.mark.django_db
def test_manga_chapter_sync(authenticated_client):
    # Created so the sync endpoint can resolve media_id "12345"; the row itself
    # is looked up by id, not via a local variable.
    MediaItem.objects.create(
        external_id="12345",
        media_type="Manga",
        title="Monster",
        metadata={"id": "12345", "idMal": 12345},
    )

    # Set up active connections with mock tokens that trigger simulated successes
    user = User.objects.get(username="testuser")
    TrackerConnection.objects.create(
        user=user, tracker="anilist", username="anilist_user", token="mock-token"
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", username="mal_user", token="mock-token"
    )

    url = reverse(
        "api_manga_chapter_sync", kwargs={"media_id": "12345", "chapter_number": "10"}
    )
    res = authenticated_client.post(url)
    assert res.status_code == 200
    assert res.data["success"] is True
    assert res.data["results"]["anilist"]["success"] is True
    assert res.data["results"]["myanimelist"]["success"] is True
