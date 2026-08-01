from unittest.mock import MagicMock

import pytest
from adapters.persistence.django_tracker_repository_adapter import (
    DjangoTrackerRepositoryAdapter,
)
from animetix.models import MangaTrackerLink, MediaItem, TrackerConnection
from core.domain.services.manga_tracker_service import MangaTrackerService
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


@pytest.fixture
def svc(db):
    user = User.objects.create_user(username="svc", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="One Punch-Man"
    )
    TrackerConnection.objects.create(user=user, tracker="anilist", token="tok")
    anilist = MagicMock()
    anilist.search.return_value = [
        {"remote_id": "30013", "title": "One Punch-Man", "chapters": 200}
    ]
    anilist.read_progress.return_value = 164
    anilist.write_progress.return_value = True
    service = MangaTrackerService(
        repository=DjangoTrackerRepositoryAdapter(),
        adapters={"anilist": anilist, "myanimelist": MagicMock()},
    )
    return service, anilist, user, manga


def test_suggest_creates_a_suggested_link_without_pushing(svc):
    service, anilist, user, _manga = svc

    links = service.suggest(user, "suwayomi:1:809")

    assert len(links) == 1
    assert links[0].status == "suggested"
    assert links[0].remote_id == "30013"
    assert links[0].remote_title == "One Punch-Man"
    anilist.write_progress.assert_not_called()


def test_a_suggested_link_never_pushes(svc):
    service, anilist, user, _manga = svc
    service.suggest(user, "suwayomi:1:809")

    results = service.push(user, "suwayomi:1:809", 5)

    anilist.write_progress.assert_not_called()
    assert results == {}


def test_confirm_reads_and_stores_the_remote_progress(svc):
    service, anilist, user, _manga = svc
    service.suggest(user, "suwayomi:1:809")

    link = service.confirm(user, "suwayomi:1:809", "anilist", "30013")

    assert link.status == "confirmed"
    assert link.remote_progress == 164
    anilist.read_progress.assert_called_once_with("30013", token="tok")


def test_push_never_lowers_the_remote_counter(svc):
    service, anilist, user, _manga = svc
    service.suggest(user, "suwayomi:1:809")
    service.confirm(user, "suwayomi:1:809", "anilist", "30013")

    service.push(user, "suwayomi:1:809", 3)

    anilist.write_progress.assert_not_called()


def test_push_sends_and_updates_when_ahead(svc):
    service, anilist, user, manga = svc
    service.suggest(user, "suwayomi:1:809")
    service.confirm(user, "suwayomi:1:809", "anilist", "30013")

    results = service.push(user, "suwayomi:1:809", 165)

    anilist.write_progress.assert_called_once_with("30013", 165, token="tok")
    assert results["anilist"]["success"] is True
    link = MangaTrackerLink.objects.get(user=user, manga=manga, tracker="anilist")
    assert link.remote_progress == 165


def test_push_is_skipped_when_the_remote_progress_is_unknown(svc):
    service, anilist, user, _manga = svc
    service.suggest(user, "suwayomi:1:809")
    anilist.read_progress.return_value = None
    service.confirm(user, "suwayomi:1:809", "anilist", "30013")
    anilist.read_progress.reset_mock()

    service.push(user, "suwayomi:1:809", 165)

    # On retente la lecture, mais on n'écrit pas à l'aveugle.
    anilist.read_progress.assert_called_once()
    anilist.write_progress.assert_not_called()


def test_unlink_removes_the_link(svc):
    service, _anilist, user, manga = svc
    service.suggest(user, "suwayomi:1:809")

    assert service.unlink(user, "suwayomi:1:809", "anilist") is True
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 0


def test_unknown_manga_yields_nothing(svc):
    service, _anilist, user, _manga = svc
    assert service.suggest(user, "suwayomi:1:absent") == []
    assert service.push(user, "suwayomi:1:absent", 5) == {}


def test_list_links_returns_only_this_manga_s_links(svc):
    service, _anilist, user, manga = svc
    other_manga = MediaItem.objects.create(
        external_id="suwayomi:1:810", media_type="Manga", title="Berserk"
    )
    service.suggest(user, "suwayomi:1:809")
    MangaTrackerLink.objects.create(
        user=user,
        manga=other_manga,
        tracker="myanimelist",
        remote_id="2",
        remote_title="Berserk",
    )

    links = service.list_links(user, "suwayomi:1:809")

    assert len(links) == 1
    assert links[0].manga_id == manga.id


def test_list_all_links_returns_every_link_for_the_user(svc):
    service, _anilist, user, _manga = svc
    other_manga = MediaItem.objects.create(
        external_id="suwayomi:1:810", media_type="Manga", title="Berserk"
    )
    service.suggest(user, "suwayomi:1:809")
    MangaTrackerLink.objects.create(
        user=user,
        manga=other_manga,
        tracker="myanimelist",
        remote_id="2",
        remote_title="Berserk",
    )

    links = service.list_all_links(user)

    assert len(links) == 2


def test_connected_trackers_lists_only_trackers_with_a_connection(svc):
    service, _anilist, user, _manga = svc

    assert service.connected_trackers(user) == ["anilist"]

    other_user = User.objects.create_user(username="nolink", password="pw")
    assert service.connected_trackers(other_user) == []


@pytest.mark.django_db
def test_push_isolates_a_failing_tracker_from_the_others():
    """Une panne (levée d'exception) sur un tracker ne doit ni interrompre
    la poussée des autres, ni faire disparaître leurs résultats du dict
    renvoyé. Les adaptateurs réels ne sont pas censés lever (ils renvoient
    False/None), mais c'est une défense en profondeur : avant ce chantier,
    chaque tracker avait son propre garde-fou.
    """
    user = User.objects.create_user(username="two-trackers", password="pw")
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:811", media_type="Manga", title="Vagabond"
    )
    TrackerConnection.objects.create(user=user, tracker="anilist", token="tok-a")
    TrackerConnection.objects.create(user=user, tracker="myanimelist", token="tok-m")
    MangaTrackerLink.objects.create(
        user=user,
        manga=manga,
        tracker="anilist",
        remote_id="1",
        remote_title="Vagabond",
        remote_progress=1,
        status="confirmed",
    )
    MangaTrackerLink.objects.create(
        user=user,
        manga=manga,
        tracker="myanimelist",
        remote_id="2",
        remote_title="Vagabond",
        remote_progress=1,
        status="confirmed",
    )

    anilist = MagicMock()
    anilist.write_progress.side_effect = RuntimeError("AniList timeout")
    myanimelist = MagicMock()
    myanimelist.write_progress.return_value = True

    service = MangaTrackerService(
        repository=DjangoTrackerRepositoryAdapter(),
        adapters={"anilist": anilist, "myanimelist": myanimelist},
    )

    results = service.push(user, "suwayomi:1:811", 5)

    myanimelist.write_progress.assert_called_once_with("2", 5, token="tok-m")
    assert results["anilist"]["success"] is False
    assert results["myanimelist"]["success"] is True
