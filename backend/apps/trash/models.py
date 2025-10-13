"""
Trash model for GeoAnnotator.

Handles soft-deleted GPS points with 30-day retention period.
"""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


class Trash(models.Model):
    """
    Soft-deleted GPS point with 30-day retention period.

    Lifecycle:
    1. Point deleted → Trash entry created, all shares deactivated
    2. Point restored (within 30 days) → Trash entry deleted, shares reactivated
    3. 30 days elapsed → Scheduled task permanently deletes point (CASCADE)
    """

    # Retention period: 30 days
    RETENTION_DAYS = 30

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique trash entry identifier"
    )

    gps_point = models.OneToOneField(
        'points.GPSPoint',
        on_delete=models.CASCADE,
        related_name='trash_entry',
        help_text="Trashed GPS point (one-to-one relationship)"
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deleted_points',
        help_text="User who deleted the point"
    )

    deleted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Deletion timestamp"
    )

    permanent_deletion_at = models.DateTimeField(
        db_index=True,
        help_text="Auto-calculated: deleted_at + 30 days"
    )

    original_is_public = models.BooleanField(
        default=False,
        help_text="Original public status (for restoration)"
    )

    class Meta:
        db_table = 'trash'
        verbose_name = 'Trash Item'
        verbose_name_plural = 'Trash Items'
        indexes = [
            models.Index(fields=['permanent_deletion_at'], name='idx_trash_permanent_deletion'),
            models.Index(fields=['deleted_by'], name='idx_trash_deleted_by'),
            models.Index(fields=['-deleted_at'], name='idx_trash_deleted_at'),
        ]
        ordering = ['-deleted_at']  # Most recent first

    def save(self, *args, **kwargs):
        """Auto-calculate permanent_deletion_at if not set."""
        if not self.permanent_deletion_at:
            self.permanent_deletion_at = self.deleted_at or timezone.now()
            self.permanent_deletion_at += timedelta(days=self.RETENTION_DAYS)

        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Calculate days remaining until permanent deletion."""
        if timezone.now() >= self.permanent_deletion_at:
            return 0

        delta = self.permanent_deletion_at - timezone.now()
        return max(0, delta.days)

    @property
    def is_expired(self):
        """Check if retention period has expired."""
        return timezone.now() >= self.permanent_deletion_at

    def restore(self):
        """
        Restore point from trash.

        Returns:
            GPSPoint: The restored point

        Raises:
            ValueError: If retention period expired
        """
        if self.is_expired:
            raise ValueError("Cannot restore: retention period expired")

        # Restore original public status
        self.gps_point.is_public = self.original_is_public
        self.gps_point.save(update_fields=['is_public'])

        # Reactivate all non-revoked shares
        for share in self.gps_point.shares.all():
            share.reactivate()

        # Get the point before deleting trash entry
        point = self.gps_point

        # Delete trash entry (point is now active)
        self.delete()

        return point

    def __str__(self):
        days = self.days_remaining
        return f"🗑️ {self.gps_point.title} ({days} days remaining)"

    @classmethod
    def cleanup_expired(cls):
        """
        Permanently delete all expired trash items.

        This should be called by a scheduled task (e.g., daily cron job).

        Returns:
            int: Number of points permanently deleted
        """
        expired_items = cls.objects.filter(
            permanent_deletion_at__lte=timezone.now()
        )

        count = 0
        for item in expired_items:
            # Delete the GPS point (CASCADE will delete Trash, Annotations, Shares)
            item.gps_point.delete()
            count += 1

        return count


class AnnotationTrash(models.Model):
    """
    Soft-deleted annotation with 30-day retention period.

    Lifecycle:
    1. Annotation deleted → AnnotationTrash entry created
    2. Annotation restored (within 30 days) → AnnotationTrash entry deleted
    3. 30 days elapsed → Scheduled task permanently deletes annotation

    Note: When a point is deleted, its annotations are deleted via CASCADE,
    NOT moved to AnnotationTrash. AnnotationTrash is only for individually
    deleted annotations.
    """

    # Retention period: 30 days
    RETENTION_DAYS = 30

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique trash entry identifier"
    )

    annotation = models.OneToOneField(
        'annotations.Annotation',
        on_delete=models.CASCADE,
        related_name='trash_entry',
        help_text="Trashed annotation (one-to-one relationship)"
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deleted_annotations',
        help_text="User who deleted the annotation"
    )

    deleted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Deletion timestamp"
    )

    permanent_deletion_at = models.DateTimeField(
        db_index=True,
        help_text="Auto-calculated: deleted_at + 30 days"
    )

    class Meta:
        db_table = 'annotation_trash'
        verbose_name = 'Annotation Trash Item'
        verbose_name_plural = 'Annotation Trash Items'
        indexes = [
            models.Index(fields=['permanent_deletion_at'], name='idx_annot_trash_perm_del'),
            models.Index(fields=['deleted_by'], name='idx_annot_trash_deleted_by'),
            models.Index(fields=['-deleted_at'], name='idx_annot_trash_deleted_at'),
        ]
        ordering = ['-deleted_at']  # Most recent first

    def save(self, *args, **kwargs):
        """Auto-calculate permanent_deletion_at if not set."""
        if not self.permanent_deletion_at:
            self.permanent_deletion_at = self.deleted_at or timezone.now()
            self.permanent_deletion_at += timedelta(days=self.RETENTION_DAYS)

        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Calculate days remaining until permanent deletion."""
        if timezone.now() >= self.permanent_deletion_at:
            return 0

        delta = self.permanent_deletion_at - timezone.now()
        return max(0, delta.days)

    @property
    def is_expired(self):
        """Check if retention period has expired."""
        return timezone.now() >= self.permanent_deletion_at

    def restore(self):
        """
        Restore annotation from trash.

        Returns:
            Annotation: The restored annotation

        Raises:
            ValueError: If retention period expired
        """
        if self.is_expired:
            raise ValueError("Cannot restore: retention period expired")

        # Get the annotation before deleting trash entry
        annotation = self.annotation

        # Delete trash entry (annotation is now active)
        self.delete()

        return annotation

    def __str__(self):
        days = self.days_remaining
        return f"🗑️ Annotation {self.annotation.id} ({days} days remaining)"

    @classmethod
    def cleanup_expired(cls):
        """
        Permanently delete all expired annotation trash items.

        This should be called by a scheduled task (e.g., daily cron job).

        Returns:
            int: Number of annotations permanently deleted
        """
        expired_items = cls.objects.filter(
            permanent_deletion_at__lte=timezone.now()
        )

        count = 0
        for item in expired_items:
            # Delete the annotation (will reclaim quota)
            item.annotation.delete()
            count += 1

        return count
