import pytest
from animetix.models import MangaChapter, MangaReadingProgress, MediaItem
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
