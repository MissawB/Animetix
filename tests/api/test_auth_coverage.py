"""Real-behavior coverage tests for ``animetix.auth``.

Every external boundary (Google IAP token verification, the Google public-keys
HTTP fetch, ``jwt.decode`` / ``jwt.get_unverified_header``) is patched at the
module level so no real network or Google calls happen.  All assertions check
observable behavior: returned tuples/values, exception type + message, request
``META`` mutations and database side effects (staff/superuser flags, created
users, saved emails).

The module is imported under the ``animetix.*`` namespace (``backend/api`` is on
the pythonpath) so coverage is attributed to ``animetix.auth``.
"""

# E402: the Django/DRF imports below intentionally follow _force_traced_import()
# so the module under test is re-executed under the live coverage tracer first.
# ruff: noqa: E402

import importlib
import sys
from unittest.mock import MagicMock, patch

import jwt
import pytest


# ``animetix/auth.py`` is imported by Django during ``django.setup()`` -- it is
# wired into AUTHENTICATION_BACKENDS / MIDDLEWARE / DRF auth classes, under the
# ``animetix.auth`` dotted path (``backend/api`` is also on the
# pythonpath, so the same file resolves under the bare ``animetix.auth`` name).
# Because the file was executed *before* pytest-cov started tracing, coverage.py
# would otherwise report it as "module-not-measured" and collect zero data.
#
# To fix this we re-execute the module while the tracer is active.  Two things
# are required:
#   1. drop every ``sys.modules`` alias for the file so ``import_module`` truly
#      re-runs the file body (rather than returning the cached module), and
#   2. invalidate coverage's per-file ``_should_trace`` cache, which already
#      contains a "do not trace / already imported" decision for this path from
#      startup -- without this the re-execution is silently not recorded.
def _force_traced_import():
    try:
        import coverage

        cov = coverage.Coverage.current()
        if cov is not None and getattr(cov, "_collector", None) is not None:
            # The collector memoises a "do not trace / already-imported"
            # disposition for auth.py (it was first seen before the file was
            # registered as a measured source).  Clearing that cache lets the
            # forthcoming re-import be traced.
            cache = getattr(cov._collector, "should_trace_cache", None)
            if hasattr(cache, "clear"):
                cache.clear()
    except Exception:  # pragma: no cover - coverage not active (plain run)
        pass

    for _name in ("animetix.auth", "animetix.auth"):
        sys.modules.pop(_name, None)
    return importlib.import_module("animetix.auth")


auth_mod = _force_traced_import()
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, override_settings
from rest_framework import exceptions

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture(autouse=True)
def _reset_public_keys_cache():
    """The module caches public keys in globals; reset around every test."""
    auth_mod._public_keys_cache = {}
    auth_mod._public_keys_expiry = 0
    yield
    auth_mod._public_keys_cache = {}
    auth_mod._public_keys_expiry = 0


# --------------------------------------------------------------------------- #
# verify_iap_jwt
# --------------------------------------------------------------------------- #
def test_verify_iap_jwt_no_audience_returns_none():
    assert auth_mod.verify_iap_jwt("token", None) is None
    assert auth_mod.verify_iap_jwt("token", "") is None


def test_verify_iap_jwt_success_returns_payload():
    payload = {"email": "a@b.com"}
    with patch.object(auth_mod.id_token, "verify_token", return_value=payload) as vt:
        result = auth_mod.verify_iap_jwt("token", "aud")
    assert result == payload
    vt.assert_called_once()
    assert vt.call_args.kwargs["audience"] == "aud"


def test_verify_iap_jwt_verify_raises_returns_none():
    with patch.object(
        auth_mod.id_token, "verify_token", side_effect=ValueError("boom")
    ):
        assert auth_mod.verify_iap_jwt("token", "aud") is None


# --------------------------------------------------------------------------- #
# IAPRemoteUserMiddleware.process_request
# --------------------------------------------------------------------------- #
def _middleware():
    return auth_mod.IAPRemoteUserMiddleware(get_response=lambda r: r)


def test_middleware_no_assertion_bypasses(rf):
    request = rf.get("/x")
    assert _middleware().process_request(request) is None


def test_middleware_falsy_payload_raises_permission_denied(rf):
    request = rf.get("/x", HTTP_X_GOOG_IAP_JWT_ASSERTION="jwt")
    with patch.object(auth_mod, "verify_iap_jwt", return_value=None):
        with pytest.raises(PermissionDenied, match="Invalid IAP JWT Assertion"):
            _middleware().process_request(request)


def test_middleware_payload_missing_email_raises(rf):
    request = rf.get("/x", HTTP_X_GOOG_IAP_JWT_ASSERTION="jwt")
    with patch.object(auth_mod, "verify_iap_jwt", return_value={"sub": "x"}):
        with pytest.raises(PermissionDenied, match="missing email claim"):
            _middleware().process_request(request)


def test_middleware_success_sets_remote_user(rf):
    request = rf.get("/x", HTTP_X_GOOG_IAP_JWT_ASSERTION="jwt")
    mw = _middleware()
    with patch.object(auth_mod, "verify_iap_jwt", return_value={"email": "u@e.com"}):
        # Make super().process_request a no-op so we only assert the META side effect.
        with patch.object(RemoteUserMiddleware, "process_request", return_value=None):
            mw.process_request(request)
    assert request.META[mw.header] == "u@e.com"


# --------------------------------------------------------------------------- #
# IAPRemoteUserBackend
# --------------------------------------------------------------------------- #
def test_clean_username_email_and_plain():
    backend = auth_mod.IAPRemoteUserBackend()
    assert backend.clean_username("john@example.com") == "john"
    assert backend.clean_username("john") == "john"


@pytest.mark.django_db
@override_settings(IAP_APPROVED_ADMIN_EMAILS=["admin@example.com"])
def test_update_user_permissions_grants_admin():
    user = User.objects.create_user(username="admin", email="admin@example.com")
    assert not user.is_staff and not user.is_superuser
    auth_mod.IAPRemoteUserBackend()._update_user_permissions(user)
    user.refresh_from_db()
    assert user.is_staff and user.is_superuser


@pytest.mark.django_db
@override_settings(IAP_APPROVED_ADMIN_EMAILS=[])
def test_update_user_permissions_revokes_admin():
    user = User.objects.create_user(
        username="ex-admin",
        email="ex@example.com",
        is_staff=True,
        is_superuser=True,
    )
    auth_mod.IAPRemoteUserBackend()._update_user_permissions(user)
    user.refresh_from_db()
    assert not user.is_staff and not user.is_superuser


@pytest.mark.django_db
@override_settings(IAP_APPROVED_ADMIN_EMAILS=[])
def test_configure_user_sets_email_and_permissions():
    user = User.objects.create_user(username="cfg")
    backend = auth_mod.IAPRemoteUserBackend()
    backend.current_email = "cfg@example.com"
    returned = backend.configure_user(None, user, created=True)
    assert returned is user
    user.refresh_from_db()
    assert user.email == "cfg@example.com"


@pytest.mark.django_db
@override_settings(IAP_APPROVED_ADMIN_EMAILS=[])
def test_authenticate_happy_path_saves_email():
    user = User.objects.create_user(username="auth-u")
    backend = auth_mod.IAPRemoteUserBackend()
    with patch.object(RemoteUserBackend, "authenticate", return_value=user):
        result = backend.authenticate(None, "auth-u@example.com")
    assert result is user
    assert backend.current_email == "auth-u@example.com"
    user.refresh_from_db()
    assert user.email == "auth-u@example.com"


@pytest.mark.django_db
def test_authenticate_returns_none_when_super_returns_none():
    backend = auth_mod.IAPRemoteUserBackend()
    with patch.object(RemoteUserBackend, "authenticate", return_value=None):
        assert backend.authenticate(None, "nobody@example.com") is None


# --------------------------------------------------------------------------- #
# get_google_public_keys
# --------------------------------------------------------------------------- #
def test_public_keys_cache_hit_skips_request():
    auth_mod._public_keys_cache = {"kid": "cert"}
    auth_mod._public_keys_expiry = auth_mod.time.time() + 1000
    with patch.object(auth_mod.requests, "get") as get:
        result = auth_mod.get_google_public_keys()
    assert result == {"kid": "cert"}
    get.assert_not_called()


def test_public_keys_success_parses_max_age():
    resp = MagicMock()
    resp.headers = {"Cache-Control": "public, max-age=600"}
    resp.json.return_value = {"kid1": "cert1"}
    resp.raise_for_status.return_value = None
    before = auth_mod.time.time()
    with patch.object(auth_mod.requests, "get", return_value=resp):
        result = auth_mod.get_google_public_keys()
    assert result == {"kid1": "cert1"}
    # expiry advanced roughly by max-age (600s)
    assert auth_mod._public_keys_expiry >= before + 500


def test_public_keys_malformed_max_age_uses_default():
    resp = MagicMock()
    resp.headers = {"Cache-Control": "max-age=notanint"}
    resp.json.return_value = {"kid2": "cert2"}
    resp.raise_for_status.return_value = None
    before = auth_mod.time.time()
    with patch.object(auth_mod.requests, "get", return_value=resp):
        result = auth_mod.get_google_public_keys()
    assert result == {"kid2": "cert2"}
    # default 3600 applied despite malformed header
    assert auth_mod._public_keys_expiry >= before + 3000


def test_public_keys_request_raises_returns_stale_cache():
    auth_mod._public_keys_cache = {"stale": "cert"}
    auth_mod._public_keys_expiry = 0  # expired -> forces fetch attempt
    with patch.object(
        auth_mod.requests, "get", side_effect=RuntimeError("network down")
    ):
        result = auth_mod.get_google_public_keys()
    assert result == {"stale": "cert"}


# --------------------------------------------------------------------------- #
# GoogleIdentityAuthentication.authenticate
# --------------------------------------------------------------------------- #
def _auth():
    return auth_mod.GoogleIdentityAuthentication()


def test_google_auth_no_header_returns_none(rf):
    assert _auth().authenticate(rf.get("/x")) is None


def test_google_auth_malformed_header_returns_none(rf):
    assert _auth().authenticate(rf.get("/x", HTTP_AUTHORIZATION="onlyonepart")) is None
    assert _auth().authenticate(rf.get("/x", HTTP_AUTHORIZATION="Basic abc")) is None


@pytest.mark.django_db
@override_settings(FIREBASE_AUTH_EMULATOR_HOST="localhost:9099")
def test_google_auth_emulator_success(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    payload = {"email": "emu@example.com"}
    with patch.object(auth_mod.jwt, "decode", return_value=payload):
        user, returned_payload = _auth().authenticate(request)
    assert returned_payload == payload
    assert user.email == "emu@example.com"


@pytest.mark.django_db
@override_settings(FIREBASE_AUTH_EMULATOR_HOST="localhost:9099")
def test_google_auth_emulator_missing_email(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with patch.object(auth_mod.jwt, "decode", return_value={"sub": "x"}):
        with pytest.raises(exceptions.AuthenticationFailed, match="Invalid Emulator"):
            _auth().authenticate(request)


@pytest.mark.django_db
@override_settings(FIREBASE_AUTH_EMULATOR_HOST="localhost:9099")
def test_google_auth_emulator_decode_raises(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with patch.object(auth_mod.jwt, "decode", side_effect=ValueError("bad")):
        with pytest.raises(exceptions.AuthenticationFailed, match="Invalid Emulator"):
            _auth().authenticate(request)


@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_no_public_keys(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with patch.object(auth_mod, "get_google_public_keys", return_value={}):
        with pytest.raises(
            exceptions.AuthenticationFailed, match="Google public keys unavailable"
        ):
            _auth().authenticate(request)


@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_bad_kid(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with patch.object(auth_mod, "get_google_public_keys", return_value={"good": "c"}):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "missing"}
        ):
            with pytest.raises(exceptions.AuthenticationFailed, match="Invalid kid"):
                _auth().authenticate(request)


@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_expired_signature(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with (
        patch.object(auth_mod, "get_google_public_keys", return_value={"k": "c"}),
        patch.object(auth_mod, "load_pem_x509_certificate", return_value=MagicMock()),
    ):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "k"}
        ):
            with patch.object(
                auth_mod.jwt, "decode", side_effect=jwt.ExpiredSignatureError()
            ):
                with pytest.raises(
                    exceptions.AuthenticationFailed, match="ID Token has expired"
                ):
                    _auth().authenticate(request)


@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_invalid_token(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with (
        patch.object(auth_mod, "get_google_public_keys", return_value={"k": "c"}),
        patch.object(auth_mod, "load_pem_x509_certificate", return_value=MagicMock()),
    ):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "k"}
        ):
            with patch.object(
                auth_mod.jwt,
                "decode",
                side_effect=jwt.InvalidTokenError("nope"),
            ):
                with pytest.raises(
                    exceptions.AuthenticationFailed, match="Invalid ID Token"
                ):
                    _auth().authenticate(request)


@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_generic_exception(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with (
        patch.object(auth_mod, "get_google_public_keys", return_value={"k": "c"}),
        patch.object(auth_mod, "load_pem_x509_certificate", return_value=MagicMock()),
    ):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "k"}
        ):
            with patch.object(
                auth_mod.jwt, "decode", side_effect=RuntimeError("weird")
            ):
                with pytest.raises(
                    exceptions.AuthenticationFailed, match="Authentication failed"
                ):
                    _auth().authenticate(request)


@pytest.mark.django_db
@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_production_missing_email(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    with (
        patch.object(auth_mod, "get_google_public_keys", return_value={"k": "c"}),
        patch.object(auth_mod, "load_pem_x509_certificate", return_value=MagicMock()),
    ):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "k"}
        ):
            with patch.object(auth_mod.jwt, "decode", return_value={"sub": "x"}):
                with pytest.raises(
                    exceptions.AuthenticationFailed, match="missing email claim"
                ):
                    _auth().authenticate(request)


@pytest.mark.django_db
@override_settings(FIREBASE_AUTH_EMULATOR_HOST=None)
def test_google_auth_production_success(rf):
    request = rf.get("/x", HTTP_AUTHORIZATION="Bearer token")
    payload = {"email": "prod@example.com"}
    with (
        patch.object(auth_mod, "get_google_public_keys", return_value={"k": "c"}),
        patch.object(auth_mod, "load_pem_x509_certificate", return_value=MagicMock()),
    ):
        with patch.object(
            auth_mod.jwt, "get_unverified_header", return_value={"kid": "k"}
        ):
            with patch.object(auth_mod.jwt, "decode", return_value=payload):
                user, returned = _auth().authenticate(request)
    assert returned == payload
    assert user.email == "prod@example.com"


# --------------------------------------------------------------------------- #
# _get_or_create_user
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_get_or_create_user_returns_existing():
    existing = User.objects.create_user(username="ex", email="ex@example.com")
    result = _auth()._get_or_create_user("ex@example.com")
    assert result.pk == existing.pk


@pytest.mark.django_db
def test_get_or_create_user_creates_new():
    result = _auth()._get_or_create_user("fresh@example.com")
    assert result.pk is not None
    assert result.username == "fresh"
    assert result.email == "fresh@example.com"
    assert not result.has_usable_password()


@pytest.mark.django_db
def test_get_or_create_user_username_collision_suffix():
    # Pre-create a user whose username equals the email prefix.
    User.objects.create_user(username="dup", email="other@example.com")
    result = _auth()._get_or_create_user("dup@example.com")
    assert result.username == "dup_1"
    assert result.email == "dup@example.com"


# --------------------------------------------------------------------------- #
# DeveloperApiKeyAuthentication.authenticate
# --------------------------------------------------------------------------- #
def _dev_auth():
    return auth_mod.DeveloperApiKeyAuthentication()


def _make_profile(tier="pro", is_active=True, username="dev"):
    # A Profile is auto-created via a post_save signal on User; fetch and
    # update it rather than creating a second one (OneToOne -> would collide).
    user = User.objects.create_user(username=username, is_active=is_active)
    profile = user.profile
    profile.tier = tier
    profile.save()
    return profile


def test_dev_auth_no_key_returns_none(rf):
    assert _dev_auth().authenticate(rf.get("/x")) is None


def test_dev_auth_bad_prefix(rf):
    request = rf.get("/x", HTTP_X_API_KEY="bad_key_value")
    with pytest.raises(exceptions.AuthenticationFailed, match="Invalid API Key format"):
        _dev_auth().authenticate(request)


def test_dev_auth_too_few_parts(rf):
    request = rf.get("/x", HTTP_X_API_KEY="ax_pro_only")
    with pytest.raises(
        exceptions.AuthenticationFailed, match="Invalid API Key structure"
    ):
        _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_profile_not_found(rf):
    request = rf.get("/x", HTTP_X_API_KEY="ax_pro_999999_secret")
    with pytest.raises(
        exceptions.AuthenticationFailed, match="Developer Profile not found"
    ):
        _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_value_error_pk(rf):
    # Non-numeric pk -> ValueError caught and surfaced as profile-not-found.
    request = rf.get("/x", HTTP_X_API_KEY="ax_pro_notanint_secret")
    with pytest.raises(
        exceptions.AuthenticationFailed, match="Developer Profile not found"
    ):
        _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_non_pro_tier(rf):
    profile = _make_profile(tier="free")
    request = rf.get("/x", HTTP_X_API_KEY=f"ax_pro_{profile.pk}_secret")
    with pytest.raises(exceptions.AuthenticationFailed, match="restricted to Pro tier"):
        _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_bad_key(rf):
    from animetix.models import Profile

    profile = _make_profile(tier="pro")
    request = rf.get("/x", HTTP_X_API_KEY=f"ax_pro_{profile.pk}_secret")
    with patch.object(Profile, "check_api_key", return_value=False):
        with pytest.raises(exceptions.AuthenticationFailed, match="Invalid API Key"):
            _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_inactive_user(rf):
    from animetix.models import Profile

    profile = _make_profile(tier="pro", is_active=False)
    request = rf.get("/x", HTTP_X_API_KEY=f"ax_pro_{profile.pk}_secret")
    with patch.object(Profile, "check_api_key", return_value=True):
        with pytest.raises(
            exceptions.AuthenticationFailed, match="account is disabled"
        ):
            _dev_auth().authenticate(request)


@pytest.mark.django_db
def test_dev_auth_success(rf):
    from animetix.models import Profile

    profile = _make_profile(tier="pro")
    api_key = f"ax_pro_{profile.pk}_secret"
    request = rf.get("/x", HTTP_X_API_KEY=api_key)
    with patch.object(Profile, "check_api_key", return_value=True):
        user, returned_key = _dev_auth().authenticate(request)
    assert user.pk == profile.user.pk
    assert returned_key == api_key
