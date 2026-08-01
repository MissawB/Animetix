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
