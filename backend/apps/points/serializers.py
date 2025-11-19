"""
Serializers for points app.

Handles GPS points, tags, editing locks, and spatial data.
"""

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db.models import Q
from rest_framework import serializers

from apps.authentication.models import User

from .models import GPSPoint
from .models import PointType
from .models import Tag
from .models import UserTypeOrder


class UserSummarySerializer(serializers.ModelSerializer):
    """
    User summary serializer for nested relations.

    Only includes id and email (lighter than full UserSerializer).
    Matches OpenAPI schema: UserSummary
    """

    class Meta:
        model = User
        fields = ["id", "email"]
        read_only_fields = ["id", "email"]


class TagSerializer(serializers.ModelSerializer):
    """
    Tag serializer.

    Simple name-only serialization with owner information.
    Matches OpenAPI schema: Tag
    """

    owner = UserSummarySerializer(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]


class PointTypeSerializer(serializers.ModelSerializer):
    """
    PointType serializer with multilingual support.

    Includes full details with JSON names field for multilingual support.
    """

    owner = UserSummarySerializer(read_only=True)
    type = serializers.CharField(source="type_choice", read_only=True)

    class Meta:
        model = PointType
        fields = [
            "id",
            "type",
            "names",
            "creation_language",
            "icon",
            "order",
            "owner",
            "visibility",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "type", "owner", "status", "created_at", "updated_at"]

    def validate_names(self, value):
        """Validate names field."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Names must be a dictionary mapping language codes to names."
            )

        if len(value) == 0:
            raise serializers.ValidationError("At least one translation must be provided.")

        # Validate language codes are lowercase
        for lang_code in value.keys():
            if not lang_code.islower():
                raise serializers.ValidationError(
                    f"Language code '{lang_code}' must be lowercase (ISO 639-1)."
                )

        return value

    def validate_creation_language(self, value):
        """Validate creation language is lowercase."""
        if not value.islower():
            raise serializers.ValidationError("Creation language must be lowercase (ISO 639-1).")
        return value

    def to_representation(self, instance):
        """Convert icon URLs to absolute URLs if they're relative paths."""
        data = super().to_representation(instance)

        # Convert relative static/media URLs to absolute URLs
        icon = data.get("icon")
        if icon and isinstance(icon, str):
            # If icon starts with / but not http/https, make it absolute
            if icon.startswith("/") and not icon.startswith("http"):
                request = self.context.get("request")
                if request:
                    data["icon"] = request.build_absolute_uri(icon)

        return data

    def validate(self, attrs):
        """Cross-field validation."""
        # Check that creation_language has a corresponding name
        if "names" in attrs and "creation_language" in attrs:
            if attrs["creation_language"] not in attrs["names"]:
                raise serializers.ValidationError(
                    {
                        "creation_language": (
                            f"Creation language '{attrs['creation_language']}' must have a "
                            "corresponding name."
                        )
                    }
                )

        # Validate duplicate names for updates
        if "names" in attrs:
            user = self.context["request"].user
            names = attrs["names"]

            # Check if another type with these names already exists for this user
            existing_query = PointType.objects.filter(owner=user, names=names, status="active")

            # Exclude current instance if this is an update
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)

            if existing_query.exists():
                raise serializers.ValidationError(
                    {"names": "A point type with these names already exists."}
                )

        return attrs

    def create(self, validated_data):
        """Create a new point type for the authenticated user."""
        user = self.context["request"].user
        validated_data["owner"] = user
        validated_data["type_choice"] = "custom"

        # Set default icon if not provided
        if "icon" not in validated_data or not validated_data["icon"]:
            validated_data["icon"] = "📍"

        # Auto-assign order if not provided
        if "order" not in validated_data:
            from django.db.models import Q

            max_order = PointType.objects.filter(
                Q(owner=user) | Q(owner__isnull=True), status="active"
            ).aggregate(max_order=serializers.models.Max("order"))["max_order"]
            validated_data["order"] = (max_order or 0) + 1

        # Get creation language from user preferences
        if "creation_language" not in validated_data:
            from apps.settings.models import UserPreferences

            try:
                prefs = UserPreferences.objects.get(user=user)
                validated_data["creation_language"] = prefs.language
            except UserPreferences.DoesNotExist:
                validated_data["creation_language"] = "en"

        return super().create(validated_data)


class CreatePointTypeSerializer(serializers.ModelSerializer):
    """Serializer for creating point types (simplified input)."""

    class Meta:
        model = PointType
        fields = ["names", "creation_language", "icon", "order", "visibility"]
        extra_kwargs = {"names": {"required": True}}

    def validate_names(self, value):
        """Validate names field."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Names must be a dictionary.")

        if len(value) == 0:
            raise serializers.ValidationError("At least one translation is required.")

        return value

    def validate(self, attrs):
        """Validate the entire serializer data."""
        user = self.context["request"].user
        names = attrs.get("names")

        if names:
            existing_type = PointType.objects.filter(
                owner=user, names=names, status="active"
            ).exists()

            if existing_type:
                raise serializers.ValidationError(
                    {"names": "A point type with these names already exists."}
                )

        # Validate max types per user
        active_types_count = PointType.objects.filter(owner=user, status="active").count()

        if active_types_count >= settings.MAX_POINT_TYPES_PER_USER:
            raise serializers.ValidationError(
                {
                    "names": (
                        "You have reached the maximum of "
                        f"{settings.MAX_POINT_TYPES_PER_USER} point types. "
                        "Please delete some types before creating new ones."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        """Create with user from context and defaults."""
        user = self.context["request"].user
        validated_data["owner"] = user
        validated_data["type_choice"] = "custom"

        if "icon" not in validated_data or not validated_data["icon"]:
            validated_data["icon"] = "📍"

        if "order" not in validated_data:
            from django.db.models import Q

            max_order = PointType.objects.filter(
                Q(owner=user) | Q(owner__isnull=True), status="active"
            ).aggregate(max_order=serializers.models.Max("order"))["max_order"]
            validated_data["order"] = (max_order or 0) + 1

        # Get creation language from user preferences if not provided
        if "creation_language" not in validated_data:
            from apps.settings.models import UserPreferences

            try:
                prefs = UserPreferences.objects.get(user=user)
                validated_data["creation_language"] = prefs.language
            except UserPreferences.DoesNotExist:
                validated_data["creation_language"] = "en"

        return PointType.objects.create(**validated_data)


class PointTypeReorderSerializer(serializers.Serializer):
    """Serializer for reordering point types with per-user custom order."""

    order = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        help_text="List of {id, order} objects",
    )

    def validate_order(self, value):
        """Validate that all IDs exist and are accessible to the user."""

        user = self.context["request"].user
        type_ids = [item["id"] for item in value]

        # Check all types exist and are accessible (user's types OR base types)
        accessible_types = PointType.objects.filter(
            Q(id__in=type_ids), Q(owner=user) | Q(owner__isnull=True), status="active"
        ).values_list("id", flat=True)

        accessible_types_str = {str(tid) for tid in accessible_types}
        provided_ids = set(type_ids)

        if accessible_types_str != provided_ids:
            invalid_ids = provided_ids - accessible_types_str
            raise serializers.ValidationError(f"Invalid or inaccessible type IDs: {invalid_ids}")

        return value

    def save(self):
        """Save user-specific custom order for all types."""

        user = self.context["request"].user
        order_data = self.validated_data["order"]

        # Create or update UserTypeOrder for each type
        for item in order_data:
            UserTypeOrder.objects.update_or_create(
                user=user, type_id=item["id"], defaults={"order": int(item["order"])}
            )

        return {"success": True, "updated": len(order_data)}


class EditingLockSerializer(serializers.Serializer):
    """
    Editing lock serializer.

    Shows who is editing and when lock expires.
    Matches OpenAPI schema: EditingLock
    """

    locked_by = UserSummarySerializer(source="editing_lock_user", read_only=True)
    acquired_at = serializers.DateTimeField(source="editing_lock_acquired_at", read_only=True)
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
    shared_by = serializers.SerializerMethodField()

    # GeoJSON location (auto-generated from lat/lon)
    location = serializers.SerializerMethodField()

    class Meta:
        model = GPSPoint
        fields = [
            "id",
            "title",
            "description",
            "location",
            "latitude",
            "longitude",
            "owner",
            "type",
            "tags",
            "is_public",
            "created_at",
            "updated_at",
            "editing_lock",
            "permission",
            "annotation_count",
            "shared_by",
        ]
        read_only_fields = [
            "id",
            "owner",
            "created_at",
            "updated_at",
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
                "type": "Point",
                "coordinates": [obj.location.x, obj.location.y],  # [longitude, latitude]
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
        user = self.context.get("request").user if self.context.get("request") else None

        if not user or not user.is_authenticated:
            return "view" if obj.is_public else None

        # Owner has full permissions
        if obj.owner == user:
            return "owner"

        # Check share permissions
        from apps.sharing.models import Share

        share = Share.objects.filter(gps_point=obj, recipient_user=user, is_active=True).first()

        if share:
            return share.permission_level

        # Public points are view-only
        if obj.is_public:
            return "view"

        return None

    def get_annotation_count(self, obj):
        """Get the count of non-deleted annotations for this point."""
        # Exclude annotations that have a trash_entry (soft-deleted)
        return obj.annotations.exclude(trash_entry__isnull=False).count()

    def get_shared_by(self, obj):
        """
        Get the username of the friend who shared this point with the current user.

        Returns username if point was shared by a friend, None if user is owner or point is public.
        """
        user = self.context.get("request").user if self.context.get("request") else None

        if not user or not user.is_authenticated:
            return None

        # If user is the owner, return None
        if obj.owner == user:
            return None

        # Check if point was shared with user
        from apps.sharing.models import Share

        share = Share.objects.filter(
            gps_point=obj,
            recipient_user=user,
            is_active=True
        ).select_related("owner").first()

        if share and share.owner:
            return share.owner.username

        return None

    def create(self, validated_data):
        """
        Create GPS point from latitude/longitude.

        Converts lat/lon to PostGIS Point and sets owner.
        """
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")

        # Create PostGIS Point (longitude, latitude - note the order!)
        validated_data["location"] = Point(longitude, latitude, srid=4326)

        # Set owner from request user
        validated_data["owner"] = self.context["request"].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update GPS point, including location if lat/lon changed.
        """
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

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
        fields = ["title", "description", "latitude", "longitude", "type_id", "tags", "is_public"]

    def validate_type_id(self, value):
        """Validate that type exists and belongs to user or is a base type."""
        if not value:
            return None

        user = self.context["request"].user

        try:
            point_type = PointType.objects.get(id=value, status="active")

            # Type must belong to user or be a base type (owner=None)
            if point_type.owner is not None and point_type.owner != user:
                raise serializers.ValidationError("You can only use your own types or base types.")

            return point_type
        except PointType.DoesNotExist:
            raise serializers.ValidationError("Point type not found or has been deleted.") from None

    def create(self, validated_data):
        """
        Create GPS point with auto-created tags and type.
        """
        tag_names = validated_data.pop("tags", [])
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")
        point_type = validated_data.pop("type_id", None)

        # Create PostGIS Point
        validated_data["location"] = Point(longitude, latitude, srid=4326)
        validated_data["owner"] = self.context["request"].user

        # Set default type if not provided
        if not point_type:
            point_type = PointType.get_default_type()

        validated_data["type"] = point_type

        # Create point
        point = GPSPoint.objects.create(**validated_data)

        # Create/get tags and associate
        user = self.context["request"].user
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name.lower().strip(), owner=user)
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
        fields = ["title", "description", "latitude", "longitude", "type_id", "tags", "is_public"]

    def validate_type_id(self, value):
        """Validate that type exists and belongs to user or is a base type."""
        if not value:
            return None

        user = self.context["request"].user

        try:
            point_type = PointType.objects.get(id=value, status="active")

            if point_type.owner is not None and point_type.owner != user:
                raise serializers.ValidationError("You can only use your own types or base types.")

            return point_type
        except PointType.DoesNotExist:
            raise serializers.ValidationError("Point type not found or has been deleted.") from None

    def update(self, instance, validated_data):
        """
        Update GPS point with optional location, type, and tag changes.
        """
        tag_names = validated_data.pop("tags", None)
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)
        point_type = validated_data.pop("type_id", None)

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
            user = self.context["request"].user
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower().strip(), owner=user)
                instance.tags.add(tag)

        return instance


class GPSPointListSerializer(serializers.ModelSerializer):
    """
    Lightweight GPS Point serializer for list views.

    Excludes heavy fields like description and editing lock.
    """

    latitude = serializers.FloatField(source="location.y", read_only=True)
    longitude = serializers.FloatField(source="location.x", read_only=True)
    owner = UserSummarySerializer(read_only=True)
    type = PointTypeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    permission = serializers.SerializerMethodField()
    annotation_count = serializers.SerializerMethodField()

    class Meta:
        model = GPSPoint
        fields = [
            "id",
            "title",
            "latitude",
            "longitude",
            "owner",
            "type",
            "tags",
            "is_public",
            "created_at",
            "updated_at",
            "permission",
            "annotation_count",
        ]

    def get_permission(self, obj):
        """Determine current user's permission level."""
        user = self.context.get("request").user if self.context.get("request") else None

        if not user or not user.is_authenticated:
            return "view" if obj.is_public else None

        if obj.owner == user:
            return "owner"

        from apps.sharing.models import Share

        share = Share.objects.filter(gps_point=obj, recipient_user=user, is_active=True).first()

        if share:
            return share.permission_level

        if obj.is_public:
            return "view"

        return None

    def get_annotation_count(self, obj):
        """Get the count of non-deleted annotations for this point."""
        # Exclude annotations that have a trash_entry (soft-deleted)
        return obj.annotations.exclude(trash_entry__isnull=False).count()
