"""
GPS Point and Tag models for GeoAnnotator.

Handles geographic locations with metadata and categorization via tags.
"""

import uuid
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import functions
from django.utils import timezone
from datetime import timedelta


class PointType(models.Model):
    """
    Point type for categorizing GPS points with multilingual names.

    Types can be base (system defaults) or custom (user-created).
    Each type has multilingual names stored as a JSON object.
    Names follow fallback order: user language → English → creation language.
    """

    TYPE_CHOICES = [
        ('base', 'Base'),
        ('custom', 'Custom'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

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

    type_choice = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='custom',
        db_column='type',
        help_text="Type classification (base or custom)"
    )

    names = models.JSONField(
        default=dict,
        help_text="Multilingual names (map of language_code: name)"
    )

    creation_language = models.CharField(
        max_length=10,
        default='en',
        help_text="ISO 639-1 language code at creation"
    )

    icon = models.TextField(
        default='📍',
        help_text="Icon URL, emoji, data URI, or asset reference"
    )

    order = models.IntegerField(
        default=0,
        help_text="Display order (lower values first)"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='point_types',
        db_column='user',
        help_text="Type owner (null for base types)"
    )

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='private',
        help_text="Visibility (public or private)"
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
        indexes = [
            models.Index(fields=['owner', 'order'], name='idx_pointtype_owner_order'),
            models.Index(fields=['owner', 'status'], name='idx_pointtype_owner_status'),
            models.Index(fields=['type_choice'], name='idx_pointtype_type'),
        ]
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'names'],
                name='unique_pointtype_name_per_user'
            )
        ]

    def clean(self):
        """Validate type constraints."""
        super().clean()

        # Validate at least one name exists
        if not self.names or len(self.names) == 0:
            raise ValidationError({
                'names': 'At least one translation must be provided.'
            })

        # Validate creation_language exists in names (for new objects)
        if self._state.adding and self.creation_language not in self.names:
            raise ValidationError({
                'creation_language': f'Creation language "{self.creation_language}" '
                                   f'must have a corresponding name in the names field.'
            })

        # Validate base types have creation_language='en'
        if self.type_choice == 'base' and self.creation_language != 'en':
            raise ValidationError({
                'creation_language': 'Base types must have English as creation language.'
            })

        # Validate base types have owner=None
        if self.type_choice == 'base' and self.owner is not None:
            raise ValidationError({
                'owner': 'Base types cannot have an owner.'
            })

        # Validate custom types have owner
        if self.type_choice == 'custom' and self.owner is None:
            raise ValidationError({
                'owner': 'Custom types must have an owner.'
            })

        # Validate max types per user
        if self.owner and self._state.adding:  # Only check on creation (use _state.adding since pk has default value)
            active_types_count = PointType.objects.filter(
                owner=self.owner,
                status='active'
            ).count()

            if active_types_count >= settings.MAX_POINT_TYPES_PER_USER:
                raise ValidationError({
                    'owner': (
                        'You have reached the maximum of '
                        f'{settings.MAX_POINT_TYPES_PER_USER} custom point types. '
                        'Please delete some types before creating new ones.'
                    )
                })

    def save(self, *args, **kwargs):
        """Override save to handle type deletion logic."""
        if self.pk and self.status == 'deleted':
            # Get default type
            default_type = self.get_default_type()

            # Reassign points to default type
            GPSPoint.objects.filter(type=self).update(type=default_type)

        super().save(*args, **kwargs)

    @classmethod
    def get_default_type(cls):
        """Get or create the default base 'Point' type."""
        from django.db import IntegrityError

        # Try to find existing default type
        # Use filter().first() to avoid JSONField comparison issues with get()
        default_type = cls.objects.filter(
            owner__isnull=True,
            type_choice='base',
            creation_language='en'
        ).first()

        if not default_type:
            # Create default type
            try:
                default_type = cls.objects.create(
                    names={"en": "Point"},
                    owner=None,
                    type_choice="base",
                    icon="📍",
                    order=0,
                    creation_language="en",
                    visibility="public",
                )
            except IntegrityError:
                # If creation fails due to constraint (race condition), try fetching again
                default_type = cls.objects.filter(
                    owner__isnull=True,
                    type_choice='base',
                    creation_language='en'
                ).first()

                if not default_type:
                    # If still not found, raise the error
                    raise

        return default_type

    def get_name(self, language_code='en'):
        """
        Get name in specified language with fallback logic.

        Fallback order:
        1. Requested language
        2. English ('en')
        3. Creation language

        Args:
            language_code: ISO 639-1 language code (default: 'en')

        Returns:
            str: Name in best available language
        """
        # Try requested language
        if language_code in self.names:
            return self.names[language_code]

        # Fallback to English
        if 'en' in self.names:
            return self.names['en']

        # Fallback to creation language
        if self.creation_language in self.names:
            return self.names[self.creation_language]

        # Fallback to any available name (should never happen due to validation)
        if self.names:
            return next(iter(self.names.values()))

        return "Unnamed"

    def __str__(self):
        name = self.get_name('en')
        if self.owner:
            return f"{name} ({self.owner.email})"
        return f"{name} (Base Type)"


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
        return f"{self.user.email}: {self.type.get_name('en')} (order={self.order})"


class Tag(models.Model):
    """
    Tag for categorizing GPS points.

    Tags are unique per user (case-insensitive).
    Each user can only access tags they created.
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

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tags',
        help_text="Tag owner"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Tag creation timestamp"
    )

    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        # Case-insensitive unique constraint on name per user
        constraints = [
            models.UniqueConstraint(
                functions.Lower('name'),
                'owner',
                name='unique_tag_name_per_user'
            )
        ]
        indexes = [
            models.Index(fields=['name'], name='idx_tag_name'),
            models.Index(fields=['owner'], name='idx_tag_owner'),
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.owner.email})"


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
