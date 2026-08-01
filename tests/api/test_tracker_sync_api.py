from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from animetix.models import MediaItem, TrackerConnection
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
def mock_tracker_adapters():
    anilist_mock = MagicMock()
    anilist_mock.write_progress.return_value = True
    mal_mock = MagicMock()
    mal_mock.write_progress.return_value = True

    container = get_container()
    container.persistence.anilist_adapter.override(anilist_mock)
    container.persistence.myanimelist_adapter.override(mal_mock)
    yield {"anilist": anilist_mock, "myanimelist": mal_mock}
    container.persistence.anilist_adapter.reset_last_overriding()
    container.persistence.myanimelist_adapter.reset_last_overriding()


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
def test_manga_chapter_sync(authenticated_client, mock_tracker_adapters):
    from animetix.models import MangaTrackerLink

    # Created so the sync endpoint can resolve media_id "12345"; the row itself
    # is looked up by id, not via a local variable.
    manga = MediaItem.objects.create(
        external_id="12345",
        media_type="Manga",
        title="Monster",
        metadata={"id": "12345", "idMal": 12345},
    )

    # Set up active connections plus CONFIRMED links so the service actually
    # pushes: an unconfirmed link (or none at all) pushes nothing by design.
    user = User.objects.get(username="testuser")
    TrackerConnection.objects.create(
        user=user, tracker="anilist", username="anilist_user", token="anilist-token"
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", username="mal_user", token="mal-token"
    )
    MangaTrackerLink.objects.create(
        user=user,
        manga=manga,
        tracker="anilist",
        remote_id="12345",
        remote_title="Monster",
        remote_progress=1,
        status="confirmed",
    )
    MangaTrackerLink.objects.create(
        user=user,
        manga=manga,
        tracker="myanimelist",
        remote_id="12345",
        remote_title="Monster",
        remote_progress=1,
        status="confirmed",
    )

    url = reverse(
        "api_manga_chapter_sync", kwargs={"media_id": "12345", "chapter_number": "10"}
    )
    res = authenticated_client.post(url)
    assert res.status_code == 200
    assert res.data["success"] is True
    assert res.data["results"]["anilist"]["success"] is True
    assert res.data["results"]["myanimelist"]["success"] is True
    mock_tracker_adapters["anilist"].write_progress.assert_called_once()
    mock_tracker_adapters["myanimelist"].write_progress.assert_called_once()


@pytest.mark.django_db
def test_manga_chapter_sync_auto_transitions(authenticated_client):
    from animetix.models import FavoriteManga, MangaChapter

    manga = MediaItem.objects.create(
        external_id="sync_manga_1",
        media_type="Manga",
        title="Sync Manga",
    )
    user = User.objects.get(username="testuser")

    # Create Favorite record
    fav = FavoriteManga.objects.create(
        user=user, manga=manga, status="plan_to_read", last_read_chapter=0.0
    )

    # Add chapters: 1.0, 2.0, 3.0
    MangaChapter.objects.create(manga=manga, number=1.0)
    MangaChapter.objects.create(manga=manga, number=2.0)
    MangaChapter.objects.create(manga=manga, number=3.0)

    url = reverse(
        "api_manga_chapter_sync",
        kwargs={"media_id": "sync_manga_1", "chapter_number": "1.0"},
    )
    res = authenticated_client.post(url)
    assert res.status_code == 200

    # Verify transition from plan_to_read -> reading (since chapters 2.0, 3.0 remain)
    fav.refresh_from_db()
    assert fav.last_read_chapter == 1.0
    assert fav.status == "reading"

    # Now read chapter 3.0 (the last one)
    url_last = reverse(
        "api_manga_chapter_sync",
        kwargs={"media_id": "sync_manga_1", "chapter_number": "3.0"},
    )
    res_last = authenticated_client.post(url_last)
    assert res_last.status_code == 200

    # Verify transition from reading -> completed (since no chapters > 3.0 exist)
    fav.refresh_from_db()
    assert fav.last_read_chapter == 3.0
    assert fav.status == "completed"


@pytest.mark.django_db
def test_sync_pushes_nothing_without_a_confirmed_link(authenticated_client):
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.get(username="testuser")
    MediaItem.objects.create(
        external_id="no_link_manga", media_type="Manga", title="Sans liaison"
    )
    TrackerConnection.objects.create(user=user, tracker="anilist", token="tok")

    url = reverse(
        "api_manga_chapter_sync",
        kwargs={"media_id": "no_link_manga", "chapter_number": "5"},
    )
    res = authenticated_client.post(url)

    assert res.status_code == 200
    assert res.data["success"] is True
    assert res.data.get("results", {}) == {}
