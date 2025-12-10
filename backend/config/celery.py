"""
Celery configuration for GeoAnnotator.

Configures Celery for background task processing and periodic tasks.
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

logger = logging.getLogger(__name__)

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create Celery app
app = Celery("geoannotator")

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


# Log email configuration on startup
@app.on_after_configure.connect
def log_email_config(sender, **kwargs):
    """Log email backend configuration on Celery startup."""

    logger.info("=" * 60)
    logger.info("CELERY EMAIL CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Settings Module: {settings.SETTINGS_MODULE}")
    logger.info(f"Email Backend: {settings.EMAIL_BACKEND}")

    if "mailjet" in settings.EMAIL_BACKEND.lower():
        api_key = getattr(settings, "MAILJET_API_KEY", None)
        secret_key = getattr(settings, "MAILJET_SECRET_KEY", None)
        logger.info("Backend Type: Mailjet HTTP API")
        logger.info(f"API Key Configured: {bool(api_key)}")
        logger.info(f"Secret Key Configured: {bool(secret_key)}")
        if api_key:
            logger.info(f"API Key Preview: {api_key[:8]}...")
        logger.info(f"Default From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        logger.info(f"Default From Name: {getattr(settings, 'DEFAULT_FROM_NAME', 'Not set')}")
    elif "smtp" in settings.EMAIL_BACKEND.lower():
        logger.info("Backend Type: SMTP")
        logger.info(f"SMTP Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        logger.info(f"SMTP Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")

    logger.info("=" * 60)


# Configure periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    "cleanup-deleted-users-daily": {
        "task": "apps.authentication.tasks.cleanup_deleted_users",
        "schedule": crontab(hour=13, minute=0),  # Run daily at 13:00 PM
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
    "cleanup-expired-tokens-daily": {
        "task": "apps.authentication.tasks.cleanup_expired_confirmation_tokens",
        "schedule": crontab(hour=13, minute=30),  # Run daily at 13:30 PM
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
    "backup-database-weekly": {
        "task": "apps.core.tasks.backup_database_task",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Run weekly on Sunday at 2:00 AM
        "options": {
            "expires": 7200,  # Task expires after 2 hours if not executed
        },
    },
}

# Configure timezone for scheduled tasks
app.conf.timezone = "UTC"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f"Request: {self.request!r}")
