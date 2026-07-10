from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from animetix.models import FavoriteManga, MangaChapter, MediaItem, Notification
from animetix.tasks.manga_tasks import check_manga_updates_task
from django.contrib.auth.models import User


@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def mock_suwayomi_adapter():
    mock = MagicMock()
    container = get_container()
    container.persistence.suwayomi_adapter.override(mock)
    yield mock
    container.persistence.suwayomi_adapter.reset_last_overriding()


@pytest.mark.django_db
def test_simulated_manga_updates(test_user):
    # 1. Create a non-suwayomi manga and link user to favorites
    manga = MediaItem.objects.create(
        external_id="mock_manga_id", media_type="Manga", title="Mock Manga Series"
    )
    FavoriteManga.objects.create(user=test_user, manga=manga)

    # 2. Add initial chapter 1
    MangaChapter.objects.create(manga=manga, number=1.0, title="Chapter 1")

    # 3. Run updates task
    result = check_manga_updates_task()
    assert "Synced 1 new chapters." in result

    # 4. Verify chapter 2 was created
    assert MangaChapter.objects.filter(manga=manga, number=2.0).exists()

    # 5. Verify notification was created and sent
    notif = Notification.objects.get(user=test_user)
    assert notif.notification_type == "info"
    assert "Mock Manga Series" in notif.message
    assert "2.0" in notif.message
    assert notif.link == "/media/manga/mock_manga_id/2.0/"


@pytest.mark.django_db
def test_suwayomi_manga_updates(test_user, mock_suwayomi_adapter):
    # 1. Create a suwayomi manga and link user
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:123",
        media_type="Manga",
        title="One Piece",
        metadata={"source_id": "1", "suwayomi_id": "123"},
    )
    FavoriteManga.objects.create(user=test_user, manga=manga)

    # 2. Mock Suwayomi get_chapters response
    mock_suwayomi_adapter.get_chapters.return_value = [
        {"id": "ch1_ext", "chapterNumber": 1.0, "name": "Romance Dawn"}
    ]

    # 3. Run task
    result = check_manga_updates_task()
    assert "Synced 1 new chapters." in result

    # 4. Verify chapter 1 was saved in DB
    chapter = MangaChapter.objects.get(manga=manga, number=1.0)
    assert chapter.title == "Romance Dawn"
    assert chapter.external_id == "ch1_ext"

    # 5. Verify notification
    notif = Notification.objects.get(user=test_user)
    assert "One Piece" in notif.message
    assert "1.0" in notif.message
    assert notif.link == "/media/manga/suwayomi:1:123/1.0/"

    # 6. Run again - should not sync any new chapters
    mock_suwayomi_adapter.get_chapters.return_value = [
        {"id": "ch1_ext", "chapterNumber": 1.0, "name": "Romance Dawn"}
    ]
    result = check_manga_updates_task()
    assert "Synced 0 new chapters." in result
