"""
Serializers for trash app.

Handles soft-deleted points and annotations with 30-day retention and restoration.
"""

from rest_framework import serializers

from apps.points.serializers import GPSPointListSerializer
from apps.annotations.serializers import AnnotationSerializer
from apps.authentication.serializers import UserSerializer
from apps.sharing.serializers import ShareSerializer
from .models import Trash, AnnotationTrash


class TrashSerializer(serializers.ModelSerializer):
    """
    Trash serializer with full details.

    Includes nested point, deletion info, days remaining, annotations, and shares.
    Matches OpenAPI schema: Trash
    """
    gps_point = GPSPointListSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    annotations = serializers.SerializerMethodField()
    shares = serializers.SerializerMethodField()

    def get_days_remaining(self, obj):
        """Get days remaining from model property."""
        return obj.days_remaining

    def get_is_expired(self, obj):
        """Get is_expired from model property."""
        return obj.is_expired

    def get_annotations(self, obj):
        """Get all annotations for this point."""
        annotations = obj.gps_point.annotations.all()
        return AnnotationSerializer(annotations, many=True, context=self.context).data

    def get_shares(self, obj):
        """Get all shares for this point (including deactivated ones)."""
        shares = obj.gps_point.shares.all()
        return ShareSerializer(shares, many=True, context=self.context).data

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
            'annotations',
            'shares',
        ]
        read_only_fields = [
            'id',
            'gps_point',
            'deleted_by',
            'deleted_at',
            'permanent_deletion_at',
            'days_remaining',
            'is_expired',
            'annotations',
            'shares',
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


class AnnotationTrashSerializer(serializers.ModelSerializer):
    """
    Annotation trash serializer with full details.

    Includes nested annotation, associated point, deletion info, and days remaining.
    """
    annotation = AnnotationSerializer(read_only=True)
    gps_point = serializers.SerializerMethodField()
    deleted_by = UserSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    def get_days_remaining(self, obj):
        """Get days remaining from model property."""
        return obj.days_remaining

    def get_is_expired(self, obj):
        """Get is_expired from model property."""
        return obj.is_expired

    def get_gps_point(self, obj):
        """Get the point associated with the annotation."""
        return GPSPointListSerializer(obj.annotation.gps_point, context=self.context).data

    class Meta:
        model = AnnotationTrash
        fields = [
            'id',
            'annotation',
            'gps_point',
            'deleted_by',
            'deleted_at',
            'permanent_deletion_at',
            'days_remaining',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'annotation',
            'gps_point',
            'deleted_by',
            'deleted_at',
            'permanent_deletion_at',
            'days_remaining',
            'is_expired',
        ]


class RestoreAnnotationTrashSerializer(serializers.Serializer):
    """
    Restore annotation trash serializer.

    Validates annotation can be restored (not expired).
    """

    def validate(self, attrs):
        """
        Validate annotation trash item can be restored.
        """
        annotation_trash = self.instance

        # Check if expired
        if annotation_trash.is_expired:
            raise serializers.ValidationError({
                'error': 'PERMANENTLY_DELETED',
                'message': 'This annotation has been permanently deleted (>30 days).',
            })

        # Check user has permission (must be point owner or original deleter)
        user = self.context['request'].user
        point_owner = annotation_trash.annotation.gps_point.owner

        if point_owner != user and annotation_trash.deleted_by != user:
            raise serializers.ValidationError({
                'error': 'ACCESS_DENIED',
                'message': 'You do not have permission to restore this annotation.',
            })

        return attrs

    def save(self):
        """
        Restore annotation from trash.
        """
        annotation_trash = self.instance
        annotation_trash.restore()
        return annotation_trash.annotation


class DeleteAnnotationPermanentlySerializer(serializers.Serializer):
    """
    Permanently delete annotation trash serializer.

    Validates user has permission and deletes annotation permanently.
    """

    def validate(self, attrs):
        """
        Validate user has permission to permanently delete.
        """
        annotation_trash = self.instance
        user = self.context['request'].user

        # Only point owner can permanently delete
        if annotation_trash.annotation.gps_point.owner != user:
            raise serializers.ValidationError({
                'error': 'ACCESS_DENIED',
                'message': 'Only the point owner can permanently delete.',
            })

        return attrs

    def save(self):
        """
        Permanently delete annotation and trash entry.
        """
        annotation_trash = self.instance
        annotation = annotation_trash.annotation

        # Delete will reclaim quota
        annotation.delete()
        annotation_trash.delete()

        return None


class EmptyAnnotationTrashSerializer(serializers.Serializer):
    """
    Empty entire annotation trash serializer.

    Permanently deletes all trashed annotations for current user's points.
    """

    def validate(self, attrs):
        """
        Count items to be deleted.
        """
        user = self.context['request'].user

        # Get all annotation trash items for user's points
        annotation_trash_items = AnnotationTrash.objects.filter(
            annotation__gps_point__owner=user
        )
        self.context['annotation_trash_items'] = annotation_trash_items
        self.context['count'] = annotation_trash_items.count()

        return attrs

    def save(self):
        """
        Permanently delete all annotation trash items.
        """
        annotation_trash_items = self.context['annotation_trash_items']

        # Delete all annotations (cascades)
        for annotation_trash in annotation_trash_items:
            annotation_trash.annotation.delete()

        return {'deleted_count': self.context['count']}
