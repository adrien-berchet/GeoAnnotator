"""
User model extension for GeoAnnotator.

Extends Django's built-in User model with storage quota tracking, usernames,
email encryption, and account management features.
"""

import hashlib
import random
import uuid
from datetime import timedelta

import fernet_fields
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ActiveUserManager(BaseUserManager["User"]):
    """Manager that returns only active (non-deleted) users."""

    def get_queryset(self):
        """Return queryset filtered to only active users (deleted_at IS NULL)."""
        return super().get_queryset().filter(deleted_at__isnull=True)


class UserManager(BaseUserManager["User"]):
    """Custom manager for User model with username."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Create and return a regular user with username and optional email.

        Args:
            username: User's username (used for login)
            email: User's email address (optional, encrypted at rest)
            password: User's password
            **extra_fields: Additional fields

        Returns:
            User object
        """
        if not username:
            raise ValueError("Username is required")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.generate_verification_code()  # Generate verification code
        user.save(using=self._db)

        # Send verification email
        self.send_verification_email(user)

        return user

    def send_verification_email(self, user):
        """
        Send an email with the verification code to the user.

        Args:
            user: User object to send the verification email to
        """
        from django.core.mail import send_mail

        send_mail(
            subject="Votre code de vérification",
            message=f"Votre code de vérification est : {user.verification_code}",
            from_email="noreply@geoannotator.com",
            recipient_list=[user.email],
        )

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Create and return a superuser with username and password.

        Args:
            username: Superuser's username
            email: Superuser's email address (optional)
            password: Superuser's password
            **extra_fields: Additional fields

        Returns:
            User object with superuser privileges
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Extended User model with storage quota tracking.

    Additional fields:
    - id: UUID primary key (instead of auto-incrementing integer)
    - email: Required unique email (used for login, not username)
    - storage_used: Bytes used by user's annotations (files)
    - storage_limit: Maximum bytes allowed (default 2GB)
    - is_verified: Whether the user's email is verified
    - verification_code: Code used for email verification
    """

    # Override id to use UUID
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique user identifier"
    )

    # Username is the login username (unique, required)
    username = models.CharField(
        max_length=100, unique=True, db_index=True, help_text="User's username (used for login)"
    )

    # Email hash for uniqueness check (SHA-256 of lowercase email)
    email_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
        help_text="SHA-256 hash of lowercase email for uniqueness enforcement",
    )

    # Email encrypted at rest (required for account recovery and notifications)
    email = fernet_fields.EncryptedEmailField(
        max_length=255,
        help_text="User email address (encrypted at rest, required for account recovery)",
    )

    # Storage quota fields
    storage_used = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Bytes used by user's annotation files",
    )

    storage_limit = models.BigIntegerField(
        default=2 * 1024 * 1024 * 1024,  # 2GB default
        validators=[MinValueValidator(0)],
        help_text="Maximum bytes allowed (default 2GB)",
    )

    # Account verification fields
    is_verified = models.BooleanField(
        default=False, help_text="Indicates whether the user's email is verified."
    )

    verification_code = models.CharField(
        max_length=6, blank=True, help_text="Code used for email verification."
    )

    # Soft delete timestamp (NULL for active users)
    deleted_at = models.DateTimeField(
        blank=True, null=True, help_text="Soft delete timestamp, NULL for active users"
    )

    # Pending email for email change flow
    pending_email = fernet_fields.EncryptedEmailField(
        blank=True,
        null=True,
        max_length=255,
        help_text="Temporary storage for unconfirmed email changes",
    )

    # Use username as the login field
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []  # No additional required fields for createsuperuser

    # Use custom managers
    objects = UserManager()  # Default manager (includes deleted users)
    active = ActiveUserManager()  # Manager for active users only

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["username"], name="idx_user_username"),
            models.Index(fields=["email_hash"], name="idx_user_email_hash"),
            models.Index(fields=["is_active"], name="idx_user_active"),
        ]
        ordering = ["-date_joined"]

    @staticmethod
    def hash_email(email: str) -> str:
        """
        Generate SHA-256 hash of lowercase email with salt for uniqueness.

        Uses HMAC with a secret salt to prevent rainbow table attacks.
        Even if the database is compromised, attackers cannot reverse the hash
        without knowing the SECRET_KEY.
        """
        import hmac

        from django.conf import settings

        # Use Django's SECRET_KEY as salt (already in environment)
        # This makes rainbow tables useless without the secret
        normalized_email = email.lower().strip()
        salt = settings.SECRET_KEY.encode()

        # HMAC-SHA256 (more secure than plain SHA-256)
        return hmac.new(salt, normalized_email.encode(), hashlib.sha256).hexdigest()

    def save(self, *args, **kwargs):
        """Override save to auto-generate email_hash from email."""
        if not self.username:
            raise ValueError("Username is required")

        # Generate email_hash from email for uniqueness check
        if self.email:
            email_str = str(self.email)
            self.email_hash = self.hash_email(email_str)

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
        self.save(update_fields=["storage_used"])

    def remove_storage_usage(self, file_size):
        """Decrement storage usage (call after file deletion)."""
        self.storage_used = max(0, self.storage_used - file_size)
        self.save(update_fields=["storage_used"])

    def generate_verification_code(self):
        """Generate a random 6-digit verification code."""
        self.verification_code = f"{random.randint(100000, 999999)}"
        self.save()

    def __str__(self):
        # Return username
        return self.username


class EmailChangeConfirmation(models.Model):
    """
    Temporary token storage for email change confirmation flow.

    Stores email change requests until confirmed via token link.
    Tokens expire after 30 minutes.
    """

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="email_change_confirmations",
        help_text="User requesting email change",
    )

    new_email = fernet_fields.EncryptedEmailField(
        max_length=255, help_text="Requested new email address (encrypted)"
    )

    new_email_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of new email for uniqueness check before confirmation",
    )

    token = models.CharField(max_length=128, unique=True, help_text="HMAC-based confirmation token")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Token creation timestamp")

    expires_at = models.DateTimeField(
        help_text="Token expiration timestamp (created_at + 30 minutes)"
    )

    confirmed_at = models.DateTimeField(
        blank=True, null=True, help_text="Timestamp when confirmed, NULL if pending"
    )

    class Meta:
        db_table = "email_change_confirmations"
        verbose_name = "Email Change Confirmation"
        verbose_name_plural = "Email Change Confirmations"
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_confirmed(self):
        """Check if email change has been confirmed."""
        return self.confirmed_at is not None

    def save(self, *args, **kwargs):
        """Set expires_at and new_email_hash if not already set."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)

        # Generate hash for new email
        if self.new_email:
            from apps.authentication.models import User

            self.new_email_hash = User.hash_email(str(self.new_email))

        super().save(*args, **kwargs)

    def __str__(self):
        status = "✓" if self.confirmed_at else ("⏰" if not self.is_expired else "❌")
        return f"{status} {self.user} → {self.new_email}"


class AccountLog(models.Model):
    """
    Audit trail for sensitive account operations.

    Logs all account changes for security and debugging purposes.
    """

    # Operation type choices
    OPERATION_CHOICES = [
        ("USERNAME_CHANGED", "Username Changed"),
        ("EMAIL_CHANGED", "Email Changed"),
        ("PASSWORD_CHANGED", "Password Changed"),
        ("ACCOUNT_DELETED", "Account Deleted"),
        ("EMAIL_CHANGE_REQUESTED", "Email Change Requested"),
        ("EMAIL_CHANGE_CONFIRMED", "Email Change Confirmed"),
    ]

    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="account_logs",
        null=True,
        help_text="User whose account was modified",
    )

    operation = models.CharField(
        max_length=50, choices=OPERATION_CHOICES, help_text="Type of account operation"
    )

    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="Client IP address")

    user_agent = models.CharField(
        max_length=256, blank=True, null=True, help_text="Client user agent"
    )

    timestamp = models.DateTimeField(auto_now_add=True, help_text="When operation occurred")

    details = models.JSONField(
        blank=True, null=True, help_text="Additional operation-specific data"
    )

    class Meta:
        db_table = "account_logs"
        verbose_name = "Account Log"
        verbose_name_plural = "Account Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_operation_display()} - {self.user} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
