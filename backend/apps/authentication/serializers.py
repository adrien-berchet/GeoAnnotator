"""
Serializers for authentication app.

Handles user registration, login, profile, token management, and account management.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .services import validate_pseudonym


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
        fields = ["email", "password"]

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
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    User login serializer.

    Validates credentials and returns JWT tokens.
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
        Validate email and password, authenticate user.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,  # Our User model uses email as USERNAME_FIELD
            password=password,
        )

        if user is None:
            raise AuthenticationFailed(
                detail={
                    "error": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                },
                code="authentication_failed",
            )

        if not user.is_active:
            raise AuthenticationFailed(
                detail={
                    "error": "ACCOUNT_DISABLED",
                    "message": "User account is disabled.",
                },
                code="authentication_failed",
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

    Returns user account details including pseudonym and email (decrypted for owner).
    Excludes sensitive fields like password, deleted_at, pending_email.
    """

    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "pseudonym",
            "email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "created_at",
            "updated_at",
        ]


class PseudonymUpdateSerializer(serializers.Serializer):
    """
    Pseudonym update serializer.

    Validates pseudonym rules and uniqueness before update.
    """

    pseudonym = serializers.CharField(max_length=100, required=True)

    def validate_pseudonym(self, value):
        """
        Validate pseudonym against all rules.
        """
        user = self.context.get('request').user
        validation_result = validate_pseudonym(value, exclude_user_id=user.id)

        if not validation_result['valid'] or not validation_result['available']:
            raise serializers.ValidationError(validation_result['error'])

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
        user = self.context.get('request').user

        # Check if same as current email
        if str(user.email) == value:
            raise serializers.ValidationError("New email must be different from current email.")

        # Check if email already in use by another user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
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
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """
        Validate new password strength.
        """
        # Django's validate_password already runs, but we can add custom checks
        old_password = self.initial_data.get('old_password')
        if old_password and value == old_password:
            raise serializers.ValidationError("New password must be different from current password.")
        return value


class AccountDeletionConfirmSerializer(serializers.Serializer):
    """
    Account deletion confirmation serializer.

    Validates token and user_id for account deletion confirmation.
    """

    token = serializers.CharField(max_length=128, required=True)
    user_id = serializers.UUIDField(required=True)


class PseudonymValidationSerializer(serializers.Serializer):
    """
    Pseudonym validation serializer.

    Used for frontend inline validation (doesn't modify data).
    """

    pseudonym = serializers.CharField(max_length=100, required=True)
