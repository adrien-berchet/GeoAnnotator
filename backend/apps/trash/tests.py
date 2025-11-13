"""
Simple test to verify trash models are working.
"""

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase

from apps.annotations.models import Annotation
from apps.points.models import GPSPoint
from apps.trash.models import AnnotationTrash
from apps.trash.models import Trash
from apps.trash.services import AnnotationTrashService
from apps.trash.services import TrashService

User = get_user_model()


class TrashTestCase(TestCase):
    """Test cases for trash functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="test", email="test@trash.com", password="testpassword")

        location = Point(2.3522, 48.8566, srid=4326)  # Paris
        self.point = GPSPoint.objects.create(
            title="Test Point",
            description="Test description",
            location=location,
            owner=self.user,
            is_public=False,
        )

        self.annotation = Annotation.objects.create(
            gps_point=self.point, type="text", text_content="<p>Test annotation</p>", order=0
        )

    def test_annotation_trash_creation(self):
        """Test moving annotation to trash."""
        # Move annotation to trash
        trash = AnnotationTrashService.move_to_trash(self.annotation, self.user)

        # Verify trash entry created
        self.assertIsNotNone(trash)
        self.assertEqual(trash.annotation, self.annotation)
        self.assertEqual(trash.deleted_by, self.user)
        self.assertTrue(trash.days_remaining > 0)
        self.assertFalse(trash.is_expired)

        # Verify point still exists
        self.assertTrue(GPSPoint.objects.filter(id=self.point.id).exists())

    def test_annotation_trash_restore(self):
        """Test restoring annotation from trash."""
        # Move to trash
        trash = AnnotationTrashService.move_to_trash(self.annotation, self.user)
        trash_id = trash.id

        # Restore
        restored = AnnotationTrashService.restore_from_trash(trash)

        # Verify annotation restored
        self.assertEqual(restored.id, self.annotation.id)

        # Verify trash entry deleted
        self.assertFalse(AnnotationTrash.objects.filter(id=trash_id).exists())

    def test_point_trash_creation(self):
        """Test moving point to trash."""
        # Move point to trash
        trash = TrashService.move_to_trash(self.point, self.user)

        # Verify trash entry created
        self.assertIsNotNone(trash)
        self.assertEqual(trash.gps_point, self.point)
        self.assertEqual(trash.deleted_by, self.user)
        self.assertTrue(trash.days_remaining > 0)
        self.assertFalse(trash.is_expired)

        # Verify point still exists (soft delete)
        self.assertTrue(GPSPoint.objects.filter(id=self.point.id).exists())

    def test_point_trash_restore(self):
        """Test restoring point from trash."""
        # Move to trash
        trash = TrashService.move_to_trash(self.point, self.user)
        trash_id = trash.id

        # Restore
        restored = TrashService.restore_from_trash(trash)

        # Verify point restored
        self.assertEqual(restored.id, self.point.id)

        # Verify trash entry deleted
        self.assertFalse(Trash.objects.filter(id=trash_id).exists())

    def test_get_user_trash_stats(self):
        """Test getting trash statistics."""
        # Move annotation to trash
        AnnotationTrashService.move_to_trash(self.annotation, self.user)

        # Get stats
        stats = AnnotationTrashService.get_trash_stats(self.user)

        # Verify stats
        self.assertEqual(stats["total_items"], 1)
        self.assertGreaterEqual(stats["oldest_item_age_days"], 0)
