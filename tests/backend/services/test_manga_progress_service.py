from unittest.mock import MagicMock

import pytest
from adapters.persistence.django_manga_progress_repository_adapter import (
    DjangoMangaProgressRepositoryAdapter,
)
from animetix.models import (
    FavoriteManga,
    MangaChapter,
    MangaPage,
    MangaReadingProgress,
    MediaItem,
)
from core.domain.services.manga_progress_service import MangaProgressService
from django.contrib.auth.models import User
from django.db import IntegrityError


@pytest.mark.django_db
def test_progress_is_unique_per_user_and_chapter():
    user = User.objects.create_user(username="reader", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="One Punch-Man"
    )
    chapter = MangaChapter.objects.create(manga=manga, number=164.2)

    MangaReadingProgress.objects.create(user=user, chapter=chapter, last_page_read=11)

    with pytest.raises(IntegrityError):
        MangaReadingProgress.objects.create(user=user, chapter=chapter)


@pytest.mark.django_db
def test_progress_defaults_and_cascade():
    user = User.objects.create_user(username="reader2", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:810", media_type="Manga", title="Berserk"
    )
    chapter = MangaChapter.objects.create(manga=manga, number=1.0)

    progress = MangaReadingProgress.objects.create(user=user, chapter=chapter)
    assert progress.last_page_read == 0
    assert progress.is_read is False

    chapter.delete()
    assert MangaReadingProgress.objects.count() == 0


@pytest.fixture
def service_fixtures(db):
    user = User.objects.create_user(username="svc_reader", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="OPM"
    )
    c1 = MangaChapter.objects.create(manga=manga, number=1.0, external_id="1")
    c2 = MangaChapter.objects.create(manga=manga, number=2.0, external_id="2")
    for i in range(1, 6):
        MangaPage.objects.create(chapter=c1, number=i, image_url=f"http://h/{i}.jpg")
    suwayomi = MagicMock()
    service = MangaProgressService(
        progress_repository=DjangoMangaProgressRepositoryAdapter(),
        suwayomi_adapter=suwayomi,
    )
    return service, suwayomi, user, manga, c1, c2


def test_last_page_read_never_regresses(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=False
    )
    result = service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=1, is_read=False
    )

    assert result["last_page_read"] == 4


def test_marking_unread_resets_the_cursor(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.record_progress(user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True)
    result = service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=0, is_read=False
    )

    assert result["last_page_read"] == 0
    assert result["is_read"] is False


def test_completion_updates_favorite_and_flags_it_once(service_fixtures):
    service, _suwayomi, user, manga, _c1, _c2 = service_fixtures

    first = service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True
    )
    second = service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True
    )

    assert first["chapter_completed"] is True
    # Déjà lu : la vue ne doit pas repousser une seconde fois vers les trackers.
    assert second["chapter_completed"] is False
    assert FavoriteManga.objects.get(user=user, manga=manga).last_read_chapter == 1.0


def test_resume_prefers_the_chapter_in_progress(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.record_progress(user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True)
    service.record_progress(
        user, "suwayomi:1:809", 2.0, last_page_read=2, is_read=False
    )

    payload = service.get_manga_progress(user, "suwayomi:1:809")

    assert payload["resume"] == {"chapter_number": 2.0, "last_page_read": 2}
    assert payload["read_count"] == 1
    assert payload["total_count"] == 2


def test_resume_falls_back_to_next_unread_chapter(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.record_progress(user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True)

    payload = service.get_manga_progress(user, "suwayomi:1:809")

    assert payload["resume"] == {"chapter_number": 2.0, "last_page_read": 0}


def test_resume_is_null_when_everything_is_read(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.set_read(user, "suwayomi:1:809", [1.0, 2.0], is_read=True)

    payload = service.get_manga_progress(user, "suwayomi:1:809")
    assert payload["resume"] is None


def test_unknown_manga_returns_none(service_fixtures):
    service, _suwayomi, user, _manga, _c1, _c2 = service_fixtures
    assert service.get_manga_progress(user, "suwayomi:1:does-not-exist") is None


def test_suwayomi_mirror_is_called_with_the_chapter_external_id(service_fixtures):
    service, suwayomi, user, _manga, _c1, _c2 = service_fixtures

    service.record_progress(user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=True)

    suwayomi.update_chapters_read_state.assert_called_once_with(
        ["1"], is_read=True, last_page_read=4
    )


def test_mirror_failure_does_not_break_the_write(service_fixtures):
    from adapters.persistence.suwayomi_adapter import SuwayomiUnavailableError

    service, suwayomi, user, _manga, _c1, _c2 = service_fixtures
    suwayomi.update_chapters_read_state.side_effect = SuwayomiUnavailableError("down")

    result = service.record_progress(
        user, "suwayomi:1:809", 1.0, last_page_read=4, is_read=False
    )

    assert result["last_page_read"] == 4
