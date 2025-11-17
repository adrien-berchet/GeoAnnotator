"""
Authentication and account management services.

Handles JWT token generation, validation, user authentication logic,
username validation, email changes, and account management.
"""

import hashlib
import hmac
import re

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.sharing.models import Share

from .models import AccountLog
from .models import EmailConfirmation
from .models import User

# Username validation regex: alphanumeric and simple special characters, no spaces
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$')


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
        try:
            # Find user by email_hash (since email is encrypted)
            email_hash = User.hash_email(email)
            user = User.objects.get(email_hash=email_hash)

            # Authenticate with username and password
            authenticated_user = authenticate(username=user.username, password=password)

            if (
                authenticated_user
                and isinstance(authenticated_user, User)
                and authenticated_user.is_active
            ):
                return authenticated_user
        except User.DoesNotExist:
            pass

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
            email_hash = User.hash_email(email)
            return User.objects.get(email_hash=email_hash)
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


class EmailConfirmationService:
    """Unified service for email confirmation flows (registration and email changes)."""

    @staticmethod
    def generate_confirmation_token(
        user: User, confirmation_type: str, new_email: str | None = None
    ) -> str:
        """
        Generate HMAC-based confirmation token for email verification.

        Args:
            user: User object
            confirmation_type: 'registration' or 'email_change'
            new_email: New email address (required for email_change type)

        Returns:
            str: HMAC-based token (128 characters)
        """

        # Generate token using HMAC with user ID, timestamp, and email
        timestamp = str(timezone.now().timestamp())
        email_to_use = new_email if new_email else user.email
        message = f"{user.id}:{email_to_use}:{timestamp}:{confirmation_type}"
        token = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Delete any existing pending confirmations for this user and type
        EmailConfirmation.objects.filter(
            user=user,
            confirmation_type=confirmation_type,
            confirmed_at__isnull=True,
        ).delete()

        # Create new confirmation record
        EmailConfirmation.objects.create(
            user=user,
            confirmation_type=confirmation_type,
            token=token,
            new_email=new_email,
        )

        return token

    @staticmethod
    def validate_confirmation_token(
        token: str,
    ) -> tuple[bool, str | None, EmailConfirmation | None]:
        """
        Validate email confirmation token.

        Args:
            token: Confirmation token string

        Returns:
            tuple: (is_valid, error_message, confirmation)
                - is_valid: True if token is valid
                - error_message: Error message if invalid, None otherwise
                - confirmation: EmailConfirmation object if valid, None otherwise
        """
        try:
            confirmation = EmailConfirmation.objects.get(token=token)

            # Check if already confirmed
            if confirmation.is_confirmed:
                return False, "This confirmation link has already been used.", None

            # Check if expired
            if confirmation.is_expired:
                return False, "This confirmation link has expired. Please request a new one.", None

            # Valid token
            return True, None, confirmation

        except EmailConfirmation.DoesNotExist:
            return False, "Invalid confirmation link.", None

    @staticmethod
    def confirm_email(token: str) -> tuple[bool, str | None]:
        """
        Confirm user email with token (handles both registration and email change).

        Args:
            token: Confirmation token string

        Returns:
            tuple: (success, error_message)
        """
        is_valid, error_message, confirmation = (
            EmailConfirmationService.validate_confirmation_token(token)
        )

        if not is_valid:
            return False, error_message

        user = confirmation.user

        # Handle based on confirmation type
        if confirmation.confirmation_type == EmailConfirmation.REGISTRATION:
            # Mark user as verified
            user.is_verified = True
            user.save(update_fields=["is_verified"])

            # Log the confirmation
            AccountLog.objects.create(
                user=user,
                operation="EMAIL_CONFIRMED",
                details={"email": str(user.email)},
            )

        elif confirmation.confirmation_type == EmailConfirmation.EMAIL_CHANGE:
            # Update user email
            old_email = str(user.email)
            user.email = confirmation.new_email
            user.save(update_fields=["email"])

            # Log the email change
            AccountLog.objects.create(
                user=user,
                operation="EMAIL_CHANGE_CONFIRMED",
                details={"old_email": old_email, "new_email": str(confirmation.new_email)},
            )

        # Mark confirmation as completed
        confirmation.confirmed_at = timezone.now()
        confirmation.save(update_fields=["confirmed_at"])

        return True, None

    @staticmethod
    def send_confirmation_email(
        user: User, token: str, confirmation_type: str, new_email: str | None = None
    ) -> None:
        """
        Send confirmation email to user with token link.

        Args:
            user: User object
            token: Confirmation token
            confirmation_type: 'registration' or 'email_change'
            new_email: New email address (for email_change type)
        """
        # Get frontend URL from settings
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

        # Select templates and subject based on confirmation type
        if confirmation_type == EmailConfirmation.REGISTRATION:
            confirmation_link = f"{frontend_url}/confirm-email?token={token}"
            html_template = "emails/confirm_registration.html"
            text_template = "emails/confirm_registration.txt"
            subject = "Confirmez votre adresse email - GeoAnnotator"
            recipient = user.email
            context = {
                "user": user,
                "confirmation_link": confirmation_link,
            }
        else:  # EMAIL_CHANGE
            confirmation_link = f"{frontend_url}/account/confirm-email?token={token}"
            html_template = "emails/confirm_email_change.html"
            text_template = "emails/confirm_email_change.txt"
            subject = "Confirm Email Address Change"
            recipient = new_email
            context = {
                "username": user.username,
                "new_email": new_email,
                "confirmation_link": confirmation_link,
            }

        # Render email templates
        html_message = render_to_string(html_template, context)
        text_message = render_to_string(text_template, context)

        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
        )

    @staticmethod
    def resend_confirmation_email(email: str) -> tuple[bool, str | None]:
        """
        Resend registration confirmation email to user.

        Args:
            email: User email address

        Returns:
            tuple: (success, error_message)
        """
        try:
            # Find user by email
            email_hash = User.hash_email(email)
            user = User.objects.get(email_hash=email_hash)

            # Check if already verified
            if user.is_verified:
                return False, "This email address is already verified."

            # Generate new token
            token = EmailConfirmationService.generate_confirmation_token(
                user, EmailConfirmation.REGISTRATION
            )

            # Send email
            EmailConfirmationService.send_confirmation_email(
                user, token, EmailConfirmation.REGISTRATION
            )

            # Log the resend
            AccountLog.objects.create(
                user=user,
                operation="CONFIRMATION_EMAIL_RESENT",
                details={"email": str(user.email)},
            )

            return True, None

        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return (
                False,
                "If this email is registered and unverified, a confirmation email will be sent.",
            )


# Account Management Services


def _check_username_length(username: str) -> tuple[bool, str | None]:
    """
    Check if username length is valid (3-100 characters).

    Args:
        username: The username to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if len(username) > 100:
        return False, "Username must be at most 100 characters long."

    return True, None


def _check_username_start(username: str) -> tuple[bool, str | None]:
    """
    Check if username starts with alphanumeric character.

    Args:
        username: The username to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty."

    if not username[0].isalnum():
        return False, "Username must start with a letter or number."

    return True, None


def _check_username_characters(username: str) -> tuple[bool, str | None]:
    """
    Check if username contains only allowed characters.

    Allowed: letters, numbers, underscores, hyphens.
    NO SPACES allowed per spec.md line 46.

    Args:
        username: The username to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Pattern: alphanumeric, underscore, hyphen (NO spaces)
    # Must start with alphanumeric (checked separately)
    pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*$")

    if not pattern.match(username):
        # Check if space is the issue
        if " " in username:
            return False, "Username cannot contain spaces."
        return False, "Username can only contain letters, numbers, underscores, and hyphens."

    return True, None


def _check_username_spaces(username: str) -> tuple[bool, str | None]:
    """
    Check username doesn't contain any spaces.
    This check is now redundant with _check_username_characters but kept for clarity.

    Args:
        username: The username to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    # NO spaces allowed per spec
    if " " in username:
        return False, "Username cannot contain spaces."

    return True, None


def _check_username_uniqueness(username: str, exclude_user_id=None) -> tuple[bool, str | None]:
    """
    Check if username is unique (case-insensitive).

    Args:
        username: The username to check
        exclude_user_id: Optional user ID to exclude from uniqueness check

    Returns:
        Tuple of (is_available, error_message)
    """
    # Check uniqueness (case-insensitive)
    query = User.objects.filter(username__iexact=username)
    if exclude_user_id:
        query = query.exclude(id=exclude_user_id)

    is_available = not query.exists()

    if not is_available:
        return False, "This username is already taken."

    return True, None


def validate_username(username: str, exclude_user_id=None) -> dict:
    """
    Validate username against all rules.

    Rules:
    - Length: 3-100 characters
    - Must start with alphanumeric character
    - Allowed characters: letters, numbers, underscores, hyphens
    - No spaces allowed
    - Case-insensitive uniqueness across all users

    Args:
        username: The username to validate
        exclude_user_id: Optional user ID to exclude from uniqueness check (for updates)

    Returns:
        dict with keys:
            - valid (bool): Whether username is valid
            - available (bool): Whether username is available (unique)
            - errors (list[str]): List of error messages (empty if valid)
    """
    errors = []

    # Run all validation checks
    checks = [
        _check_username_length,
        _check_username_start,
        _check_username_characters,
        _check_username_spaces,
    ]

    for check in checks:
        is_valid, error_msg = check(username)
        if not is_valid:
            errors.append(error_msg)

    # If format invalid, don't check uniqueness
    if errors:
        return {
            "valid": False,
            "available": None,  # Not checked when format is invalid
            "errors": errors,
        }

    # Check uniqueness only if format is valid
    is_available, error_msg = _check_username_uniqueness(username, exclude_user_id)
    if not is_available:
        return {"valid": True, "available": False, "errors": [error_msg]}

    return {"valid": True, "available": True, "errors": []}


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
        message = f"{user.id}:delete:{timestamp}".encode()
        token = hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()
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
            token_hash, timestamp_str = token.rsplit(":", 1)
            timestamp = int(timestamp_str)

            # Check if token has expired (7 days for account deletion)
            token_age = timezone.now().timestamp() - timestamp
            if token_age > 7 * 24 * 60 * 60:  # 7 days
                return False

            # Regenerate token and compare
            message = f"{user.id}:delete:{timestamp}".encode()
            expected_hash = hmac.new(
                settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(token_hash, expected_hash)

        except (ValueError, AttributeError):
            return False


def send_deletion_confirmation(user, token: str):
    """
    Send account deletion confirmation email.

    Args:
        user: User object
        token: Confirmation token
    """
    # Build confirmation link
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    confirmation_link = f"{frontend_url}/account/confirm-delete?token={token}&user_id={user.id}"

    # Render HTML and plain text versions
    html_message = render_to_string(
        "emails/confirm_account_deletion.html",
        {
            "username": user.username or str(user.email),
            "confirmation_link": confirmation_link,
        },
    )
    plain_message = render_to_string(
        "emails/confirm_account_deletion.txt",
        {
            "username": user.username or str(user.email),
            "confirmation_link": confirmation_link,
        },
    )

    send_mail(
        subject="⚠️ Confirm Account Deletion",
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
    user.save(update_fields=["deleted_at"])

    # Unshare all user's content
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
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        # Get user agent
        user_agent = request.headers.get("user-agent", "")[:256]

    AccountLog.objects.create(
        user=user,
        operation=operation,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )
