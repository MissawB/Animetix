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
    def process_request(self, request):
        jwt_assertion = request.META.get("HTTP_X_GOOG_IAP_JWT_ASSERTION")
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
        request.META[self.header] = email
        super().process_request(request)

class IAPRemoteUserBackend(RemoteUserBackend):
    create_unknown_user = True

    def clean_username(self, username):
        # Extract prefix if username is an email address
        if '@' in username:
            return username.split('@')[0]
        return username

    def configure_user(self, request, user, created=True):
        # Set email if we captured it during authenticate
        email = getattr(self, 'current_email', None)
        if email:
            user.email = email
            user.save()
        self._update_user_permissions(user)
        return user

    def authenticate(self, request, remote_user, **kwargs):
        self.current_email = remote_user
        user = super().authenticate(request, remote_user, **kwargs)
        if user:
            if remote_user and '@' in remote_user:
                user.email = remote_user
                user.save()
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
