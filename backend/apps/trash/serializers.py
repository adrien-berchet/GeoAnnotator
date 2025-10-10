"""
Serializers for trash app.

Handles soft-deleted points with 30-day retention and restoration.
"""

from rest_framework import serializers

from apps.points.serializers import GPSPointListSerializer
from apps.authentication.serializers import UserSerializer
from .models import Trash


class TrashSerializer(serializers.ModelSerializer):
    """
    Trash serializer with full details.

    Includes nested point, deletion info, and days remaining.
    Matches OpenAPI schema: Trash
    """
    gps_point = GPSPointListSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Trash
        fields = [
            'id',
            'gps_point',
            'deleted_by',
            'deleted_at',
            'permanent_deletion_at',
            'days_remaining',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'gps_point',
            'deleted_by',
            'deleted_at',
            'permanent_deletion_at',
            'days_remaining',
            'is_expired',
        ]


class RestoreTrashSerializer(serializers.Serializer):
    """
    Restore trash serializer.

    Validates point can be restored (not expired).
    Matches OpenAPI schema: RestoreTrashRequest
    """

    def validate(self, attrs):
        """
        Validate trash item can be restored.
        """
        trash = self.instance

        # Check if expired
        if trash.is_expired:
            raise serializers.ValidationError({
                'error': 'PERMANENTLY_DELETED',
                'message': 'This point has been permanently deleted (>30 days).',
            })

        # Check user has permission (must be owner or original deleter)
        user = self.context['request'].user

        if trash.gps_point.owner != user and trash.deleted_by != user:
            raise serializers.ValidationError({
                'error': 'ACCESS_DENIED',
                'message': 'You do not have permission to restore this point.',
            })

        return attrs

    def save(self):
        """
        Restore point from trash.
        """
        trash = self.instance
        trash.restore()
        return trash.gps_point


class DeletePermanentlySerializer(serializers.Serializer):
    """
    Permanently delete trash serializer.

    Validates user has permission and deletes point permanently.
    Matches OpenAPI schema: DeletePermanentlyRequest
    """

    def validate(self, attrs):
        """
        Validate user has permission to permanently delete.
        """
        trash = self.instance
        user = self.context['request'].user

        # Only owner can permanently delete
        if trash.gps_point.owner != user:
            raise serializers.ValidationError({
                'error': 'ACCESS_DENIED',
                'message': 'Only the point owner can permanently delete.',
            })

        return attrs

    def save(self):
        """
        Permanently delete point and trash entry.
        """
        trash = self.instance
        point = trash.gps_point

        # Delete will cascade to annotations, shares, and update quota
        point.delete()
        trash.delete()

        return None


class EmptyTrashSerializer(serializers.Serializer):
    """
    Empty entire trash serializer.

    Permanently deletes all trashed points for current user.
    Matches OpenAPI schema: EmptyTrashRequest
    """

    def validate(self, attrs):
        """
        Count items to be deleted.
        """
        user = self.context['request'].user

        # Get all trash items for user
        trash_items = Trash.objects.filter(gps_point__owner=user)
        self.context['trash_items'] = trash_items
        self.context['count'] = trash_items.count()

        return attrs

    def save(self):
        """
        Permanently delete all trash items.
        """
        trash_items = self.context['trash_items']

        # Delete all points (cascades to annotations, shares, trash)
        for trash in trash_items:
            trash.gps_point.delete()

        return {'deleted_count': self.context['count']}
