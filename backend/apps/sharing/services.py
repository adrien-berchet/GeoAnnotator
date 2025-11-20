"""
Sharing services.

Handles permissions, email invitations, and share management.
"""

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from apps.authentication.models import User
from apps.points.models import GPSPoint

from .models import AutoShareRule
from .models import Friendship
from .models import Share


class PermissionService:
    """Service for checking and managing permissions."""

    PERMISSION_LEVELS = ["view", "edit", "manage", "owner"]

    @staticmethod
    def get_user_permission(point: GPSPoint, user: User) -> str | None:
        """
        Get user's permission level for a point.

        Args:
            point: GPSPoint object
            user: User object

        Returns:
            str: 'owner', 'manage', 'edit', 'view', or None
        """
        # Owner has full permissions
        if point.owner == user:
            return "owner"

        # Check share permissions
        share = Share.objects.filter(
            gps_point=point,
            recipient_user=user,
            is_active=True,
        ).first()

        if share:
            return share.permission_level

        # Public points are view-only
        if point.is_public:
            return "view"

        return None

    @staticmethod
    def has_permission(point: GPSPoint, user: User, required_level: str) -> bool:
        """
        Check if user has at least the required permission level.

        Args:
            point: GPSPoint object
            user: User object
            required_level: 'view', 'edit', or 'manage'

        Returns:
            bool: True if user has permission
        """
        user_level = PermissionService.get_user_permission(point, user)

        if user_level is None:
            return False

        # Permission hierarchy: owner > manage > edit > view
        hierarchy = {
            "view": 0,
            "edit": 1,
            "manage": 2,
            "owner": 3,
        }

        return hierarchy.get(user_level, -1) >= hierarchy.get(required_level, 99)

    @staticmethod
    def can_view(point: GPSPoint, user: User) -> bool:
        """Check if user can view point."""
        return PermissionService.has_permission(point, user, "view")

    @staticmethod
    def can_edit(point: GPSPoint, user: User) -> bool:
        """Check if user can edit point."""
        return PermissionService.has_permission(point, user, "edit")

    @staticmethod
    def can_share(point: GPSPoint, user: User) -> bool:
        """Check if user can share point (requires manage permission)."""
        return PermissionService.has_permission(point, user, "manage")

    @staticmethod
    def is_owner(point: GPSPoint, user: User) -> bool:
        """Check if user is owner."""
        return point.owner == user

    @staticmethod
    def get_accessible_points(user: User, include_public: bool = True):
        """
        Get all points accessible to user.

        Args:
            user: User object
            include_public: Include public points

        Returns:
            QuerySet of GPSPoint objects
        """
        # Build filter conditions
        conditions = Q(owner=user) | Q(shares__recipient_user=user, shares__is_active=True)

        if include_public:
            conditions |= Q(is_public=True)

        query = GPSPoint.objects.filter(conditions).distinct()

        # Exclude trashed points (points with a Trash entry, check manually for expiration)
        query = query.filter(trash_entry__isnull=True)

        # Optimize queries by selecting related objects
        query = query.select_related("type", "type__owner", "owner")

        return query


class EmailInvitationService:
    """Service for email invitations."""

    INVITATION_EXPIRY_DAYS = 7

    @staticmethod
    def send_invitation(share: Share) -> bool:
        """
        Send invitation email to recipient.

        Args:
            share: Share object

        Returns:
            bool: True if email sent successfully
        """
        # Generate acceptance URL
        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        acceptance_url = f"{base_url}/shares/accept/{share.invitation_token}"

        # Email content
        subject = f"{share.owner.email} shared a GPS point with you"
        message = f"""
Hello,

{share.owner.email} has shared a GPS point with you on GeoAnnotator.

Point: {share.gps_point.title}
Permission: {share.permission_level}

Click the link below to accept the invitation:
{acceptance_url}

This invitation will expire in {EmailInvitationService.INVITATION_EXPIRY_DAYS} days.

---
GeoAnnotator Team
        """.strip()

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[share.recipient_email],
                fail_silently=False,
            )

            # Update invitation sent timestamp
            share.invitation_sent_at = timezone.now()
            share.save()

            return True
        except Exception as e:
            print(f"Failed to send invitation email: {e}")
            return False

    @staticmethod
    def is_invitation_expired(share: Share) -> bool:
        """
        Check if invitation has expired (7 days).

        Args:
            share: Share object

        Returns:
            bool: True if expired
        """
        if not share.invitation_sent_at:
            return False

        expiry = share.invitation_sent_at + timedelta(
            days=EmailInvitationService.INVITATION_EXPIRY_DAYS
        )
        return timezone.now() > expiry

    @staticmethod
    def get_invitation_status(share: Share) -> str:
        """
        Get invitation status.

        Args:
            share: Share object

        Returns:
            str: 'pending', 'accepted', or 'expired'
        """
        if share.accepted_at:
            return "accepted"

        if EmailInvitationService.is_invitation_expired(share):
            return "expired"

        return "pending"


class ShareService:
    """Service for share management."""

    @staticmethod
    def create_share(
        point: GPSPoint,
        recipient_email: str,
        permission_level: str,
        owner: User,
    ) -> Share:
        """
        Create share and send invitation.

        Args:
            point: GPSPoint to share
            recipient_email: Recipient email address
            permission_level: 'view', 'edit', or 'manage'
            owner: User creating share

        Returns:
            Share object

        Raises:
            ValueError: If validation fails
        """
        # Validate permission level
        if permission_level not in ["view", "edit", "manage"]:
            raise ValueError(f"Invalid permission level: {permission_level}")

        # Check if user has permission to share
        if not PermissionService.can_share(point, owner):
            raise ValueError("User does not have permission to share this point")

        # Check for duplicate share
        existing = Share.objects.filter(
            gps_point=point,
            recipient_email=recipient_email,
        ).first()

        if existing:
            raise ValueError(f"Point already shared with {recipient_email}")

        # Check if recipient is the owner or point owner
        if recipient_email == owner.email or recipient_email == point.owner.email:
            raise ValueError("Cannot share point with yourself or the owner")

        # Check if recipient user exists
        recipient_user = None
        try:
            email_hash = User.hash_email(recipient_email)
            recipient_user = User.objects.get(email_hash=email_hash)
        except User.DoesNotExist:
            pass  # Will be linked when user accepts invitation

        # Create share
        share = Share.objects.create(
            gps_point=point,
            owner=point.owner,  # Always use original owner
            recipient_email=recipient_email,
            recipient_user=recipient_user,
            permission_level=permission_level,
        )

        # Send invitation email
        EmailInvitationService.send_invitation(share)

        return share

    @staticmethod
    def update_share_permission(share: Share, permission_level: str, user: User) -> Share:
        """
        Update share permission level.

        Args:
            share: Share object
            permission_level: New permission level
            user: User updating share

        Returns:
            Updated Share object

        Raises:
            ValueError: If validation fails
        """
        # Validate permission level
        if permission_level not in ["view", "edit", "manage"]:
            raise ValueError(f"Invalid permission level: {permission_level}")

        # Check if user has permission to update
        if not PermissionService.can_share(share.gps_point, user):
            raise ValueError("User does not have permission to update this share")

        share.permission_level = permission_level
        share.save()

        return share

    @staticmethod
    def revoke_share(share: Share, user: User, cascade: bool = True) -> None:
        """
        Revoke share (delete it).

        Args:
            share: Share object
            user: User revoking share
            cascade: If True, also revoke downstream shares

        Raises:
            ValueError: If user doesn't have permission
        """
        # Check if user has permission to revoke
        if not PermissionService.can_share(share.gps_point, user):
            raise ValueError("User does not have permission to revoke this share")

        # Cascade revoke: delete shares created by this recipient
        if cascade and share.recipient_user:
            downstream_shares = Share.objects.filter(
                gps_point=share.gps_point,
                owner=share.recipient_user,
            )
            downstream_shares.delete()

        # Delete share
        share.delete()

    @staticmethod
    def accept_invitation(invitation_token: str, user: User) -> Share:
        """
        Accept share invitation.

        Args:
            invitation_token: UUID invitation token
            user: User accepting invitation

        Returns:
            Share object

        Raises:
            ValueError: If token invalid or expired
        """
        try:
            share = Share.objects.get(invitation_token=invitation_token)
        except Share.DoesNotExist:
            raise ValueError("Invalid invitation token") from None

        # Check if already accepted
        if share.accepted_at:
            raise ValueError("Invitation already accepted")

        # Check if expired
        if EmailInvitationService.is_invitation_expired(share):
            raise ValueError("Invitation has expired (7 days)")

        # Accept invitation
        share.accept(user)

        return share

    @staticmethod
    def deactivate_shares_for_point(point: GPSPoint) -> None:
        """
        Deactivate all shares for a point (when moving to trash).

        Args:
            point: GPSPoint object
        """
        Share.objects.filter(gps_point=point).update(is_active=False)

    @staticmethod
    def reactivate_shares_for_point(point: GPSPoint) -> None:
        """
        Reactivate all shares for a point (when restoring from trash).

        Args:
            point: GPSPoint object
        """
        Share.objects.filter(gps_point=point).update(is_active=True)


class FriendshipService:
    """Service for managing friendships between users."""

    @staticmethod
    def add_friend(user: User, friend_username: str) -> Friendship:
        """
        Add a friend by username.

        Creates a bidirectional friendship - two Friendship records are created,
        one for each direction.

        Args:
            user: User who is adding the friend
            friend_username: Username of the friend to add

        Returns:
            Friendship object (user → friend)

        Raises:
            ValueError: If friend not found, trying to add self, or friendship exists
        """
        # Validate username
        if not friend_username or not friend_username.strip():
            raise ValueError("Username is required")

        friend_username = friend_username.strip()

        # Check if trying to add self
        if user.username == friend_username:
            raise ValueError("Cannot add yourself as a friend")

        # Find friend by username
        try:
            friend = User.objects.get(username=friend_username)
        except User.DoesNotExist:
            raise ValueError(f"User with username '{friend_username}' not found") from None

        # Check if friendship already exists (either direction)
        existing = Friendship.objects.filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user)
        ).exists()

        if existing:
            raise ValueError(f"Already friends with {friend_username}")

        # Create bidirectional friendship
        friendship_1 = Friendship.objects.create(user=user, friend=friend)
        Friendship.objects.create(user=friend, friend=user)

        return friendship_1

    @staticmethod
    def remove_friend(user: User, friend: User) -> dict:
        """
        Remove a friendship and revoke all shares in both directions.

        This is a bidirectional operation:
        1. Delete friendship records (both directions)
        2. Revoke all shares FROM user TO friend
        3. Revoke all shares FROM friend TO user

        Args:
            user: User who is removing the friend
            friend: Friend to remove

        Returns:
            dict with counts: {
                'friendships_deleted': int,
                'shares_revoked_to_friend': int,
                'shares_revoked_from_friend': int,
                'total_shares_revoked': int
            }

        Raises:
            ValueError: If not friends or friend not found
        """
        # Check if friendship exists
        friendship_exists = Friendship.objects.filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user)
        ).exists()

        if not friendship_exists:
            raise ValueError(f"Not friends with {friend.username}")

        # Delete friendships (both directions)
        friendships_deleted = Friendship.objects.filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user)
        ).delete()[0]

        # Revoke shares FROM user TO friend
        # Find shares where user is owner and friend is recipient
        shares_to_friend = Share.objects.filter(
            owner=user,
            recipient_user=friend,
        )
        shares_revoked_to_friend = shares_to_friend.count()
        shares_to_friend.delete()

        # Revoke shares FROM friend TO user
        # Find shares where friend is owner and user is recipient
        shares_from_friend = Share.objects.filter(
            owner=friend,
            recipient_user=user,
        )
        shares_revoked_from_friend = shares_from_friend.count()
        shares_from_friend.delete()

        return {
            "friendships_deleted": friendships_deleted,
            "shares_revoked_to_friend": shares_revoked_to_friend,
            "shares_revoked_from_friend": shares_revoked_from_friend,
            "total_shares_revoked": shares_revoked_to_friend + shares_revoked_from_friend,
        }

    @staticmethod
    def get_friends(user: User):
        """
        Get all friends of a user with share statistics.

        Returns a queryset of User objects that are friends with the given user,
        annotated with share counts.

        Args:
            user: User to get friends for

        Returns:
            QuerySet of User objects (friends)
        """
        from django.db.models import Count

        # Get friend IDs from friendships where user is the initiator
        friendship_ids = Friendship.objects.filter(user=user).values_list("friend_id", flat=True)

        # Get friends and annotate with share counts
        friends = (
            User.objects.filter(id__in=friendship_ids)
            .annotate(
                # Count shares sent to this friend
                shares_sent_count=Count(
                    "shares_received",
                    filter=Q(shares_received__owner=user, shares_received__is_active=True),
                ),
                # Count shares received from this friend
                shares_received_count=Count(
                    "shares_sent",
                    filter=Q(shares_sent__recipient_user=user, shares_sent__is_active=True),
                ),
            )
            .order_by("username")
        )

        return friends

    @staticmethod
    def get_shared_points_with_friend(user: User, friend: User):
        """
        Get all points shared with a specific friend.

        Returns points owned by user that are shared with friend.

        Args:
            user: User who owns the points
            friend: Friend to check shares with

        Returns:
            QuerySet of GPSPoint objects shared with friend
        """
        # Get points owned by user that are shared with friend
        shared_points = GPSPoint.objects.filter(
            owner=user, shares__recipient_user=friend, shares__is_active=True
        ).distinct()

        return shared_points

    @staticmethod
    def are_friends(user: User, friend: User) -> bool:
        """
        Check if two users are friends.

        Args:
            user: First user
            friend: Second user

        Returns:
            bool: True if friends, False otherwise
        """
        return Friendship.objects.filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user)
        ).exists()

    @staticmethod
    def get_friendship(user: User, friend: User) -> Friendship | None:
        """
        Get the friendship object between two users.

        Args:
            user: First user
            friend: Second user

        Returns:
            Friendship object or None if not friends
        """
        return Friendship.objects.filter(Q(user=user, friend=friend)).first()


class BatchShareService:
    """Service for batch sharing operations."""

    @staticmethod
    def batch_create_shares(
        point_ids: list[str],
        usernames: list[str],
        permission_level: str,
        owner: User,
    ) -> dict:
        """
        Share multiple points with multiple users.

        Creates shares for each combination of point and username.
        Automatically creates friendships if they don't exist (hybrid approach).

        Args:
            point_ids: List of GPS point UUIDs to share
            usernames: List of usernames to share with
            permission_level: Permission level for all shares ('view', 'edit', 'manage')
            owner: User creating the shares

        Returns:
            dict with results: {
                'success_count': int,
                'error_count': int,
                'already_shared_count': int,
                'total_attempted': int,
                'results': [
                    {
                        'point_id': str,
                        'username': str,
                        'status': 'success' | 'error' | 'already_shared',
                        'error': str (if status == 'error'),
                        'share_id': str (if status == 'success')
                    }
                ]
            }
        """
        results = []
        success_count = 0
        error_count = 0
        already_shared_count = 0

        # Validate permission level
        if permission_level not in ["view", "edit", "manage"]:
            return {
                "success_count": 0,
                "error_count": len(point_ids) * len(usernames),
                "total_attempted": len(point_ids) * len(usernames),
                "error": f"Invalid permission level: {permission_level}",
                "results": [],
            }

        # Get all points and validate ownership/permissions
        points = GPSPoint.objects.filter(id__in=point_ids)
        point_dict = {str(p.id): p for p in points}

        # Get all users by username
        users = User.objects.filter(username__in=usernames)
        user_dict = {u.username: u for u in users}

        # Process each combination
        for point_id in point_ids:
            point = point_dict.get(point_id)

            if not point:
                # Point not found or no access
                for username in usernames:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "error",
                            "error": "Point not found or access denied",
                        }
                    )
                    error_count += 1
                continue

            # Check if user has permission to share this point
            if not PermissionService.can_share(point, owner):
                for username in usernames:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "error",
                            "error": "No permission to share this point",
                        }
                    )
                    error_count += 1
                continue

            # Share with each user
            for username in usernames:
                friend = user_dict.get(username)

                if not friend:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "error",
                            "error": f"User '{username}' not found",
                        }
                    )
                    error_count += 1
                    continue

                # Check if trying to share with self
                if friend == owner:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "error",
                            "error": "Cannot share with yourself",
                        }
                    )
                    error_count += 1
                    continue

                # Create friendship if it doesn't exist (hybrid approach)
                try:
                    if not FriendshipService.are_friends(owner, friend):
                        FriendshipService.add_friend(owner, username)
                except ValueError:
                    # Friendship might already exist (race condition), ignore
                    pass

                # Check if already shared
                existing_share = Share.objects.filter(
                    gps_point=point,
                    recipient_user=friend,
                ).first()

                if existing_share:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "already_shared",
                            "message": "Already shared with this user",
                        }
                    )
                    already_shared_count += 1
                    continue

                # Create share
                try:
                    # Get recipient email for backward compatibility
                    recipient_email = friend.email

                    share = Share.objects.create(
                        gps_point=point,
                        owner=point.owner,
                        recipient_email=recipient_email,
                        recipient_user=friend,
                        permission_level=permission_level,
                        accepted_at=timezone.now(),  # Auto-accept for existing users
                    )

                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "success",
                            "share_id": str(share.id),
                        }
                    )
                    success_count += 1

                except Exception as e:
                    results.append(
                        {
                            "point_id": point_id,
                            "username": username,
                            "status": "error",
                            "error": str(e),
                        }
                    )
                    error_count += 1

        return {
            "success_count": success_count,
            "error_count": error_count,
            "already_shared_count": already_shared_count,
            "total_attempted": len(point_ids) * len(usernames),
            "results": results,
        }


class AutoShareService:
    """Service for automatic sharing based on rules."""

    @staticmethod
    def apply_auto_share_rules(point: GPSPoint) -> dict:
        """
        Apply auto-share rules for a newly created point.

        Evaluates all active rules for the point owner and creates shares
        with friends based on matching rules.

        When multiple rules match for the same friend:
        - Uses the highest permission level

        Skips auto-sharing if:
        - Point already manually shared with friend
        - Friend doesn't exist or friendship removed

        Args:
            point: Newly created GPSPoint object

        Returns:
            dict with results: {
                'shares_created': int,
                'skipped_count': int,
                'error_count': int,
                'results': [
                    {
                        'friend_username': str,
                        'status': 'success' | 'skipped' | 'error',
                        'reason': str (if skipped or error),
                        'share_id': str (if success),
                        'permission_level': str (if success)
                    }
                ]
            }
        """
        results = []
        shares_created = 0
        skipped_count = 0
        error_count = 0

        # Get all active rules for the point owner
        active_rules = (
            AutoShareRule.objects.filter(user=point.owner, is_active=True)
            .select_related("friend")
            .prefetch_related("point_types", "tags")
        )

        if not active_rules:
            return {
                "shares_created": 0,
                "skipped_count": 0,
                "error_count": 0,
                "results": [],
            }

        # Group rules by friend and find highest permission for each
        friend_rules = {}  # friend_id -> (friend, highest_permission, matching_rules)

        for rule in active_rules:
            # Check if rule matches the point
            if not rule.matches_point(point):
                continue

            friend = rule.friend
            friend_id = friend.id

            # Get permission hierarchy value
            hierarchy = {"view": 0, "edit": 1, "manage": 2}
            current_permission = rule.permission_level
            current_level = hierarchy.get(current_permission, 0)

            # Track highest permission for this friend
            if friend_id not in friend_rules:
                friend_rules[friend_id] = (friend, current_permission, [rule])
            else:
                existing_friend, existing_permission, existing_rules = friend_rules[friend_id]
                existing_level = hierarchy.get(existing_permission, 0)

                if current_level > existing_level:
                    friend_rules[friend_id] = (friend, current_permission, [rule])
                elif current_level == existing_level:
                    # Same permission level, just track the rule
                    existing_rules.append(rule)
                    friend_rules[friend_id] = (existing_friend, existing_permission, existing_rules)

        # Create shares for each friend
        for friend, permission_level, _matching_rules in friend_rules.values():
            # Check if friendship still exists
            if not FriendshipService.are_friends(point.owner, friend):
                results.append(
                    {
                        "friend_username": friend.username,
                        "status": "skipped",
                        "reason": "Friendship no longer exists",
                    }
                )
                skipped_count += 1
                continue

            # Check if already manually shared
            existing_share = Share.objects.filter(gps_point=point, recipient_user=friend).first()

            if existing_share:
                results.append(
                    {
                        "friend_username": friend.username,
                        "status": "skipped",
                        "reason": "Already shared manually",
                    }
                )
                skipped_count += 1
                continue

            # Create auto-share
            try:
                share = Share.objects.create(
                    gps_point=point,
                    owner=point.owner,
                    recipient_email=friend.email,
                    recipient_user=friend,
                    permission_level=permission_level,
                    accepted_at=timezone.now(),  # Auto-accept for friends
                )

                results.append(
                    {
                        "friend_username": friend.username,
                        "status": "success",
                        "share_id": str(share.id),
                        "permission_level": permission_level,
                    }
                )
                shares_created += 1

                # TODO: Send notification to friend about auto-shared point

            except Exception as e:
                results.append(
                    {
                        "friend_username": friend.username,
                        "status": "error",
                        "reason": str(e),
                    }
                )
                error_count += 1

        return {
            "shares_created": shares_created,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "results": results,
        }

    @staticmethod
    def get_matching_rules_for_point(point: GPSPoint) -> list[AutoShareRule]:
        """
        Get all active rules that would match a given point.

        Useful for previewing which friends will receive a point.

        Args:
            point: GPSPoint object

        Returns:
            List of matching AutoShareRule objects
        """
        # Get all active rules for the point owner
        active_rules = (
            AutoShareRule.objects.filter(user=point.owner, is_active=True)
            .select_related("friend")
            .prefetch_related("point_types", "tags")
        )

        matching_rules = []
        for rule in active_rules:
            if rule.matches_point(point):
                matching_rules.append(rule)

        return matching_rules
