"""
Development settings for GeoAnnotator.

Includes debug tools and relaxed security for local development.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in development

# Development email backend (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Add development-specific apps
INSTALLED_APPS += [
    'django_extensions',  # Optional: useful development tools
]

# Django Debug Toolbar (optional)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# File storage (local filesystem for development)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
