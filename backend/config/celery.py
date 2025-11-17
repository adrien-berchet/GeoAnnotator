"""
Celery configuration for GeoAnnotator.

Configures Celery for background task processing and periodic tasks.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create Celery app
app = Celery("geoannotator")

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    "cleanup-deleted-users-daily": {
        "task": "apps.authentication.tasks.cleanup_deleted_users",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
    "cleanup-expired-tokens-daily": {
        "task": "apps.authentication.tasks.cleanup_expired_confirmation_tokens",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3:00 AM
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
}

# Configure timezone for scheduled tasks
app.conf.timezone = "UTC"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f"Request: {self.request!r}")
