"""
Serializers for annotations app.

Handles text, image, document, and file annotations with quota validation.
"""

import humanize
from rest_framework import serializers

from .models import Annotation


MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB


def validate_file_size(file, max_size=MAX_FILE_SIZE):
    """
    Validate file size against maximum allowed.

    Args:
        file: Uploaded file object with size attribute
        max_size: Maximum allowed size in bytes (default: 1GB)

    Raises:
        serializers.ValidationError: If file exceeds maximum size
    """
    if file.size > max_size:
        file_size = humanize.naturalsize(file.size)
        max_size_formatted = humanize.naturalsize(max_size)
        raise serializers.ValidationError(
            f'This file is too big ({file_size}). Maximum allowed size is {max_size_formatted}.'
        )


class AnnotationSerializer(serializers.ModelSerializer):
    """
    Annotation serializer with full details.

    Handles polymorphic types: text, image, document, file.
    Includes trash status for annotations in the trash.
    Matches OpenAPI schema: Annotation
    """
    gps_point_id = serializers.UUIDField(source='gps_point.id', read_only=True)
    file = serializers.SerializerMethodField()
    is_trashed = serializers.SerializerMethodField()
    trash_days_remaining = serializers.SerializerMethodField()
    trash_id = serializers.SerializerMethodField()

    class Meta:
        model = Annotation
        fields = [
            'id',
            'gps_point_id',
            'type',
            'text_content',
            'file',
            'order',
            'created_at',
            'is_trashed',
            'trash_days_remaining',
            'trash_id',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'is_trashed',
            'trash_days_remaining',
            'trash_id',
        ]

    def get_is_trashed(self, obj):
        """Check if annotation is in trash."""
        return hasattr(obj, 'trash_entry') and obj.trash_entry is not None

    def get_trash_days_remaining(self, obj):
        """Get days remaining before permanent deletion (None if not trashed)."""
        if hasattr(obj, 'trash_entry') and obj.trash_entry:
            return obj.trash_entry.days_remaining
        return None

    def get_trash_id(self, obj):
        """Get trash entry ID (None if not trashed)."""
        if hasattr(obj, 'trash_entry') and obj.trash_entry:
            return str(obj.trash_entry.id)
        return None

    def get_file(self, obj):
        """
        Get file metadata object (FileMetadata schema).
        Returns None if no file attached.
        """
        if not obj.file:
            return None

        request = self.context.get('request')
        url = None
        if request:
            url = request.build_absolute_uri(
                f'/api/v1/points/{obj.gps_point_id}/annotations/{obj.id}/download'
            )

        return {
            'url': url or obj.file.url,
            'file_name': obj.file_name,
            'file_size': obj.file_size,
            'mime_type': obj.mime_type,
            'can_preview': obj.can_preview,
        }

    def validate(self, attrs):
        """
        Validate annotation based on type.

        - text: requires text_content
        - image/document/file: requires file upload
        """
        annotation_type = attrs.get('type')
        text_content = attrs.get('text_content')
        file_upload = attrs.get('file')

        if annotation_type == 'text':
            if not text_content:
                raise serializers.ValidationError({
                    'text_content': 'Text content is required for text annotations.'
                })
            if file_upload:
                raise serializers.ValidationError({
                    'file': 'Text annotations cannot have file attachments.'
                })

        elif annotation_type in ['image', 'document', 'file']:
            if not file_upload:
                raise serializers.ValidationError({
                    'file': f'File upload is required for {annotation_type} annotations.'
                })
            if text_content:
                raise serializers.ValidationError({
                    'text_content': f'{annotation_type.capitalize()} annotations cannot have text content.'
                })

        else:
            raise serializers.ValidationError({
                'type': f'Invalid annotation type: {annotation_type}'
            })

        return attrs

    def validate_file(self, value):
        """
        Validate file size against user quota.
        """
        if value:
            user = self.context['request'].user

            # Check file size limit (1GB per file)
            validate_file_size(value, MAX_FILE_SIZE)

            # Check user storage quota
            if not user.has_storage_quota(value.size):
                required = humanize.naturalsize(value.size)
                available = humanize.naturalsize(user.storage_limit - user.storage_used)
                raise serializers.ValidationError({
                    'error': 'QUOTA_EXCEEDED',
                    'message': f'Insufficient storage quota. '
                               f'Required: {required}, '
                               f'Available: {available}',
                })

        return value

    def create(self, validated_data):
        """
        Create annotation and update user storage quota.
        """
        annotation = super().create(validated_data)

        # Update user storage quota if file attached
        if annotation.file:
            user = self.context['request'].user
            user.add_storage_usage(annotation.file_size)

        return annotation

    def update(self, instance, validated_data):
        """
        Update annotation (text only).
        File annotations cannot be updated - they must be deleted and recreated.
        """
        # Don't allow updates to file annotations
        if instance.type != 'text':
            raise serializers.ValidationError({
                'error': 'INVALID_OPERATION',
                'message': 'File annotations cannot be updated. Delete and create a new annotation instead.'
            })

        # Don't allow file changes
        if 'file' in validated_data:
            raise serializers.ValidationError({
                'error': 'INVALID_OPERATION',
                'message': 'Cannot replace file. Delete annotation and create new one.'
            })

        return super().update(instance, validated_data)


class CreateTextAnnotationSerializer(serializers.ModelSerializer):
    """
    Create text annotation serializer.

    Simplified for text-only annotations.
    Matches OpenAPI schema: CreateTextAnnotationRequest
    """
    class Meta:
        model = Annotation
        fields = ['text_content']

    def create(self, validated_data):
        """Create text annotation."""
        validated_data['type'] = 'text'
        return super().create(validated_data)


class CreateFileAnnotationSerializer(serializers.ModelSerializer):
    """
    Create file annotation serializer.

    Handles image, document, and generic file uploads.
    Matches OpenAPI schema: CreateFileAnnotationRequest
    """
    class Meta:
        model = Annotation
        fields = ['type', 'file']

    def validate_type(self, value):
        """Validate type is file-based."""
        if value not in ['image', 'document', 'file']:
            raise serializers.ValidationError(
                f'Invalid type for file annotation: {value}'
            )
        return value

    def validate_file(self, value):
        """Validate file size and quota."""
        if not value:
            raise serializers.ValidationError('File is required.')

        user = self.context['request'].user

        # Check file size limit (1GB per file)
        validate_file_size(value, MAX_FILE_SIZE)

        # Check user storage quota
        if not user.has_storage_quota(value.size):
            required = humanize.naturalsize(value.size)
            available = humanize.naturalsize(user.storage_limit - user.storage_used)
            raise serializers.ValidationError({
                'error': 'QUOTA_EXCEEDED',
                'message': f'Insufficient storage quota. '
                           f'Required: {required}, '
                           f'Available: {available}',
            })

        return value

    def create(self, validated_data):
        """
        Create file annotation and update quota.
        """
        annotation = super().create(validated_data)

        # Update user storage quota
        user = self.context['request'].user
        user.add_storage_usage(annotation.file_size)

        return annotation


class UpdateTextAnnotationSerializer(serializers.ModelSerializer):
    """
    Update text annotation serializer.

    Allows editing text content only.
    Matches OpenAPI schema: UpdateTextAnnotationRequest
    """
    class Meta:
        model = Annotation
        fields = ['text_content']
