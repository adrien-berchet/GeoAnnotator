"""
Production settings for GeoAnnotator.

Security-focused settings for deployment.
"""

import os

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Production hosts (set via environment variable)
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()]

# Add production-specific apps
INSTALLED_APPS += [
    "storages",  # For S3-compatible storage
]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Note: SECURE_BROWSER_XSS_FILTER is deprecated as of Django 4.0
# Modern browsers have built-in XSS protection enabled by default
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email Configuration - Mailjet API (HTTP instead of SMTP)
# Uses HTTP API to bypass SMTP port blocking on some hosting platforms
EMAIL_BACKEND = "apps.core.mailjet_backend.MailjetBackend"
MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY")
MAILJET_SECRET_KEY = os.environ.get("MAILJET_SECRET_KEY")
DEFAULT_FROM_NAME = os.environ.get("DEFAULT_FROM_NAME", "GeoAnnotator")

# Legacy SMTP config (fallback - can be removed if not needed)
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.environ.get("EMAIL_HOST", "in-v3.mailjet.com")
# EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# File storage (S3-compatible for production)
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-west-3")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")
AWS_DEFAULT_ACL = "private"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "media": {"BACKEND": "storages.backends.s3.S3Storage"},
}

# URL pour accéder aux fichiers
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Logging configuration for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "config": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
