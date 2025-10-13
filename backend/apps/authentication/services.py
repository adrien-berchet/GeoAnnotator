"""
Authentication services.

Handles JWT token generation, validation, and user authentication logic.
"""

from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User


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

        if user and user.is_active:
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
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user,
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
            refresh = RefreshToken(refresh_token)
            return str(refresh.access_token)
        except TokenError as e:
            raise TokenError(f"Invalid or expired refresh token: {str(e)}")

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
            user_id = refresh.get('user_id')
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
