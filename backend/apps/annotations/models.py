"""
Annotation model for GeoAnnotator.

Handles text notes and file attachments for GPS points.
"""

import uuid
import os
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


def annotation_file_path(instance, filename):
    """Generate upload path for annotation files."""
    # Upload to: annotations/<point_id>/<annotation_id>/<filename>
    return os.path.join(
        'annotations',
        str(instance.gps_point.id),
        str(instance.id),
        filename
    )


class Annotation(models.Model):
    """
    Content attached to a GPS point (text, image, document, or file).

    Types:
    - text: Rich text HTML with emoticons
    - image: Image files (JPEG, PNG, TIFF, GIF)
    - document: Documents (PDF, Office formats)
    - file: Generic files
    """

    # Annotation type choices
    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'
    TYPE_DOCUMENT = 'document'
    TYPE_FILE = 'file'

    TYPE_CHOICES = [
        (TYPE_TEXT, 'Text'),
        (TYPE_IMAGE, 'Image'),
        (TYPE_DOCUMENT, 'Document'),
        (TYPE_FILE, 'File'),
    ]

    # MIME type sets
    IMAGE_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/tiff', 'image/gif'
    }

    DOCUMENT_MIME_TYPES = {
        'application/pdf',
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/msword',
        'application/vnd.ms-excel',
    }

    PREVIEWABLE_MIME_TYPES = IMAGE_MIME_TYPES | {'application/pdf'}

    # Max file size: 1GB
    MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique annotation identifier"
    )

    gps_point = models.ForeignKey(
        'points.GPSPoint',
        on_delete=models.CASCADE,
        related_name='annotations',
        help_text="Associated GPS point"
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True,
        help_text="Annotation type (text/image/document/file)"
    )

    # Text annotation fields
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Rich text HTML (only for text type)"
    )

    # File annotation fields
    file = models.FileField(
        upload_to=annotation_file_path,
        blank=True,
        null=True,
        max_length=500,
        help_text="File upload (only for non-text types)"
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename"
    )

    file_size = models.BigIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(MAX_FILE_SIZE)
        ],
        help_text="File size in bytes (max 1GB)"
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="MIME type (e.g., image/jpeg)"
    )

    can_preview = models.BooleanField(
        default=False,
        help_text="Preview supported (images and PDFs)"
    )

    order = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Display order (lower values first)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Upload/creation timestamp"
    )

    class Meta:
        db_table = 'annotations'
        verbose_name = 'Annotation'
        verbose_name_plural = 'Annotations'
        indexes = [
            models.Index(fields=['gps_point'], name='idx_annotation_point'),
            models.Index(fields=['type'], name='idx_annotation_type'),
            models.Index(fields=['gps_point', 'order'], name='idx_annotation_point_order'),
        ]
        ordering = ['order', '-created_at']

    def clean(self):
        """Validate annotation type constraints."""
        from django.core.exceptions import ValidationError

        if self.type == self.TYPE_TEXT:
            if not self.text_content:
                raise ValidationError("Text annotations must have text_content")
            if self.file:
                raise ValidationError("Text annotations cannot have files")
        else:
            if not self.file:
                raise ValidationError(f"{self.type} annotations must have a file")
            if self.text_content:
                raise ValidationError(f"{self.type} annotations cannot have text_content")

    def save(self, *args, **kwargs):
        """Auto-set can_preview based on MIME type."""
        if self.mime_type:
            self.can_preview = self.mime_type in self.PREVIEWABLE_MIME_TYPES

        # Extract filename from file if not set
        if self.file and not self.file_name:
            self.file_name = os.path.basename(self.file.name)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete file from storage when annotation is deleted."""
        if self.file:
            # Delete the file from storage
            storage = self.file.storage
            if storage.exists(self.file.name):
                storage.delete(self.file.name)

            # Update user's storage quota
            owner = self.gps_point.owner
            owner.remove_storage_usage(self.file_size)

        super().delete(*args, **kwargs)

    @property
    def is_text(self):
        """Check if this is a text annotation."""
        return self.type == self.TYPE_TEXT

    @property
    def is_file(self):
        """Check if this is a file annotation."""
        return self.type in [self.TYPE_IMAGE, self.TYPE_DOCUMENT, self.TYPE_FILE]

    def __str__(self):
        if self.type == self.TYPE_TEXT:
            preview = self.text_content[:50] if self.text_content else ''
            return f"Text: {preview}..."
        else:
            return f"{self.type.capitalize()}: {self.file_name}"
