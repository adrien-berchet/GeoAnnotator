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

from .models import Share


class PermissionService:
    """Service for checking and managing permissions."""

    PERMISSION_LEVELS = ["view", "edit", "transfer", "owner"]

    @staticmethod
    def get_user_permission(point: GPSPoint, user: User) -> str | None:
        """
        Get user's permission level for a point.

        Args:
            point: GPSPoint object
            user: User object

        Returns:
            str: 'owner', 'transfer', 'edit', 'view', or None
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
            required_level: 'view', 'edit', or 'transfer'

        Returns:
            bool: True if user has permission
        """
        user_level = PermissionService.get_user_permission(point, user)

        if user_level is None:
            return False

        # Permission hierarchy: owner > transfer > edit > view
        hierarchy = {
            "view": 0,
            "edit": 1,
            "transfer": 2,
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
        """Check if user can share point (requires transfer permission)."""
        return PermissionService.has_permission(point, user, "transfer")

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
            permission_level: 'view', 'edit', or 'transfer'
            owner: User creating share

        Returns:
            Share object

        Raises:
            ValueError: If validation fails
        """
        # Validate permission level
        if permission_level not in ["view", "edit", "transfer"]:
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
            recipient_user = User.objects.get(email=recipient_email)
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
        if permission_level not in ["view", "edit", "transfer"]:
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
