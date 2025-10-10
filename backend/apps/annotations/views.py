"""
Annotation views for managing text and file annotations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, Http404

from .models import Annotation
from .serializers import (
    AnnotationSerializer,
    CreateTextAnnotationSerializer,
    CreateFileAnnotationSerializer,
    UpdateTextAnnotationSerializer,
)
from .services import AnnotationService, ImagePreviewService
from apps.sharing.services import PermissionService


class AnnotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Annotation CRUD operations.

    Endpoints:
    - GET /api/points/{point_id}/annotations/ - List annotations for point
    - POST /api/points/{point_id}/annotations/ - Create new annotation (text or file)
    - GET /api/points/{point_id}/annotations/{id}/ - Retrieve annotation detail
    - PATCH /api/points/{point_id}/annotations/{id}/ - Update annotation
    - DELETE /api/points/{point_id}/annotations/{id}/ - Delete annotation
    - GET /api/points/{point_id}/annotations/{id}/download/ - Download file annotation
    """
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for annotations

    def get_serializer_class(self):
        if self.action == 'create':
            # Client determines which serializer by sending type field
            annotation_type = self.request.data.get('type')
            if annotation_type == 'text':
                return CreateTextAnnotationSerializer
            elif annotation_type in ['image', 'pdf', 'document']:
                return CreateFileAnnotationSerializer
            return AnnotationSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateTextAnnotationSerializer
        return AnnotationSerializer

    def get_queryset(self):
        """Return annotations for the specified point."""
        point_id = self.kwargs.get('point_pk')  # Changed from 'point_id' to 'point_pk'
        if point_id:
            # Annotations for a specific point
            return Annotation.objects.filter(gps_point_id=point_id)
        else:
            # All annotations for accessible points (if called without point_id)
            user = self.request.user
            accessible_points = PermissionService.get_accessible_points(user, include_public=True)
            return Annotation.objects.filter(gps_point__in=accessible_points)

    def create(self, request, point_pk=None):  # Changed from point_id to point_pk
        """Create new annotation (text or file)."""
        from apps.points.models import GPSPoint

        # Get the point from URL
        try:
            point = GPSPoint.objects.get(pk=point_pk)
        except GPSPoint.DoesNotExist:
            return Response(
                {'error': 'POINT_NOT_FOUND', 'message': 'Point not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check edit permission
        if not PermissionService.can_edit(point, request.user):
            return Response(
                {'error': 'PERMISSION_DENIED', 'message': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        annotation_type = request.data.get('type')

        if annotation_type == 'text':
            serializer = CreateTextAnnotationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Create text annotation
            annotation = AnnotationService.create_text_annotation(
                gps_point_id=point_pk,
                text_content=serializer.validated_data['text_content']
            )

        elif annotation_type in ['image', 'pdf', 'document']:
            serializer = CreateFileAnnotationSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            try:
                # Create file annotation (validates quota)
                annotation = AnnotationService.create_file_annotation(
                    gps_point_id=point_pk,
                    annotation_type=annotation_type,
                    uploaded_file=serializer.validated_data['file'],
                    user=request.user
                )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': f'Invalid annotation type: {annotation_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return created annotation
        response_serializer = AnnotationSerializer(annotation, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, point_pk=None):
        """Get annotation detail."""
        annotation = self.get_object()

        # Check view permission on point
        if not PermissionService.can_view(annotation.gps_point, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AnnotationSerializer(annotation, context={'request': request})
        return Response(serializer.data)

    def partial_update(self, request, pk=None, point_pk=None):
        """Update annotation (text only)."""
        annotation = self.get_object()

        # Check edit permission on point
        if not PermissionService.can_edit(annotation.gps_point, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only text annotations can be updated
        if annotation.type != 'text':
            return Response(
                {
                    'error': 'INVALID_OPERATION',
                    'message': 'File annotations cannot be updated. Delete and create a new annotation instead.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateTextAnnotationSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update via service
        AnnotationService.update_text_annotation(
            annotation=annotation,
            text_content=serializer.validated_data['text_content']
        )

        response_serializer = AnnotationSerializer(annotation, context={'request': request})
        return Response(response_serializer.data)

    def update(self, request, pk=None, point_pk=None):
        """Update annotation (PUT method - same as PATCH for text annotations)."""
        return self.partial_update(request, pk=pk, point_pk=point_pk)

    def destroy(self, request, pk=None, point_pk=None):
        """Delete annotation."""
        annotation = self.get_object()

        # Check if owner (only owner can delete)
        if not PermissionService.is_owner(annotation.gps_point, request.user):
            return Response(
                {'error': 'Only point owner can delete annotations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Delete via service (handles quota reclaim)
        AnnotationService.delete_annotation(annotation, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, point_pk=None):
        """Download file annotation."""
        annotation = self.get_object()

        # Check view permission
        if not PermissionService.can_view(annotation.gps_point, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only file annotations can be downloaded
        if annotation.type == 'text':
            return Response(
                {'error': 'Text annotations cannot be downloaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not annotation.file:
            raise Http404("File not found")

        # Return file response
        response = FileResponse(
            annotation.file.open('rb'),
            content_type=annotation.mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{annotation.file_name}"'

        return response

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview image annotation (resized)."""
        annotation = self.get_object()

        # Check view permission
        if not PermissionService.can_view(annotation.gps_point, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only image annotations can be previewed
        if annotation.type != 'image':
            return Response(
                {'error': 'Only image annotations can be previewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not annotation.file:
            raise Http404("File not found")

        # Get preview size from query params (default 1920x1080)
        max_width = int(request.query_params.get('width', 1920))
        max_height = int(request.query_params.get('height', 1080))

        try:
            # Generate preview
            preview_image = ImagePreviewService.generate_preview(
                annotation.file,
                max_width=max_width,
                max_height=max_height
            )

            # Return image response
            response = FileResponse(
                preview_image,
                content_type=annotation.mime_type or 'image/jpeg'
            )
            return response

        except Exception as e:
            return Response(
                {'error': f'Failed to generate preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
