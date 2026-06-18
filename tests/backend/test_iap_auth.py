import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from backend.api.animetix.auth import IAPRemoteUserMiddleware, IAPRemoteUserBackend

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def middleware():
    return IAPRemoteUserMiddleware(lambda r: None)


@pytest.mark.django_db
@patch("backend.api.animetix.auth.id_token.verify_token")
def test_iap_middleware_success(mock_verify, rf, middleware, settings):
    settings.GCP_IAP_AUDIENCE = "mock-audience"
    settings.IAP_APPROVED_ADMIN_EMAILS = ["admin@animetix.com"]

    mock_verify.return_value = {"email": "admin@animetix.com", "sub": "google-user-123"}

    request = rf.get("/admin/curation/")
    request.META["HTTP_X_GOOG_IAP_JWT_ASSERTION"] = "valid-assertion-token"
    request.user = AnonymousUser()
    request.session = MagicMock()

    # Run process_request on middleware
    middleware.process_request(request)

    # Assert Remote User header was set
    assert request.META["REMOTE_USER"] == "admin@animetix.com"

    # Manually run the backend authentication to verify user creation and permissions mapping
    backend = IAPRemoteUserBackend()
    user = backend.authenticate(request, remote_user="admin@animetix.com")

    assert user is not None
    assert user.email == "admin@animetix.com"
    assert user.username == "admin"
    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
@patch("backend.api.animetix.auth.id_token.verify_token")
def test_iap_middleware_failure(mock_verify, rf, middleware, settings):
    settings.GCP_IAP_AUDIENCE = "mock-audience"
    mock_verify.side_effect = Exception("Signature verification failed")

    request = rf.get("/admin/curation/")
    request.META["HTTP_X_GOOG_IAP_JWT_ASSERTION"] = "invalid-assertion-token"

    with pytest.raises(PermissionDenied) as exc_info:
        middleware.process_request(request)
    assert "Invalid IAP JWT Assertion" in str(exc_info.value)


@pytest.mark.django_db
def test_iap_middleware_bypass_local(rf, middleware):
    request = rf.get("/admin/curation/")
    # Assertion header is completely missing

    middleware.process_request(request)
    # Assert REMOTE_USER is not injected
    assert "REMOTE_USER" not in request.META


@pytest.mark.django_db
@patch("backend.api.animetix.auth.id_token.verify_token")
def test_iap_backend_staff_revocation(mock_verify, rf, settings):
    settings.GCP_IAP_AUDIENCE = "mock-audience"
    settings.IAP_APPROVED_ADMIN_EMAILS = []  # Empty approved list

    # Pre-create staff user
    User.objects.create(
        username="staffuser",
        email="staffuser@animetix.com",
        is_staff=True,
        is_superuser=True,
    )

    backend = IAPRemoteUserBackend()
    # Authenticate will trigger _update_user_permissions and revoke staff permissions
    authenticated_user = backend.authenticate(
        None, remote_user="staffuser@animetix.com"
    )

    assert authenticated_user.is_staff is False
    assert authenticated_user.is_superuser is False
