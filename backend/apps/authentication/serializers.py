"""
Serializers for authentication app.

Handles user registration, login, profile, token management, and account management.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .services import validate_username


class UserSerializer(serializers.ModelSerializer):
    """
    User profile serializer.

    Includes storage quota information (read-only).
    Matches OpenAPI schema: User
    """

    email = serializers.EmailField(read_only=True)
    storage_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "date_joined",
            "storage_used",
            "storage_limit",
            "storage_percentage",
        ]
        read_only_fields = [
            "id",
            "email",
            "date_joined",
            "storage_used",
            "storage_limit",
            "storage_percentage",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    User registration serializer.

    Validates password strength (min 8 chars, uppercase, lowercase, numbers).
    Matches OpenAPI schema: RegisterRequest
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
        min_length=8,
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        """
        Validate email is not already registered.
        """
        email_hash = User.hash_email(value)
        if User.objects.filter(email_hash=email_hash).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_password(self, value):
        """
        Validate password contains uppercase, lowercase, and numbers.
        """
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        return value

    def create(self, validated_data):
        """
        Create user with hashed password and default storage quota (2GB).
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    User login serializer.

    Validates email and password, authenticates user.
    Matches OpenAPI schema: LoginRequest
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """
        Validate credentials and authenticate user.
        Uses AuthenticationService for email-based authentication.
        """
        from apps.authentication.services import AuthenticationService

        email = attrs.get("email")
        password = attrs.get("password")

        user = AuthenticationService.authenticate_user(email, password)

        if not user:
            raise AuthenticationFailed("Invalid email or password", code="authentication_failed")

        # Check if email is verified
        if not user.is_verified:
            raise AuthenticationFailed(
                "Please verify your email before logging in. Check your inbox for the confirmation link.",
                code="email_not_verified",
            )

        attrs["user"] = user
        return attrs


class TokenSerializer(serializers.Serializer):
    """
    JWT token response serializer.

    Returns access token, refresh token, and user profile.
    Matches OpenAPI schema: TokenResponse
    """

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)

    @staticmethod
    def get_tokens_for_user(user):
        """
        Generate JWT tokens for authenticated user.

        Returns:
            dict: {access: str, refresh: str, user: User}
        """
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user,
        }


class RefreshTokenSerializer(serializers.Serializer):
    """
    Refresh token serializer.

    Accepts refresh token and returns new access token.
    Matches OpenAPI schema: RefreshRequest
    """

    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        """
        Validate refresh token is valid and not expired.
        """
        try:
            RefreshToken(value)
        except Exception:
            raise AuthenticationFailed(
                detail={
                    "error": "INVALID_TOKEN",
                    "message": "Refresh token is invalid or expired.",
                },
                code="token_not_valid",
            ) from None
        return value


# Account Management Serializers


class AccountSerializer(serializers.ModelSerializer):
    """
    Account information serializer.

    Returns user account details including username and email (decrypted for owner).
    Excludes sensitive fields like password, deleted_at, pending_email.
    """

    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "email",
            "date_joined",
        ]


class UsernameUpdateSerializer(serializers.Serializer):
    """
    Username update serializer.

    Validates username rules and uniqueness before update.
    """

    username = serializers.CharField(max_length=100, required=True)

    def validate_username(self, value):
        """
        Validate username against all rules.

        Raises ValidationError with all error messages if invalid.
        """
        user = self.context.get("request").user
        validation_result = validate_username(value, exclude_user_id=user.id)

        if not validation_result["valid"] or not validation_result["available"]:
            # Join all errors into a single error message for DRF
            # (DRF displays first error, but we could also raise multiple)
            error_messages = validation_result["errors"]
            if len(error_messages) == 1:
                raise serializers.ValidationError(error_messages[0])
            else:
                # Multiple errors: raise all as a list
                raise serializers.ValidationError(error_messages)

        return value


class EmailChangeSerializer(serializers.Serializer):
    """
    Email change initiation serializer.

    Validates new email and checks it's not already in use.
    """

    new_email = serializers.EmailField(required=True)

    def validate_new_email(self, value):
        """
        Validate new email is not in use and different from current.
        """
        user = self.context.get("request").user

        # Check if same as current email
        if str(user.email) == value:
            raise serializers.ValidationError("New email must be different from current email.")

        # Check if email already in use by another user
        email_hash = User.hash_email(value)
        if User.objects.filter(email_hash=email_hash).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email address is already in use.")

        return value


class EmailConfirmSerializer(serializers.Serializer):
    """
    Email confirmation serializer.

    Validates token and user_id for email change confirmation.
    """

    token = serializers.CharField(max_length=128, required=True)
    user_id = serializers.UUIDField(required=True)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Password change serializer.

    Requires old password verification and validates new password.
    """

    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
        min_length=8,
    )

    def validate_old_password(self, value):
        """
        Verify old password is correct.
        """
        user = self.context.get("request").user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """
        Validate new password strength.
        """
        # Django's validate_password already runs, but we can add custom checks
        old_password = self.initial_data.get("old_password")
        if old_password and value == old_password:
            raise serializers.ValidationError(
                "New password must be different from current password."
            )
        return value


class AccountDeletionConfirmSerializer(serializers.Serializer):
    """
    Account deletion confirmation serializer.

    Validates token and user_id for account deletion confirmation.
    """

    token = serializers.CharField(max_length=128, required=True)
    user_id = serializers.UUIDField(required=True)


class UsernameValidationSerializer(serializers.Serializer):
    """
    Username validation serializer.

    Used for frontend inline validation (doesn't modify data).
    No validation here - validation logic is in the view to return 200 with valid=false.
    """

    username = serializers.CharField(required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password reset request serializer.

    Accepts email address to send password reset link.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate email exists in system.
        """
        from .models import User

        # Normalize email
        email_normalized = value.lower().strip()
        email_hash = User.hash_email(email_normalized)

        try:
            User.objects.get(email_hash=email_hash)
        except User.DoesNotExist:
            # Don't reveal whether email exists (security best practice)
            # Return success message regardless
            pass

        return email_normalized


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password reset confirmation serializer.

    Validates token and new password for password reset.
    """

    token = serializers.CharField(max_length=128, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
        min_length=8,
        help_text="New password (minimum 8 characters, must contain uppercase, lowercase, and numbers)",
    )

    def validate_new_password(self, value):
        """
        Validate new password strength.
        """
        # Django's validate_password already runs
        # Just ensure it meets minimum requirements
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        return value
