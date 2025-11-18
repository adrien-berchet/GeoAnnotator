"""
Unit tests for annotation models.

Tests validation, file handling, and storage management.
"""

import os
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.annotations.models import Annotation
from apps.annotations.models import annotation_file_path


class TestAnnotationFilePathFunction:
    """Test annotation_file_path utility function."""

    def test_generates_correct_path(self, gps_point):
        """Should generate path with point ID and annotation ID."""
        annotation = Mock()
        annotation.id = "test-annotation-id"
        annotation.gps_point = gps_point

        path = annotation_file_path(annotation, "test.jpg")

        expected = os.path.join("annotations", str(gps_point.id), "test-annotation-id", "test.jpg")
        assert path == expected


class TestAnnotationModel:
    """Test Annotation model."""

    def test_clean_text_annotation_without_content_fails(self, gps_point):
        """Text annotation without text_content should fail validation."""
        annotation = Annotation(gps_point=gps_point, type="text")

        with pytest.raises(ValidationError) as exc_info:
            annotation.clean()

        assert "text_content" in str(exc_info.value)

    def test_clean_text_annotation_with_file_fails(self, gps_point):
        """Text annotation with file should fail validation."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.txt", b"content")
        annotation = Annotation(gps_point=gps_point, type="text", text_content="Test", file=file)

        with pytest.raises(ValidationError) as exc_info:
            annotation.clean()

        assert "cannot have files" in str(exc_info.value)

    def test_clean_image_annotation_without_file_fails(self, gps_point):
        """Image annotation without file should fail validation."""
        annotation = Annotation(gps_point=gps_point, type="image")

        with pytest.raises(ValidationError) as exc_info:
            annotation.clean()

        assert "must have a file" in str(exc_info.value)

    def test_clean_image_annotation_with_text_content_fails(self, gps_point):
        """Image annotation with text_content should fail validation."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.jpg", b"content")
        annotation = Annotation(gps_point=gps_point, type="image", file=file, text_content="Test")

        with pytest.raises(ValidationError) as exc_info:
            annotation.clean()

        assert "cannot have text_content" in str(exc_info.value)

    def test_save_sets_can_preview_for_image(self, gps_point):
        """Saving image annotation should set can_preview to True."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        annotation = Annotation(
            gps_point=gps_point, type="image", file=file, mime_type="image/jpeg"
        )

        annotation.save()

        assert annotation.can_preview is True

    def test_save_sets_can_preview_for_pdf(self, gps_point):
        """Saving PDF annotation should set can_preview to True."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        annotation = Annotation(
            gps_point=gps_point, type="document", file=file, mime_type="application/pdf"
        )

        annotation.save()

        assert annotation.can_preview is True

    def test_save_sets_can_preview_false_for_other_types(self, gps_point):
        """Saving non-previewable file should set can_preview to False."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.zip", b"content", content_type="application/zip")
        annotation = Annotation(
            gps_point=gps_point, type="file", file=file, mime_type="application/zip"
        )

        annotation.save()

        assert annotation.can_preview is False

    def test_save_extracts_filename_from_file(self, gps_point):
        """Saving annotation without file_name should extract it from file."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("mytest.jpg", b"content", content_type="image/jpeg")
        annotation = Annotation(
            gps_point=gps_point, type="image", file=file, mime_type="image/jpeg"
        )

        annotation.save()

        assert annotation.file_name == "mytest.jpg"

    def test_is_text_property_returns_true_for_text(self, text_annotation):
        """is_text should return True for text annotations."""
        assert text_annotation.is_text is True

    def test_is_text_property_returns_false_for_image(self, image_annotation):
        """is_text should return False for image annotations."""
        assert image_annotation.is_text is False

    def test_is_file_property_returns_true_for_image(self, image_annotation):
        """is_file should return True for image annotations."""
        assert image_annotation.is_file is True

    def test_is_file_property_returns_true_for_document(self, document_annotation):
        """is_file should return True for document annotations."""
        assert document_annotation.is_file is True

    def test_is_file_property_returns_false_for_text(self, text_annotation):
        """is_file should return False for text annotations."""
        assert text_annotation.is_file is False

    def test_str_returns_text_preview_for_text_annotation(self, text_annotation):
        """__str__ should return text preview for text annotations."""
        text_annotation.text_content = "A" * 100
        result = str(text_annotation)

        assert "Text:" in result
        assert len(result) < 60  # Should be truncated

    def test_str_returns_file_info_for_file_annotation(self, image_annotation):
        """__str__ should return file info for file annotations."""
        result = str(image_annotation)

        assert "Image:" in result
        assert image_annotation.file_name in result

    def test_delete_removes_file_from_storage(self, image_annotation):
        """Deleting annotation should remove file from storage."""

        # Mock storage to verify delete is called
        with patch.object(image_annotation.file.storage, "delete") as mock_delete:
            with patch.object(
                image_annotation.file.storage, "exists", return_value=True
            ) as mock_exists:
                image_annotation.delete()

                mock_exists.assert_called_once_with(image_annotation.file.name)
                mock_delete.assert_called_once_with(image_annotation.file.name)

    def test_delete_updates_user_storage_quota(self, image_annotation):
        """Deleting annotation should update user's storage quota."""
        owner = image_annotation.gps_point.owner
        file_size = image_annotation.file_size
        initial_usage = owner.storage_used

        with patch.object(image_annotation.file.storage, "delete"):
            with patch.object(image_annotation.file.storage, "exists", return_value=True):
                image_annotation.delete()

        owner.refresh_from_db()
        assert owner.storage_used == initial_usage - file_size

    def test_delete_handles_storage_exception_gracefully(self, image_annotation):
        """Deleting annotation should handle storage errors gracefully."""
        # Mock storage.exists to raise exception (e.g., S3 403)
        with patch.object(
            image_annotation.file.storage, "exists", side_effect=Exception("S3 403 Forbidden")
        ):
            with patch.object(image_annotation.file.storage, "delete") as mock_delete:
                # Should not raise exception
                image_annotation.delete()

                # Should still attempt to delete
                mock_delete.assert_called_once()

    def test_delete_handles_delete_exception_gracefully(self, image_annotation):
        """Deleting annotation should handle delete errors gracefully."""
        with patch.object(image_annotation.file.storage, "exists", return_value=True):
            with patch.object(
                image_annotation.file.storage, "delete", side_effect=Exception("Delete failed")
            ):
                # Should not raise exception
                image_annotation.delete()

    def test_delete_text_annotation_does_not_affect_storage(self, text_annotation):
        """Deleting text annotation should not affect storage quota."""
        owner = text_annotation.gps_point.owner
        initial_usage = owner.storage_used

        text_annotation.delete()

        owner.refresh_from_db()
        assert owner.storage_used == initial_usage
