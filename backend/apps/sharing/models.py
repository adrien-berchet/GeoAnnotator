"""
Share model for GeoAnnotator.

Handles sharing GPS points with other users via email invitations.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveShareManager(models.Manager):
    """Manager that returns only active shares (is_active=True)."""

    def get_queryset(self):
        """Return queryset filtered to only active shares."""
        return super().get_queryset().filter(is_active=True)


class Friendship(models.Model):
    """
    Friendship relationship between two users.

    Friendships are bidirectional - if User A is friends with User B,
    then User B is automatically friends with User A.

    Friendships are used to:
    1. Show a list of users you've shared points with
    2. Enable quick sharing with known users
    3. View shared points organized by friend

    When a friendship is removed, all shares in both directions are revoked.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique friendship identifier"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_initiated",
        help_text="User who initiated or maintains this friendship record",
    )

    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_received",
        help_text="The friend user",
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Friendship creation timestamp")

    class Meta:
        db_table = "friendships"
        verbose_name = "Friendship"
        verbose_name_plural = "Friendships"
        constraints = [
            # Prevent duplicate friendships
            models.UniqueConstraint(
                fields=["user", "friend"], name="unique_friendship"
            ),
            # Prevent self-friendship
            models.CheckConstraint(
                check=~models.Q(user=models.F("friend")),
                name="no_self_friendship"
            ),
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_friendship_user"),
            models.Index(fields=["friend"], name="idx_friendship_friend"),
            models.Index(fields=["user", "friend"], name="idx_friendship_pair"),
        ]
        ordering = ["-created_at"]

    def clean(self):
        """Validate friendship constraints."""
        from django.core.exceptions import ValidationError

        # Prevent self-friendship
        if self.user == self.friend:
            raise ValidationError("Cannot be friends with yourself")

        # Check for reverse friendship to maintain bidirectional consistency
        if self.pk is None:  # Only on creation
            reverse_exists = Friendship.objects.filter(
                user=self.friend, friend=self.user
            ).exists()
            if reverse_exists:
                raise ValidationError(
                    "Friendship already exists in the reverse direction"
                )

    def __str__(self):
        return f"{self.user.username} ↔ {self.friend.username}"


class Share(models.Model):
    """
    Sharing relationship between a point owner and a recipient.

    Permission levels:
    - view: Can view point and annotations
    - edit: Can view + edit point and annotations
    - manage: Can view + edit + share with others and manage existing shares

    Invitation flow:
    1. Owner creates share → invitation_token generated, email sent
    2. Recipient clicks link → invitation accepted, recipient_user set
    3. Point deleted → is_active set to false
    4. Point restored → is_active restored (if not revoked)
    """

    # Permission level choices
    PERMISSION_VIEW = "view"
    PERMISSION_EDIT = "edit"
    PERMISSION_MANAGE = "manage"

    PERMISSION_CHOICES = [
        (PERMISSION_VIEW, "View"),
        (PERMISSION_EDIT, "Edit"),
        (PERMISSION_MANAGE, "Manage"),
    ]

    # Invitation status
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"

    # Token expiry: 7 days
    INVITATION_EXPIRY_DAYS = 7

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique share identifier"
    )

    gps_point = models.ForeignKey(
        "points.GPSPoint",
        on_delete=models.CASCADE,
        related_name="shares",
        help_text="Shared GPS point",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shares_sent",
        help_text="Point owner (who created the share)",
    )

    recipient_email = models.EmailField(
        db_index=True, help_text="Recipient email (may not be registered yet)"
    )

    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shares_received",
        help_text="Recipient user (set when invitation accepted)",
    )

    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_VIEW,
        db_index=True,
        help_text="Permission level (view/edit/manage)",
    )

    invitation_token = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, help_text="Token for email invitation link"
    )

    invitation_sent_at = models.DateTimeField(
        auto_now_add=True, help_text="Invitation email sent timestamp"
    )

    accepted_at = models.DateTimeField(
        null=True, blank=True, help_text="Invitation acceptance timestamp"
    )

    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Share is active (false when point trashed)"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Share creation timestamp")

    # Managers
    objects = models.Manager()  # Default manager (includes inactive shares)
    active = ActiveShareManager()  # Manager for active shares only

    class Meta:
        db_table = "shares"
        verbose_name = "Share"
        verbose_name_plural = "Shares"
        constraints = [
            # No duplicate shares to the same email for a point
            models.UniqueConstraint(
                fields=["gps_point", "recipient_email"], name="unique_share_per_point_email"
            )
        ]
        indexes = [
            models.Index(fields=["gps_point"], name="idx_share_point"),
            models.Index(fields=["recipient_email"], name="idx_share_recipient_email"),
            models.Index(fields=["recipient_user"], name="idx_share_recipient_user"),
            models.Index(fields=["invitation_token"], name="idx_share_token"),
            models.Index(fields=["is_active"], name="idx_share_active"),
        ]
        ordering = ["-created_at"]

    @property
    def invitation_status(self):
        """Get invitation status (pending or accepted)."""
        return self.STATUS_ACCEPTED if self.accepted_at else self.STATUS_PENDING

    @property
    def is_invitation_expired(self):
        """Check if invitation token has expired (7 days)."""
        if self.accepted_at:
            return False  # Already accepted

        expiry_date = self.invitation_sent_at + timedelta(days=self.INVITATION_EXPIRY_DAYS)
        return timezone.now() > expiry_date

    @property
    def invitation_expires_at(self):
        """Calculate invitation expiry timestamp."""
        return self.invitation_sent_at + timedelta(days=self.INVITATION_EXPIRY_DAYS)

    def accept(self, user):
        """
        Accept the invitation.

        Args:
            user: The user accepting the invitation

        Returns:
            bool: True if accepted, False if already accepted or expired
        """
        if self.accepted_at:
            return False  # Already accepted

        if self.is_invitation_expired:
            return False  # Expired

        self.accepted_at = timezone.now()
        self.recipient_user = user
        self.save(update_fields=["accepted_at", "recipient_user"])
        return True

    def deactivate(self):
        """Deactivate share (when point is trashed)."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def reactivate(self):
        """Reactivate share (when point is restored from trash)."""
        self.is_active = True
        self.save(update_fields=["is_active"])

    def has_permission(self, permission_level):
        """
        Check if this share has at least the specified permission level.

        Permission hierarchy: view < edit < transfer
        """
        levels = {
            self.PERMISSION_VIEW: 1,
            self.PERMISSION_EDIT: 2,
            self.PERMISSION_TRANSFER: 3,
        }
        return levels.get(self.permission_level, 0) >= levels.get(permission_level, 0)

    def clean(self):
        """Validate share constraints."""
        from django.core.exceptions import ValidationError

        # If accepted, recipient_user must be set
        if self.accepted_at and not self.recipient_user:
            raise ValidationError("Accepted shares must have recipient_user set")

        # Owner cannot share with themselves
        if self.owner.email == self.recipient_email:
            raise ValidationError("Cannot share with yourself")

    def __str__(self):
        status = "✓" if self.accepted_at else "⏳"
        return f"{status} {self.gps_point.title} → {self.recipient_email} ({self.permission_level})"
