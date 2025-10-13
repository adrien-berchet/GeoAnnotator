"""
Trash views for managing soft-deleted points and annotations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Trash, AnnotationTrash
from .serializers import (
    TrashSerializer, AnnotationTrashSerializer,
    RestoreAnnotationTrashSerializer, DeleteAnnotationPermanentlySerializer,
    EmptyAnnotationTrashSerializer
)
from .services import TrashService, AnnotationTrashService
from apps.sharing.services import PermissionService


class TrashViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Trash operations.

    Endpoints:
    - GET /api/trash/ - List trash items
    - POST /api/trash/{id}/restore/ - Restore from trash
    - DELETE /api/trash/{id}/permanent/ - Permanently delete
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TrashSerializer
    pagination_class = None  # Disable pagination for trash

    def get_queryset(self):
        """Return trash items for current user's points."""
        return TrashService.get_user_trash(self.request.user)

    def restore(self, request, pk=None):
        """Restore point from trash."""
        # pk is the point_id, not trash_id
        try:
            trash = Trash.objects.get(gps_point_id=pk)
        except Trash.DoesNotExist:
            return Response(
                {'error': 'TRASH_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is owner
        if not PermissionService.is_owner(trash.gps_point, request.user):
            return Response(
                {'error': 'Only owner can restore points'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if expired
        if trash.is_expired:
            return Response(
                {'error': 'PERMANENTLY_DELETED', 'message': 'This point has been permanently deleted (>30 days)'},
                status=status.HTTP_410_GONE
            )

        # Restore via service
        restored_point = TrashService.restore_from_trash(trash)

        # Return the restored point data
        from apps.points.serializers import GPSPointSerializer
        serializer = GPSPointSerializer(restored_point, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def permanent_delete(self, request, pk=None):
        """Permanently delete point."""
        # pk is the point_id, not trash_id
        try:
            trash = Trash.objects.get(gps_point_id=pk)
        except Trash.DoesNotExist:
            return Response(
                {'error': 'TRASH_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is owner
        if not PermissionService.is_owner(trash.gps_point, request.user):
            return Response(
                {'error': 'Only owner can permanently delete points'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Permanently delete via service
        TrashService.permanently_delete(trash, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def empty(self, request):
        """Empty entire trash for current user."""
        count = TrashService.empty_trash(request.user)

        return Response(
            {
                'message': f'Trash emptied: {count} items permanently deleted',
                'deleted_count': count
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get trash statistics."""
        stats = TrashService.get_trash_stats(request.user)

        return Response(stats, status=status.HTTP_200_OK)


class AnnotationTrashViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Annotation Trash operations.

    Endpoints:
    - GET /api/trash/annotations/ - List annotation trash items
    - POST /api/trash/annotations/{id}/restore/ - Restore annotation from trash
    - DELETE /api/trash/annotations/{id}/permanent/ - Permanently delete annotation
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnnotationTrashSerializer
    pagination_class = None  # Disable pagination for trash

    def get_queryset(self):
        """Return annotation trash items for current user's points."""
        return AnnotationTrashService.get_user_trash(self.request.user)

    def restore(self, request, pk=None):
        """Restore annotation from trash."""
        # pk is the annotation_id, not annotation_trash_id
        try:
            annotation_trash = AnnotationTrash.objects.get(annotation_id=pk)
        except AnnotationTrash.DoesNotExist:
            return Response(
                {'error': 'ANNOTATION_TRASH_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is point owner
        if not PermissionService.is_owner(annotation_trash.annotation.gps_point, request.user):
            return Response(
                {'error': 'Only point owner can restore annotations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if expired
        if annotation_trash.is_expired:
            return Response(
                {'error': 'PERMANENTLY_DELETED', 'message': 'This annotation has been permanently deleted (>30 days)'},
                status=status.HTTP_410_GONE
            )

        # Restore via service
        restored_annotation = AnnotationTrashService.restore_from_trash(annotation_trash)

        # Return the restored annotation data
        from apps.annotations.serializers import AnnotationSerializer
        serializer = AnnotationSerializer(restored_annotation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def permanent_delete(self, request, pk=None):
        """Permanently delete annotation."""
        # pk is the annotation_id, not annotation_trash_id
        try:
            annotation_trash = AnnotationTrash.objects.get(annotation_id=pk)
        except AnnotationTrash.DoesNotExist:
            return Response(
                {'error': 'ANNOTATION_TRASH_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is point owner
        if not PermissionService.is_owner(annotation_trash.annotation.gps_point, request.user):
            return Response(
                {'error': 'Only point owner can permanently delete annotations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Permanently delete via service
        AnnotationTrashService.permanently_delete(annotation_trash, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def empty(self, request):
        """Empty entire annotation trash for current user."""
        count = AnnotationTrashService.empty_trash(request.user)

        return Response(
            {
                'message': f'Annotation trash emptied: {count} items permanently deleted',
                'deleted_count': count
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get annotation trash statistics."""
        stats = AnnotationTrashService.get_trash_stats(request.user)

        return Response(stats, status=status.HTTP_200_OK)
