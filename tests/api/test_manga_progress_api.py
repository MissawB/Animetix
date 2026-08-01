import pytest
from animetix.models import MangaChapter, MangaPage, MangaReadingProgress, MediaItem
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def reader(db):
    client = APIClient()
    user = User.objects.create_user(username="progress_reader", password="pw")
    client.force_authenticate(user=user)
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="OPM"
    )
    chapter = MangaChapter.objects.create(manga=manga, number=164.2, external_id="7")
    for i in range(1, 4):
        MangaPage.objects.create(
            chapter=chapter, number=i, image_url=f"http://h/{i}.jpg"
        )
    return client, user, manga, chapter


@pytest.mark.django_db
def test_progress_requires_authentication(api_client):
    url = reverse("api_manga_progress", kwargs={"media_id": "suwayomi:1:809"})
    assert api_client.get(url).status_code == 403


@pytest.mark.django_db
def test_progress_returns_204_for_a_manga_absent_from_the_catalog(reader):
    client, *_ = reader
    url = reverse("api_manga_progress", kwargs={"media_id": "suwayomi:1:unknown"})
    assert client.get(url).status_code == 204


@pytest.mark.django_db
def test_put_then_get_progress_roundtrip(reader):
    client, user, _manga, chapter = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )
    res = client.put(put_url, {"last_page_read": 1, "is_read": False}, format="json")
    assert res.status_code == 200
    assert res.data["last_page_read"] == 1

    get_url = reverse("api_manga_progress", kwargs={"media_id": "suwayomi:1:809"})
    payload = client.get(get_url).data
    assert payload["chapters"][0] == {
        "number": 164.2,
        "is_read": False,
        "last_page_read": 1,
        "page_count": 3,
    }
    assert payload["resume"] == {"chapter_number": 164.2, "last_page_read": 1}
    assert MangaReadingProgress.objects.filter(user=user, chapter=chapter).count() == 1


@pytest.mark.django_db
def test_decimal_chapter_numbers_are_preserved(reader):
    client, _user, _manga, _chapter = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )
    res = client.put(put_url, {"last_page_read": 2, "is_read": False}, format="json")
    assert res.data["number"] == 164.2


@pytest.mark.django_db
def test_put_on_unknown_chapter_returns_404(reader):
    client, *_ = reader
    url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "999"},
    )
    assert (
        client.put(
            url, {"last_page_read": 0, "is_read": False}, format="json"
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_mark_read_in_bulk(reader):
    client, _user, manga, _chapter = reader
    MangaChapter.objects.create(manga=manga, number=165.0, external_id="8")
    url = reverse("api_manga_progress_mark_read", kwargs={"media_id": "suwayomi:1:809"})

    res = client.post(
        url, {"chapter_numbers": [164.2, 165.0], "is_read": True}, format="json"
    )

    assert res.status_code == 200
    assert res.data["updated"] == 2


@pytest.mark.django_db
def test_chapter_completed_pushes_to_trackers_once_on_transition(reader, mocker):
    # Mocked where it is *used* (animetix.api.core.manga), not where it is
    # defined: the view imports it at module level, so patching there is what
    # actually intercepts the call.
    push_mock = mocker.patch("animetix.api.core.manga.push_manga_progress_to_trackers")
    client, *_ = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )

    first = client.put(put_url, {"last_page_read": 2, "is_read": True}, format="json")
    assert first.status_code == 200
    assert push_mock.call_count == 1

    # Same chapter, already read: chapter_completed is only True on the
    # unread->read transition, so a repeat PUT must NOT push again.
    second = client.put(put_url, {"last_page_read": 2, "is_read": True}, format="json")
    assert second.status_code == 200
    assert push_mock.call_count == 1


@pytest.mark.django_db
def test_tracker_push_failure_does_not_break_the_response(reader, mocker):
    mocker.patch(
        "animetix.api.core.manga.push_manga_progress_to_trackers",
        side_effect=RuntimeError("tracker down"),
    )
    client, user, _manga, chapter = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )

    res = client.put(put_url, {"last_page_read": 2, "is_read": True}, format="json")

    assert res.status_code == 200
    assert (
        MangaReadingProgress.objects.get(user=user, chapter=chapter).last_page_read == 2
    )


@pytest.mark.django_db
def test_progress_is_isolated_between_users(reader):
    client, _user, _manga, _chapter = reader
    other_client = APIClient()
    other_user = User.objects.create_user(username="other_reader", password="pw")
    other_client.force_authenticate(user=other_user)

    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )
    client.put(put_url, {"last_page_read": 3, "is_read": False}, format="json")

    get_url = reverse("api_manga_progress", kwargs={"media_id": "suwayomi:1:809"})
    other_payload = other_client.get(get_url).data
    # The second user has never read anything: no last_page_read leaked from
    # the first user's write.
    assert other_payload["chapters"][0]["last_page_read"] == 0
    assert other_payload["resume"] is None

    # The second user's own write must not clobber the first user's progress.
    other_client.put(put_url, {"last_page_read": 1, "is_read": False}, format="json")
    first_payload = client.get(get_url).data
    assert first_payload["chapters"][0]["last_page_read"] == 3


@pytest.mark.django_db
def test_put_with_negative_last_page_read_returns_400(reader):
    client, *_ = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "164.2"},
    )
    res = client.put(put_url, {"last_page_read": -1, "is_read": False}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_put_with_non_numeric_chapter_number_returns_400(reader):
    client, *_ = reader
    put_url = reverse(
        "api_manga_chapter_progress",
        kwargs={"media_id": "suwayomi:1:809", "chapter_number": "not-a-number"},
    )
    res = client.put(put_url, {"last_page_read": 0, "is_read": False}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_mark_read_with_non_numeric_chapter_number_returns_400(reader):
    client, *_ = reader
    url = reverse("api_manga_progress_mark_read", kwargs={"media_id": "suwayomi:1:809"})
    res = client.post(
        url,
        {"chapter_numbers": [164.2, "not-a-number"], "is_read": True},
        format="json",
    )
    assert res.status_code == 400
