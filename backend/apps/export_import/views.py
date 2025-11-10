"""
Export/Import views for multi-format data exchange.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from .services import ExportService, ImportService
from apps.sharing.services import PermissionService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_view(request):
    """
    POST /api/export/
    Export points in various formats: geojson, gpx, kml, csv, zip

    Request body:
    {
        "format": "geojson|gpx|kml|csv|zip",
        "point_ids": [1, 2, 3],  // Optional, exports all accessible points if omitted
        "include_annotations": true  // Optional, only for geojson/zip formats
    }
    """
    export_format = request.data.get('format', 'geojson')
    point_ids = request.data.get('point_ids', [])
    include_annotations = request.data.get('include_annotations', False)

    # Get accessible points
    accessible_points = PermissionService.get_accessible_points(
        request.user,
        include_public=True
    )

    # Filter by point_ids if provided
    if point_ids:
        accessible_points = accessible_points.filter(id__in=point_ids)

    if not accessible_points.exists():
        return Response(
            {'error': 'NO_POINTS_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Export based on format
    try:
        if export_format == 'geojson':
            content = ExportService.export_geojson(
                list(accessible_points),
                include_annotations=include_annotations
            )
            return ExportService.get_export_response(content, 'geojson')

        elif export_format == 'gpx':
            content = ExportService.export_gpx(list(accessible_points))
            return ExportService.get_export_response(content, 'gpx')

        elif export_format == 'kml':
            content = ExportService.export_kml(list(accessible_points))
            return ExportService.get_export_response(content, 'kml')

        elif export_format == 'csv':
            content = ExportService.export_csv(list(accessible_points))
            return ExportService.get_export_response(content, 'csv')

        elif export_format == 'zip':
            content = ExportService.export_zip(
                list(accessible_points),
                include_annotations=include_annotations
            )
            return ExportService.get_export_response(content, 'zip')

        else:
            return Response(
                {'error': f'Unsupported format: {export_format}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': f'Export failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def import_view(request):
    """
    POST /api/import/
    Import points from various formats: geojson, gpx, csv, kml, zip

    Request (multipart/form-data):
    - file: uploaded file
    - format: geojson|gpx|csv|kml|zip
    - merge_strategy: create_new|skip|replace (optional, default: create_new)

    Response:
    {
        "total_points": 100,
        "imported_points": 95,
        "skipped_points": 3,
        "failed_points": 2,
        "errors": [
            {"line_number": 5, "error": "INVALID_COORDINATES", "message": "Latitude out of range"},
            ...
        ]
    }
    """
    import_format = request.data.get('format')
    merge_strategy = request.data.get('merge_strategy', 'create_new')
    uploaded_file = request.FILES.get('file')

    if not import_format:
        return Response(
            {'error': 'Format is required (geojson, gpx, csv, kml, zip)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not uploaded_file:
        return Response(
            {'error': 'File is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Read file content
    try:
        # ZIP files are binary, others are text
        if import_format == 'zip':
            file_content = uploaded_file.read()
        else:
            file_content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {'error': 'File must be UTF-8 encoded'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Import based on format
    try:
        if import_format == 'geojson':
            result = ImportService.import_geojson(
                file_content,
                request.user,
                merge_strategy
            )

        elif import_format == 'gpx':
            result = ImportService.import_gpx(
                file_content,
                request.user
            )

        elif import_format == 'csv':
            result = ImportService.import_csv(
                file_content,
                request.user,
                merge_strategy
            )

        elif import_format == 'kml':
            result = ImportService.import_kml(
                file_content,
                request.user,
                merge_strategy
            )

        elif import_format == 'zip':
            result = ImportService.import_zip(
                file_content,
                request.user,
                merge_strategy
            )

        else:
            return Response(
                {'error': f'Unsupported format: {import_format}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return import result
        # Check for format errors (complete failure)
        if result.get('errors'):
            for error in result['errors']:
                if error.get('error') in ['INVALID_JSON', 'INVALID_CSV', 'INVALID_GPX', 'INVALID_KML', 'INVALID_ZIP']:
                    return Response(
                        {'error': 'INVALID_FORMAT', 'message': error.get('message')},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Return 200 for both full and partial success
        # Client can check failed_points/errors for details
        return Response(result, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Import failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
