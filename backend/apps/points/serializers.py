"""
Serializers for points app.

Handles GPS points, tags, editing locks, and spatial data.
"""

from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.authentication.models import User
from apps.authentication.serializers import UserSerializer
from .models import GPSPoint, Tag, PointType


class TagSerializer(serializers.ModelSerializer):
    """
    Tag serializer.

    Simple name-only serialization.
    Matches OpenAPI schema: Tag
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSummarySerializer(serializers.ModelSerializer):
    """
    User summary serializer for nested relations.

    Only includes id and email (lighter than full UserSerializer).
    Matches OpenAPI schema: UserSummary
    """
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']


class PointTypeSerializer(serializers.ModelSerializer):
    """
    PointType serializer with full details.

    Includes user information and all type fields.
    """
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = PointType
        fields = ['id', 'name', 'icon', 'order', 'user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate unique name per user (case-insensitive)."""
        user = self.context['request'].user

        # Check for duplicate name
        queryset = PointType.objects.filter(
            user=user,
            name__iexact=value,
            status='active'
        )

        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "You already have a type with this name. Type names must be unique."
            )

        return value

    def create(self, validated_data):
        """Create a new point type for the authenticated user."""
        user = self.context['request'].user
        validated_data['user'] = user

        # Set default icon if not provided
        if 'icon' not in validated_data or not validated_data['icon']:
            validated_data['icon'] = '/icons/default.svg'

        # Auto-assign order if not provided
        if 'order' not in validated_data:
            max_order = PointType.objects.filter(user=user).aggregate(
                max_order=serializers.models.Max('order')
            )['max_order']
            validated_data['order'] = (max_order or 0) + 1

        return super().create(validated_data)


class CreatePointTypeSerializer(serializers.ModelSerializer):
    """Serializer for creating point types (simplified input)."""

    class Meta:
        model = PointType
        fields = ['name', 'icon', 'order']

    def create(self, validated_data):
        """Create with user from context and defaults."""
        user = self.context['request'].user
        validated_data['user'] = user

        if 'icon' not in validated_data or not validated_data['icon']:
            validated_data['icon'] = '/icons/default.svg'

        if 'order' not in validated_data:
            max_order = PointType.objects.filter(user=user).aggregate(
                max_order=serializers.models.Max('order')
            )['max_order']
            validated_data['order'] = (max_order or 0) + 1

        return PointType.objects.create(**validated_data)


class PointTypeReorderSerializer(serializers.Serializer):
    """Serializer for reordering point types with per-user custom order."""

    order = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        help_text="List of {id, order} objects"
    )

    def validate_order(self, value):
        """Validate that all IDs exist and are accessible to the user."""
        from django.db.models import Q
        user = self.context['request'].user
        type_ids = [item['id'] for item in value]

        # Check all types exist and are accessible (user's types OR base types)
        accessible_types = PointType.objects.filter(
            Q(id__in=type_ids),
            Q(user=user) | Q(user__isnull=True),
            status='active'
        ).values_list('id', flat=True)

        accessible_types_str = set(str(tid) for tid in accessible_types)
        provided_ids = set(type_ids)

        if accessible_types_str != provided_ids:
            invalid_ids = provided_ids - accessible_types_str
            raise serializers.ValidationError(
                f"Invalid or inaccessible type IDs: {invalid_ids}"
            )

        return value

    def save(self):
        """Save user-specific custom order for all types."""
        from .models import UserTypeOrder

        user = self.context['request'].user
        order_data = self.validated_data['order']

        # Create or update UserTypeOrder for each type
        for item in order_data:
            UserTypeOrder.objects.update_or_create(
                user=user,
                type_id=item['id'],
                defaults={'order': int(item['order'])}
            )

        return {'success': True, 'updated': len(order_data)}


class EditingLockSerializer(serializers.Serializer):
    """
    Editing lock serializer.

    Shows who is editing and when lock expires.
    Matches OpenAPI schema: EditingLock
    """
    locked_by = UserSummarySerializer(source='editing_lock_user', read_only=True)
    acquired_at = serializers.DateTimeField(source='editing_lock_acquired_at', read_only=True)
    expires_at = serializers.SerializerMethodField()

    def get_expires_at(self, obj):
        """Calculate lock expiration (acquired_at + 15 minutes)."""
        if obj.editing_lock_acquired_at:
            from datetime import timedelta
            return obj.editing_lock_acquired_at + timedelta(minutes=15)
        return None


class GPSPointSerializer(serializers.ModelSerializer):
    """
    GPS Point serializer with full details.

    Includes nested owner, tags, editing lock, and permission level.
    Matches OpenAPI schema: GPSPoint
    """
    # lat/lon for input and output
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    # Read-only computed fields
    owner = UserSummarySerializer(read_only=True)
    type = PointTypeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    editing_lock = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    annotation_count = serializers.SerializerMethodField()

    # GeoJSON location (auto-generated from lat/lon)
    location = serializers.SerializerMethodField()

    class Meta:
        model = GPSPoint
        fields = [
            'id',
            'title',
            'description',
            'location',
            'latitude',
            'longitude',
            'owner',
            'type',
            'tags',
            'is_public',
            'created_at',
            'updated_at',
            'editing_lock',
            'permission',
            'annotation_count',
        ]
        read_only_fields = [
            'id',
            'owner',
            'created_at',
            'updated_at',
        ]

    def get_latitude(self, obj):
        """Extract latitude from PostGIS Point."""
        if obj.location:
            return obj.location.y  # y = latitude
        return None

    def get_longitude(self, obj):
        """Extract longitude from PostGIS Point."""
        if obj.location:
            return obj.location.x  # x = longitude
        return None

    def get_location(self, obj):
        """Convert PostGIS Point to GeoJSON format."""
        if obj.location:
            return {
                'type': 'Point',
                'coordinates': [obj.location.x, obj.location.y]  # [longitude, latitude]
            }
        return None

    def get_editing_lock(self, obj):
        """
        Get editing lock details or None if not locked.

        Returns None if no active lock, otherwise returns lock details.
        """
        if obj.editing_lock_user and obj.editing_lock_acquired_at:
            # Point is locked, return lock details
            serializer = EditingLockSerializer(obj)
            return serializer.data
        return None

    def get_permission(self, obj):
        """
        Determine current user's permission level.

        Returns: 'owner', 'transfer', 'edit', or 'view'
        """
        user = self.context.get('request').user if self.context.get('request') else None

        if not user or not user.is_authenticated:
            return 'view' if obj.is_public else None

        # Owner has full permissions
        if obj.owner == user:
            return 'owner'

        # Check share permissions
        from apps.sharing.models import Share
        share = Share.objects.filter(gps_point=obj, recipient_user=user, is_active=True).first()

        if share:
            return share.permission_level

        # Public points are view-only
        if obj.is_public:
            return 'view'

        return None

    def get_annotation_count(self, obj):
        """Get the count of non-deleted annotations for this point."""
        # Exclude annotations that have a trash_entry (soft-deleted)
        return obj.annotations.exclude(trash_entry__isnull=False).count()

    def create(self, validated_data):
        """
        Create GPS point from latitude/longitude.

        Converts lat/lon to PostGIS Point and sets owner.
        """
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')

        # Create PostGIS Point (longitude, latitude - note the order!)
        validated_data['location'] = Point(longitude, latitude, srid=4326)

        # Set owner from request user
        validated_data['owner'] = self.context['request'].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update GPS point, including location if lat/lon changed.
        """
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)

        if latitude is not None and longitude is not None:
            instance.location = Point(longitude, latitude, srid=4326)

        return super().update(instance, validated_data)


class CreateGPSPointSerializer(serializers.ModelSerializer):
    """
    Create GPS Point serializer.

    Accepts latitude/longitude, type_id, and tag names (auto-creates tags).
    Matches OpenAPI schema: CreateGPSPointRequest
    """
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    type_id = serializers.UUIDField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = GPSPoint
        fields = ['title', 'description', 'latitude', 'longitude', 'type_id', 'tags', 'is_public']

    def validate_type_id(self, value):
        """Validate that type exists and belongs to user or is a base type."""
        if not value:
            return None

        user = self.context['request'].user

        try:
            point_type = PointType.objects.get(id=value, status='active')

            # Type must belong to user or be a base type (user=None)
            if point_type.user is not None and point_type.user != user:
                raise serializers.ValidationError(
                    "You can only use your own types or base types."
                )

            return point_type
        except PointType.DoesNotExist:
            raise serializers.ValidationError("Point type not found or has been deleted.")

    def create(self, validated_data):
        """
        Create GPS point with auto-created tags and type.
        """
        tag_names = validated_data.pop('tags', [])
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        point_type = validated_data.pop('type_id', None)

        # Create PostGIS Point
        validated_data['location'] = Point(longitude, latitude, srid=4326)
        validated_data['owner'] = self.context['request'].user

        # Set default type if not provided
        if not point_type:
            point_type, _ = PointType.objects.get_or_create(
                name='Point',
                user=None,
                defaults={'icon': '/icons/default.svg', 'order': 0}
            )

        validated_data['type'] = point_type

        # Create point
        point = GPSPoint.objects.create(**validated_data)

        # Create/get tags and associate
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name.lower().strip())
            point.tags.add(tag)

        return point


class UpdateGPSPointSerializer(serializers.ModelSerializer):
    """
    Update GPS Point serializer.

    Allows partial updates with optional tag and type replacement.
    Matches OpenAPI schema: UpdateGPSPointRequest
    """
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    type_id = serializers.UUIDField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = GPSPoint
        fields = ['title', 'description', 'latitude', 'longitude', 'type_id', 'tags', 'is_public']

    def validate_type_id(self, value):
        """Validate that type exists and belongs to user or is a base type."""
        if not value:
            return None

        user = self.context['request'].user

        try:
            point_type = PointType.objects.get(id=value, status='active')

            if point_type.user is not None and point_type.user != user:
                raise serializers.ValidationError(
                    "You can only use your own types or base types."
                )

            return point_type
        except PointType.DoesNotExist:
            raise serializers.ValidationError("Point type not found or has been deleted.")

    def update(self, instance, validated_data):
        """
        Update GPS point with optional location, type, and tag changes.
        """
        tag_names = validated_data.pop('tags', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        point_type = validated_data.pop('type_id', None)

        # Update location if both lat/lon provided
        if latitude is not None and longitude is not None:
            instance.location = Point(longitude, latitude, srid=4326)

        # Update type if provided
        if point_type is not None:
            instance.type = point_type

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update tags if provided
        if tag_names is not None:
            instance.tags.clear()
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower().strip())
                instance.tags.add(tag)

        return instance


class GPSPointListSerializer(serializers.ModelSerializer):
    """
    Lightweight GPS Point serializer for list views.

    Excludes heavy fields like description and editing lock.
    """
    latitude = serializers.FloatField(source='location.y', read_only=True)
    longitude = serializers.FloatField(source='location.x', read_only=True)
    owner = UserSummarySerializer(read_only=True)
    type = PointTypeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    permission = serializers.SerializerMethodField()
    annotation_count = serializers.SerializerMethodField()

    class Meta:
        model = GPSPoint
        fields = [
            'id',
            'title',
            'latitude',
            'longitude',
            'owner',
            'type',
            'tags',
            'is_public',
            'created_at',
            'updated_at',
            'permission',
            'annotation_count',
        ]

    def get_permission(self, obj):
        """Determine current user's permission level."""
        user = self.context.get('request').user if self.context.get('request') else None

        if not user or not user.is_authenticated:
            return 'view' if obj.is_public else None

        if obj.owner == user:
            return 'owner'

        from apps.sharing.models import Share
        share = Share.objects.filter(gps_point=obj, recipient_user=user, is_active=True).first()

        if share:
            return share.permission_level

        if obj.is_public:
            return 'view'

        return None

    def get_annotation_count(self, obj):
        """Get the count of non-deleted annotations for this point."""
        # Exclude annotations that have a trash_entry (soft-deleted)
        return obj.annotations.exclude(trash_entry__isnull=False).count()
