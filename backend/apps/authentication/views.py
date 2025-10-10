"""
Authentication views for user registration, login, token refresh, and profile management.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    TokenSerializer,
    RefreshTokenSerializer,
    UserSerializer,
)
from .services import AuthenticationService


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register
    Register a new user account.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user via service
        user = AuthenticationService.create_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )

        # Generate tokens
        token_data = AuthenticationService.generate_tokens(user)

        # Serialize user data
        user_serializer = UserSerializer(user)
        response_data = {
            'access': token_data['access'],
            'refresh': token_data['refresh'],
            'user': user_serializer.data
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login
    Authenticate user and return JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Authenticate via service
        user = AuthenticationService.authenticate_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )

        if not user:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        token_data = AuthenticationService.generate_tokens(user)

        # Serialize user data
        user_serializer = UserSerializer(user)
        response_data = {
            'access': token_data['access'],
            'refresh': token_data['refresh'],
            'user': user_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    POST /api/auth/refresh
    Refresh access token using refresh token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh']

        try:
            # Refresh access token via service
            new_access_token = AuthenticationService.refresh_access_token(refresh_token)

            return Response(
                {'access': new_access_token},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile - Get current user profile
    PUT/PATCH /api/auth/profile - Update current user profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Require authentication
def logout_view(request):
    """
    POST /api/auth/logout
    Logout user (client should discard tokens).
    """
    # JWT is stateless, so logout is client-side token deletion
    # Return 204 No Content (no response body)
    return Response(status=status.HTTP_204_NO_CONTENT)
