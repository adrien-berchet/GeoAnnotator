"""
Annotations services.

Handles file uploads, storage quota management, and preview generation.
"""

import mimetypes
from io import BytesIO

from django.core.files.uploadedfile import UploadedFile
from django.db import models as db_models
from PIL import Image

from apps.authentication.models import User

from .models import Annotation


class StorageQuotaService:
    """Service for managing user storage quotas."""

    @staticmethod
    def check_quota(user: User, file_size: int) -> bool:
        """
        Check if user has enough storage quota for a file.

        Args:
            user: User object
            file_size: File size in bytes

        Returns:
            bool: True if quota available, False otherwise
        """
        return user.has_storage_quota(file_size)

    @staticmethod
    def add_usage(user: User, file_size: int) -> None:
        """
        Add file size to user's storage usage.

        Args:
            user: User object
            file_size: File size in bytes
        """
        user.add_storage_usage(file_size)

    @staticmethod
    def remove_usage(user: User, file_size: int) -> None:
        """
        Remove file size from user's storage usage (on file deletion).

        Args:
            user: User object
            file_size: File size in bytes
        """
        user.remove_storage_usage(file_size)

    @staticmethod
    def get_available_quota(user: User) -> int:
        """
        Get available storage quota for user.

        Args:
            user: User object

        Returns:
            int: Available bytes
        """
        return user.storage_limit - user.storage_used

    @staticmethod
    def reclaim_quota_for_point(point_id: str, user: User) -> int:
        """
        Reclaim storage quota for all annotations of a point.

        Args:
            point_id: GPSPoint UUID
            user: User object

        Returns:
            int: Total bytes reclaimed
        """
        annotations = Annotation.objects.filter(gps_point_id=point_id, file__isnull=False)

        total_reclaimed = 0
        for annotation in annotations:
            if annotation.file_size:
                user.remove_storage_usage(annotation.file_size)
                total_reclaimed += annotation.file_size

        return total_reclaimed

    @staticmethod
    def is_quota_warning(user: User) -> bool:
        """
        Check if user is at quota warning threshold (90% or more).

        Args:
            user: User object

        Returns:
            bool: True if at or above 90% quota usage
        """
        if user.storage_limit == 0:
            return False
        usage_percentage = (user.storage_used / user.storage_limit) * 100
        return usage_percentage >= 90.0

    @staticmethod
    def get_quota_info(user: User) -> dict:
        """
        Get detailed quota information for user.

        Args:
            user: User object

        Returns:
            dict: Quota information including usage, limit, remaining, percentage
        """
        storage_remaining = user.storage_limit - user.storage_used
        usage_percentage = (
            (user.storage_used / user.storage_limit * 100) if user.storage_limit > 0 else 0
        )

        return {
            "storage_used": user.storage_used,
            "storage_limit": user.storage_limit,
            "storage_remaining": storage_remaining,
            "usage_percentage": round(usage_percentage, 2),
            "is_warning": StorageQuotaService.is_quota_warning(user),
        }


class FileUploadService:
    """Service for file uploads and validation."""

    # Max file size: 1GB
    MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024

    # Allowed MIME types
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }

    ALLOWED_DOCUMENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
    }

    DISALLOWED_TYPES = {
        "application/x-executable",
        "application/x-sharedlib",
        "application/x-sh",
        "application/x-python-code",
        "application/javascript",
    }

    @staticmethod
    def validate_file(uploaded_file: UploadedFile, annotation_type: str) -> dict:
        """
        Validate uploaded file.

        Args:
            uploaded_file: Django UploadedFile
            annotation_type: 'image', 'document', or 'file'

        Returns:
            dict: {
                'valid': bool,
                'error': str (if not valid),
                'mime_type': str,
                'file_size': int
            }
        """
        # Check file size
        if uploaded_file.size > FileUploadService.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File size ({uploaded_file.size} bytes) exceeds maximum (1GB)",
            }

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type:
            mime_type = uploaded_file.content_type

        # Check for disallowed types
        if mime_type in FileUploadService.DISALLOWED_TYPES:
            return {
                "valid": False,
                "error": f"File type {mime_type} is not allowed",
            }

        # Type-specific validation
        if annotation_type == "image":
            if mime_type not in FileUploadService.ALLOWED_IMAGE_TYPES:
                return {
                    "valid": False,
                    "error": f"Invalid image type: {mime_type}",
                }
        elif annotation_type == "document":
            if mime_type not in FileUploadService.ALLOWED_DOCUMENT_TYPES:
                return {
                    "valid": False,
                    "error": f"Invalid document type: {mime_type}",
                }

        return {
            "valid": True,
            "mime_type": mime_type,
            "file_size": uploaded_file.size,
        }

    @staticmethod
    def can_preview(mime_type: str) -> bool:
        """
        Check if file type supports preview.

        Args:
            mime_type: MIME type string

        Returns:
            bool: True if previewable
        """
        previewable_types = FileUploadService.ALLOWED_IMAGE_TYPES | {"application/pdf"}
        return mime_type in previewable_types


class ImagePreviewService:
    """Service for generating image previews."""

    MAX_PREVIEW_WIDTH = 1920
    MAX_PREVIEW_HEIGHT = 1080

    @staticmethod
    def generate_preview(image_file, max_width: int = None, max_height: int = None) -> BytesIO:
        """
        Generate resized preview for an image.

        Args:
            image_file: File object
            max_width: Maximum width (default 1920)
            max_height: Maximum height (default 1080)

        Returns:
            BytesIO: Resized image bytes
        """
        max_width = max_width or ImagePreviewService.MAX_PREVIEW_WIDTH
        max_height = max_height or ImagePreviewService.MAX_PREVIEW_HEIGHT

        # Open image
        img = Image.open(image_file)

        # Calculate new size maintaining aspect ratio
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to BytesIO
        output = BytesIO()
        img_format = img.format or "JPEG"
        img.save(output, format=img_format, quality=85)
        output.seek(0)

        return output

    @staticmethod
    def get_image_dimensions(image_file) -> tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image_file: File object

        Returns:
            tuple: (width, height)
        """
        img = Image.open(image_file)
        return img.size


class AnnotationService:
    """Service for annotation operations."""

    @staticmethod
    def create_text_annotation(
        gps_point_id: str,
        text_content: str,
    ) -> Annotation:
        """
        Create text annotation.

        Args:
            gps_point_id: GPSPoint UUID
            text_content: HTML text content

        Returns:
            Annotation object
        """
        # Get max order for this point and increment
        max_order = (
            Annotation.objects.filter(gps_point_id=gps_point_id).aggregate(db_models.Max("order"))[
                "order__max"
            ]
            or -1
        )

        return Annotation.objects.create(
            gps_point_id=gps_point_id,
            type="text",
            text_content=text_content,
            order=max_order + 1,
        )

    @staticmethod
    def create_file_annotation(
        gps_point_id: str,
        annotation_type: str,
        uploaded_file: UploadedFile,
        user: User,
    ) -> Annotation:
        """
        Create file annotation (image/document/file).

        Args:
            gps_point_id: GPSPoint UUID
            annotation_type: 'image', 'document', or 'file'
            uploaded_file: Django UploadedFile
            user: User (for quota management)

        Returns:
            Annotation object

        Raises:
            ValueError: If validation fails or quota exceeded
        """
        # Validate file
        validation = FileUploadService.validate_file(uploaded_file, annotation_type)
        if not validation["valid"]:
            raise ValueError(validation["error"])

        # Check quota
        if not StorageQuotaService.check_quota(user, validation["file_size"]):
            raise ValueError(
                f"Insufficient storage quota. "
                f"Required: {validation['file_size']} bytes, "
                f"Available: {StorageQuotaService.get_available_quota(user)} bytes"
            )

        # Get max order for this point and increment
        max_order = (
            Annotation.objects.filter(gps_point_id=gps_point_id).aggregate(db_models.Max("order"))[
                "order__max"
            ]
            or -1
        )

        # Create annotation
        annotation = Annotation.objects.create(
            gps_point_id=gps_point_id,
            type=annotation_type,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=validation["file_size"],
            mime_type=validation["mime_type"],
            order=max_order + 1,
        )

        # Update quota
        StorageQuotaService.add_usage(user, annotation.file_size)

        return annotation

    @staticmethod
    def delete_annotation(annotation: Annotation, user: User) -> None:
        """
        Soft delete annotation by moving it to trash (30-day retention).
        Reclaims storage quota immediately upon deletion.

        Args:
            annotation: Annotation object
            user: User (for quota management)
        """
        # Import here to avoid circular import
        from apps.trash.services import AnnotationTrashService

        # Reclaim quota if file attached (before moving to trash)
        if annotation.file and annotation.file_size:
            StorageQuotaService.remove_usage(user, annotation.file_size)

        # Move to trash (soft delete)
        AnnotationTrashService.move_to_trash(annotation, user)

    @staticmethod
    def permanently_delete_annotation(annotation: Annotation, user: User) -> None:
        """
        Permanently delete annotation from trash or directly.

        If annotation is in trash, quota was already reclaimed when moved to trash.
        If annotation is NOT in trash (direct permanent delete), reclaim quota now.

        Args:
            annotation: Annotation object
            user: User (for quota management)
        """
        # Check if annotation is in trash
        is_in_trash = hasattr(annotation, "trash_entry") and annotation.trash_entry

        # Reclaim quota if file attached AND not in trash
        # (if in trash, quota was already reclaimed on soft delete)
        if not is_in_trash and annotation.file and annotation.file_size:
            StorageQuotaService.remove_usage(user, annotation.file_size)

        # Delete file from storage
        if annotation.file:
            annotation.file.delete(save=False)

        # Delete annotation
        annotation.delete()

    @staticmethod
    def update_text_annotation(annotation: Annotation, text_content: str) -> Annotation:
        """
        Update text annotation content.

        Args:
            annotation: Annotation object
            text_content: New HTML content

        Returns:
            Updated Annotation object

        Raises:
            ValueError: If annotation is not text type
        """
        if annotation.type != "text":
            raise ValueError("Can only update text content for text annotations")

        annotation.text_content = text_content
        annotation.save()
        return annotation
