import pytest
from animetix.models import MangaTrackerLink, MediaItem
from django.contrib.auth.models import User
from django.db import IntegrityError


@pytest.mark.django_db
def test_link_is_unique_per_user_manga_and_tracker():
    user = User.objects.create_user(username="reader", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="One Punch-Man"
    )
    MangaTrackerLink.objects.create(
        user=user, manga=manga, tracker="anilist", remote_id="21", remote_title="OPM"
    )

    with pytest.raises(IntegrityError):
        MangaTrackerLink.objects.create(
            user=user, manga=manga, tracker="anilist", remote_id="99", remote_title="X"
        )


@pytest.mark.django_db
def test_link_defaults_are_suggested_and_unknown_progress():
    user = User.objects.create_user(username="reader2", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:810", media_type="Manga", title="Berserk"
    )
    link = MangaTrackerLink.objects.create(
        user=user,
        manga=manga,
        tracker="myanimelist",
        remote_id="2",
        remote_title="Berserk",
    )

    assert link.status == "suggested"
    assert link.remote_progress is None

    manga.delete()
    assert MangaTrackerLink.objects.count() == 0
