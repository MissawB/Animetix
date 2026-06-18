import google.auth
import google.auth.transport.requests
from django.conf import settings
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)


class DatabaseWrapper(PostgresDatabaseWrapper):
    def get_new_connection(self, conn_params):
        use_iam = getattr(settings, "DJANGO_DB_USE_IAM", False)

        if use_iam:
            conn_params = conn_params.copy()
            try:
                # Retrieve the Google OAuth2 access token for IAM auth
                scopes = [
                    "https://www.googleapis.com/auth/sqlservice.admin",
                    "https://www.googleapis.com/auth/cloud-platform",
                ]
                credentials, project = google.auth.default(scopes=scopes)
                auth_req = google.auth.transport.requests.Request()
                credentials.refresh(auth_req)

                # Set OAuth2 token as connection password
                conn_params["password"] = credentials.token
            except Exception as e:
                # Fallback logging if authentication token fetch fails
                import logging  # noqa: E402

                logger = logging.getLogger("django.db.backends")
                logger.error(f"Failed to fetch PostgreSQL IAM OAuth2 token: {e}")
                raise

        return super().get_new_connection(conn_params)
