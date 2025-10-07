"""
GPS Point and Tag models for GeoAnnotator.

Handles geographic locations with metadata and categorization via tags.
"""

import uuid
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone
from datetime import timedelta


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
