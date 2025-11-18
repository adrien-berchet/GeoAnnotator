"""
Unit tests for trash serializers.

Tests validation for trash, restore, and permanent deletion operations.
"""

from datetime import timedelta

from django.utils import timezone

from apps.trash.models import AnnotationTrash
from apps.trash.models import Trash
from apps.trash.serializers import AnnotationTrashSerializer
from apps.trash.serializers import DeleteAnnotationPermanentlySerializer
from apps.trash.serializers import DeletePermanentlySerializer
from apps.trash.serializers import EmptyAnnotationTrashSerializer
from apps.trash.serializers import EmptyTrashSerializer
from apps.trash.serializers import RestoreAnnotationTrashSerializer
from apps.trash.serializers import RestoreTrashSerializer
from apps.trash.serializers import TrashSerializer


class TestTrashSerializer:
    """Test TrashSerializer."""

    def test_serializer_contains_all_fields(self, trash_entry_alice):
        """Serializer should include all expected fields."""
        serializer = TrashSerializer(trash_entry_alice)
        data = serializer.data

        assert "id" in data
        assert "gps_point" in data
        assert "deleted_by" in data
        assert "deleted_at" in data
        assert "permanent_deletion_at" in data
        assert "days_remaining" in data
        assert "is_expired" in data
        assert "annotations" in data
        assert "shares" in data

    def test_get_days_remaining(self, trash_entry_alice):
        """Should calculate days remaining correctly."""
        serializer = TrashSerializer(trash_entry_alice)
        data = serializer.data

        assert "days_remaining" in data
        assert isinstance(data["days_remaining"], int)
        assert data["days_remaining"] >= 0

    def test_get_is_expired(self, trash_entry_alice):
        """Should determine expiration status correctly."""
        serializer = TrashSerializer(trash_entry_alice)
        data = serializer.data

        assert "is_expired" in data
        assert isinstance(data["is_expired"], bool)

    def test_get_annotations(self, trash_entry_alice, text_annotation):
        """Should include annotations for trashed point."""
        # Add annotation to the trashed point
        text_annotation.gps_point = trash_entry_alice.gps_point
        text_annotation.save()

        serializer = TrashSerializer(trash_entry_alice)
        data = serializer.data

        assert "annotations" in data
        assert isinstance(data["annotations"], list)

    def test_get_shares(self, trash_entry_alice, alice, bob):
        """Should include shares for trashed point."""
        from apps.sharing.models import Share

        # Create a share for the trashed point
        Share.objects.create(
            gps_point=trash_entry_alice.gps_point,
            owner=alice,
            recipient_email=bob.email,
            recipient_user=bob,
        )

        serializer = TrashSerializer(trash_entry_alice)
        data = serializer.data

        assert "shares" in data
        assert isinstance(data["shares"], list)


class TestRestoreTrashSerializer:
    """Test RestoreTrashSerializer."""

    def test_validate_expired_trash_fails(self, api_request_factory, alice, trash_entry_alice):
        """Should fail to restore expired trash."""
        request = api_request_factory.post("/api/trash/restore/")
        request.user = alice

        # Make trash expired
        trash_entry_alice.deleted_at = timezone.now() - timedelta(days=31)
        trash_entry_alice.permanent_deletion_at = timezone.now() - timedelta(days=1)
        trash_entry_alice.save()

        serializer = RestoreTrashSerializer(
            trash_entry_alice, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        # Check for error in validation errors (dict format)
        errors = serializer.errors
        assert "error" in str(errors) or "PERMANENTLY_DELETED" in str(errors)

    def test_validate_unauthorized_restore_fails(self, api_request_factory, bob, trash_entry_alice):
        """Should fail to restore trash without permission."""
        request = api_request_factory.post("/api/trash/restore/")
        request.user = bob  # Bob is not owner or deleter

        serializer = RestoreTrashSerializer(
            trash_entry_alice, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        errors = serializer.errors
        assert "error" in str(errors) or "ACCESS_DENIED" in str(errors)

    def test_validate_owner_can_restore(self, api_request_factory, alice, trash_entry_alice):
        """Owner should be able to restore trash."""
        request = api_request_factory.post("/api/trash/restore/")
        request.user = alice

        serializer = RestoreTrashSerializer(
            trash_entry_alice, data={}, context={"request": request}
        )

        assert serializer.is_valid(raise_exception=True)

    def test_save_restores_point(self, api_request_factory, alice, trash_entry_alice):
        """Save should restore point from trash."""
        request = api_request_factory.post("/api/trash/restore/")
        request.user = alice

        serializer = RestoreTrashSerializer(
            trash_entry_alice, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        restored_point = serializer.save()
        assert restored_point == trash_entry_alice.gps_point

        # Verify trash entry is deleted
        assert not Trash.objects.filter(id=trash_entry_alice.id).exists()


class TestDeletePermanentlySerializer:
    """Test DeletePermanentlySerializer."""

    def test_validate_non_owner_fails(self, api_request_factory, bob, trash_entry_alice):
        """Non-owner should not be able to permanently delete."""
        request = api_request_factory.delete("/api/trash/delete/")
        request.user = bob

        serializer = DeletePermanentlySerializer(
            trash_entry_alice, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        errors = serializer.errors
        assert "error" in str(errors) or "ACCESS_DENIED" in str(errors)

    def test_validate_owner_can_delete(self, api_request_factory, alice, trash_entry_alice):
        """Owner should be able to permanently delete."""
        request = api_request_factory.delete("/api/trash/delete/")
        request.user = alice

        serializer = DeletePermanentlySerializer(
            trash_entry_alice, data={}, context={"request": request}
        )

        assert serializer.is_valid(raise_exception=True)

    def test_save_deletes_permanently(self, api_request_factory, alice, trash_entry_alice):
        """Save should permanently delete point and trash entry."""
        request = api_request_factory.delete("/api/trash/delete/")
        request.user = alice

        point_id = trash_entry_alice.gps_point.id
        trash_id = trash_entry_alice.id

        serializer = DeletePermanentlySerializer(
            trash_entry_alice, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        assert result is None

        # Verify both deleted
        from apps.points.models import GPSPoint

        assert not GPSPoint.objects.filter(id=point_id).exists()
        assert not Trash.objects.filter(id=trash_id).exists()


class TestEmptyTrashSerializer:
    """Test EmptyTrashSerializer."""

    def test_validate_counts_items(
        self, api_request_factory, alice, trash_entry_alice, trash_entry_bob
    ):
        """Validate should count trash items for user."""
        request = api_request_factory.post("/api/trash/empty/")
        request.user = alice

        serializer = EmptyTrashSerializer(data={}, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

        # Alice should have 1 trash item
        assert serializer.context["count"] == 1

    def test_save_deletes_all_user_trash(
        self, api_request_factory, alice, trash_entry_alice, trash_entry_bob
    ):
        """Save should delete all trash for current user only."""
        request = api_request_factory.post("/api/trash/empty/")
        request.user = alice

        alice_point_id = trash_entry_alice.gps_point.id

        serializer = EmptyTrashSerializer(data={}, context={"request": request})
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        assert result["deleted_count"] == 1

        # Verify Alice's trash deleted, Bob's remains
        from apps.points.models import GPSPoint

        assert not GPSPoint.objects.filter(id=alice_point_id).exists()
        assert Trash.objects.filter(id=trash_entry_bob.id).exists()


class TestAnnotationTrashSerializer:
    """Test AnnotationTrashSerializer."""

    def test_serializer_contains_all_fields(self, annotation_trash_entry):
        """Serializer should include all expected fields."""
        serializer = AnnotationTrashSerializer(annotation_trash_entry)
        data = serializer.data

        assert "id" in data
        assert "annotation" in data
        assert "gps_point" in data
        assert "deleted_by" in data
        assert "deleted_at" in data
        assert "permanent_deletion_at" in data
        assert "days_remaining" in data
        assert "is_expired" in data

    def test_get_days_remaining(self, annotation_trash_entry):
        """Should calculate days remaining correctly."""
        serializer = AnnotationTrashSerializer(annotation_trash_entry)
        data = serializer.data

        assert "days_remaining" in data
        assert isinstance(data["days_remaining"], int)

    def test_get_is_expired(self, annotation_trash_entry):
        """Should determine expiration status correctly."""
        serializer = AnnotationTrashSerializer(annotation_trash_entry)
        data = serializer.data

        assert "is_expired" in data
        assert isinstance(data["is_expired"], bool)

    def test_get_gps_point(self, annotation_trash_entry):
        """Should include associated GPS point."""
        serializer = AnnotationTrashSerializer(annotation_trash_entry)
        data = serializer.data

        assert "gps_point" in data
        assert isinstance(data["gps_point"], dict)


class TestRestoreAnnotationTrashSerializer:
    """Test RestoreAnnotationTrashSerializer."""

    def test_validate_expired_annotation_trash_fails(
        self, api_request_factory, alice, annotation_trash_entry
    ):
        """Should fail to restore expired annotation trash."""
        request = api_request_factory.post("/api/trash/annotations/restore/")
        request.user = alice

        # Make annotation trash expired
        annotation_trash_entry.deleted_at = timezone.now() - timedelta(days=31)
        annotation_trash_entry.permanent_deletion_at = timezone.now() - timedelta(days=1)
        annotation_trash_entry.save()

        serializer = RestoreAnnotationTrashSerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        errors = serializer.errors
        assert "error" in str(errors) or "PERMANENTLY_DELETED" in str(errors)

    def test_validate_unauthorized_restore_fails(
        self, api_request_factory, bob, annotation_trash_entry
    ):
        """Should fail to restore annotation trash without permission."""
        request = api_request_factory.post("/api/trash/annotations/restore/")
        request.user = bob  # Bob is not owner or deleter

        serializer = RestoreAnnotationTrashSerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        errors = serializer.errors
        assert "error" in str(errors) or "ACCESS_DENIED" in str(errors)

    def test_validate_owner_can_restore(self, api_request_factory, alice, annotation_trash_entry):
        """Point owner should be able to restore annotation trash."""
        request = api_request_factory.post("/api/trash/annotations/restore/")
        request.user = alice

        serializer = RestoreAnnotationTrashSerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )

        assert serializer.is_valid(raise_exception=True)

    def test_save_restores_annotation(self, api_request_factory, alice, annotation_trash_entry):
        """Save should restore annotation from trash."""
        request = api_request_factory.post("/api/trash/annotations/restore/")
        request.user = alice

        serializer = RestoreAnnotationTrashSerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        restored_annotation = serializer.save()
        assert restored_annotation == annotation_trash_entry.annotation

        # Verify trash entry is deleted
        assert not AnnotationTrash.objects.filter(id=annotation_trash_entry.id).exists()


class TestDeleteAnnotationPermanentlySerializer:
    """Test DeleteAnnotationPermanentlySerializer."""

    def test_validate_non_owner_fails(self, api_request_factory, bob, annotation_trash_entry):
        """Non-owner should not be able to permanently delete annotation."""
        request = api_request_factory.delete("/api/trash/annotations/delete/")
        request.user = bob

        serializer = DeleteAnnotationPermanentlySerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )

        assert not serializer.is_valid()
        errors = serializer.errors
        assert "error" in str(errors) or "ACCESS_DENIED" in str(errors)

    def test_validate_owner_can_delete(self, api_request_factory, alice, annotation_trash_entry):
        """Point owner should be able to permanently delete annotation."""
        request = api_request_factory.delete("/api/trash/annotations/delete/")
        request.user = alice

        serializer = DeleteAnnotationPermanentlySerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )

        assert serializer.is_valid(raise_exception=True)

    def test_save_deletes_permanently(self, api_request_factory, alice, annotation_trash_entry):
        """Save should permanently delete annotation and trash entry."""
        request = api_request_factory.delete("/api/trash/annotations/delete/")
        request.user = alice

        annotation_id = annotation_trash_entry.annotation.id
        trash_id = annotation_trash_entry.id

        serializer = DeleteAnnotationPermanentlySerializer(
            annotation_trash_entry, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        assert result is None

        # Verify both deleted
        from apps.annotations.models import Annotation

        assert not Annotation.objects.filter(id=annotation_id).exists()
        assert not AnnotationTrash.objects.filter(id=trash_id).exists()


class TestEmptyAnnotationTrashSerializer:
    """Test EmptyAnnotationTrashSerializer."""

    def test_validate_counts_items(
        self, api_request_factory, alice, annotation_trash_entry, bob, annotation_trash_bob
    ):
        """Validate should count annotation trash items for user's points."""
        request = api_request_factory.post("/api/trash/annotations/empty/")
        request.user = alice

        serializer = EmptyAnnotationTrashSerializer(data={}, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

        # Alice should have 1 annotation trash item
        assert serializer.context["count"] == 1

    def test_save_deletes_all_user_annotation_trash(
        self, api_request_factory, alice, annotation_trash_entry, annotation_trash_bob
    ):
        """Save should delete all annotation trash for current user's points only."""
        request = api_request_factory.post("/api/trash/annotations/empty/")
        request.user = alice

        alice_annotation_id = annotation_trash_entry.annotation.id

        serializer = EmptyAnnotationTrashSerializer(data={}, context={"request": request})
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        assert result["deleted_count"] == 1

        # Verify Alice's annotation trash deleted, Bob's remains
        from apps.annotations.models import Annotation

        assert not Annotation.objects.filter(id=alice_annotation_id).exists()
        assert AnnotationTrash.objects.filter(id=annotation_trash_bob.id).exists()
