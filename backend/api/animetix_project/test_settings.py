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
        *REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],  # noqa: F405
    ],
}

EVENTARC_RECEIVER_URL = "http://localhost:8000/api/events/gcs-upload/"

RATELIMIT_ENABLE = False

# Tests must not depend on a running Redis. DRF throttling and any cache.get/set
# go through the default cache, so force an in-memory LocMem backend regardless of
# whether REDIS_URL is set in the environment.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "animetix-test-cache",
    }
}

# Tests use the in-memory channel layer (no Redis / channels_redis dependency).
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
