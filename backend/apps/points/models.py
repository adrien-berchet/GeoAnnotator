"""
GPS Point and Tag models for GeoAnnotator.

Handles geographic locations with metadata and categorization via tags.
"""

import uuid
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import timedelta


class PointType(models.Model):
    """
    Point type for categorizing GPS points with custom icons.

    Types can be user-specific or base types (user=None for system defaults).
    Each user can create up to 1000 types with unique names.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique point type identifier"
    )

    name = models.CharField(
        max_length=100,
        help_text="Type name (must be unique per user)"
    )

    icon = models.CharField(
        max_length=500,
        default='📍',
        help_text="Icon URL, emoji, or asset reference"
    )

    order = models.IntegerField(
        default=0,
        help_text="Display order (lower values first)"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='point_types',
        help_text="Type owner (null for base/system types)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Type status (active or soft-deleted)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Creation timestamp"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp"
    )

    class Meta:
        db_table = 'point_types'
        verbose_name = 'Point Type'
        verbose_name_plural = 'Point Types'
        constraints = [
            # Unique name per user (case-insensitive)
            models.UniqueConstraint(
                models.functions.Lower('name'),
                'user',
                name='unique_pointtype_name_per_user',
                violation_error_message="Type name must be unique per user"
            )
        ]
        indexes = [
            models.Index(fields=['user', 'order'], name='idx_pointtype_user_order'),
            models.Index(fields=['user', 'status'], name='idx_pointtype_user_status'),
        ]
        ordering = ['order', 'name']

    def clean(self):
        """Validate type constraints."""
        super().clean()

        # Validate max 1000 types per user
        if self.user and not self.pk:  # Only check on creation
            active_types_count = PointType.objects.filter(
                user=self.user,
                status='active'
            ).count()

            if active_types_count >= 1000:
                raise ValidationError({
                    'user': 'You have reached the maximum of 1000 point types. '
                           'Please delete some types before creating new ones.'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return f"{self.name} ({self.user.email})"
        return f"{self.name} (Base Type)"


class UserTypeOrder(models.Model):
    """
    User-specific ordering for point types.

    Allows each user to customize the display order of ALL types
    (including base types) in their dropdowns and lists.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='type_orders',
        help_text="User who customized the order"
    )

    type = models.ForeignKey(
        PointType,
        on_delete=models.CASCADE,
        related_name='user_orders',
        help_text="The point type being ordered"
    )

    order = models.IntegerField(
        default=0,
        help_text="Display order for this user (lower values first)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_type_orders'
        verbose_name = 'User Type Order'
        verbose_name_plural = 'User Type Orders'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'type'],
                name='unique_user_type_order',
                violation_error_message="Each user can only have one order value per type"
            )
        ]
        indexes = [
            models.Index(fields=['user', 'order'], name='idx_userorder_user_order'),
        ]
        ordering = ['order']

    def __str__(self):
        return f"{self.user.email}: {self.type.name} (order={self.order})"


class Tag(models.Model):
    """
    Tag for categorizing GPS points.

    Tags are shared globally (case-insensitive unique).
    Examples: "forest", "hiking", "restaurant"
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique tag identifier"
    )

    name = models.CharField(
        max_length=50,
        help_text="Tag name (alphanumeric, hyphens, underscores only)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Tag creation timestamp"
    )

    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        # Case-insensitive unique constraint on name
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('name'),
                name='unique_tag_name_case_insensitive'
            )
        ]
        indexes = [
            models.Index(fields=['name'], name='idx_tag_name'),
        ]
        ordering = ['name']

    def __str__(self):
        return self.name


class GPSPoint(models.Model):
    """
    Geographic location with metadata, annotations, and sharing capabilities.

    Core entity representing a GPS point with:
    - Location (PostGIS Point with WGS 84 coordinates)
    - Ownership and sharing
    - Editing locks (15-minute duration)
    - Tags for categorization
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique point identifier"
    )

    title = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Point title (required)"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Rich text HTML description with emoticons"
    )

    # PostGIS Point field (SRID 4326 = WGS 84)
    location = gis_models.PointField(
        srid=4326,
        geography=True,  # Use geography for accurate distance calculations
        help_text="Geographic coordinates (longitude, latitude)"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_points',
        help_text="Point owner"
    )

    type = models.ForeignKey(
        PointType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points',
        help_text="Point type (defaults to base 'Point' type)"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='points',
        help_text="Categorization tags"
    )

    is_public = models.BooleanField(
        default=False,
        help_text="Public visibility (accessible to all users)"
    )

    # Editing lock fields (15-minute automatic release)
    editing_lock_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_points',
        help_text="User currently editing (null if unlocked)"
    )

    editing_lock_acquired_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Lock acquisition timestamp"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Creation timestamp"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp"
    )

    class Meta:
        db_table = 'gps_points'
        verbose_name = 'GPS Point'
        verbose_name_plural = 'GPS Points'
        indexes = [
            # Spatial index (GIST) for bounding box queries
            # Created automatically by PostGIS for PointField
            models.Index(fields=['owner'], name='idx_point_owner'),
            models.Index(fields=['is_public'], name='idx_point_public'),
            models.Index(fields=['owner', '-created_at'], name='idx_point_owner_timeline'),
        ]
        ordering = ['-created_at']

    @property
    def latitude(self):
        """Extract latitude from location Point."""
        return self.location.y if self.location else None

    @property
    def longitude(self):
        """Extract longitude from location Point."""
        return self.location.x if self.location else None

    @property
    def is_locked(self):
        """Check if point is currently locked."""
        if not self.editing_lock_user or not self.editing_lock_acquired_at:
            return False

        # Auto-expire lock after 15 minutes
        lock_expiry = self.editing_lock_acquired_at + timedelta(minutes=15)
        return timezone.now() < lock_expiry

    @property
    def lock_expires_at(self):
        """Calculate lock expiration time."""
        if not self.editing_lock_acquired_at:
            return None
        return self.editing_lock_acquired_at + timedelta(minutes=15)

    def acquire_lock(self, user):
        """
        Acquire editing lock for a user.

        Returns:
            bool: True if lock acquired, False if already locked by another user
        """
        # Check if already locked by another user
        if self.is_locked and self.editing_lock_user != user:
            return False

        # Acquire or refresh lock
        self.editing_lock_user = user
        self.editing_lock_acquired_at = timezone.now()
        self.save(update_fields=['editing_lock_user', 'editing_lock_acquired_at'])
        return True

    def release_lock(self, user=None):
        """
        Release editing lock.

        Args:
            user: If provided, only release if locked by this user

        Returns:
            bool: True if lock released, False if locked by another user
        """
        if user and self.editing_lock_user != user:
            return False

        self.editing_lock_user = None
        self.editing_lock_acquired_at = None
        self.save(update_fields=['editing_lock_user', 'editing_lock_acquired_at'])
        return True

    def __str__(self):
        return f"{self.title} ({self.latitude}, {self.longitude})"
