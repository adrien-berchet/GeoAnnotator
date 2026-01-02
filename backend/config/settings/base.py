"""
Base Django settings for GeoAnnotator project.

All common settings shared across environments.
For development, see settings/development.py
For production, see settings/production.py
"""

import os
import warnings
from datetime import timedelta
from pathlib import Path

import environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
env = environ.Env()
env_file = BASE_DIR / str(env.str("ENV_PATH", ".env"))
if env_file.exists():
    environ.Env.read_env(env_file, parse_comments=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-in-production")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # PostGIS support
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "apps.authentication",
    "apps.points",
    "apps.annotations",
    "apps.sharing",
    "apps.trash",
    "apps.export_import",
    "apps.settings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files in production
    "corsheaders.middleware.CorsMiddleware",  # CORS before CommonMiddleware
    "apps.core.middleware.RequestIDMiddleware",  # Request ID tracking for distributed tracing
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# Use DATABASE_URL if provided (Docker), otherwise fallback to individual env vars
if "DATABASE_URL" in os.environ:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=600,
            engine="django.contrib.gis.db.backends.postgis",
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.environ.get("POSTGRES_DB", "geoannotator"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "authentication.User"

# REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/hour",  # Default rate for authenticated users
        "anon": "100/hour",  # Default rate for anonymous users
        "account": "10/min",  # Account operations (pseudonym, password changes)
        "email": "3/hour",  # Email operations (change email, delete account)
        "validation": "30/min",  # Validation endpoints (pseudonym validation)
    },
    "EXCEPTION_HANDLER": "config.exception_handlers.custom_exception_handler",
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

# Storage quota settings (in bytes)
DEFAULT_STORAGE_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

# Point type limits
MAX_POINT_TYPES_PER_USER = 1000

# Trash retention (in days)
TRASH_RETENTION_DAYS = 30

# Email configuration (to be configured per environment)
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "geoannotator.noreply@gmail.com")

# Fernet encryption key for sensitive data (email addresses)
# Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
FERNET_KEY = os.environ.get("FERNET_KEY", "")
if not FERNET_KEY:
    warnings.warn(
        "FERNET_KEY not set. Email encryption will not work. "
        "Generate a key with: "
        "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
        stacklevel=2,
    )

# Celery Configuration
# Use REDIS_URL as fallback if specific Celery URLs not set
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# IMPORTANT: Disable result backend to reduce Redis queries
# Our tasks (email sending, cleanup) don't need to store results
# This alone saves thousands of Redis commands per day
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True

# Reduce Redis polling frequency for Celery Beat scheduler
# Since our scheduled tasks only run once daily, we don't need frequent checks
# Default is 0 (as fast as possible), which causes excessive Redis queries
CELERY_BEAT_MAX_LOOP_INTERVAL = 300  # Check schedule every 5 minutes max

# Reduce Redis polling frequency for Celery Worker
# These settings dramatically reduce Redis queries when the queue is empty
CELERY_BROKER_TRANSPORT_OPTIONS = {
    # How long to wait for a message before returning (seconds)
    # Higher = fewer Redis queries when idle, but slower task pickup
    "visibility_timeout": 43200,  # 12 hours (tasks won't be retried for 12h if worker dies)
    # Socket timeout - this affects the BRPOP blocking timeout
    "socket_timeout": 30,
    # Connection timeout
    "socket_connect_timeout": 30,
    # Keep connection alive to reduce reconnection overhead
    "socket_keepalive": True,
    # Health check interval (seconds) - reduce frequency of health pings
    "health_check_interval": 60,
}

# Disable broker heartbeat to reduce Redis queries
# Heartbeat is useful for detecting dead connections quickly, but causes extra queries
CELERY_BROKER_HEARTBEAT = 0  # Disable heartbeat

# Worker configuration to reduce polling
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Fetch one task at a time
CELERY_WORKER_CONCURRENCY = 1  # Single worker process (overridden by --concurrency flag)

# Disable worker gossip, mingle, and heartbeat to reduce Redis traffic
# These are used for multi-worker coordination, not needed for single worker
CELERY_WORKER_ENABLE_REMOTE_CONTROL = False  # Disable remote control commands
CELERY_WORKER_SEND_TASK_EVENTS = False  # Don't send task events
CELERY_TASK_SEND_SENT_EVENT = False  # Don't send task-sent events

# Event loop settings - increase drain timeout to reduce polling frequency
CELERY_BROKER_POOL_LIMIT = 1  # Single connection pool

# SSL/TLS configuration for external Redis (Upstash, Redis Cloud)
# Required when using rediss:// (SSL) connections
if CELERY_BROKER_URL.startswith("rediss://"):
    # For redis-py, use ssl.CERT_REQUIRED directly
    # Don't set ssl_cert_reqs in broker config, let redis-py handle it
    CELERY_BROKER_USE_SSL = True
    # CELERY_REDIS_BACKEND_USE_SSL = True

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False  # Override in development
# Parse CORS origins from environment variable (comma-separated)
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]

# GeoDjango configuration
# GDAL and GEOS library paths (set if not in default locations)
# GDAL_LIBRARY_PATH = '/path/to/libgdal.so'
# GEOS_LIBRARY_PATH = '/path/to/libgeos_c.so'

# Frontend URL for email confirmation links
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Sentry Configuration for Error Tracking and Performance Monitoring
# Get Sentry DSN from environment variable (optional)
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(
    os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
)  # 10% of transactions

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        # Set traces_sample_rate to capture performance data
        # In production, you may want to lower this to reduce overhead
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        # Send all events to Sentry
        send_default_pii=False,  # Don't send personally identifiable information
        # Include request ID in breadcrumbs
        before_send=lambda event, hint: event,
    )
