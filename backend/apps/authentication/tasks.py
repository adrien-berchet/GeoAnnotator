"""
Celery tasks for authentication app.

Handles periodic cleanup of soft-deleted users and other background tasks.
"""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import User


@shared_task
def cleanup_deleted_users():
    """
    Permanently delete users who have been soft-deleted for more than 30 days.

    This task should be scheduled to run daily via Celery Beat.
    It finds all users with deleted_at timestamp older than 30 days and
    permanently removes them from the database.

    Returns:
        dict: Statistics about the cleanup operation
            - users_deleted: Number of users permanently deleted
            - timestamp: When the cleanup was performed
    """
    # Calculate the cutoff date (30 days ago)
    cutoff_date = timezone.now() - timedelta(days=30)

    # Find users deleted more than 30 days ago
    users_to_delete = User.objects.filter(deleted_at__isnull=False, deleted_at__lt=cutoff_date)

    # Count before deletion
    count = users_to_delete.count()

    # Permanently delete these users
    # This will cascade delete related records (EmailChangeConfirmation, AccountLog, etc.)
    users_to_delete.delete()

    return {
        "users_deleted": count,
        "timestamp": timezone.now().isoformat(),
        "cutoff_date": cutoff_date.isoformat(),
    }
