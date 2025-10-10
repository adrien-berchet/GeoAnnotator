"""
Serializers for export_import app.

Handles multi-format export (GeoJSON, GPX, KML, CSV, ZIP) and import.
"""

from rest_framework import serializers


class ExportRequestSerializer(serializers.Serializer):
    """
    Export request serializer.

    Accepts format, point IDs filter, and annotation inclusion.
    Matches OpenAPI schema: ExportRequest
    """
    format = serializers.ChoiceField(
        choices=['geojson', 'gpx', 'kml', 'csv', 'zip'],
        required=True,
    )
    point_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    include_annotations = serializers.BooleanField(default=True)

    def validate_format(self, value):
        """Validate export format is supported."""
        supported_formats = ['geojson', 'gpx', 'kml', 'csv', 'zip']
        if value not in supported_formats:
            raise serializers.ValidationError(
                f'Invalid export format: {value}. '
                f'Supported formats: {", ".join(supported_formats)}'
            )
        return value

    def validate_point_ids(self, value):
        """
        Validate point IDs exist and user has access.
        """
        if value:
            from apps.points.models import GPSPoint
            user = self.context['request'].user

            # Check all points exist and user has access
            for point_id in value:
                try:
                    point = GPSPoint.objects.get(id=point_id)
                except GPSPoint.DoesNotExist:
                    raise serializers.ValidationError(
                        f'Point {point_id} does not exist.'
                    )

                # Check user has access (owner, shared, or public)
                from apps.points.serializers import GPSPointSerializer
                serializer = GPSPointSerializer(point, context=self.context)
                permission = serializer.get_permission(point)

                if permission is None:
                    raise serializers.ValidationError({
                        'error': 'ACCESS_DENIED',
                        'message': f'You do not have access to point {point_id}.',
                    })

        return value


class ImportRequestSerializer(serializers.Serializer):
    """
    Import request serializer.

    Accepts file upload, format, and merge strategy.
    Matches OpenAPI schema: ImportRequest
    """
    format = serializers.ChoiceField(
        choices=['geojson', 'gpx', 'kml', 'csv'],
        required=True,
    )
    file = serializers.FileField(required=True)
    merge_strategy = serializers.ChoiceField(
        choices=['create_new', 'skip', 'replace'],
        default='create_new',
    )

    def validate_format(self, value):
        """Validate import format is supported."""
        supported_formats = ['geojson', 'gpx', 'kml', 'csv']
        if value not in supported_formats:
            raise serializers.ValidationError(
                f'Invalid import format: {value}. '
                f'Supported formats: {", ".join(supported_formats)}'
            )
        return value

    def validate_file(self, value):
        """
        Validate file size and type.
        """
        # Max import file size: 100MB
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size ({value.size} bytes) exceeds maximum allowed (100MB).'
            )

        return value

    def validate(self, attrs):
        """
        Validate file extension matches format.
        """
        file_format = attrs['format']
        file_upload = attrs['file']

        # Expected extensions
        extensions = {
            'geojson': ['.geojson', '.json'],
            'gpx': ['.gpx'],
            'kml': ['.kml'],
            'csv': ['.csv'],
        }

        file_name = file_upload.name.lower()
        expected_exts = extensions.get(file_format, [])

        if not any(file_name.endswith(ext) for ext in expected_exts):
            raise serializers.ValidationError({
                'file': f'File extension does not match format "{file_format}". '
                        f'Expected: {", ".join(expected_exts)}'
            })

        return attrs


class ImportResultSerializer(serializers.Serializer):
    """
    Import result serializer.

    Returns summary of imported, skipped, and failed points.
    Matches OpenAPI schema: ImportResult
    """
    total_points = serializers.IntegerField()
    imported_points = serializers.IntegerField()
    skipped_points = serializers.IntegerField()
    failed_points = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    class Meta:
        fields = [
            'total_points',
            'imported_points',
            'skipped_points',
            'failed_points',
            'errors',
        ]


class ImportErrorSerializer(serializers.Serializer):
    """
    Import error serializer for individual point errors.

    Matches OpenAPI schema: ImportError
    """
    line_number = serializers.IntegerField()
    error = serializers.CharField()
    message = serializers.CharField()

    class Meta:
        fields = ['line_number', 'error', 'message']
