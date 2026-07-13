import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _mk_user(balance):
    from animetix.models import Profile

    User = get_user_model()
    u = User.objects.create_user(username="vr", password="x")
    Profile.objects.filter(user=u).update(wallet_balance=balance)
    return u


def test_video_rag_anonymous_is_403():
    # This project's DEFAULT_AUTHENTICATION_CLASSES (GoogleIdentityAuthentication /
    # DeveloperApiKeyAuthentication, neither of which sets a WWW-Authenticate
    # header) makes IsAuthenticated's permission_denied() fall through DRF's
    # request.authenticators / successful_authenticator check to PermissionDenied
    # (403) rather than NotAuthenticated (401) for anonymous requests. Verified
    # against the existing precedent in test_companion_api.py::
    # test_companion_interact_authenticated_only, which asserts 403 for the same
    # IsAuthenticated + deduct_berrix pattern.
    resp = APIClient().get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 403


def test_video_rag_zero_balance_is_402():
    # `video_temporal` has no writer an ordinary user can reach, so the real
    # service would report the index unavailable against the (empty) test DB.
    # This test is about the *balance* check specifically, so the whole
    # service is overridden with a mock (same pattern as
    # `test_video_rag_happy_path_deducts_and_returns` below) whose
    # `is_available()` is truthy by default -- letting the request reach
    # `deduct_berrix`.
    from unittest.mock import MagicMock

    from animetix.containers import get_container

    u = _mk_user(0)
    mock_service = MagicMock()
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    try:
        c = APIClient()
        c.force_authenticate(u)
        resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    finally:
        container.agentic.video_rag_service.reset_last_overriding()
    assert resp.status_code == 402


def test_video_rag_search_index_empty_no_charge():
    """`video_temporal`'s only writer (`VideoRAGIndexView`) is admin-gated and
    hidden from the UI, so for an ordinary user the collection is empty. This
    drives the real, un-mocked service against the (empty) test DB -- no
    patching of the availability check -- and asserts the search is refused
    before Berrix is touched at all."""
    u = _mk_user(100)
    c = APIClient()
    c.force_authenticate(u)
    resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 503
    assert "index" in resp.json()["error"].lower()
    from animetix.models import Profile

    assert Profile.objects.get(user=u).wallet_balance == 100


def test_video_rag_happy_path_deducts_and_returns():
    from unittest.mock import MagicMock

    from animetix.containers import get_container
    from animetix.models import Profile

    u = _mk_user(100)
    mock_service = MagicMock()
    mock_service.search_video_segment.return_value = [{"id": 1}]
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    try:
        c = APIClient()
        c.force_authenticate(u)
        resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    finally:
        container.agentic.video_rag_service.reset_last_overriding()
    assert resp.status_code == 200
    assert Profile.objects.get(user=u).wallet_balance == 94  # 100 - 6
