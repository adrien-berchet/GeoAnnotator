"""
Authentication and account management services.

Handles JWT token generation, validation, user authentication logic,
pseudonym validation, email changes, and account management.
"""

import hashlib
import hmac
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailChangeConfirmation, AccountLog


# Pseudonym validation regex: alphanumeric and simple special characters, no spaces
PSEUDONYM_PATTERN = re.compile(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$')


class AuthenticationService:
    """Service for user authentication and JWT token management."""

    @staticmethod
    def authenticate_user(email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            email: User email address
            password: User password

        Returns:
            User object if authenticated, None otherwise
        """
        user = authenticate(username=email, password=password)

        if user and isinstance(user, User) and user.is_active:
            return user

        return None

    @staticmethod
    def generate_tokens(user: User) -> dict:
        """
        Generate JWT access and refresh tokens for user.

        Args:
            user: User object

        Returns:
            dict: {
                'access': str (1 hour validity),
                'refresh': str (7 days validity),
                'user': User object
            }
        """
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user,
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            str: New access token

        Raises:
            TokenError: If refresh token is invalid or expired
        """
        try:
            refresh = RefreshToken(token=refresh_token)
            return str(refresh.access_token)
        except TokenError as e:
            raise ValueError(f"Invalid or expired refresh token: {str(e)}") from None

    @staticmethod
    def validate_token(token: str) -> bool:
        """
        Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            RefreshToken(token)
            return True
        except TokenError:
            return False

    @staticmethod
    def get_user_from_token(token: str) -> User | None:
        """
        Extract user from JWT token.

        Args:
            token: JWT token string

        Returns:
            User object if token is valid, None otherwise
        """
        try:
            refresh = RefreshToken(token)
            user_id = refresh.get("user_id")
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None

    @staticmethod
    def create_user(email: str, password: str) -> User:
        """
        Create new user with hashed password and default storage quota.

        Args:
            email: User email address
            password: User password

        Returns:
            User object
        """
        # USERNAME_FIELD is 'email', so pass it as the first positional arg
        user = User.objects.create_user(
            email,  # USERNAME_FIELD
            password=password,
        )
        return user

    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User object if found, None otherwise
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def verify_user_code(user: User, code: str) -> bool:
        """
        Verify the user's verification code.

        Args:
            user: User object
            code: Verification code to validate

        Returns:
            bool: True if the code is valid, False otherwise
        """
        if user.verification_code == code:
            user.is_verified = True
            user.verification_code = ""  # Clear the code after verification
            user.save()
            return True
        return False


# Account Management Services


def validate_pseudonym(pseudonym: str, exclude_user_id=None) -> dict:
    """
    Validate pseudonym against rules.

    Rules:
    - Length: 1-99 characters
    - Pattern: alphanumeric and simple special characters only
    - No spaces allowed
    - Case-insensitive uniqueness across all users

    Args:
        pseudonym: The pseudonym to validate
        exclude_user_id: Optional user ID to exclude from uniqueness check (for updates)

    Returns:
        dict with keys:
            - valid (bool): Whether pseudonym is valid
            - available (bool): Whether pseudonym is available (unique)
            - error (str|None): Error message if invalid
    """
    # Check length
    if not pseudonym or len(pseudonym) == 0:
        return {
            "valid": False,
            "available": None,
            "error": "Pseudonym is required."
        }

    if len(pseudonym) >= 100:
        return {
            "valid": False,
            "available": None,
            "error": "Pseudonym must be less than 100 characters."
        }

    # Check for spaces
    if ' ' in pseudonym:
        return {
            "valid": False,
            "available": None,
            "error": "Pseudonym cannot contain spaces."
        }

    # Check pattern
    if not PSEUDONYM_PATTERN.match(pseudonym):
        return {
            "valid": False,
            "available": None,
            "error": "Pseudonym can only contain letters, numbers, and simple special characters."
        }

    # Check uniqueness (case-insensitive)
    query = User.objects.filter(pseudonym__iexact=pseudonym)
    if exclude_user_id:
        query = query.exclude(id=exclude_user_id)

    is_available = not query.exists()

    if not is_available:
        return {
            "valid": True,
            "available": False,
            "error": "This pseudonym is already taken. Please choose a different one."
        }

    return {
        "valid": True,
        "available": True,
        "error": None
    }


class EmailChangeTokenGenerator:
    """
    Generate and validate HMAC-based tokens for email change confirmation.

    Tokens are single-use and expire after 30 minutes.
    """

    @staticmethod
    def generate_token(user, new_email: str) -> str:
        """
        Generate a secure token for email change confirmation.

        Args:
            user: User object
            new_email: New email address

        Returns:
            str: HMAC token
        """
        timestamp = int(timezone.now().timestamp())
        message = f"{user.id}:{new_email}:{timestamp}".encode('utf-8')
        token = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{timestamp}"

    @staticmethod
    def validate_token(token: str, user, new_email: str) -> bool:
        """
        Validate an email change confirmation token.

        Args:
            token: Token string
            user: User object
            new_email: New email address

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            token_hash, timestamp_str = token.rsplit(':', 1)
            timestamp = int(timestamp_str)

            # Check if token has expired (30 minutes)
            token_age = timezone.now().timestamp() - timestamp
            if token_age > 30 * 60:  # 30 minutes
                return False

            # Regenerate token and compare
            message = f"{user.id}:{new_email}:{timestamp}".encode('utf-8')
            expected_hash = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                message,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(token_hash, expected_hash)

        except (ValueError, AttributeError):
            return False


class AccountDeletionTokenGenerator:
    """
    Generate and validate HMAC-based tokens for account deletion confirmation.

    Similar to email change tokens but for account deletion.
    """

    @staticmethod
    def generate_token(user) -> str:
        """
        Generate a secure token for account deletion confirmation.

        Args:
            user: User object

        Returns:
            str: HMAC token
        """
        timestamp = int(timezone.now().timestamp())
        message = f"{user.id}:delete:{timestamp}".encode('utf-8')
        token = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{timestamp}"

    @staticmethod
    def validate_token(token: str, user) -> bool:
        """
        Validate an account deletion confirmation token.

        Args:
            token: Token string
            user: User object

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            token_hash, timestamp_str = token.rsplit(':', 1)
            timestamp = int(timestamp_str)

            # Check if token has expired (7 days for account deletion)
            token_age = timezone.now().timestamp() - timestamp
            if token_age > 7 * 24 * 60 * 60:  # 7 days
                return False

            # Regenerate token and compare
            message = f"{user.id}:delete:{timestamp}".encode('utf-8')
            expected_hash = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                message,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(token_hash, expected_hash)

        except (ValueError, AttributeError):
            return False


def send_email_change_confirmation(user, new_email: str, token: str):
    """
    Send email change confirmation email.

    Args:
        user: User object
        new_email: New email address
        token: Confirmation token
    """
    # Build confirmation link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    confirmation_link = f"{frontend_url}/account/confirm-email?token={token}&user_id={user.id}"

    # Render HTML and plain text versions
    html_message = render_to_string('emails/confirm_email_change.html', {
        'pseudonym': user.pseudonym or str(user.email),
        'new_email': new_email,
        'confirmation_link': confirmation_link,
    })
    plain_message = render_to_string('emails/confirm_email_change.txt', {
        'pseudonym': user.pseudonym or str(user.email),
        'new_email': new_email,
        'confirmation_link': confirmation_link,
    })

    send_mail(
        subject='Confirm Email Address Change',
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
        fail_silently=False,
    )


def send_deletion_confirmation(user, token: str):
    """
    Send account deletion confirmation email.

    Args:
        user: User object
        token: Confirmation token
    """
    # Build confirmation link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    confirmation_link = f"{frontend_url}/account/confirm-delete?token={token}&user_id={user.id}"

    # Render HTML and plain text versions
    html_message = render_to_string('emails/confirm_account_deletion.html', {
        'pseudonym': user.pseudonym or str(user.email),
        'confirmation_link': confirmation_link,
    })
    plain_message = render_to_string('emails/confirm_account_deletion.txt', {
        'pseudonym': user.pseudonym or str(user.email),
        'confirmation_link': confirmation_link,
    })

    send_mail(
        subject='⚠️ Confirm Account Deletion',
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[str(user.email)],
        fail_silently=False,
    )


def soft_delete_user(user):
    """
    Soft delete a user account.

    Sets deleted_at timestamp and unshares all user's content.

    Args:
        user: User object to soft delete
    """
    # Set deleted_at timestamp
    user.deleted_at = timezone.now()
    user.save(update_fields=['deleted_at'])

    # Unshare all user's content
    from apps.sharing.models import Share
    Share.objects.filter(owner=user, is_active=True).update(is_active=False)


def log_account_operation(user, operation: str, request=None, details: dict = None):
    """
    Log an account operation to the audit trail.

    Args:
        user: User object
        operation: Operation type (one of AccountLog.OPERATION_CHOICES)
        request: Optional HTTP request object for IP/user agent
        details: Optional additional details dict
    """
    ip_address = None
    user_agent = None

    if request:
        # Get IP address from request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:256]

    AccountLog.objects.create(
        user=user,
        operation=operation,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )
