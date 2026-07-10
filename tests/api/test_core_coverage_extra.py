"""Extra coverage tests for animetix.api.core targeting branches not covered by
``test_core_coverage.py``.

Same pattern as the sibling file: neutralise permissions, drive views via
``RequestFactory`` + ``force_authenticate``, mock all I/O (services, adapters,
httpx, ``safe_http_request``). No false-green: every test asserts the status
code and, where meaningful, the JSON body / side effects.

Targets the previously-missing line ranges in core.py:
  93-96  (image_proxy generic exception -> 404)
  152-197 (MediaSearchView.post image-search flow)
  215-216 (GameSessionView.get)
  288-289 (RegisterView create_user exception -> 400)
  394-395 (TransparencyData positive_rate branch)
  504-510 (suwayomi_image_proxy non-200 / exception)
  552/583/652/696/703-705 (Suwayomi views: not-configured / exception)
  732-775 (FavoriteMangaToggleView auto-import path)
  910-1069 (MangaChapterSyncView: invalid chapter, anilist/MAL resolution+sync)
"""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from animetix.api.core import (
    FavoriteMangaToggleView,
    GameSessionView,
    MangaChapterSyncView,
    MediaSearchView,
    RegisterView,
    SuwayomiExtensionsActionView,
    SuwayomiExtensionsListView,
    SuwayomiImportView,
    SuwayomiSearchView,
    TransparencyDataView,
    image_proxy_view,
    suwayomi_image_proxy,
)
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.test import force_authenticate

GET_CONTAINER_MEDIA = "animetix.api.core.media.get_container"
GET_CONTAINER_MANGA = "animetix.api.core.manga.get_container"


@pytest.fixture
def factory():
    return RequestFactory()


def _drive(view_cls, request, user=None, **view_kwargs):
    with patch.object(view_cls, "permission_classes", []):
        view = view_cls.as_view()
        if user is not None:
            force_authenticate(request, user=user)
        return view(request, **view_kwargs)


# --------------------------------------------------------------------------- #
# image_proxy_view: generic exception -> 404 (lines 93-96)
# --------------------------------------------------------------------------- #
def test_image_proxy_generic_exception_returns_404(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch(
            "animetix.api.core.media.safe_http_request",
            side_effect=RuntimeError("network boom"),
        ),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 404


def test_image_proxy_non_200_upstream_returns_404(factory):
    """Upstream returns non-200; the success block is skipped -> falls through to 404."""
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    upstream = MagicMock(status_code=500, content=b"", headers={})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch("animetix.api.core.media.safe_http_request", return_value=upstream),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# MediaSearchView.post image-search flow (lines 152-197)
# --------------------------------------------------------------------------- #
def _post_image_view(request, *, quota=True):
    """Instantiate MediaSearchView with mocked injected services and call .post."""
    view = MediaSearchView()
    view.guardrail_service = MagicMock()
    view.usage_port = MagicMock()
    view.usage_port.check_quota.return_value = quota
    drf_request = Request(request, parsers=[MultiPartParser(), JSONParser()])
    return view, drf_request


@pytest.mark.django_db
def test_media_search_post_quota_exceeded(factory):
    user = User.objects.create_user(username="qe", password="pw")
    request = factory.post("/search/")
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request, quota=False)
    response = view.post(drf_request)
    assert response.status_code == 403
    assert "quota" in response.data["error"].lower()


@pytest.mark.django_db
def test_media_search_post_no_image(factory):
    user = User.objects.create_user(username="ni", password="pw")
    request = factory.post("/search/")
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request)
    response = view.post(drf_request)
    assert response.status_code == 400
    assert response.data["error"] == "No image provided"


@pytest.mark.django_db
def test_media_search_post_image_too_large(factory):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = User.objects.create_user(username="big", password="pw")
    img = SimpleUploadedFile("x.png", b"data", content_type="image/png")
    request = factory.post("/search/", {"image": img})
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request)
    with patch("animetix.api.core.media.validate_file_size", return_value=False):
        response = view.post(drf_request)
    assert response.status_code == 413


@pytest.mark.django_db
def test_media_search_post_invalid_mime(factory):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = User.objects.create_user(username="badmime", password="pw")
    img = SimpleUploadedFile("x.png", b"data", content_type="image/png")
    request = factory.post("/search/", {"image": img})
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request)
    with (
        patch("animetix.api.core.media.validate_file_size", return_value=True),
        patch("animetix.api.core.media.validate_file_mime_type", return_value=False),
    ):
        response = view.post(drf_request)
    assert response.status_code == 415


@pytest.mark.django_db
def test_media_search_post_success(factory):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = User.objects.create_user(username="okimg", password="pw")
    img = SimpleUploadedFile("x.png", b"imgbytes", content_type="image/png")
    request = factory.post("/search/", {"image": img})
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request)
    container = MagicMock()
    container.core.cross_modal_search_service.deep_multimodal_search.return_value = [
        {"id": "7", "title": "ByImage"}
    ]
    with (
        patch("animetix.api.core.media.validate_file_size", return_value=True),
        patch("animetix.api.core.media.validate_file_mime_type", return_value=True),
        patch(GET_CONTAINER_MEDIA, return_value=container),
    ):
        response = view.post(drf_request)
    assert response.status_code == 200
    assert response.data[0]["id"] == "7"
    view.usage_port.log_usage.assert_called_once()


@pytest.mark.django_db
def test_media_search_post_exception_returns_500(factory):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = User.objects.create_user(username="exc", password="pw")
    img = SimpleUploadedFile("x.png", b"imgbytes", content_type="image/png")
    request = factory.post("/search/", {"image": img})
    force_authenticate(request, user=user)
    request.user = user
    view, drf_request = _post_image_view(request)
    with patch(
        "animetix.api.core.media.validate_file_size",
        side_effect=RuntimeError("boom"),
    ):
        response = view.post(drf_request)
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# GameSessionView.get (lines 215-216)
# --------------------------------------------------------------------------- #
def test_game_session_get(factory):
    request = factory.get("/game/session/")
    fake_session = {
        "media_type": "Anime",
        "is_ranked": True,
        "is_daily": False,
        "game_over": False,
        "guesses": ["a", "b"],
    }
    with patch(
        "animetix.api.core.accounts.get_session_service", return_value=fake_session
    ):
        response = _drive(GameSessionView, request)
    assert response.status_code == 200
    assert response.data["media_type"] == "Anime"
    assert response.data["guess_count"] == 2


# --------------------------------------------------------------------------- #
# RegisterView create_user exception -> 400 (lines 288-289)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_register_create_user_exception(factory):
    request = factory.post(
        "/auth/register/",
        {"username": "newx", "password": "pw12345", "email": "n@x.com"},
    )
    with patch(
        "animetix.api.core.accounts.User.objects.create_user",
        side_effect=RuntimeError("db down"),
    ):
        response = _drive(RegisterView, request)
    assert response.status_code == 400
    assert "db down" in response.data["error"]


# --------------------------------------------------------------------------- #
# TransparencyData positive_rate branch (lines 394-395)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_transparency_with_feedback(factory):
    from animetix.models import AIFeedback

    # Two feedbacks, one positive -> positive_rate computed branch executed.
    AIFeedback.objects.create(is_positive=True)
    AIFeedback.objects.create(is_positive=False)
    request = factory.get("/transparency/")
    response = _drive(TransparencyDataView, request)
    assert response.status_code == 200
    assert response.data["global_metrics"]["total_feedbacks"] == 2
    assert response.data["global_metrics"]["community_satisfaction"] == 0.5


# --------------------------------------------------------------------------- #
# suwayomi_image_proxy non-200 / exception (lines 504-510)
# --------------------------------------------------------------------------- #
def test_suwayomi_image_non_200(factory):
    encoded = base64.b64encode(b"relative/page.png").decode()
    request = factory.get("/suwayomi-image/", {"page_url": encoded})
    upstream = MagicMock(status_code=404, content=b"", headers={})
    with (
        patch("core.config.settings") as mock_settings,
        patch("animetix.api.core.suwayomi.safe_http_request", return_value=upstream),
    ):
        mock_settings.SUWAYOMI_URL = "http://suwayomi.local"
        mock_settings.SUWAYOMI_PASSWORD = ""
        response = suwayomi_image_proxy(request)
    assert response.status_code == 404


def test_suwayomi_image_exception(factory):
    encoded = base64.b64encode(b"relative/page.png").decode()
    request = factory.get("/suwayomi-image/", {"page_url": encoded})
    with (
        patch("core.config.settings") as mock_settings,
        patch(
            "animetix.api.core.suwayomi.safe_http_request",
            side_effect=RuntimeError("conn refused"),
        ),
    ):
        mock_settings.SUWAYOMI_URL = "http://suwayomi.local"
        mock_settings.SUWAYOMI_PASSWORD = ""
        response = suwayomi_image_proxy(request)
    assert response.status_code == 500


def test_suwayomi_image_absolute_authorized_url(factory):
    """Absolute URL that matches the configured base is allowed through."""
    encoded = base64.b64encode(b"http://suwayomi.local/page.png").decode()
    request = factory.get("/suwayomi-image/", {"page_url": encoded})
    upstream = MagicMock(
        status_code=200, content=b"PNG", headers={"Content-Type": "image/png"}
    )
    with (
        patch("core.config.settings") as mock_settings,
        patch("animetix.api.core.suwayomi.safe_http_request", return_value=upstream),
    ):
        mock_settings.SUWAYOMI_URL = "http://suwayomi.local"
        mock_settings.SUWAYOMI_PASSWORD = "pw"
        response = suwayomi_image_proxy(request)
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# Suwayomi views: not-configured branches (552, 583, 652, 696)
# --------------------------------------------------------------------------- #
def test_suwayomi_search_not_configured(factory):
    request = factory.get("/suwayomi/search/", {"source_id": "s1"})
    view = SuwayomiSearchView()
    view.suwayomi_adapter = None
    response = view.get(Request(request))
    assert response.status_code == 500


@pytest.mark.django_db
def test_suwayomi_import_not_configured(factory):
    request = factory.post(
        "/import/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    view = SuwayomiImportView()
    view.suwayomi_adapter = None
    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 500


def test_suwayomi_extensions_list_not_configured(factory):
    request = factory.get("/extensions/")
    view = SuwayomiExtensionsListView()
    view.suwayomi_adapter = None
    response = view.get(Request(request))
    assert response.status_code == 500


def test_suwayomi_extensions_action_not_configured(factory):
    request = factory.post(
        "/extensions/action/",
        json.dumps({"ids": ["1"], "action": "install"}),
        content_type="application/json",
    )
    view = SuwayomiExtensionsActionView()
    view.suwayomi_adapter = None
    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 500


def test_suwayomi_extensions_action_exception(factory):
    """update_extensions raising -> 500 (lines 703-705)."""
    request = factory.post(
        "/extensions/action/",
        json.dumps({"ids": ["1"], "action": "update"}),
        content_type="application/json",
    )
    view = SuwayomiExtensionsActionView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.update_extensions.side_effect = RuntimeError("boom")
    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# FavoriteMangaToggleView auto-import path (lines 732-775)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_favorite_toggle_autoimport_not_configured(factory):
    user = User.objects.create_user(username="fa1", password="pw")
    request = factory.post(
        "/media/Manga/new-x/favorite/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    container = MagicMock()
    container.persistence.suwayomi_adapter.return_value = None
    with patch(GET_CONTAINER_MANGA, return_value=container):
        force_authenticate(request, user=user)
        with patch.object(FavoriteMangaToggleView, "permission_classes", []):
            view = FavoriteMangaToggleView.as_view()
            response = view(request, media_id="new-x")
    assert response.status_code == 500


@pytest.mark.django_db
def test_favorite_toggle_autoimport_details_missing(factory):
    user = User.objects.create_user(username="fa2", password="pw")
    request = factory.post(
        "/media/Manga/new-y/favorite/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    container = MagicMock()
    adapter = MagicMock()
    adapter.get_manga_details.return_value = None
    container.persistence.suwayomi_adapter.return_value = adapter
    with patch(GET_CONTAINER_MANGA, return_value=container):
        force_authenticate(request, user=user)
        with patch.object(FavoriteMangaToggleView, "permission_classes", []):
            view = FavoriteMangaToggleView.as_view()
            response = view(request, media_id="new-y")
    assert response.status_code == 404


@pytest.mark.django_db
def test_favorite_toggle_autoimport_success(factory):
    from animetix.models import FavoriteManga, MediaItem

    user = User.objects.create_user(username="fa3", password="pw")
    request = factory.post(
        "/media/Manga/new-z/favorite/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    container = MagicMock()
    adapter = MagicMock()
    adapter.get_manga_details.return_value = {
        "title": "Auto Imported",
        "description": "d",
        "thumbnailUrl": "http://thumb/y.png",
        "author": "A",
        "artist": "B",
        "status": "ongoing",
    }
    container.persistence.suwayomi_adapter.return_value = adapter
    with patch(GET_CONTAINER_MANGA, return_value=container):
        force_authenticate(request, user=user)
        with patch.object(FavoriteMangaToggleView, "permission_classes", []):
            view = FavoriteMangaToggleView.as_view()
            response = view(request, media_id="new-z")
    assert response.status_code == 200
    assert response.data["is_favorite"] is True
    # Manga was auto-created and favorited.
    assert MediaItem.objects.filter(external_id="new-z").exists()
    assert FavoriteManga.objects.filter(user=user).count() == 1


# --------------------------------------------------------------------------- #
# MangaChapterSyncView branches (910-1069)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_chapter_sync_invalid_chapter_number(factory):
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv1", password="pw")
    MediaItem.objects.create(external_id="man-iv", media_type="Manga", title="IV")
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="mock-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")
    response = _drive(
        MangaChapterSyncView,
        request,
        user=user,
        media_id="man-iv",
        chapter_number="abc",
    )
    assert response.status_code == 400
    assert "Invalid chapter" in response.data["error"]


@pytest.mark.django_db
def test_chapter_sync_anilist_resolve_by_title(factory):
    """Non-numeric id, no metadata id -> resolves AniList id via GraphQL search,
    then performs a real (mocked) mutation request."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv2", password="pw")
    MediaItem.objects.create(
        external_id="man-al", media_type="Manga", title="AniManga", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    search_resp = MagicMock(status_code=200)
    search_resp.json.return_value = {"data": {"Media": {"id": 555}}}
    mutation_resp = MagicMock(status_code=200)
    mutation_resp.json.return_value = {"data": {}}

    client = MagicMock()
    client.post.side_effect = [search_resp, mutation_resp]
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-al",
            chapter_number="4",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"] == {"success": True}


@pytest.mark.django_db
def test_chapter_sync_anilist_unresolvable(factory):
    """Title search returns no Media -> anilist id unresolved -> error result."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv3", password="pw")
    MediaItem.objects.create(
        external_id="man-no", media_type="Manga", title="Unknown", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    search_resp = MagicMock(status_code=200)
    search_resp.json.return_value = {"data": {"Media": None}}
    client = MagicMock()
    client.post.return_value = search_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-no",
            chapter_number="2",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["success"] is False
    assert "resolve" in response.data["results"]["anilist"]["error"].lower()


@pytest.mark.django_db
def test_chapter_sync_anilist_real_mutation_error(factory):
    """metadata id resolves anilist id; mutation returns non-200 -> error result."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv4", password="pw")
    MediaItem.objects.create(
        external_id="man-meta",
        media_type="Manga",
        title="Meta",
        metadata={"id": "999"},
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    mutation_resp = MagicMock(status_code=400, text="bad request")
    client = MagicMock()
    client.post.return_value = mutation_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-meta",
            chapter_number="6",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["success"] is False
    assert "AniList API error" in response.data["results"]["anilist"]["error"]


@pytest.mark.django_db
def test_chapter_sync_mal_resolve_via_jikan_and_real_update(factory):
    """No mal id in metadata -> resolve via Jikan, then real (mocked) PATCH."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv5", password="pw")
    MediaItem.objects.create(
        external_id="man-mal", media_type="Manga", title="MalT", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    jikan_resp = MagicMock(status_code=200)
    jikan_resp.json.return_value = {"data": [{"mal_id": 321}]}
    patch_resp = MagicMock(status_code=200)

    client = MagicMock()
    client.get.return_value = jikan_resp
    client.patch.return_value = patch_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-mal",
            chapter_number="8",
        )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"] == {"success": True}


@pytest.mark.django_db
def test_chapter_sync_mal_unresolvable(factory):
    """Jikan returns empty -> mal id unresolved -> error result."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv6", password="pw")
    MediaItem.objects.create(
        external_id="man-mn", media_type="Manga", title="NoMal", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    jikan_resp = MagicMock(status_code=200)
    jikan_resp.json.return_value = {"data": []}
    client = MagicMock()
    client.get.return_value = jikan_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-mn",
            chapter_number="3",
        )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"]["success"] is False
    assert "resolve" in response.data["results"]["myanimelist"]["error"].lower()


@pytest.mark.django_db
def test_chapter_sync_anilist_metadata_id_non_int(factory):
    """metadata['id'] is non-numeric -> int() raises -> swallowed (929-930);
    falls back to title search which also yields nothing -> unresolved."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv8", password="pw")
    MediaItem.objects.create(
        external_id="man-bad",
        media_type="Manga",
        title="BadMeta",
        metadata={"id": "not-a-number"},
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    search_resp = MagicMock(status_code=200)
    search_resp.json.return_value = {"data": {"Media": None}}
    client = MagicMock()
    client.post.return_value = search_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-bad",
            chapter_number="1",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["success"] is False


@pytest.mark.django_db
def test_chapter_sync_anilist_search_raises(factory):
    """httpx.Client raising during AniList title search -> except logged (955-956),
    id stays unresolved -> error result."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv9", password="pw")
    MediaItem.objects.create(
        external_id="man-sx", media_type="Manga", title="SearchX", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    with patch("httpx.Client", side_effect=RuntimeError("net down")):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-sx",
            chapter_number="1",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["success"] is False


@pytest.mark.django_db
def test_chapter_sync_anilist_mutation_raises(factory):
    """metadata id resolves anilist id; mutation client raises -> except (1005-1006)."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv10", password="pw")
    MediaItem.objects.create(
        external_id="man-mx",
        media_type="Manga",
        title="MutX",
        metadata={"id": "42"},
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    with patch("httpx.Client", side_effect=RuntimeError("mutation boom")):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-mx",
            chapter_number="2",
        )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["success"] is False
    assert "mutation boom" in response.data["results"]["anilist"]["error"]


@pytest.mark.django_db
def test_chapter_sync_mal_jikan_raises(factory):
    """Jikan client raises -> except logged (1032-1033), mal id unresolved -> error."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv11", password="pw")
    MediaItem.objects.create(
        external_id="man-jx", media_type="Manga", title="JikanX", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    with patch("httpx.Client", side_effect=RuntimeError("jikan down")):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-jx",
            chapter_number="2",
        )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"]["success"] is False
    assert "resolve" in response.data["results"]["myanimelist"]["error"].lower()


@pytest.mark.django_db
def test_chapter_sync_mal_update_raises(factory):
    """mal id from metadata; PATCH client raises -> except (1068-1069)."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv12", password="pw")
    MediaItem.objects.create(
        external_id="man-ux",
        media_type="Manga",
        title="UpdX",
        metadata={"idMal": 55},
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    with patch("httpx.Client", side_effect=RuntimeError("patch boom")):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-ux",
            chapter_number="3",
        )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"]["success"] is False
    assert "patch boom" in response.data["results"]["myanimelist"]["error"]


@pytest.mark.django_db
def test_chapter_sync_mal_real_update_error(factory):
    """mal_id present in metadata; PATCH returns non-200 -> error result."""
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="sv7", password="pw")
    MediaItem.objects.create(
        external_id="man-me",
        media_type="Manga",
        title="MalErr",
        metadata={"mal_id": 77},
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="real-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")

    patch_resp = MagicMock(status_code=403, text="forbidden")
    client = MagicMock()
    client.patch.return_value = patch_resp
    client_cm = MagicMock()
    client_cm.__enter__.return_value = client

    with patch("httpx.Client", return_value=client_cm):
        response = _drive(
            MangaChapterSyncView,
            request,
            user=user,
            media_id="man-me",
            chapter_number="9",
        )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"]["success"] is False
    assert "MAL API error" in response.data["results"]["myanimelist"]["error"]
