"""
Celery tasks for core functionality.

Background tasks for system maintenance and operations.
"""

import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def backup_database_task(self):
    """
    Celery task to create and upload database backup to S3.

    Scheduled to run weekly via Celery Beat.
    See config/celery.py for schedule configuration.

    Returns:
        dict: Backup result summary
    """
    logger.info("Starting scheduled database backup")

    try:
        # Call the management command
        # Verbose output will be logged by the command
        call_command(
            "backup_database",
            verbosity=1,  # Normal output
            retention_days=90,  # Keep 90 days of backups
            skip_cleanup=False,  # Cleanup old backups
        )

        logger.info("Database backup completed successfully")
        return {"status": "success", "message": "Database backup completed"}

    except Exception as e:
        logger.exception(f"Database backup failed: {e}")
        # Don't raise - let Celery log the error but don't retry
        return {"status": "error", "message": str(e)}
