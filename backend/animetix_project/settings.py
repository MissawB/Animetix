"""
Django settings for animetix_project project.
"""

from pathlib import Path
import os
import environ

# Initialize environ
env = environ.Env()
# Read .env file at the project root
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# --- AUTO-DETECTION MODE DEV vs PROD ---
# Si DJANGO_SECRET_KEY n'est pas dans l'environnement, on est en DEV
IS_PRODUCTION = os.getenv('DJANGO_SECRET_KEY') is not None

if IS_PRODUCTION:
    SECRET_KEY = env('DJANGO_SECRET_KEY')
    DEBUG = env.bool('DJANGO_DEBUG', default=False)
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
else:
    # Mode Développement Souple
    SECRET_KEY = 'django-insecure-dev-fallback-key-very-secret'
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
    print("🛠️  Running in DEVELOPMENT mode (DEBUG=True)")

# --- HUGGING FACE SPACES CONFIG ---
X_FRAME_OPTIONS = 'ALLOWALL' 
CSRF_TRUSTED_ORIGINS = [
    "https://*.hf.space",
    "https://*.huggingface.co",
    "https://missawb-animetix-web.hf.space"
]

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax' if DEBUG else 'None'
SESSION_COOKIE_SAMESITE = 'Lax' if DEBUG else 'None'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# I18N
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Apps
INSTALLED_APPS = [
    'daphne', # Doit être avant staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'animetix',
    'channels',
    'rest_framework',
    'corsheaders',
    'graphene_django',
]

ASGI_APPLICATION = 'animetix_project.asgi.application'
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CORS_ALLOW_ALL_ORIGINS = True
GRAPHENE = {'SCHEMA': 'animetix.schema.schema'}
ROOT_URLCONF = 'animetix_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'animetix.context_processors.translation_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'animetix_project.wsgi.application'

# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {'default': env.db('DATABASE_URL')}
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Cache & Celery
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": None} if REDIS_URL.startswith("rediss://") else {}
            }
        }
    }
    CELERY_BROKER_URL = REDIS_URL
else:
    # Fallback en local si pas de Redis
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
    CELERY_BROKER_URL = "memory://"
    if not IS_PRODUCTION:
        print("ℹ️  Redis not found, using Local Memory Cache.")

CELERY_RESULT_BACKEND = REDIS_URL if REDIS_URL and not REDIS_URL.startswith("rediss://") else "rpc://" 
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sentry
import sentry_sdk
import asyncio
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

def before_send(event, hint):
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, asyncio.CancelledError):
            return None
    return event

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            LoggingIntegration(level=None, event_level=None),
        ],
        before_send=before_send,
        # Capture 100% des erreurs, mais seulement 10% des performances pour économiser le quota gratuit
        traces_sample_rate=0.1,
        send_default_pii=True, # Utile pour savoir quel utilisateur a eu l'erreur
    )
    print("✅ Sentry initialized with Django & Celery integrations.")
