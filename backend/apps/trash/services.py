"""
Trash services.

Handles soft deletion, 30-day retention, and restoration logic for points and annotations.
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from .models import Trash, AnnotationTrash
from apps.points.models import GPSPoint
from apps.annotations.models import Annotation
from apps.authentication.models import User


class TrashService:
    """Service for trash management."""

    RETENTION_DAYS = 30

    @staticmethod
    def move_to_trash(point: GPSPoint, user: User) -> Trash:
        """
        Move point to trash (soft delete).

        Args:
            point: GPSPoint to delete
            user: User performing deletion

        Returns:
            Trash object
        """
        # Create trash entry (model auto-calculates permanent_deletion_at)
        trash = Trash.objects.create(
            gps_point=point,
            deleted_by=user,
        )

        # Deactivate shares
        from apps.sharing.services import ShareService
        ShareService.deactivate_shares_for_point(point)

        return trash

    @staticmethod
    def restore_from_trash(trash: Trash) -> GPSPoint:
        """
        Restore point from trash.

        Args:
            trash: Trash object

        Returns:
            Restored GPSPoint object

        Raises:
            ValueError: If point has expired
        """
        if trash.is_expired:
            raise ValueError('Point has been permanently deleted (>30 days)')

        # Use model's restore method (reactivates shares and deletes trash entry)
        trash.restore()

        return trash.gps_point

    @staticmethod
    def permanently_delete(trash: Trash, user: User) -> None:
        """
        Permanently delete point from trash.

        Args:
            trash: Trash object
            user: User performing deletion

        Raises:
            ValueError: If user is not owner
        """
        if trash.gps_point.owner != user:
            raise ValueError('Only the point owner can permanently delete')

        point = trash.gps_point

        # Delete point (cascades to annotations, shares)
        # Annotations model delete() method will reclaim quota
        point.delete()

        # Trash entry will be deleted by cascade

    @staticmethod
    def empty_trash(user: User) -> int:
        """
        Permanently delete all trashed points for user.

        Args:
            user: User whose trash to empty

        Returns:
            int: Number of points deleted
        """
        trash_items = Trash.objects.filter(gps_point__owner=user)
        count = trash_items.count()

        for trash in trash_items:
            # Delete point (cascades)
            trash.gps_point.delete()

        return count

    @staticmethod
    def get_user_trash(user: User) -> list[Trash]:
        """
        Get all trash items for user.

        Args:
            user: User object

        Returns:
            QuerySet of Trash objects
        """
        return Trash.objects.filter(gps_point__owner=user).order_by('-deleted_at')

    @staticmethod
    def cleanup_expired() -> int:
        """
        Cleanup expired trash items (>30 days).

        This should be run as a scheduled task (e.g., daily cron job).

        Returns:
            int: Number of points permanently deleted
        """
        expired_trash = Trash.objects.filter(is_expired=True)
        count = expired_trash.count()

        for trash in expired_trash:
            # Delete point (cascades)
            trash.gps_point.delete()

        return count

    @staticmethod
    def get_trash_stats(user: User) -> dict:
        """
        Get trash statistics for user.

        Args:
            user: User object

        Returns:
            dict: {
                'total_items': int,
                'expiring_soon': int (< 7 days),
                'oldest_item_age_days': int,
            }
        """
        trash_items = Trash.objects.filter(gps_point__owner=user)
        total = trash_items.count()

        if total == 0:
            return {
                'total_items': 0,
                'expiring_soon': 0,
                'oldest_item_age_days': 0,
            }

        # Count items expiring soon (<7 days remaining)
        expiring_soon = sum(
            1 for item in trash_items if item.days_remaining <= 7
        )

        # Get oldest item
        oldest = trash_items.order_by('deleted_at').first()
        oldest_age = (timezone.now() - oldest.deleted_at).days

        return {
            'total_items': total,
            'expiring_soon': expiring_soon,
            'oldest_item_age_days': oldest_age,
        }


class AnnotationTrashService:
    """Service for annotation trash management."""

    RETENTION_DAYS = 30

    @staticmethod
    def move_to_trash(annotation: Annotation, user: User) -> AnnotationTrash:
        """
        Move annotation to trash (soft delete).

        Args:
            annotation: Annotation to delete
            user: User performing deletion

        Returns:
            AnnotationTrash object
        """
        # Create annotation trash entry (model auto-calculates permanent_deletion_at)
        annotation_trash = AnnotationTrash.objects.create(
            annotation=annotation,
            deleted_by=user,
        )

        return annotation_trash

    @staticmethod
    def restore_from_trash(annotation_trash: AnnotationTrash) -> Annotation:
        """
        Restore annotation from trash.

        Args:
            annotation_trash: AnnotationTrash object

        Returns:
            Restored Annotation object

        Raises:
            ValueError: If annotation has expired
        """
        if annotation_trash.is_expired:
            raise ValueError('Annotation has been permanently deleted (>30 days)')

        # Use model's restore method (deletes trash entry)
        annotation_trash.restore()

        return annotation_trash.annotation

    @staticmethod
    def permanently_delete(annotation_trash: AnnotationTrash, user: User) -> None:
        """
        Permanently delete annotation from trash.

        Args:
            annotation_trash: AnnotationTrash object
            user: User performing deletion

        Raises:
            ValueError: If user is not point owner
        """
        if annotation_trash.annotation.gps_point.owner != user:
            raise ValueError('Only the point owner can permanently delete')

        annotation = annotation_trash.annotation

        # Delete annotation (reclaims quota)
        annotation.delete()

        # Trash entry will be deleted by cascade

    @staticmethod
    def empty_trash(user: User) -> int:
        """
        Permanently delete all trashed annotations for user's points.

        Args:
            user: User whose annotation trash to empty

        Returns:
            int: Number of annotations deleted
        """
        annotation_trash_items = AnnotationTrash.objects.filter(
            annotation__gps_point__owner=user
        )
        count = annotation_trash_items.count()

        for annotation_trash in annotation_trash_items:
            # Delete annotation (cascades)
            annotation_trash.annotation.delete()

        return count

    @staticmethod
    def get_user_trash(user: User) -> list[AnnotationTrash]:
        """
        Get all annotation trash items for user's points.

        Args:
            user: User object

        Returns:
            QuerySet of AnnotationTrash objects
        """
        return AnnotationTrash.objects.filter(
            annotation__gps_point__owner=user
        ).order_by('-deleted_at')

    @staticmethod
    def cleanup_expired() -> int:
        """
        Cleanup expired annotation trash items (>30 days).

        This should be run as a scheduled task (e.g., daily cron job).

        Returns:
            int: Number of annotations permanently deleted
        """
        expired_trash = AnnotationTrash.objects.filter(is_expired=True)
        count = expired_trash.count()

        for annotation_trash in expired_trash:
            # Delete annotation (cascades)
            annotation_trash.annotation.delete()

        return count

    @staticmethod
    def get_trash_stats(user: User) -> dict:
        """
        Get annotation trash statistics for user.

        Args:
            user: User object

        Returns:
            dict: {
                'total_items': int,
                'expiring_soon': int (< 7 days),
                'oldest_item_age_days': int,
            }
        """
        annotation_trash_items = AnnotationTrash.objects.filter(
            annotation__gps_point__owner=user
        )
        total = annotation_trash_items.count()

        if total == 0:
            return {
                'total_items': 0,
                'expiring_soon': 0,
                'oldest_item_age_days': 0,
            }

        # Count items expiring soon (<7 days remaining)
        expiring_soon = sum(
            1 for item in annotation_trash_items if item.days_remaining <= 7
        )

        # Get oldest item
        oldest = annotation_trash_items.order_by('deleted_at').first()
        oldest_age = (timezone.now() - oldest.deleted_at).days

        return {
            'total_items': total,
            'expiring_soon': expiring_soon,
            'oldest_item_age_days': oldest_age,
        }
