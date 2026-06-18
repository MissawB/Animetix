import pytest
from unittest.mock import patch
import jwt
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from backend.api.animetix.auth import GoogleIdentityAuthentication

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def authenticator():
    return GoogleIdentityAuthentication()


@pytest.mark.django_db
@patch("backend.api.animetix.auth.get_google_public_keys")
@patch("jwt.decode")
def test_gcip_auth_success(mock_decode, mock_certs, rf, authenticator, settings):
    settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
    settings.FIREBASE_AUTH_EMULATOR_HOST = None

    mock_certs.return_value = {"key1": "cert_data"}
    mock_decode.return_value = {"email": "test@animetix.com", "sub": "gcip-uid-456"}

    # Mock unverified header kid lookup
    with patch("jwt.get_unverified_header", return_value={"kid": "key1"}):
        request = rf.get("/api/v1/auth/me/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer valid-jwt-token"

        user, token = authenticator.authenticate(request)

        assert user is not None
        assert user.email == "test@animetix.com"
        assert user.username == "test"
        assert token["sub"] == "gcip-uid-456"


@pytest.mark.django_db
def test_gcip_auth_emulator_success(rf, authenticator, settings):
    settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
    settings.FIREBASE_AUTH_EMULATOR_HOST = "localhost:9099"

    # Mock decoding emulator token
    with patch("jwt.decode", return_value={"email": "emulator@animetix.com"}):
        request = rf.get("/api/v1/auth/me/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer emulator-unsigned-token"

        user, token = authenticator.authenticate(request)

        assert user is not None
        assert user.email == "emulator@animetix.com"
        assert user.username == "emulator"


@pytest.mark.django_db
@patch("backend.api.animetix.auth.get_google_public_keys")
def test_gcip_auth_invalid_header(mock_certs, rf, authenticator):
    request = rf.get("/api/v1/auth/me/")
    request.META["HTTP_AUTHORIZATION"] = "InvalidFormatHeader"

    result = authenticator.authenticate(request)
    assert result is None


@pytest.mark.django_db
@patch("backend.api.animetix.auth.get_google_public_keys")
@patch("jwt.decode")
def test_gcip_auth_expired_token(mock_decode, mock_certs, rf, authenticator, settings):
    settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
    settings.FIREBASE_AUTH_EMULATOR_HOST = None

    mock_certs.return_value = {"key1": "cert_data"}
    mock_decode.side_effect = jwt.ExpiredSignatureError("Signature has expired")

    with patch("jwt.get_unverified_header", return_value={"kid": "key1"}):
        request = rf.get("/api/v1/auth/me/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer expired-jwt-token"

        with pytest.raises(AuthenticationFailed) as exc_info:
            authenticator.authenticate(request)
        assert "ID Token has expired" in str(exc_info.value)
