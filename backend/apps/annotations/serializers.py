"""
Serializers for annotations app.

Handles text, image, document, and file annotations with quota validation.
"""

from rest_framework import serializers

from .models import Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    """
    Annotation serializer with full details.
    
    Handles polymorphic types: text, image, document, file.
    Matches OpenAPI schema: Annotation
    """
    file_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Annotation
        fields = [
            'id',
            'gps_point',
            'type',
            'text_content',
            'file',
            'file_name',
            'file_size',
            'mime_type',
            'can_preview',
            'file_url',
            'preview_url',
            'download_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_size',
            'mime_type',
            'can_preview',
            'file_url',
            'preview_url',
            'download_url',
            'created_at',
            'updated_at',
        ]
    
    def get_file_url(self, obj):
        """Get file URL for download."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(
                    f'/api/v1/annotations/{obj.id}/download'
                )
        return None
    
    def get_preview_url(self, obj):
        """Get preview URL (only for previewable types)."""
        if obj.can_preview and obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(
                    f'/api/v1/annotations/{obj.id}/preview'
                )
        return None
    
    def get_download_url(self, obj):
        """Get download URL."""
        return self.get_file_url(obj)
    
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
            max_file_size = 1024 * 1024 * 1024  # 1GB
            if value.size > max_file_size:
                raise serializers.ValidationError(
                    f'File size ({value.size} bytes) exceeds maximum allowed (1GB).'
                )
            
            # Check user storage quota
            if not user.has_storage_quota(value.size):
                raise serializers.ValidationError({
                    'error': 'QUOTA_EXCEEDED',
                    'message': f'Insufficient storage quota. '
                               f'Required: {value.size} bytes, '
                               f'Available: {user.storage_limit - user.storage_used} bytes',
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
        Update annotation (file replacement not allowed, only text edits).
        """
        # Don't allow file changes (delete and recreate instead)
        if 'file' in validated_data and instance.file:
            raise serializers.ValidationError({
                'file': 'Cannot replace file. Delete annotation and create new one.'
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
        fields = ['gps_point', 'text_content']
    
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
        fields = ['gps_point', 'type', 'file']
    
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
        max_file_size = 1024 * 1024 * 1024  # 1GB
        if value.size > max_file_size:
            raise serializers.ValidationError(
                f'File size ({value.size} bytes) exceeds maximum allowed (1GB).'
            )
        
        # Check user storage quota
        if not user.has_storage_quota(value.size):
            raise serializers.ValidationError({
                'error': 'QUOTA_EXCEEDED',
                'message': f'Insufficient storage quota. '
                           f'Required: {value.size} bytes, '
                           f'Available: {user.storage_limit - user.storage_used} bytes',
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
    
    def validate(self, attrs):
        """Ensure annotation is text type."""
        if self.instance.type != 'text':
            raise serializers.ValidationError(
                'Can only update text content for text annotations.'
            )
        return attrs
