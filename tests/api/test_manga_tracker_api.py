from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from animetix.models import MangaTrackerLink, MediaItem, TrackerConnection
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def linked(db):
    client = APIClient()
    user = User.objects.create_user(username="linker", password="pw")
    client.force_authenticate(user=user)
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="One Punch-Man"
    )
    TrackerConnection.objects.create(user=user, tracker="anilist", token="tok")

    adapter = MagicMock()
    adapter.search.return_value = [
        {"remote_id": "30013", "title": "One Punch-Man", "chapters": 200}
    ]
    adapter.read_progress.return_value = 164
    adapter.write_progress.return_value = True
    container = get_container()
    container.persistence.anilist_adapter.override(adapter)
    yield client, user, manga, adapter
    container.persistence.anilist_adapter.reset_last_overriding()


@pytest.mark.django_db
def test_trackers_endpoint_requires_authentication(api_client):
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"})
    assert api_client.get(url).status_code == 403


@pytest.mark.django_db
def test_get_returns_204_for_a_manga_absent_from_the_catalog(linked):
    client, *_ = linked
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:nope"})
    assert client.get(url).status_code == 204


@pytest.mark.django_db
def test_get_suggests_and_persists_the_link(linked):
    client, user, manga, adapter = linked
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"})

    payload = client.get(url).data

    assert payload["links"][0]["tracker"] == "anilist"
    assert payload["links"][0]["status"] == "suggested"
    assert payload["links"][0]["remote_title"] == "One Punch-Man"
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 1

    # Deuxième appel : la proposition est servie depuis la base, pas re-cherchée.
    adapter.search.reset_mock()
    client.get(url)
    adapter.search.assert_not_called()


@pytest.mark.django_db
def test_link_confirms_and_reads_remote_progress(linked):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    url = reverse("api_manga_trackers_link", kwargs={"media_id": "suwayomi:1:809"})
    res = client.post(url, {"tracker": "anilist", "remote_id": "30013"}, format="json")

    assert res.status_code == 200
    assert res.data["status"] == "confirmed"
    assert res.data["remote_progress"] == 164


@pytest.mark.django_db
def test_search_returns_candidates(linked):
    client, *_ = linked
    url = reverse("api_manga_trackers_search", kwargs={"media_id": "suwayomi:1:809"})

    res = client.post(url, {"tracker": "anilist", "query": "one punch"}, format="json")

    assert res.status_code == 200
    assert res.data["results"][0]["remote_id"] == "30013"


@pytest.mark.django_db
def test_unlink_removes_the_link(linked):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    url = reverse(
        "api_manga_trackers_unlink",
        kwargs={"media_id": "suwayomi:1:809", "tracker": "anilist"},
    )
    assert client.delete(url).status_code == 200
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 0


@pytest.mark.django_db
def test_profile_links_lists_every_link(linked):
    client, *_ = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    res = client.get(reverse("api_tracker_links"))

    assert res.status_code == 200
    assert res.data[0]["manga_title"] == "One Punch-Man"
    assert res.data[0]["tracker"] == "anilist"
