"""
Django management command: cleanup_trash

Permanently deletes expired trash items (retention period > 30 days).

Usage:
    python manage.py cleanup_trash [--dry-run]

Options:
    --dry-run: Show what would be deleted without actually deleting

Scheduled Execution:
    Run this command daily via cron:
    0 2 * * * cd /path/to/project && python manage.py cleanup_trash

    Or use Django-Q, Celery, or APScheduler for periodic tasks.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.trash.models import Trash


class Command(BaseCommand):
    """
    Management command to cleanup expired trash items.
    """

    help = "Permanently delete GPS points in trash that have exceeded 30-day retention period"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information about each deletion",
        )

    def handle(self, *args, **options):
        """
        Execute the cleanup command.

        Args:
            options: Command options (dry_run, verbose)
        """
        dry_run = options.get("dry_run", False)
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.NOTICE("Starting trash cleanup..."))
        self.stdout.write(f"Current time: {timezone.now().isoformat()}")

        # Find expired items
        expired_items = Trash.objects.filter(
            permanent_deletion_at__lte=timezone.now()
        ).select_related("gps_point", "deleted_by")

        total_count = expired_items.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No expired items found"))
            return

        self.stdout.write(self.style.WARNING(f"Found {total_count} expired item(s)"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("[DRY RUN] No items will be deleted"))

        # Process deletions
        deleted_count = 0
        total_size_freed = 0

        for item in expired_items:
            point = item.gps_point
            point_title = point.title
            point_id = point.id
            deleted_at = item.deleted_at
            deleted_by = item.deleted_by.email if item.deleted_by else "Unknown"

            # Calculate storage to be freed (sum of annotation file sizes)
            storage_freed = sum(
                ann.file_size
                for ann in point.annotations.filter(file__isnull=False)
                if ann.file_size
            )

            if verbose or dry_run:
                self.stdout.write(
                    f'  - Point "{point_title}" (ID: {point_id})\n'
                    f"    Deleted by: {deleted_by}\n"
                    f"    Deleted at: {deleted_at.isoformat()}\n"
                    f"    Annotations: {point.annotations.count()}\n"
                    f"    Storage freed: {self._format_size(storage_freed)}"
                )

            if not dry_run:
                # Permanently delete
                point.delete()  # CASCADE will delete Trash, Annotations, Shares
                deleted_count += 1
                total_size_freed += storage_freed

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\n[DRY RUN] Would delete {total_count} item(s)"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully deleted {deleted_count} expired item(s)")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Total storage freed: {self._format_size(total_size_freed)}")
            )

    def _format_size(self, bytes_size):
        """
        Format file size for display.

        Args:
            bytes_size: Size in bytes

        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        if bytes_size == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0

        size = float(bytes_size)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
