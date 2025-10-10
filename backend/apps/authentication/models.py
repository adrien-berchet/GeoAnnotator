"""
User model extension for GeoAnnotator.

Extends Django's built-in User model with storage quota tracking.
"""

import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinValueValidator


class UserManager(BaseUserManager):
    """Custom manager for User model with email as username."""

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with email and password.

        Args:
            email: User's email address (used as username)
            password: User's password
            **extra_fields: Additional fields

        Returns:
            User object
        """
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=email,  # Set both email and username
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with email and password.

        Args:
            email: Superuser's email address
            password: Superuser's password
            **extra_fields: Additional fields

        Returns:
            User object with superuser privileges
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Extended User model with storage quota tracking.

    Additional fields:
    - id: UUID primary key (instead of auto-incrementing integer)
    - email: Required unique email (used for login, not username)
    - storage_used: Bytes used by user's annotations (files)
    - storage_limit: Maximum bytes allowed (default 2GB)
    """

    # Override id to use UUID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique user identifier"
    )

    # Email is the primary identifier (not username)
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="User email address (used for login)"
    )

    # Username not used for login, but required by AbstractUser
    # Set it to email automatically
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Auto-generated from email"
    )

    # Storage quota fields
    storage_used = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Bytes used by user's annotation files"
    )

    storage_limit = models.BigIntegerField(
        default=2 * 1024 * 1024 * 1024,  # 2GB default
        validators=[MinValueValidator(0)],
        help_text="Maximum bytes allowed (default 2GB)"
    )

    # Use email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields for createsuperuser

    # Use custom manager
    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['is_active'], name='idx_user_active'),
        ]
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        """Override save to auto-generate username from email."""
        if not self.username:
            # Use email as username (required by AbstractUser)
            self.username = self.email
        super().save(*args, **kwargs)

    @property
    def storage_percentage(self):
        """Calculate storage usage percentage."""
        if self.storage_limit == 0:
            return 100.0
        return (self.storage_used / self.storage_limit) * 100

    def has_storage_quota(self, file_size):
        """Check if user has enough storage quota for a file."""
        return (self.storage_used + file_size) <= self.storage_limit

    def add_storage_usage(self, file_size):
        """Increment storage usage (call after successful file upload)."""
        self.storage_used += file_size
        self.save(update_fields=['storage_used'])

    def remove_storage_usage(self, file_size):
        """Decrement storage usage (call after file deletion)."""
        self.storage_used = max(0, self.storage_used - file_size)
        self.save(update_fields=['storage_used'])

    def __str__(self):
        return self.email
