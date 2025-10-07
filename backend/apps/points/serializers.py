"""
Serializers for points app.

Handles GPS points, tags, editing locks, and spatial data.
"""

from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.authentication.serializers import UserSerializer
from .models import GPSPoint, Tag


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
        model = 'authentication.User'
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']


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
    latitude = serializers.FloatField(write_only=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(write_only=True, min_value=-180, max_value=180)
    
    # Read-only computed fields
    owner = UserSummarySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    editing_lock = EditingLockSerializer(source='*', read_only=True)
    permission = serializers.SerializerMethodField()
    
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
            'tags',
            'is_public',
            'created_at',
            'updated_at',
            'editing_lock',
            'permission',
        ]
        read_only_fields = [
            'id',
            'owner',
            'created_at',
            'updated_at',
        ]
    
    def get_location(self, obj):
        """Convert PostGIS Point to GeoJSON format."""
        if obj.location:
            return {
                'type': 'Point',
                'coordinates': [obj.location.x, obj.location.y]  # [longitude, latitude]
            }
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
    
    Accepts latitude/longitude and tag names (auto-creates tags).
    Matches OpenAPI schema: CreateGPSPointRequest
    """
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )
    
    class Meta:
        model = GPSPoint
        fields = ['title', 'description', 'latitude', 'longitude', 'tags', 'is_public']
    
    def create(self, validated_data):
        """
        Create GPS point with auto-created tags.
        """
        tag_names = validated_data.pop('tags', [])
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        
        # Create PostGIS Point
        validated_data['location'] = Point(longitude, latitude, srid=4326)
        validated_data['owner'] = self.context['request'].user
        
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
    
    Allows partial updates with optional tag replacement.
    Matches OpenAPI schema: UpdateGPSPointRequest
    """
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )
    
    class Meta:
        model = GPSPoint
        fields = ['title', 'description', 'latitude', 'longitude', 'tags', 'is_public']
    
    def update(self, instance, validated_data):
        """
        Update GPS point with optional location and tag changes.
        """
        tag_names = validated_data.pop('tags', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        # Update location if both lat/lon provided
        if latitude is not None and longitude is not None:
            instance.location = Point(longitude, latitude, srid=4326)
        
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
    tags = TagSerializer(many=True, read_only=True)
    permission = serializers.SerializerMethodField()
    
    class Meta:
        model = GPSPoint
        fields = [
            'id',
            'title',
            'latitude',
            'longitude',
            'owner',
            'tags',
            'is_public',
            'created_at',
            'updated_at',
            'permission',
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
