from .settings import *

# Clear everything and set a fresh test DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': False,
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Ensure heavy features are off
FEATURES = {
    'EXPERIMENTAL_MODES': True,
}

# Mock out heavy logging/tracking
sentry_sdk.init = lambda **kwargs: None

# Allow session-based authentication in tests for Django test client compatibility
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        *REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'],
    ]
}

EVENTARC_RECEIVER_URL = 'http://localhost:8000/api/events/gcs-upload/'
