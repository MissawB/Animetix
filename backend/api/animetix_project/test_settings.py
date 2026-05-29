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
