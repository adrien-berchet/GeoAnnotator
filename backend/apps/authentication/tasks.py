"""
Celery tasks for authentication app.

Handles periodic cleanup of soft-deleted users and email sending.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailChangeConfirmation
from .models import EmailConfirmation
from .models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, ignore_result=True)
def send_email_async(
    self,
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list[str],
    html_message: str | None = None,
):
    """
    Send email asynchronously via Celery.

    Args:
        subject: Email subject
        message: Plain text message
        from_email: Sender email
        recipient_list: List of recipient emails
        html_message: Optional HTML message

    Retries up to 3 times with 60 second delay between attempts.
    """
    from django.conf import settings

    logger.info(f"📧 Sending email: '{subject}' to {recipient_list}")
    logger.info(f"Using backend: {settings.EMAIL_BACKEND}")

    try:
        # Send email using configured backend (Mailjet HTTP API or SMTP)
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"✅ Email sent successfully: '{subject}' to {recipient_list}")
    except Exception as exc:
        logger.error(f"❌ Email sending failed: {exc}", exc_info=True)
        # Retry on failure (network issues, API errors, etc.)
        raise self.retry(exc=exc) from exc


@shared_task(ignore_result=True)
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


@shared_task(ignore_result=True)
def cleanup_expired_confirmation_tokens():
    """
    Delete expired email confirmation tokens.

    This task should be scheduled to run daily via Celery Beat.
    It removes:
    - EmailConfirmation tokens expired for more than 7 days
    - EmailChangeConfirmation tokens expired for more than 7 days

    Keeping expired tokens for 7 days allows users to understand why
    their link doesn't work (expired vs invalid).

    Returns:
        dict: Statistics about the cleanup operation
            - email_confirmations_deleted: Number of registration confirmations deleted
            - email_change_confirmations_deleted: Number of email change confirmations deleted
            - timestamp: When the cleanup was performed
    """
    # Calculate cutoff (7 days ago)
    cutoff_date = timezone.now() - timedelta(days=7)

    # Delete old EmailConfirmation records (registration)
    email_confirmations = EmailConfirmation.objects.filter(expires_at__lt=cutoff_date)
    email_confirmations_count = email_confirmations.count()
    email_confirmations.delete()

    # Delete old EmailChangeConfirmation records (email changes)
    email_change_confirmations = EmailChangeConfirmation.objects.filter(expires_at__lt=cutoff_date)
    email_change_confirmations_count = email_change_confirmations.count()
    email_change_confirmations.delete()

    return {
        "email_confirmations_deleted": email_confirmations_count,
        "email_change_confirmations_deleted": email_change_confirmations_count,
        "timestamp": timezone.now().isoformat(),
        "cutoff_date": cutoff_date.isoformat(),
    }
