"""
Serializers for sharing app.

Handles point sharing, permissions, and email invitations.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone
from rest_framework import serializers

from apps.authentication.serializers import UserSerializer
from apps.points.serializers import GPSPointListSerializer
from apps.points.serializers import GPSPointSerializer
from apps.points.serializers import PointTypeSerializer
from apps.points.serializers import TagSerializer
from apps.sharing.models import AutoShareRule
from apps.sharing.models import Friendship
from apps.sharing.models import Share


class ShareSerializer(serializers.ModelSerializer):
    """
    Share serializer with full details.

    Includes nested owner, recipient, point, and invitation status.
    Matches OpenAPI schema: Share
    """

    owner = UserSerializer(read_only=True)
    recipient_user = UserSerializer(read_only=True)
    gps_point = GPSPointListSerializer(read_only=True)
    invitation_status = serializers.SerializerMethodField()

    class Meta:
        model = Share
        fields = [
            "id",
            "gps_point",
            "owner",
            "recipient_email",
            "recipient_user",
            "permission_level",
            "invitation_token",
            "invitation_sent_at",
            "accepted_at",
            "invitation_status",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "recipient_user",
            "invitation_token",
            "invitation_sent_at",
            "accepted_at",
            "invitation_status",
            "is_active",
            "created_at",
        ]

    def get_invitation_status(self, obj):
        """
        Get invitation status: pending, accepted, or expired.
        """
        if obj.accepted_at:
            return "accepted"

        # Check if invitation expired (7 days)
        if obj.invitation_sent_at:
            expiry = obj.invitation_sent_at + timedelta(days=7)
            if timezone.now() > expiry:
                return "expired"

        return "pending"


class CreateShareSerializer(serializers.ModelSerializer):
    """
    Create share serializer.

    Accepts recipient email and permission level, sends invitation.
    Matches OpenAPI schema: CreateShareRequest
    """

    class Meta:
        model = Share
        fields = ["recipient_email", "permission_level"]

    def validate_permission_level(self, value):
        """Validate permission level is valid."""
        if value not in ["view", "edit", "manage"]:
            raise serializers.ValidationError(
                f"Invalid permission level: {value}. Must be one of: view, edit, manage"
            )
        return value

    def validate(self, attrs):
        """
        Validate share creation:
        - User must have manage permission
        - Cannot share with self
        - No duplicate shares for same email

        Note: gps_point comes from view context, not from request data
        """
        user = self.context["request"].user
        gps_point = self.context.get("gps_point")
        if not gps_point:
            raise serializers.ValidationError(
                {
                    "error": "MISSING_POINT",
                    "gps_point": "GPS point is required.",
                }
            )

        recipient_email = attrs["recipient_email"]

        # Check if user has manage permission
        point_serializer = GPSPointSerializer(gps_point, context=self.context)
        permission = point_serializer.get_permission(gps_point)

        if permission not in ["manage", "owner"]:
            raise serializers.ValidationError(
                {
                    "error": "ACCESS_DENIED",
                    "owner": "You do not have permission to share this point.",
                }
            )

        # Cannot share with self
        if recipient_email == user.email:
            raise serializers.ValidationError(
                {
                    "error": "SELF_SHARE",
                    "recipient_email": "Cannot share point with yourself.",
                }
            )

        # Check for existing share
        existing_share = Share.objects.filter(
            gps_point=gps_point,
            recipient_email=recipient_email,
        ).first()

        if existing_share:
            raise serializers.ValidationError(
                {
                    "error": "DUPLICATE_SHARE",
                    "recipient_email": f"Point already shared with {recipient_email}.",
                }
            )

        return attrs

    def create(self, validated_data):
        """
        Create share and send invitation email.
        """
        # Set owner from request user (original owner, not sharer) and gps_point from context
        gps_point = self.context["gps_point"]
        validated_data["gps_point"] = gps_point
        validated_data["owner"] = gps_point.owner

        # Generate invitation token (UUID auto-generated by model)
        share = super().create(validated_data)

        # TODO: Send invitation email via email service
        # For now, just mark as sent
        share.invitation_sent_at = timezone.now()
        share.save()

        return share


class UpdateShareSerializer(serializers.ModelSerializer):
    """
    Update share serializer.

    Allows permission level changes only.
    Matches OpenAPI schema: UpdateShareRequest
    """

    class Meta:
        model = Share
        fields = ["permission_level"]

    def validate_permission_level(self, value):
        """Validate permission level is valid."""
        if value not in ["view", "edit", "manage"]:
            raise serializers.ValidationError(
                f"Invalid permission level: {value}. Must be one of: view, edit, manage"
            )
        return value

    def validate(self, attrs):
        """Validate user has permission to update share."""
        share = self.instance

        # Only owner or users with manage permission can update
        point_serializer = GPSPointSerializer(share.gps_point, context=self.context)
        permission = point_serializer.get_permission(share.gps_point)

        if permission not in ["manage", "owner"]:
            raise serializers.ValidationError(
                {
                    "error": "ACCESS_DENIED",
                    "message": "You do not have permission to update this share.",
                }
            )

        return attrs


class AcceptShareSerializer(serializers.Serializer):
    """
    Accept share invitation serializer.

    Validates invitation token and links share to user.
    Matches OpenAPI schema: AcceptShareRequest
    """

    invitation_token = serializers.UUIDField()

    def validate_invitation_token(self, value):
        """
        Validate invitation token exists and is not expired.
        """
        try:
            share = Share.objects.get(invitation_token=value)
        except Share.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "error": "INVALID_TOKEN",
                    "message": "Invalid invitation token.",
                }
            ) from None

        # Check if already accepted
        if share.accepted_at:
            raise serializers.ValidationError(
                {
                    "error": "ALREADY_ACCEPTED",
                    "message": "Invitation already accepted.",
                }
            )

        # Check if expired (7 days)
        if share.invitation_sent_at:
            expiry = share.invitation_sent_at + timedelta(days=7)
            if timezone.now() > expiry:
                raise serializers.ValidationError(
                    {
                        "error": "INVITATION_EXPIRED",
                        "message": "Invitation has expired (7 days).",
                    }
                )

        self.context["share"] = share
        return value

    def save(self):
        """
        Accept invitation: link share to user and mark accepted.
        """
        share = self.context["share"]
        user = self.context["request"].user

        share.accept(user)
        return share


class FriendSerializer(serializers.Serializer):
    """
    Friend serializer with share statistics.

    Returns friend user details along with counts of shares sent/received.
    Used in friends list view.
    Note: Email is excluded for privacy.
    """

    id = serializers.UUIDField(read_only=True)
    friendship_id = serializers.SerializerMethodField()
    username = serializers.CharField(read_only=True)
    shares_sent_count = serializers.IntegerField(read_only=True, default=0)
    shares_received_count = serializers.IntegerField(read_only=True, default=0)
    friendship_created_at = serializers.SerializerMethodField()

    def get_friendship_id(self, obj):
        """Get the friendship ID."""
        user = self.context.get("request").user
        friendship = Friendship.objects.filter(user=user, friend=obj).first()
        return friendship.id if friendship else None

    def get_friendship_created_at(self, obj):
        """Get the friendship creation timestamp."""
        user = self.context.get("request").user
        friendship = Friendship.objects.filter(user=user, friend=obj).first()
        return friendship.created_at if friendship else None


class AddFriendSerializer(serializers.Serializer):
    """
    Add friend serializer.

    Accepts username of the friend to add.
    """

    username = serializers.CharField(
        required=True,
        help_text="Username of the friend to add",
        max_length=150,
    )

    def validate_username(self, value):
        """Validate username format and existence."""
        if not value or not value.strip():
            raise serializers.ValidationError("Username is required")

        value = value.strip()

        # Check if trying to add self
        user = self.context["request"].user
        if user.username == value:
            raise serializers.ValidationError("Cannot add yourself as a friend")

        # Check if user exists
        from apps.authentication.models import User

        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with username '{value}' not found") from None

        return value

    def create(self, validated_data):
        """Create friendship using FriendshipService."""
        from apps.sharing.services import FriendshipService

        user = self.context["request"].user
        username = validated_data["username"]

        try:
            friendship = FriendshipService.add_friend(user, username)
            return friendship
        except ValueError as e:
            raise serializers.ValidationError({"username": str(e)}) from None


class FriendshipSerializer(serializers.ModelSerializer):
    """
    Friendship serializer.

    Returns friendship details including friend info.
    """

    friend = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ["id", "friend", "created_at"]
        read_only_fields = ["id", "friend", "created_at"]


class SharedPointWithPermissionSerializer(serializers.Serializer):
    """
    Serializer for points with share information.

    Includes both point data and the associated share's permission level and ID.
    """

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    type = PointTypeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    share_id = serializers.SerializerMethodField()
    permission_level = serializers.SerializerMethodField()

    def get_share_id(self, obj):
        """Get the share ID for this point."""
        return getattr(obj, "share_id", None)

    def get_permission_level(self, obj):
        """Get the permission level for this point."""
        return getattr(obj, "permission_level", None)


class FriendDetailSerializer(serializers.Serializer):
    """
    Friend detail serializer with shared points.

    Returns friend details and list of points shared with them.
    Note: Email is excluded for privacy.
    """

    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    friendship_created_at = serializers.DateTimeField(read_only=True)
    shared_points = SharedPointWithPermissionSerializer(many=True, read_only=True)
    shares_sent_count = serializers.IntegerField(read_only=True)
    shares_received_count = serializers.IntegerField(read_only=True)


class BatchShareSerializer(serializers.Serializer):
    """
    Batch share serializer.

    Accepts multiple point IDs and usernames to create shares in bulk.
    """

    point_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of GPS point UUIDs to share",
        min_length=1,
    )

    usernames = serializers.ListField(
        child=serializers.CharField(max_length=150),
        required=True,
        help_text="List of usernames to share with",
        min_length=1,
    )

    permission_level = serializers.ChoiceField(
        choices=["view", "edit", "manage"],
        required=True,
        help_text="Permission level for all shares",
    )

    def validate_point_ids(self, value):
        """Validate point IDs list."""
        if not value:
            raise serializers.ValidationError("At least one point ID is required")

        if len(value) > 100:
            raise serializers.ValidationError("Cannot share more than 100 points at once")

        return value

    def validate_usernames(self, value):
        """Validate usernames list."""
        if not value:
            raise serializers.ValidationError("At least one username is required")

        if len(value) > 50:
            raise serializers.ValidationError("Cannot share with more than 50 users at once")

        # Remove duplicates and whitespace
        cleaned = [u.strip() for u in value if u.strip()]
        return list(set(cleaned))

    def create(self, validated_data):
        """Create batch shares using BatchShareService."""
        from apps.sharing.services import BatchShareService

        user = self.context["request"].user
        point_ids = [str(pid) for pid in validated_data["point_ids"]]
        usernames = validated_data["usernames"]
        permission_level = validated_data["permission_level"]

        result = BatchShareService.batch_create_shares(
            point_ids=point_ids,
            usernames=usernames,
            permission_level=permission_level,
            owner=user,
        )

        return result


class AutoShareRuleSerializer(serializers.ModelSerializer):
    """
    Auto-share rule serializer with full details.

    Returns rule configuration with nested point types and tags.
    """

    point_types = PointTypeSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = AutoShareRule
        fields = [
            "id",
            "friend",
            "permission_level",
            "share_all",
            "point_types",
            "tags",
            "match_all_tags",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class CreateAutoShareRuleSerializer(serializers.ModelSerializer):
    """
    Create auto-share rule serializer.

    Accepts friend ID, permission level, and optional filters (point types, tags).
    Validates:
    - Max 50 rules per friend
    - share_all cannot be combined with type/tag filters
    - Must have at least one filter if share_all=False
    """

    point_type_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="List of point type IDs to match (any match)",
    )

    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="List of tag IDs to match (ALL must match - AND logic)",
    )

    class Meta:
        model = AutoShareRule
        fields = [
            "friend",
            "permission_level",
            "share_all",
            "point_type_ids",
            "tag_ids",
            "match_all_tags",
            "is_active",
        ]

    def validate_permission_level(self, value):
        """Validate permission level is valid."""
        if value not in ["view", "edit", "manage"]:
            raise serializers.ValidationError(
                f"Invalid permission level: {value}. Must be one of: view, edit, manage"
            )
        return value

    def validate(self, attrs):
        """
        Validate rule creation:
        - Friend must exist and be an actual friend
        - Cannot create rule for yourself
        - Max 50 rules per friend
        - share_all cannot be combined with filters
        - Must have at least one filter if share_all=False
        """
        user = self.context["request"].user
        friend = attrs.get("friend")

        # Cannot create rule for yourself
        if friend == user:
            raise serializers.ValidationError(
                {
                    "error": "SELF_RULE",
                    "friend": "Cannot create auto-share rule for yourself",
                }
            )

        # Check if friend exists in friendships
        from apps.sharing.models import Friendship

        friendship_exists = Friendship.objects.filter(user=user, friend=friend).exists()
        if not friendship_exists:
            raise serializers.ValidationError(
                {
                    "error": "NOT_FRIEND",
                    "friend": "User is not in your friends list",
                }
            )

        # Check max rules per friend
        existing_count = AutoShareRule.objects.filter(
            user=user, friend=friend, is_active=True
        ).count()

        if existing_count >= AutoShareRule.MAX_RULES_PER_FRIEND:
            raise serializers.ValidationError(
                {
                    "error": "MAX_RULES_EXCEEDED",
                    "friend": f"Cannot create more than {AutoShareRule.MAX_RULES_PER_FRIEND} active rules per friend",
                }
            )

        # Validate share_all constraints
        share_all = attrs.get("share_all", False)
        point_type_ids = attrs.get("point_type_ids", [])
        tag_ids = attrs.get("tag_ids", [])

        if share_all:
            # share_all cannot be combined with filters
            if point_type_ids or tag_ids:
                raise serializers.ValidationError(
                    {
                        "error": "INVALID_FILTERS",
                        "share_all": "Cannot specify point types or tags when share_all is True",
                    }
                )
        else:
            # Must have at least one filter
            if not point_type_ids and not tag_ids:
                raise serializers.ValidationError(
                    {
                        "error": "NO_FILTERS",
                        "message": "Must specify at least one point type or tag, or set share_all to True",
                    }
                )

        # Validate point types exist and belong to user
        if point_type_ids:
            from apps.points.models import PointType

            point_types = PointType.objects.filter(id__in=point_type_ids, status="active").filter(
                models.Q(owner=user) | models.Q(owner__isnull=True)  # User's types or base types
            )

            if point_types.count() != len(point_type_ids):
                raise serializers.ValidationError(
                    {
                        "error": "INVALID_POINT_TYPES",
                        "point_type_ids": "Some point types do not exist or are not accessible",
                    }
                )

            attrs["_point_types"] = list(point_types)

        # Validate tags exist and belong to user
        if tag_ids:
            from apps.points.models import Tag

            tags = Tag.objects.filter(id__in=tag_ids, owner=user)

            if tags.count() != len(tag_ids):
                raise serializers.ValidationError(
                    {
                        "error": "INVALID_TAGS",
                        "tag_ids": "Some tags do not exist or do not belong to you",
                    }
                )

            attrs["_tags"] = list(tags)

        return attrs

    def create(self, validated_data):
        """Create auto-share rule and associate with point types and tags."""
        user = self.context["request"].user

        # Extract M2M data
        point_types = validated_data.pop("_point_types", [])
        tags = validated_data.pop("_tags", [])
        validated_data.pop("point_type_ids", None)
        validated_data.pop("tag_ids", None)

        # Set user
        validated_data["user"] = user

        # Create rule
        rule = super().create(validated_data)

        # Associate M2M relations
        if point_types:
            rule.point_types.set(point_types)
        if tags:
            rule.tags.set(tags)

        return rule


class UpdateAutoShareRuleSerializer(serializers.ModelSerializer):
    """
    Update auto-share rule serializer.

    Allows updating permission level and active status only.
    Point types and tags cannot be updated - delete and recreate rule instead.
    """

    class Meta:
        model = AutoShareRule
        fields = ["permission_level", "is_active"]

    def validate_permission_level(self, value):
        """Validate permission level is valid."""
        if value not in ["view", "edit", "manage"]:
            raise serializers.ValidationError(
                f"Invalid permission level: {value}. Must be one of: view, edit, manage"
            )
        return value

    def validate(self, attrs):
        """Validate user owns the rule."""
        rule = self.instance
        user = self.context["request"].user

        if rule.user != user:
            raise serializers.ValidationError(
                {
                    "error": "ACCESS_DENIED",
                    "message": "You do not have permission to update this rule",
                }
            )

        return attrs
