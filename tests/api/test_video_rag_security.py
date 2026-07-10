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


def test_video_rag_zero_balance_is_402(mocker):
    u = _mk_user(0)
    c = APIClient()
    c.force_authenticate(u)
    resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 402


def test_video_rag_happy_path_deducts_and_returns(mocker):
    from animetix.models import Profile

    u = _mk_user(100)
    mocker.patch(
        "animetix.api.labs.video.get_container"
    ).return_value.agentic.video_rag_service.return_value.search_video_segment.return_value = [
        {"id": 1}
    ]
    c = APIClient()
    c.force_authenticate(u)
    resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 200
    assert Profile.objects.get(user=u).wallet_balance == 94  # 100 - 6
