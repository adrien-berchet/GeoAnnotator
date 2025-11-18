"""
Unit tests for annotation serializers.

Tests validation, file handling, and quota checks.
"""

from unittest.mock import Mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers as drf_serializers

from apps.annotations.serializers import AnnotationSerializer
from apps.annotations.serializers import CreateFileAnnotationSerializer
from apps.annotations.serializers import CreateTextAnnotationSerializer
from apps.annotations.serializers import UpdateTextAnnotationSerializer
from apps.annotations.serializers import validate_file_size


class TestValidateFileSize:
    """Test file size validation function."""

    def test_validate_file_size_within_limit(self):
        """File within limit should pass validation."""
        file = Mock()
        file.size = 500 * 1024 * 1024  # 500MB
        max_size = 1024 * 1024 * 1024  # 1GB

        # Should not raise
        validate_file_size(file, max_size)

    def test_validate_file_size_exceeds_limit(self):
        """File exceeding limit should raise ValidationError."""
        file = Mock()
        file.size = 2 * 1024 * 1024 * 1024  # 2GB
        max_size = 1024 * 1024 * 1024  # 1GB

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            validate_file_size(file, max_size)

        assert "too big" in str(exc_info.value)


class TestAnnotationSerializer:
    """Test AnnotationSerializer."""

    def test_get_is_trashed_returns_false_when_not_trashed(self, text_annotation):
        """Should return False when annotation has no trash_entry."""
        serializer = AnnotationSerializer(text_annotation)
        assert serializer.data["is_trashed"] is False

    def test_get_trash_days_remaining_returns_none_when_not_trashed(self, text_annotation):
        """Should return None when annotation is not trashed."""
        serializer = AnnotationSerializer(text_annotation)
        assert serializer.data["trash_days_remaining"] is None

    def test_get_trash_id_returns_none_when_not_trashed(self, text_annotation):
        """Should return None when annotation is not trashed."""
        serializer = AnnotationSerializer(text_annotation)
        assert serializer.data["trash_id"] is None

    def test_validate_text_annotation_missing_content(self):
        """Text annotation without text_content should fail."""
        serializer = AnnotationSerializer()

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({"type": "text"})

        assert "text_content" in str(exc_info.value)

    def test_validate_text_annotation_with_file(self):
        """Text annotation with file should fail."""
        serializer = AnnotationSerializer()
        file = SimpleUploadedFile("test.txt", b"content")

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({"type": "text", "text_content": "Test", "file": file})

        assert "cannot have file" in str(exc_info.value)

    def test_validate_image_annotation_missing_file(self):
        """Image annotation without file should fail."""
        serializer = AnnotationSerializer()

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({"type": "image"})

        assert "file" in str(exc_info.value).lower()

    def test_validate_image_annotation_with_text_content(self):
        """Image annotation with text_content should fail."""
        serializer = AnnotationSerializer()
        file = SimpleUploadedFile("test.jpg", b"content")

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({"type": "image", "file": file, "text_content": "Test"})

        assert "cannot have text content" in str(exc_info.value)

    def test_validate_invalid_type(self):
        """Invalid annotation type should fail."""
        serializer = AnnotationSerializer()

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({"type": "invalid"})

        assert "Invalid annotation type" in str(exc_info.value)

    def test_validate_file_quota_exceeded(self, api_request_factory, alice):
        """File upload exceeding quota should fail."""
        # Set alice's quota to nearly full
        alice.storage_limit = 1024 * 1024  # 1MB
        alice.storage_used = 1024 * 1024 - 100  # 100 bytes remaining
        alice.save()

        request = api_request_factory.post("/api/annotations/")
        request.user = alice

        serializer = AnnotationSerializer(context={"request": request})
        large_file = SimpleUploadedFile("test.jpg", b"x" * 200)  # 200 bytes

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_file(large_file)

        error = exc_info.value.detail
        assert error["error"] == "QUOTA_EXCEEDED"


class TestCreateFileAnnotationSerializer:
    """Test CreateFileAnnotationSerializer."""

    def test_validate_type_image_passes(self):
        """Image type should be valid."""
        serializer = CreateFileAnnotationSerializer()
        assert serializer.validate_type("image") == "image"

    def test_validate_type_document_passes(self):
        """Document type should be valid."""
        serializer = CreateFileAnnotationSerializer()
        assert serializer.validate_type("document") == "document"

    def test_validate_type_file_passes(self):
        """File type should be valid."""
        serializer = CreateFileAnnotationSerializer()
        assert serializer.validate_type("file") == "file"

    def test_validate_type_text_fails(self):
        """Text type should fail validation."""
        serializer = CreateFileAnnotationSerializer()

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_type("text")

        assert "Invalid type" in str(exc_info.value)

    def test_validate_file_missing_fails(self, api_request_factory, alice):
        """Missing file should fail validation."""
        request = api_request_factory.post("/api/annotations/")
        request.user = alice

        serializer = CreateFileAnnotationSerializer(context={"request": request})

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_file(None)

        assert "required" in str(exc_info.value)

    def test_validate_file_quota_exceeded(self, api_request_factory, alice):
        """File exceeding quota should fail."""
        alice.storage_limit = 1024 * 1024  # 1MB
        alice.storage_used = 1024 * 1024 - 100  # 100 bytes remaining
        alice.save()

        request = api_request_factory.post("/api/annotations/")
        request.user = alice

        serializer = CreateFileAnnotationSerializer(context={"request": request})
        large_file = SimpleUploadedFile("test.jpg", b"x" * 200)  # 200 bytes

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_file(large_file)

        error = exc_info.value.detail
        assert error["error"] == "QUOTA_EXCEEDED"

    def test_validate_file_too_large(self, api_request_factory, alice):
        """File exceeding size limit should fail."""
        request = api_request_factory.post("/api/annotations/")
        request.user = alice

        serializer = CreateFileAnnotationSerializer(context={"request": request})
        # Mock a file with size > 1GB
        large_file = Mock()
        large_file.size = 2 * 1024 * 1024 * 1024  # 2GB

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate_file(large_file)

        assert "too big" in str(exc_info.value)


class TestCreateTextAnnotationSerializer:
    """Test CreateTextAnnotationSerializer."""

    def test_create_sets_type_to_text(self, gps_point):
        """Creating text annotation should set type to 'text'."""
        serializer = CreateTextAnnotationSerializer()
        data = {"text_content": "Test content", "gps_point": gps_point}

        annotation = serializer.create(data)
        assert annotation.type == "text"


class TestUpdateTextAnnotationSerializer:
    """Test UpdateTextAnnotationSerializer."""

    def test_fields_only_include_text_content(self):
        """Serializer should only expose text_content field."""
        serializer = UpdateTextAnnotationSerializer()
        assert list(serializer.fields.keys()) == ["text_content"]
