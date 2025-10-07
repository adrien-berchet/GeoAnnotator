"""
Serializers for authentication app.

Handles user registration, login, profile, and token management.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    User profile serializer.
    
    Includes storage quota information (read-only).
    Matches OpenAPI schema: User
    """
    storage_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'date_joined',
            'storage_used',
            'storage_limit',
            'storage_percentage',
        ]
        read_only_fields = [
            'id',
            'date_joined',
            'storage_used',
            'storage_limit',
            'storage_percentage',
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
        style={'input_type': 'password'},
        min_length=8,
    )
    
    class Meta:
        model = User
        fields = ['email', 'password']
    
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
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        return value
    
    def create(self, validated_data):
        """
        Create user with hashed password and default storage quota (2GB).
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
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
        style={'input_type': 'password'},
    )
    
    def validate(self, attrs):
        """
        Validate email and password, authenticate user.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = authenticate(
            request=self.context.get('request'),
            username=email,  # Our User model uses email as USERNAME_FIELD
            password=password,
        )
        
        if user is None:
            raise serializers.ValidationError(
                {
                    'error': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password.',
                },
                code='authentication_failed',
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                {
                    'error': 'ACCOUNT_DISABLED',
                    'message': 'User account is disabled.',
                },
                code='authentication_failed',
            )
        
        attrs['user'] = user
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
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user,
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
        except Exception as e:
            raise serializers.ValidationError(
                {
                    'error': 'INVALID_TOKEN',
                    'message': 'Refresh token is invalid or expired.',
                    'details': str(e),
                }
            )
        return value
