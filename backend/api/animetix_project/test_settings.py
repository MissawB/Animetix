from typing import List, cast

from .settings import *  # noqa: F403

# Clear everything and set a fresh test DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# Ensure heavy features are off
FEATURES = {
    "EXPERIMENTAL_MODES": True,
}

# Mock out heavy logging/tracking
sentry_sdk.init = lambda **kwargs: None  # noqa: F405

# Allow session-based authentication in tests for Django test client compatibility
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        *cast(
            List[str],
            REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],  # noqa: F405
        ),
    ],
}

EVENTARC_RECEIVER_URL = "http://localhost:8000/api/events/gcs-upload/"

RATELIMIT_ENABLE = False

# Tests use the in-memory channel layer (no Redis / channels_redis dependency).
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
