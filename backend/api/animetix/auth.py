import logging
import time

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import PermissionDenied
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import authentication, exceptions

logger = logging.getLogger("animetix.auth")
User = get_user_model()

# --- GCP Identity-Aware Proxy (IAP) Helpers ---


def verify_iap_jwt(jwt_assertion, expected_audience):
    """
    Verifies the IAP JWT assertion against Google's public keys.
    """
    if not expected_audience:
        logger.warning(
            "IAP expected audience is not configured. JWT verification skipped."
        )
        return None
    try:
        # verify_token fetches Google's IAP public keys and verifies signature/expiration
        payload = id_token.verify_token(
            jwt_assertion,
            request=google_requests.Request(),
            audience=expected_audience,
            certs_url="https://www.gstatic.com/iap/verify/public_key",
        )
        return payload
    except Exception as e:
        logger.error(f"IAP JWT verification failed: {e}")
        return None


class IAPRemoteUserMiddleware(RemoteUserMiddleware):
    def process_request(self, request):
        jwt_assertion = request.META.get("HTTP_X_GOOG_IAP_JWT_ASSERTION")
        if not jwt_assertion:
            # Bypass IAP login in local development or routes where IAP is inactive
            return

        expected_audience = getattr(settings, "GCP_IAP_AUDIENCE", None)
        payload = verify_iap_jwt(jwt_assertion, expected_audience)
        if not payload:
            raise PermissionDenied("Invalid IAP JWT Assertion.")

        email = payload.get("email")
        if not email:
            raise PermissionDenied("IAP JWT Assertion is missing email claim.")

        # Set REMOTE_USER so RemoteUserMiddleware can authenticate the request
        request.META[self.header] = email
        super().process_request(request)


class IAPRemoteUserBackend(RemoteUserBackend):
    create_unknown_user = True

    def clean_username(self, username):
        # Extract prefix if username is an email address
        if "@" in username:
            return username.split("@")[0]
        return username

    def configure_user(self, request, user, created=True):
        # Set email if we captured it during authenticate
        email = getattr(self, "current_email", None)
        if email:
            user.email = email
            user.save()
        self._update_user_permissions(user)
        return user

    def authenticate(self, request, remote_user, **kwargs):
        self.current_email = remote_user
        user = super().authenticate(request, remote_user, **kwargs)
        if user:
            if remote_user and "@" in remote_user:
                user.email = remote_user
                user.save()
            self._update_user_permissions(user)
        return user

    def _update_user_permissions(self, user):
        approved_admins = getattr(settings, "IAP_APPROVED_ADMIN_EMAILS", [])
        if user.email in approved_admins:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                logger.info(
                    f"Granted administrative privileges to IAP user: {user.email}"
                )
        else:
            if user.is_staff or user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
                user.save()
                logger.info(
                    f"Revoked administrative privileges from IAP user: {user.email}"
                )


# --- Google Identity Platform (GCIP) Authentication ---

GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
_public_keys_cache = {}
_public_keys_expiry = 0


def get_google_public_keys():
    global _public_keys_cache, _public_keys_expiry
    now = time.time()
    if _public_keys_cache and now < _public_keys_expiry:
        return _public_keys_cache

    try:
        response = requests.get(GOOGLE_CERTS_URL, timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        cache_control = response.headers.get("Cache-Control", "")
        max_age = 3600
        for part in cache_control.split(","):
            if "max-age" in part:
                try:
                    max_age = int(part.split("=")[1].strip())
                except (ValueError, IndexError):
                    logger.debug(f"Could not parse max-age from: {part}")

        _public_keys_cache = response.json()
        _public_keys_expiry = now + max_age
        return _public_keys_cache
    except Exception as e:
        logger.error(f"Failed to fetch Google public keys: {e}")
        return _public_keys_cache


class GoogleIdentityAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        id_token = parts[1]
        project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", "animetix")

        # Support Local Emulator
        emulator_host = getattr(settings, "FIREBASE_AUTH_EMULATOR_HOST", None)
        if emulator_host:
            try:
                payload = jwt.decode(id_token, options={"verify_signature": False})
                email = payload.get("email")
                if not email:
                    raise exceptions.AuthenticationFailed(
                        "Emulator token missing email claim."
                    )
                user = self._get_or_create_user(email)
                return (user, payload)
            except Exception as e:
                raise exceptions.AuthenticationFailed(f"Invalid Emulator ID Token: {e}")

        # Standard Production Verification
        public_keys = get_google_public_keys()
        if not public_keys:
            raise exceptions.AuthenticationFailed("Google public keys unavailable.")

        try:
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            if not kid or kid not in public_keys:
                raise exceptions.AuthenticationFailed("Invalid kid in token header.")

            cert = public_keys[kid]

            payload = jwt.decode(
                id_token,
                cert,
                algorithms=["RS256"],
                audience=project_id,
                issuer=f"https://securetoken.google.com/{project_id}",
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("ID Token has expired.")
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid ID Token: {e}")
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Authentication failed: {e}")

        email = payload.get("email")
        if not email:
            raise exceptions.AuthenticationFailed("Token is missing email claim.")

        user = self._get_or_create_user(email)
        return (user, payload)

    def _get_or_create_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            logger.debug(f"New user registration flow for email: {email}")

        base_username = email.split("@")[0]
        username = base_username
        suffix_counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{suffix_counter}"
            suffix_counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
        )
        user.set_unusable_password()
        user.save()
        logger.info(f"Automatically created User {username} for email {email}")
        return user


class DeveloperApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Authentication backend that validates API keys passed in the 'X-API-Key' header.
    Format: ax_pro_<profile_id>_<secret>
    """

    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")
        if not api_key:
            return None

        if not api_key.startswith("ax_pro_"):
            raise exceptions.AuthenticationFailed("Invalid API Key format.")

        parts = api_key.split("_")
        if len(parts) < 4:
            raise exceptions.AuthenticationFailed("Invalid API Key structure.")

        profile_id = parts[2]
        from animetix.models import Profile  # noqa: E402

        try:
            profile = Profile.objects.select_related("user").get(pk=profile_id)
        except (Profile.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed("Developer Profile not found.")

        # Check if the user is in the 'pro' tier
        if profile.tier != "pro":
            raise exceptions.AuthenticationFailed(
                "API access is restricted to Pro tier developers."
            )

        # Verify the key using Django's password hasher
        if not profile.check_api_key(api_key):
            raise exceptions.AuthenticationFailed("Invalid API Key.")

        if not profile.user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled.")

        return (profile.user, api_key)
