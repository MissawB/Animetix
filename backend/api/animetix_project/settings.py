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
PROJECT_ROOT = BASE_DIR.parent.parent

# --- AUTO-DETECTION MODE DEV vs PROD ---
# Use an explicit environment variable for production detection
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development').lower()
IS_PRODUCTION = DJANGO_ENV == 'production'

import logging

# --- LOGGING CONFIGURATION ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [time_ms:%(duration_ms)s] %(message)s',
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
        },
    },
    'filters': {
        'duration_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: setattr(record, 'duration_ms', getattr(record, 'duration_ms', 0)) or True,
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'structured_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
            'filters': ['duration_filter'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'animetix': {
            'handlers': ['structured_console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

logger = logging.getLogger('animetix')

if IS_PRODUCTION:
    SECRET_KEY = env('DJANGO_SECRET_KEY', default=None)
    if not SECRET_KEY:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("The DJANGO_SECRET_KEY environment variable is required in production.")
    DEBUG = env.bool('DJANGO_DEBUG', default=False)
    # Support dynamic ALLOWED_HOSTS via env var in production (e.g. for GCP Cloud Run)
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['missawb-animetix-web.hf.space'])

    # --- SECURITY HARDENING (PROD) ---
    SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

else:
    # Mode Développement Sécurisé (Local uniquement)
    SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-insecure-animetix-2026-v2-local-only')
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
    logger.info("🛠️  Running in DEVELOPMENT mode (DEBUG=True). Restricted to localhost.")

# --- DOS PREVENTION (OOM) ---
# Limite stricte de 50 Mo par requête pour éviter les payloads massifs
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800 
# Tout fichier > 2.5 Mo est écrit sur disque temporaire au lieu d'utiliser la RAM
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440
# Limite le nombre de champs dans un form-data (mitigation d'attaque Hash Collision)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# --- HUGGING FACE SPACES CONFIG ---
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Configuration dynamique du CSRF (Option B: Dynamique/Inconnu)
CSRF_TRUSTED_ORIGINS = env.list('EXTRA_CSRF_TRUSTED_ORIGINS', default=[])

if not IS_PRODUCTION:
    # En développement ou staging, on autorise les wildcards pour les Spaces Hugging Face
    CSRF_TRUSTED_ORIGINS += [
        "https://*.hf.space",
        "https://*.huggingface.co",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ]
else:
    # En production stricte, on ne devrait utiliser que des URLs explicites
    # On garde une fallback sécurisée si aucune n'est fournie via ENV
    if not CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = ["https://missawb-animetix-web.hf.space"]

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
# Protection CSRF : SameSite 'None' requiert impérativement un cookie sécurisé (HTTPS).
# En développement (DEBUG=True), on repasse sur 'Lax' pour éviter que le navigateur rejette le cookie de session non sécurisé.
CSRF_COOKIE_SAMESITE = 'Lax' if DEBUG else 'None'
SESSION_COOKIE_SAMESITE = 'Lax' if DEBUG else 'None'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    
# Autoriser les cookies cross-domain (essentiel pour SameSite=None)
CORS_ALLOW_CREDENTIALS = True

# --- EXTERNAL APIs & SERVICES ---
BRAIN_API_KEY = env('BRAIN_API_KEY', default='dev-insecure-key-animetix-2026')

if IS_PRODUCTION:
    if not BRAIN_API_KEY or BRAIN_API_KEY == 'dev-insecure-key-animetix-2026':
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("BRAIN_API_KEY est obligatoire et doit être sécurisée en production.")

# I18N
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Apps
INSTALLED_APPS = [
    'daphne', # Doit être avant staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Requis par allauth

    # THIRD PARTY
    'animetix',
    'channels',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',

    # ALLAUTH (OAuth)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.discord',
    'allauth.socialaccount.providers.google',
    'storages',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'backend.api.animetix.auth.IAPRemoteUserBackend',
]

# ALLAUTH CONFIG
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ASGI_APPLICATION = 'animetix_project.asgi.application'

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}

MIDDLEWARE = [
    'animetix.middleware.TracingMiddleware',  # Tracing at the very beginning of the stack
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'backend.api.animetix.auth.IAPRemoteUserMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'animetix.middleware.UserTierMiddleware',
    'animetix.middleware.UserTrackingMiddleware', # Moved after Auth
    'animetix.middleware.PersonalizationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'backend.api.animetix.auth.GoogleIdentityAuthentication',
        'backend.api.animetix.auth.DeveloperApiKeyAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Animetix API',
    'DESCRIPTION': 'Documentation des APIs REST d\'Animetix (Media Discovery & AI Games)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_PATCH': True,
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://missawb-animetix-web.hf.space",
]
ROOT_URLCONF = 'animetix_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, "frontend", "dist")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'animetix.context_processors.translation_processor',
                'animetix.context_processors.achievements_processor',
                'animetix.context_processors.features_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'animetix_project.wsgi.application'

# Database
DJANGO_DB_USE_IAM = env.bool('DJANGO_DB_USE_IAM', default=IS_PRODUCTION)

if os.getenv('DATABASE_URL'):
    DATABASES = {'default': env.db('DATABASE_URL')}
    db_host = DATABASES['default'].get('HOST', '') or DATABASES['default'].get('OPTIONS', {}).get('host', '')
    if db_host.startswith('/') or 'cloudsql' in db_host:
        # Unix socket connection (GCP Cloud SQL). Do not set sslmode='require' as it is not supported/needed over Unix sockets.
        if 'OPTIONS' not in DATABASES['default']:
            DATABASES['default']['OPTIONS'] = {}
        if 'sslmode' in DATABASES['default']['OPTIONS']:
            del DATABASES['default']['OPTIONS']['sslmode']
    else:
        # Standard TCP connection, enforce SSL
        if 'OPTIONS' not in DATABASES['default']:
            DATABASES['default']['OPTIONS'] = {}
        DATABASES['default']['OPTIONS']['sslmode'] = 'require'
        
    if DJANGO_DB_USE_IAM:
        DATABASES['default']['ENGINE'] = 'animetix.db.postgresql'
        # In Cloud SQL IAM, the user is the service account email address
        DATABASES['default']['USER'] = env('GCP_TASKS_SERVICE_ACCOUNT', default='animetix-tasks-invoker@animetix.iam.gserviceaccount.com')
        DATABASES['default']['PASSWORD'] = ''  # Will be dynamically set by wrapper
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
DATABASES['default']['ATOMIC_REQUESTS'] = False

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
        print("[INFO] Redis not found, using Local Memory Cache.")

CELERY_RESULT_BACKEND = REDIS_URL if REDIS_URL and not REDIS_URL.startswith("rediss://") else "rpc://" 
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Google Cloud Tasks Configuration
GCP_PROJECT_ID = env('GOOGLE_CLOUD_PROJECT', default='animetix')
GCP_TASKS_QUEUE_NAME = env('GCP_TASKS_QUEUE_NAME', default='animetix-queue')
GCP_TASKS_LOCATION = env('GCP_TASKS_LOCATION', default='europe-west1')
GCP_TASKS_WORKER_URL = env('GCP_TASKS_WORKER_URL', default='https://missawb-animetix-web.hf.space/api/tasks/run/')
GCP_TASKS_SERVICE_ACCOUNT = env('GCP_TASKS_SERVICE_ACCOUNT', default='animetix-tasks-invoker@animetix.iam.gserviceaccount.com')

# CELERY_BEAT_SCHEDULE has been decommissioned in favor of serverless Google Cloud Run Jobs
# and Cloud Scheduler triggers.
# The recurring tasks are mapped to the django management command:
# `python manage.py run_scheduled_task <task_key>`
#
# from celery.schedules import crontab
# CELERY_BEAT_SCHEDULE = {
#     'dpo-optimization-daily': {
#         'task': 'animetix.tasks.scheduled_dpo_optimization',
#         'schedule': crontab(hour=3, minute=0),
#     },
#     'daily-data-ingestion': {
#         'task': 'animetix.pipeline.run_daily_ingestion_workflow',
#         'schedule': crontab(hour=3, minute=0),
#     },
#     'daily-maintenance-mlops': {
#         'task': 'animetix.pipeline.run_daily_maintenance_workflow',
#         'schedule': crontab(hour=5, minute=0),
#     },
#     'hourly-health-monitoring': {
#         'task': 'animetix.pipeline.run_hourly_monitoring_workflow',
#         'schedule': crontab(minute=0),
#     },
#     'gold-dataset-lora-sensor': {
#         'task': 'animetix.pipeline.check_gold_dataset_sensor_task',
#         'schedule': crontab(minute='*/10'),
#     },
#     'gold-dataset-dpo-sensor': {
#         'task': 'animetix.pipeline.check_dpo_feedback_sensor_task',
#         'schedule': crontab(minute='*/10'),
#     },
# }

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "frontend", "dist"),
]

# --- 📁 CENTRALIZED PATHS ---
PROJECT_ROOT = BASE_DIR.parent.parent
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ARTIFACTS_DIR = os.path.join(DATA_DIR, "artifacts")
MODELS_DIR = os.path.join(DATA_DIR, "models")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Media files (uploads, generated images, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

GS_BUCKET_NAME = env('GS_BUCKET_NAME', default=None)
GS_CUSTOM_ENDPOINT = env('GS_CUSTOM_ENDPOINT', default=None)
GS_DEFAULT_KMS_KEY_NAME = env('GS_DEFAULT_KMS_KEY_NAME', default=None)

GS_OBJECT_PARAMETERS = {}
if GS_DEFAULT_KMS_KEY_NAME:
    GS_OBJECT_PARAMETERS['kms_key_name'] = GS_DEFAULT_KMS_KEY_NAME

if IS_PRODUCTION or GS_BUCKET_NAME:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'project_id': env('GOOGLE_CLOUD_PROJECT', default='animetix'),
                'custom_endpoint': GS_CUSTOM_ENDPOINT,
                'object_parameters': GS_OBJECT_PARAMETERS,
            }
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage',
        }
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

# --- FEATURE FLAGS ---
FEATURE_FLAGS = {
    'EXPERIMENTAL_MODES': env.bool('FEATURE_EXPERIMENTAL_MODES', default=not IS_PRODUCTION),
    'BETA_SOCIAL': env.bool('FEATURE_BETA_SOCIAL', default=True),
    'AI_DEBUG_DASHBOARD': env.bool('FEATURE_AI_DEBUG', default=not IS_PRODUCTION),
}

ALLOYDB_EMBEDDING_MODEL = env('ALLOYDB_EMBEDDING_MODEL', default='text-embedding-005')

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
if sentry_dsn and not os.environ.get('PYTEST_CURRENT_TEST'):
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
        send_default_pii=False, # Sécurité/RGPD : Ne pas envoyer d'infos personnelles identifiables (IP, emails, etc.)
    )
    print("[SUCCESS] Sentry initialized with Django & Celery integrations.")

# --- 🛡️ CONTENT SECURITY POLICY (CSP) ---
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net")

# En production, on retire 'unsafe-eval' pour bloquer les exécutions de scripts non sécurisées.
# On autorise uniquement si nécessaire via env.
_ALLOW_UNSAFE_EVAL = env.bool('DJANGO_CSP_ALLOW_UNSAFE_EVAL', default=not IS_PRODUCTION)
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://huggingface.co"]
if _ALLOW_UNSAFE_EVAL:
    CSP_SCRIPT_SRC.append("'unsafe-eval'")
CSP_SCRIPT_SRC = tuple(CSP_SCRIPT_SRC)

_EXTRA_IMG = env.list('EXTRA_CSP_IMG_SRC', default=[])
CSP_IMG_SRC = ["'self'", "data:", "blob:", "https://*.huggingface.co", "https://cdn.myanimelist.net", "https://m.media-amazon.com"]
if not IS_PRODUCTION:
    CSP_IMG_SRC.append("https://*.hf.space")
CSP_IMG_SRC = tuple(CSP_IMG_SRC + _EXTRA_IMG)

CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net")

_EXTRA_CONNECT = env.list('EXTRA_CSP_CONNECT_SRC', default=[])
CSP_CONNECT_SRC = ["'self'", "https://*.huggingface.co", "https://huggingface.co"]
if not IS_PRODUCTION:
    CSP_CONNECT_SRC.append("https://*.hf.space")
CSP_CONNECT_SRC = tuple(CSP_CONNECT_SRC + _EXTRA_CONNECT)

CSP_FRAME_SRC = ["'self'", "https://*.huggingface.co"]
if not IS_PRODUCTION:
    CSP_FRAME_SRC.append("https://*.hf.space")
CSP_FRAME_SRC = tuple(CSP_FRAME_SRC)

CSP_MEDIA_SRC = ["'self'", "data:", "blob:", "https://*.huggingface.co"]
if not IS_PRODUCTION:
    CSP_MEDIA_SRC.append("https://*.hf.space")
CSP_MEDIA_SRC = tuple(CSP_MEDIA_SRC)

CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)

CSP_FRAME_ANCESTORS = ["'self'", "https://huggingface.co"]
if not IS_PRODUCTION:
    CSP_FRAME_ANCESTORS.append("https://*.hf.space")
CSP_FRAME_ANCESTORS = tuple(CSP_FRAME_ANCESTORS)

# Report-only mode is useful for testing without blocking
CSP_REPORT_ONLY = env.bool('DJANGO_CSP_REPORT_ONLY', default=False)

# GCP Cloud Run & Billing Configuration
GCP_BRAIN_SERVICE_NAME = env('GCP_BRAIN_SERVICE_NAME', default='animetix-brain')
GCP_BRAIN_REGION = env('GCP_BRAIN_REGION', default='europe-west1')
GCP_BILLING_WEBHOOK_URL = env('GCP_BILLING_WEBHOOK_URL', default='https://missawb-animetix-web.hf.space/api/billing/webhook/')

# GCP Identity-Aware Proxy (IAP) Configuration
GCP_IAP_AUDIENCE = env('GCP_IAP_AUDIENCE', default=None)
IAP_APPROVED_ADMIN_EMAILS = env.list('IAP_APPROVED_ADMIN_EMAILS', default=[])
FIREBASE_AUTH_EMULATOR_HOST = env('FIREBASE_AUTH_EMULATOR_HOST', default=None)

# GCP Workflows & Eventarc Configuration
GCP_WORKFLOW_ID = env('GCP_WORKFLOW_ID', default='manga-voice-pipeline')
GCP_LOCATION = env('GCP_LOCATION', default='europe-west1')
GCS_MEDIA_BUCKET = env('GCS_MEDIA_BUCKET', default='animetix-media-bucket')
EVENTARC_RECEIVER_URL = env('EVENTARC_RECEIVER_URL', default='https://missawb-animetix-web.hf.space/api/events/gcs-upload/')
GCP_WORKFLOW_POLL_URL = env('GCP_WORKFLOW_POLL_URL', default='https://missawb-animetix-web.hf.space/api/tasks/workflow/poll/')

# --- SECURITY ---
STRICT_MODEL_VERIFICATION = False

# --- VERTEX AI VECTOR SEARCH 2.0 (COLLECTIONS) ---
VERTEX_AI_VECTOR_SEARCH_ACTIVE = env.bool('VERTEX_AI_VECTOR_SEARCH_ACTIVE', default=False)
VERTEX_AI_PROJECT_ID = env('VERTEX_AI_PROJECT_ID', default='')
VERTEX_AI_LOCATION = env('VERTEX_AI_LOCATION', default='europe-west1')
VERTEX_AI_COLLECTION_NAME = env('VERTEX_AI_COLLECTION_NAME', default='animetix_media')
VERTEX_AI_AUTO_EMBEDDINGS = env.bool('VERTEX_AI_AUTO_EMBEDDINGS', default=True)
VERTEX_AI_EMBEDDING_MODEL = env('VERTEX_AI_EMBEDDING_MODEL', default='text-embedding-005')

# --- GEMINI ENTERPRISE AGENT PLATFORM ---
VERTEX_AI_AGENT_GATEWAY_ACTIVE = env.bool('VERTEX_AI_AGENT_GATEWAY_ACTIVE', default=False)
VERTEX_AI_AGENT_POLICY_ID = env('VERTEX_AI_AGENT_POLICY_ID', default='')
VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE = env.bool('VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE', default=False)
VERTEX_AI_AGENT_ID = env('VERTEX_AI_AGENT_ID', default='animetix-core-rag-agent')

# --- ALLOYDB AI QUERYDATA (TEXT-TO-SQL) ---
ALLOYDB_NL_QUERY_ACTIVE = env.bool('ALLOYDB_NL_QUERY_ACTIVE', default=False)
ALLOYDB_NL_CONFIG_NAME = env('ALLOYDB_NL_CONFIG_NAME', default='animetix_catalog')

# --- STRIPE BILLING CONFIGURATION ---
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default=None)
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default=None)
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default=None)
STRIPE_USE_METERS = env.bool('STRIPE_USE_METERS', default=True)
STRIPE_METER_EVENT_NAME = env('STRIPE_METER_EVENT_NAME', default='rag_api_requests')
STRIPE_PRO_PRICE_ID = env('STRIPE_PRO_PRICE_ID', default='price_pro_metered')





