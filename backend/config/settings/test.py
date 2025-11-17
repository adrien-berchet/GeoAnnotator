"""
Test settings for GeoAnnotator.

Settings optimized for running tests in CI and locally.
"""

import os

from .base import *

# Disable debug for more realistic testing
DEBUG = False

# Required for tests
ALLOWED_HOSTS = ["*"]

# Use simple password hashers for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use filesystem storage for tests
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Disable S3 storage for tests
AWS_STORAGE_BUCKET_NAME = None

# Email backend for tests (in-memory)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery settings for tests - run tasks synchronously without Redis
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks immediately without worker
CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions in eager mode
CELERY_BROKER_URL = "memory://"  # Use in-memory broker for tests
CELERY_RESULT_BACKEND = "cache+memory://"  # Use in-memory result backend

# Simplify middleware for tests
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Disable CORS checks in tests
CORS_ALLOW_ALL_ORIGINS = True

# Minimal logging for tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}

# Use a faster SECRET_KEY for tests
SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-for-ci-and-local-tests")
