"""
Trash views for managing soft-deleted points.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Trash
from .serializers import TrashSerializer
from .services import TrashService
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
    pagination_class = None

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
                {'error': 'Cannot restore expired trash items'},
                status=status.HTTP_400_BAD_REQUEST
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

    @action(detail=False, methods=['post'])
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
