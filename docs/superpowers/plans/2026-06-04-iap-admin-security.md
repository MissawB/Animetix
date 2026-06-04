# Identity-Aware Proxy (IAP) Security Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure admin routes using Google Cloud Identity-Aware Proxy (IAP) in production, validating Google-signed JWT headers, automatically logging authorized users in, and syncing admin privileges, while maintaining fallback authentication in local development.

**Architecture:** Create a custom authentication module (`backend/api/animetix/auth.py`) containing a subclass of Django's `RemoteUserMiddleware` and `RemoteUserBackend`. The middleware validates the signature of `X-Goog-IAP-JWT-Assertion` using Google's public certificates. The backend maps verified email addresses to Django users and manages superuser/staff permissions dynamically based on a whitelist.

**Tech Stack:** Django (remote user auth), Google Auth Library (`google.oauth2.id_token`, `google.auth.transport.requests`), Pytest (mocking).

---

### Task 1: Create IAP Authentication Module

**Files:**
- Create: `backend/api/animetix/auth.py`

- [ ] **Step 1: Write IAP authentication middleware and backend**

Create `backend/api/animetix/auth.py` with:
```python
import logging
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import PermissionDenied
from google.auth.transport import requests
from google.oauth2 import id_token

logger = logging.getLogger('animetix.auth')

def verify_iap_jwt(jwt_assertion, expected_audience):
    """
    Verifies the IAP JWT assertion against Google's public keys.
    """
    if not expected_audience:
        logger.warning("IAP expected audience is not configured. JWT verification skipped.")
        return None
    try:
        # verify_token fetches Google's IAP public keys and verifies signature/expiration
        payload = id_token.verify_token(
            jwt_assertion,
            request=requests.Request(),
            audience=expected_audience,
            certs_url="https://www.gstatic.com/iap/verify/public_key"
        )
        return payload
    except Exception as e:
        logger.error(f"IAP JWT verification failed: {e}")
        return None

class IAPRemoteUserMiddleware(RemoteUserMiddleware):
    header = "HTTP_X_GOOG_IAP_JWT_ASSERTION"

    def process_request(self, request):
        jwt_assertion = request.META.get(self.header)
        if not jwt_assertion:
            # Bypass IAP login in local development or routes where IAP is inactive
            return

        expected_audience = getattr(settings, 'GCP_IAP_AUDIENCE', None)
        payload = verify_iap_jwt(jwt_assertion, expected_audience)
        if not payload:
            raise PermissionDenied("Invalid IAP JWT Assertion.")

        email = payload.get("email")
        if not email:
            raise PermissionDenied("IAP JWT Assertion is missing email claim.")

        # Set REMOTE_USER so RemoteUserMiddleware can authenticate the request
        request.META['REMOTE_USER'] = email
        super().process_request(request)

class IAPRemoteUserBackend(RemoteUserBackend):
    create_unknown_user = True

    def clean_username(self, username):
        # Username passed here is the email address set by middleware
        return username

    def configure_user(self, request, user):
        # Extracted email is set as Django user's email
        user.email = user.username
        # Generate clean alphanumeric username for Django internal storage
        user.username = user.email.split('@')[0]
        user.save()
        self._update_user_permissions(user)
        return user

    def authenticate(self, request, remote_user, **kwargs):
        user = super().authenticate(request, remote_user, **kwargs)
        if user:
            self._update_user_permissions(user)
        return user

    def _update_user_permissions(self, user):
        approved_admins = getattr(settings, 'IAP_APPROVED_ADMIN_EMAILS', [])
        if user.email in approved_admins:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                logger.info(f"Granted administrative privileges to IAP user: {user.email}")
        else:
            if user.is_staff or user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
                user.save()
                logger.info(f"Revoked administrative privileges from IAP user: {user.email}")
```

---

### Task 2: Configure Django Settings

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Add IAP settings and register middleware & auth backends**

Update `backend/api/animetix_project/settings.py` around line 192:
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'backend.api.animetix.auth.IAPRemoteUserBackend',
]
```

Update `backend/api/animetix_project/settings.py` around line 219:
```python
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'backend.api.animetix.auth.IAPRemoteUserMiddleware',  # Added IAP Remote User Middleware
    'allauth.account.middleware.AccountMiddleware',
    'animetix.middleware.UserTierMiddleware',
    ...
]
```

Add IAP Configuration values at the end of the file:
```python
# GCP Identity-Aware Proxy (IAP) Configuration
GCP_IAP_AUDIENCE = env('GCP_IAP_AUDIENCE', default=None)
IAP_APPROVED_ADMIN_EMAILS = env.list('IAP_APPROVED_ADMIN_EMAILS', default=[])
```

---

### Task 3: Create IAP Unit Test Suite

**Files:**
- Create: `tests/backend/test_iap_auth.py`

- [ ] **Step 1: Write test_iap_auth.py unit tests**

Create `tests/backend/test_iap_auth.py` with:
```python
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
    
    mock_verify.return_value = {
        "email": "admin@animetix.com",
        "sub": "google-user-123"
    }
    
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
    settings.IAP_APPROVED_ADMIN_EMAILS = [] # Empty approved list
    
    # Pre-create staff user
    user = User.objects.create(username="staffuser", email="staffuser@animetix.com", is_staff=True, is_superuser=True)
    
    backend = IAPRemoteUserBackend()
    # Authenticate will trigger _update_user_permissions and revoke staff permissions
    authenticated_user = backend.authenticate(None, remote_user="staffuser@animetix.com")
    
    assert authenticated_user.is_staff is False
    assert authenticated_user.is_superuser is False
```

---

### Task 4: Run Tests & Verification

- [ ] **Step 1: Execute unit tests to ensure IAP logic works**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_iap_auth.py -v
```
Expected: 4 passed.

- [ ] **Step 2: Commit all changes**

Run:
```bash
git add backend/api/animetix/auth.py backend/api/animetix_project/settings.py tests/backend/test_iap_auth.py docs/superpowers/plans/2026-06-04-iap-admin-security.md docs/superpowers/specs/2026-06-04-iap-admin-security-design.md
git commit -m "feat: implement IAP backend authentication and admin whitelist mapping middleware"
```
