"""Coverage-focused tests for animetix.api.core view module.

Pattern: build a MagicMock container, patch ``get_container`` in the
``animetix.api.core.*`` domain submodule that defines the view under test,
then drive the views via ``RequestFactory`` + ``force_authenticate``
with ``permission_classes`` neutralised (matching the existing test_cognition
style). DB-backed views use the real ORM under ``@pytest.mark.django_db``.

These complement (do not replace) tests/api/test_explore.py.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix.api.core import (
    ConfigView,
    CurrentUserView,
    CustomConfigDataView,
    FavoriteMangaListView,
    FavoriteMangaToggleView,
    LoginView,
    LogoutView,
    MangaChapterDetailView,
    MangaChapterListView,
    MangaChapterSyncView,
    MediaDetailView,
    MediaSearchView,
    RegisterView,
    SuwayomiExtensionsActionView,
    SuwayomiExtensionsListView,
    SuwayomiImportView,
    SuwayomiSearchView,
    SuwayomiSourcesView,
    TrackerConnectionLinkView,
    TrackerConnectionListView,
    TrackerConnectionUnlinkView,
    TransparencyDataView,
    image_proxy_view,
    suwayomi_image_proxy,
)
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.test import force_authenticate

GET_CONTAINER_MEDIA = "animetix.api.core.media.get_container"
GET_CONTAINER_MANGA = "animetix.api.core.manga.get_container"
GET_CONTAINER_SUWAYOMI = "animetix.api.core.suwayomi.get_container"


@pytest.fixture
def factory():
    return RequestFactory()


def _drive(view_cls, request, user=None, **view_kwargs):
    """Neutralise permissions, authenticate, and dispatch a view."""
    with patch.object(view_cls, "permission_classes", []):
        view = view_cls.as_view()
        if user is not None:
            force_authenticate(request, user=user)
        return view(request, **view_kwargs)


# --------------------------------------------------------------------------- #
# image_proxy_view (function-based)
# --------------------------------------------------------------------------- #
def test_image_proxy_missing_params(factory):
    request = factory.get("/img/")
    response = image_proxy_view(request)
    assert response.status_code == 400


def test_image_proxy_bad_base64(factory):
    request = factory.get("/img/", {"url": "@@@not-base64@@@", "sig": "x"})
    response = image_proxy_view(request)
    assert response.status_code == 400


def test_image_proxy_invalid_signature(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "deadbeef"})
    with patch("animetix.api.core.media.verify_proxy_signature", return_value=False):
        response = image_proxy_view(request)
    assert response.status_code == 403


def test_image_proxy_cache_hit(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
    ):
        mock_cache.get.return_value = {
            "content": b"BYTES",
            "content_type": "image/png",
        }
        response = image_proxy_view(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"


def test_image_proxy_success_fetch(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    upstream = MagicMock(
        status_code=200, content=b"IMG", headers={"Content-Type": "image/png"}
    )
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch("animetix.api.core.media.safe_http_request", return_value=upstream),
        patch("animetix.api.core.media.validate_file_size", return_value=True),
        patch("animetix.api.core.media.validate_file_mime_type", return_value=True),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 200
    assert response.content == b"IMG"


def test_image_proxy_too_large(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    upstream = MagicMock(status_code=200, content=b"IMG", headers={})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch("animetix.api.core.media.safe_http_request", return_value=upstream),
        patch("animetix.api.core.media.validate_file_size", return_value=False),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 413


def test_image_proxy_wrong_mime(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    upstream = MagicMock(status_code=200, content=b"IMG", headers={})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch("animetix.api.core.media.safe_http_request", return_value=upstream),
        patch("animetix.api.core.media.validate_file_size", return_value=True),
        patch("animetix.api.core.media.validate_file_mime_type", return_value=False),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 403


def test_image_proxy_unsafe_request(factory):
    encoded = base64.b64encode(b"http://example.com/a.png").decode()
    request = factory.get("/img/", {"url": encoded, "sig": "good"})
    with (
        patch("animetix.api.core.media.verify_proxy_signature", return_value=True),
        patch("animetix.api.core.media.cache") as mock_cache,
        patch(
            "animetix.api.core.media.safe_http_request",
            side_effect=ValueError("blocked"),
        ),
    ):
        mock_cache.get.return_value = None
        response = image_proxy_view(request)
    assert response.status_code == 403


# --------------------------------------------------------------------------- #
# MediaSearchView
# --------------------------------------------------------------------------- #
def test_media_search_empty_returns_empty_list(factory):
    request = factory.get("/search/")
    response = _drive(MediaSearchView, request)
    assert response.status_code == 200
    assert response.data == []


def test_media_search_success(factory):
    request = factory.get("/search/", {"q": "naruto", "media_type": "Anime"})
    container = MagicMock()
    # The view calls the provider: container.core.catalog_service().search_items(...)
    container.core.catalog_service.return_value.search_items.return_value = [
        {"id": "1", "title": "Naruto"}
    ]
    with patch(GET_CONTAINER_MEDIA, return_value=container):
        view = MediaSearchView()
        view.guardrail_service = MagicMock()
        view.guardrail_service.validate_input.return_value = {"is_safe": True}
        view.usage_port = MagicMock()
        # call the bound get directly to control injected services
        from rest_framework.parsers import JSONParser
        from rest_framework.request import Request

        drf_request = Request(request, parsers=[JSONParser()])
        response = view.get(drf_request)
    assert response.status_code == 200
    assert response.data[0]["id"] == "1"


def test_media_item_serializer_exposes_type_and_image_url():
    """The search UI reads item.type and item.image_url; the serializer must
    emit both (without them: no thumbnails, empty type tabs, and detail links
    resolving to /media/undefined/{id}/)."""
    from animetix.serializers import MediaItemSerializer

    raw = {
        "id": "5",
        "title": "Naruto",
        "media_type": "Anime",
        "image": "http://cdn/naruto.jpg",
    }
    data = MediaItemSerializer(raw).data
    assert data["type"] == "Anime"
    assert data["image_url"] == "http://cdn/naruto.jpg"
    # Backward compat: legacy `image` key stays populated.
    assert data["image"] == "http://cdn/naruto.jpg"


def test_media_search_unsafe_query(factory):
    request = factory.get("/search/", {"q": "evil"})
    view = MediaSearchView()
    view.guardrail_service = MagicMock()
    view.guardrail_service.validate_input.return_value = {
        "is_safe": False,
        "reason": "blocked",
    }
    view.usage_port = MagicMock()
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    drf_request = Request(request, parsers=[JSONParser()])
    response = view.get(drf_request)
    assert response.status_code == 400
    assert response.data["error"] == "blocked"


def test_media_search_post_unauthenticated(factory):
    request = factory.post("/search/")
    response = _drive(MediaSearchView, request)
    # AllowAny + manual is_authenticated check -> 401
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# GameSessionView covered indirectly; Config / CurrentUser / CustomConfig
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_config_view_anonymous(factory):
    # ConfigView reads SiteConfiguration (maintenance mode) from the DB.
    request = factory.get("/config/")
    response = _drive(ConfigView, request)
    assert response.status_code == 200
    assert response.data["user"]["is_authenticated"] is False
    assert response.data["theme"] == "auto"


@pytest.mark.django_db
def test_config_view_authenticated(factory):
    user = User.objects.create_user(username="cfg", password="pw")
    request = factory.get("/config/")
    response = _drive(ConfigView, request, user=user)
    assert response.status_code == 200
    assert response.data["user"]["username"] == "cfg"
    assert response.data["user"]["rank"] == "Bronze 🥉"


def test_current_user_unauthenticated(factory):
    request = factory.get("/auth/me/")
    response = _drive(CurrentUserView, request)
    assert response.status_code == 401


@pytest.mark.django_db
def test_current_user_authenticated(factory):
    user = User.objects.create_user(username="me", password="pw")
    request = factory.get("/auth/me/")
    response = _drive(CurrentUserView, request, user=user)
    assert response.status_code == 200
    assert response.data["user"]["username"] == "me"


def test_custom_config_guest(factory):
    request = factory.get("/custom-config/")
    response = _drive(CustomConfigDataView, request)
    assert response.status_code == 200
    assert response.data["status"] == "guest"


@pytest.mark.django_db
def test_custom_config_authenticated(factory):
    user = User.objects.create_user(username="cc", password="pw")
    request = factory.get("/custom-config/")
    response = _drive(CustomConfigDataView, request, user=user)
    assert response.status_code == 200
    assert response.data["status"] == "stub"


# --------------------------------------------------------------------------- #
# Auth: Login / Logout / Register
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_login_success(factory):
    User.objects.create_user(username="lo", password="secret123")
    request = factory.post("/auth/login/", {"username": "lo", "password": "secret123"})
    with patch("animetix.api.core.accounts.login"):
        response = _drive(LoginView, request)
    assert response.status_code == 200
    assert response.data["success"] is True


@pytest.mark.django_db
def test_login_invalid(factory):
    request = factory.post("/auth/login/", {"username": "x", "password": "bad"})
    response = _drive(LoginView, request)
    assert response.status_code == 401
    assert response.data["success"] is False


@pytest.mark.django_db
def test_logout(factory):
    user = User.objects.create_user(username="out", password="pw")
    request = factory.post("/auth/logout/")
    with patch("animetix.api.core.accounts.logout"):
        response = _drive(LogoutView, request, user=user)
    assert response.status_code == 200
    assert response.data["success"] is True


def test_register_missing_fields(factory):
    request = factory.post("/auth/register/", {"username": "only"})
    response = _drive(RegisterView, request)
    assert response.status_code == 400
    assert response.data["error"] == "Missing fields"


@pytest.mark.django_db
def test_register_duplicate(factory):
    User.objects.create_user(username="dup", password="pw", email="d@x.com")
    request = factory.post(
        "/auth/register/",
        {"username": "dup", "password": "pw", "email": "d@x.com"},
    )
    response = _drive(RegisterView, request)
    assert response.status_code == 400
    assert "exists" in response.data["error"]


@pytest.mark.django_db
def test_register_success(factory):
    request = factory.post(
        "/auth/register/",
        {"username": "newbie", "password": "pw12345", "email": "n@x.com"},
    )
    with patch("animetix.api.core.accounts.login"):
        response = _drive(RegisterView, request)
    assert response.status_code == 200
    assert response.data["success"] is True
    assert User.objects.filter(username="newbie").exists()


# --------------------------------------------------------------------------- #
# MediaDetailView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_media_detail_from_sql(factory):
    from animetix.models import MediaItem

    MediaItem.objects.create(external_id="sql-1", media_type="Anime", title="From SQL")
    request = factory.get("/media/Anime/sql-1/")
    response = _drive(MediaDetailView, request, media_type="Anime", item_id="sql-1")
    assert response.status_code == 200
    assert response.data["id"] == "sql-1"


@pytest.mark.django_db
def test_media_detail_catalog_fallback(factory):
    request = factory.get("/media/Anime/cat-9/")
    container = MagicMock()
    container.core.catalog_service.return_value.load_data.return_value = {
        "db": [
            {
                "id": "cat-9",
                "title": "Catalog Hit",
                "graph_nodes": {
                    "studios": ["MAPPA"],
                    "author": "Someone",
                    "related_items": [],
                },
            }
        ]
    }
    with patch(GET_CONTAINER_MEDIA, return_value=container):
        response = _drive(MediaDetailView, request, media_type="Anime", item_id="cat-9")
    assert response.status_code == 200
    assert response.data["studios"] == ["MAPPA"]


@pytest.mark.django_db
def test_media_detail_not_found(factory):
    request = factory.get("/media/Anime/missing/")
    container = MagicMock()
    container.core.catalog_service.load_data.return_value = {"db": []}
    with patch(GET_CONTAINER_MEDIA, return_value=container):
        response = _drive(
            MediaDetailView, request, media_type="Anime", item_id="missing"
        )
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# TransparencyDataView (ORM aggregation)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_transparency_data(factory):
    request = factory.get("/transparency/")
    response = _drive(TransparencyDataView, request)
    assert response.status_code == 200
    assert response.data["status"] == "synchronized"
    assert "global_metrics" in response.data


# --------------------------------------------------------------------------- #
# Manga chapters (service-backed; serializer patched to avoid deep ORM)
# --------------------------------------------------------------------------- #
def test_manga_chapter_list(factory):
    request = factory.get("/media/Manga/m1/chapters/")
    container = MagicMock()
    container.core.manga_service.return_value.get_chapters.return_value = []
    with (
        patch(GET_CONTAINER_MANGA, return_value=container),
        patch("animetix.api.core.manga.MangaChapterSerializer") as mock_ser,
    ):
        mock_ser.return_value.data = [{"number": 1.0}]
        response = _drive(MangaChapterListView, request, media_id="m1")
    assert response.status_code == 200
    assert response.data == [{"number": 1.0}]


def test_manga_chapter_detail_found(factory):
    request = factory.get("/media/Manga/m1/chapters/1/")
    container = MagicMock()
    container.core.manga_service.return_value.get_chapter_details.return_value = (
        object()
    )
    with (
        patch(GET_CONTAINER_MANGA, return_value=container),
        patch("animetix.api.core.manga.MangaChapterSerializer") as mock_ser,
    ):
        mock_ser.return_value.data = {"number": 1.0}
        response = _drive(
            MangaChapterDetailView, request, media_id="m1", chapter_number="1"
        )
    assert response.status_code == 200


def test_manga_chapter_detail_not_found(factory):
    request = factory.get("/media/Manga/m1/chapters/99/")
    container = MagicMock()
    container.core.manga_service.return_value.get_chapter_details.return_value = None
    with patch(GET_CONTAINER_MANGA, return_value=container):
        response = _drive(
            MangaChapterDetailView, request, media_id="m1", chapter_number="99"
        )
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# suwayomi_image_proxy (function-based)
# --------------------------------------------------------------------------- #
def test_suwayomi_image_missing_url(factory):
    request = factory.get("/suwayomi-image/")
    response = suwayomi_image_proxy(request)
    assert response.status_code == 400


def test_suwayomi_image_bad_base64(factory):
    request = factory.get("/suwayomi-image/", {"page_url": "@@bad@@"})
    response = suwayomi_image_proxy(request)
    assert response.status_code == 400


def test_suwayomi_image_forbidden_external(factory):
    encoded = base64.b64encode(b"http://evil.example/x.png").decode()
    request = factory.get("/suwayomi-image/", {"page_url": encoded})
    with patch("core.config.settings") as mock_settings:
        mock_settings.SUWAYOMI_URL = "http://suwayomi.local"
        mock_settings.SUWAYOMI_PASSWORD = ""
        response = suwayomi_image_proxy(request)
    assert response.status_code == 403


def test_suwayomi_image_success(factory):
    encoded = base64.b64encode(b"relative/page.png").decode()
    request = factory.get("/suwayomi-image/", {"page_url": encoded})
    upstream = MagicMock(
        status_code=200, content=b"PNG", headers={"Content-Type": "image/png"}
    )
    with (
        patch("core.config.settings") as mock_settings,
        patch("animetix.api.core.suwayomi.safe_http_request", return_value=upstream),
    ):
        mock_settings.SUWAYOMI_URL = "http://suwayomi.local"
        mock_settings.SUWAYOMI_PASSWORD = "secret"
        response = suwayomi_image_proxy(request)
    assert response.status_code == 200
    assert response.content == b"PNG"


# --------------------------------------------------------------------------- #
# Suwayomi adapter-backed views
# --------------------------------------------------------------------------- #
def test_suwayomi_sources_not_configured(factory):
    request = factory.get("/explore/suwayomi/sources/")
    with patch.object(SuwayomiSourcesView, "permission_classes", []):
        view = SuwayomiSourcesView()
        view.suwayomi_adapter = None
        from rest_framework.request import Request

        response = view.get(Request(request))
    assert response.status_code == 500


def test_suwayomi_sources_success(factory):
    request = factory.get("/explore/suwayomi/sources/")
    view = SuwayomiSourcesView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.get_sources.return_value = [{"id": "1"}]
    from rest_framework.request import Request

    response = view.get(Request(request))
    assert response.status_code == 200
    assert response.data == [{"id": "1"}]


def test_suwayomi_search_missing_source(factory):
    request = factory.get("/explore/suwayomi/search/")
    view = SuwayomiSearchView()
    view.suwayomi_adapter = MagicMock()
    from rest_framework.request import Request

    response = view.get(Request(request))
    assert response.status_code == 400


def test_suwayomi_search_success(factory):
    request = factory.get("/explore/suwayomi/search/", {"source_id": "s1", "q": "x"})
    view = SuwayomiSearchView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.search_manga.return_value = [{"id": "m"}]
    from rest_framework.request import Request

    response = view.get(Request(request))
    assert response.status_code == 200
    assert response.data == [{"id": "m"}]


def test_suwayomi_extensions_list_success(factory):
    request = factory.get("/explore/suwayomi/extensions/")
    view = SuwayomiExtensionsListView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.get_extensions.return_value = [{"pkg": "x"}]
    from rest_framework.request import Request

    response = view.get(Request(request))
    assert response.status_code == 200


def test_suwayomi_extensions_list_error(factory):
    request = factory.get("/explore/suwayomi/extensions/")
    view = SuwayomiExtensionsListView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.get_extensions.side_effect = RuntimeError("boom")
    from rest_framework.request import Request

    response = view.get(Request(request))
    assert response.status_code == 500


def test_suwayomi_extensions_action_invalid_params(factory):
    request = factory.post("/extensions/action/", {}, content_type="application/json")
    view = SuwayomiExtensionsActionView()
    view.suwayomi_adapter = MagicMock()
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 400


def test_suwayomi_extensions_action_invalid_action(factory):
    import json

    request = factory.post(
        "/extensions/action/",
        json.dumps({"ids": ["1"], "action": "explode"}),
        content_type="application/json",
    )
    view = SuwayomiExtensionsActionView()
    view.suwayomi_adapter = MagicMock()
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 400


def test_suwayomi_extensions_action_success(factory):
    import json

    request = factory.post(
        "/extensions/action/",
        json.dumps({"ids": ["1"], "action": "install"}),
        content_type="application/json",
    )
    view = SuwayomiExtensionsActionView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.update_extensions.return_value = {"ok": True}
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# SuwayomiImportView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_suwayomi_import_missing_params(factory):
    import json

    request = factory.post("/import/", json.dumps({}), content_type="application/json")
    view = SuwayomiImportView()
    view.suwayomi_adapter = MagicMock()
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 400


@pytest.mark.django_db
def test_suwayomi_import_details_missing(factory):
    import json

    request = factory.post(
        "/import/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    view = SuwayomiImportView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.get_manga_details.return_value = None
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_suwayomi_import_success(factory):
    import json

    request = factory.post(
        "/import/",
        json.dumps({"source_id": "s", "suwayomi_manga_id": "m"}),
        content_type="application/json",
    )
    view = SuwayomiImportView()
    view.suwayomi_adapter = MagicMock()
    view.suwayomi_adapter.get_manga_details.return_value = {
        "title": "Imported",
        "description": "d",
        "thumbnailUrl": "http://thumb/x.png",
    }
    container = MagicMock()
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    with patch(GET_CONTAINER_SUWAYOMI, return_value=container):
        response = view.post(Request(request, parsers=[JSONParser()]))
    assert response.status_code == 200
    assert response.data["success"] is True
    assert response.data["media_item"]["title"] == "Imported"


# --------------------------------------------------------------------------- #
# Tracker connections
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_tracker_list(factory):
    user = User.objects.create_user(username="tl", password="pw")
    request = factory.get("/profile/trackers/")
    response = _drive(TrackerConnectionListView, request, user=user)
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_tracker_link_missing_fields(factory):
    import json

    user = User.objects.create_user(username="tk", password="pw")
    request = factory.post(
        "/profile/trackers/link/",
        json.dumps({"tracker": "anilist"}),
        content_type="application/json",
    )
    response = _drive(TrackerConnectionLinkView, request, user=user)
    assert response.status_code == 400


@pytest.mark.django_db
def test_tracker_link_invalid_type(factory):
    import json

    user = User.objects.create_user(username="tk2", password="pw")
    request = factory.post(
        "/profile/trackers/link/",
        json.dumps({"tracker": "bogus", "username": "u", "token": "t"}),
        content_type="application/json",
    )
    response = _drive(TrackerConnectionLinkView, request, user=user)
    assert response.status_code == 400


@pytest.mark.django_db
def test_tracker_link_success(factory):
    import json

    user = User.objects.create_user(username="tk3", password="pw")
    request = factory.post(
        "/profile/trackers/link/",
        json.dumps({"tracker": "anilist", "username": "u", "token": "t"}),
        content_type="application/json",
    )
    response = _drive(TrackerConnectionLinkView, request, user=user)
    assert response.status_code == 200
    assert response.data["success"] is True


@pytest.mark.django_db
def test_tracker_unlink_missing(factory):
    import json

    user = User.objects.create_user(username="tu", password="pw")
    request = factory.post(
        "/profile/trackers/unlink/",
        json.dumps({}),
        content_type="application/json",
    )
    response = _drive(TrackerConnectionUnlinkView, request, user=user)
    assert response.status_code == 400


@pytest.mark.django_db
def test_tracker_unlink_success(factory):
    import json

    from animetix.models import TrackerConnection

    user = User.objects.create_user(username="tu2", password="pw")
    TrackerConnection.objects.create(user=user, tracker="anilist", token="t")
    request = factory.post(
        "/profile/trackers/unlink/",
        json.dumps({"tracker": "anilist"}),
        content_type="application/json",
    )
    response = _drive(TrackerConnectionUnlinkView, request, user=user)
    assert response.status_code == 200
    assert response.data["deleted"] is True


# --------------------------------------------------------------------------- #
# Favorites
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_favorite_list(factory):
    user = User.objects.create_user(username="fl", password="pw")
    request = factory.get("/media/favorites/")
    response = _drive(FavoriteMangaListView, request, user=user)
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_favorite_toggle_get(factory):
    user = User.objects.create_user(username="ft", password="pw")
    request = factory.get("/media/Manga/x/favorite/")
    response = _drive(FavoriteMangaToggleView, request, user=user, media_id="x")
    assert response.status_code == 200
    assert response.data["is_favorite"] is False


@pytest.mark.django_db
def test_favorite_toggle_add_and_remove(factory):
    from animetix.models import MediaItem

    user = User.objects.create_user(username="ft2", password="pw")
    MediaItem.objects.create(external_id="man-1", media_type="Manga", title="M")

    # First toggle -> favorite added
    request = factory.post(
        "/media/Manga/man-1/favorite/", {}, content_type="application/json"
    )
    response = _drive(FavoriteMangaToggleView, request, user=user, media_id="man-1")
    assert response.status_code == 200
    assert response.data["is_favorite"] is True

    # Second toggle -> removed
    request2 = factory.post(
        "/media/Manga/man-1/favorite/", {}, content_type="application/json"
    )
    response2 = _drive(FavoriteMangaToggleView, request2, user=user, media_id="man-1")
    assert response2.data["is_favorite"] is False


@pytest.mark.django_db
def test_favorite_toggle_missing_manga_no_import_params(factory):
    user = User.objects.create_user(username="ft3", password="pw")
    request = factory.post(
        "/media/Manga/none/favorite/", {}, content_type="application/json"
    )
    response = _drive(FavoriteMangaToggleView, request, user=user, media_id="none")
    assert response.status_code == 400


# --------------------------------------------------------------------------- #
# MangaChapterSyncView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_chapter_sync_manga_not_found(factory):
    user = User.objects.create_user(username="cs", password="pw")
    request = factory.post("/sync/", {}, content_type="application/json")
    response = _drive(
        MangaChapterSyncView, request, user=user, media_id="nope", chapter_number="1"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_chapter_sync_no_trackers(factory):
    from animetix.models import MediaItem

    user = User.objects.create_user(username="cs2", password="pw")
    MediaItem.objects.create(external_id="man-2", media_type="Manga", title="M2")
    request = factory.post("/sync/", {}, content_type="application/json")
    response = _drive(
        MangaChapterSyncView, request, user=user, media_id="man-2", chapter_number="3"
    )
    assert response.status_code == 200
    assert "No trackers" in response.data["message"]


@pytest.mark.django_db
def test_chapter_sync_anilist_simulated(factory):
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="cs3", password="pw")
    MediaItem.objects.create(
        external_id="123", media_type="Manga", title="Numeric", metadata={}
    )
    TrackerConnection.objects.create(
        user=user, tracker="anilist", token="mock-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")
    response = _drive(
        MangaChapterSyncView, request, user=user, media_id="123", chapter_number="5"
    )
    assert response.status_code == 200
    assert response.data["results"]["anilist"]["simulated"] is True


@pytest.mark.django_db
def test_chapter_sync_mal_simulated(factory):
    from animetix.models import MediaItem, TrackerConnection

    user = User.objects.create_user(username="cs4", password="pw")
    MediaItem.objects.create(
        external_id="man-3",
        media_type="Manga",
        title="MalManga",
        metadata={"idMal": 42},
    )
    TrackerConnection.objects.create(
        user=user, tracker="myanimelist", token="test-token", username="u"
    )
    request = factory.post("/sync/", {}, content_type="application/json")
    response = _drive(
        MangaChapterSyncView, request, user=user, media_id="man-3", chapter_number="7"
    )
    assert response.status_code == 200
    assert response.data["results"]["myanimelist"]["simulated"] is True
