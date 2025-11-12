"""
Authentication views for user registration, login, token refresh, profile management,
and account management (pseudonym, email, password, deletion).
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from .models import User, EmailChangeConfirmation
from .serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
    AccountSerializer,
    PseudonymUpdateSerializer,
    EmailChangeSerializer,
    EmailConfirmSerializer,
    PasswordChangeSerializer,
    AccountDeletionConfirmSerializer,
    PseudonymValidationSerializer,
)
from .services import (
    AuthenticationService,
    validate_pseudonym,
    EmailChangeTokenGenerator,
    AccountDeletionTokenGenerator,
    send_email_change_confirmation,
    send_deletion_confirmation,
    soft_delete_user,
    log_account_operation,
)


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

        validated_data = serializer.validated_data
        email = validated_data["email"]
        password = validated_data["password"]

        # Create user via service
        user = AuthenticationService.create_user(email=email, password=password)

        # Generate tokens
        token_data = AuthenticationService.generate_tokens(user)

        # Serialize user data
        user_serializer = UserSerializer(user)
        response_data = {
            "access": token_data["access"],
            "refresh": token_data["refresh"],
            "user": user_serializer.data,
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
            email=serializer.validated_data["email"], password=serializer.validated_data["password"]
        )

        if not user:
            return Response(
                {"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        token_data = AuthenticationService.generate_tokens(user)

        # Serialize user data
        user_serializer = UserSerializer(user)
        response_data = {
            "access": token_data["access"],
            "refresh": token_data["refresh"],
            "user": user_serializer.data,
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

        refresh_token = serializer.validated_data["refresh"]

        try:
            # Refresh access token via service
            new_access_token = AuthenticationService.refresh_access_token(refresh_token)

            return Response({"access": new_access_token}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


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
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(request.user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # Require authentication
def logout_view(request):
    """
    POST /api/auth/logout
    Logout user (client should discard tokens).
    """
    # JWT is stateless, so logout is client-side token deletion
    # Return 204 No Content (no response body)
    return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyCodeView(APIView):
    """
    POST /api/auth/verify
    Validate the user's verification code.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response(
                {"detail": "Email and code are required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if AuthenticationService.verify_user_code(user, code):
            return Response({"detail": "Account verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST
            )


# Account Management Views


class AccountOperationThrottle(UserRateThrottle):
    """Custom throttle for account operations (10 requests per minute)."""
    rate = '10/min'
    scope = 'account'


class EmailOperationThrottle(UserRateThrottle):
    """Custom throttle for email operations (3 requests per hour)."""
    rate = '3/hour'
    scope = 'email'


class ValidationThrottle(AnonRateThrottle):
    """Custom throttle for validation endpoint (30 requests per minute)."""
    rate = '30/min'
    scope = 'validation'


class AccountRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/account/
    Retrieve current authenticated user's account information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    def get_object(self):
        return self.request.user


class AccountUpdateAPIView(generics.UpdateAPIView):
    """
    PATCH /api/account/
    Update account pseudonym.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountOperationThrottle]
    serializer_class = PseudonymUpdateSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        old_pseudonym = user.pseudonym
        new_pseudonym = serializer.validated_data['pseudonym']

        # Update pseudonym
        user.pseudonym = new_pseudonym
        user.save(update_fields=['pseudonym'])

        # Log operation
        log_account_operation(
            user,
            'PSEUDONYM_CHANGED',
            request,
            details={'old_pseudonym': old_pseudonym, 'new_pseudonym': new_pseudonym}
        )

        # Return full account data
        response_serializer = AccountSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class EmailChangeRequestAPIView(APIView):
    """
    POST /api/account/change-email/
    Initiate email change process (sends confirmation link).
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailOperationThrottle]

    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data['new_email']

        # Generate token
        token = EmailChangeTokenGenerator.generate_token(user, new_email)

        # Create confirmation record
        expires_at = timezone.now() + timedelta(minutes=30)
        EmailChangeConfirmation.objects.create(
            user=user,
            new_email=new_email,
            token=token,
            expires_at=expires_at
        )

        # Send confirmation email
        send_email_change_confirmation(user, new_email, token)

        # Log operation
        log_account_operation(
            user,
            'EMAIL_CHANGE_REQUESTED',
            request,
            details={'new_email': new_email}
        )

        return Response({
            'detail': f'Confirmation email sent to {new_email}. Please check your inbox.',
            'expires_at': expires_at.isoformat()
        }, status=status.HTTP_200_OK)


class EmailConfirmAPIView(APIView):
    """
    POST /api/account/confirm-email/
    Confirm email change with token from email link.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        user_id = serializer.validated_data['user_id']

        # Verify user matches
        if str(request.user.id) != str(user_id):
            return Response(
                {'detail': 'You do not have permission to confirm this email change.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Find confirmation record
        try:
            confirmation = EmailChangeConfirmation.objects.get(
                user=request.user,
                token=token,
                confirmed_at__isnull=True
            )
        except EmailChangeConfirmation.DoesNotExist:
            return Response(
                {'detail': 'Invalid or expired confirmation token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if expired
        if confirmation.is_expired:
            return Response(
                {'detail': 'Confirmation link has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user email
        new_email = confirmation.new_email
        request.user.email = new_email
        request.user.save(update_fields=['email'])

        # Mark confirmation as confirmed
        confirmation.confirmed_at = timezone.now()
        confirmation.save(update_fields=['confirmed_at'])

        # Log operation
        log_account_operation(
            request.user,
            'EMAIL_CHANGE_CONFIRMED',
            request,
            details={'new_email': str(new_email)}
        )

        return Response({
            'detail': 'Email address updated successfully.',
            'new_email': str(new_email)
        }, status=status.HTTP_200_OK)


class PasswordChangeAPIView(APIView):
    """
    POST /api/account/change-password/
    Change user password (requires old password verification).
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountOperationThrottle]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data['new_password']

        # Update password
        user.set_password(new_password)
        user.save(update_fields=['password'])

        # Log operation
        log_account_operation(user, 'PASSWORD_CHANGED', request)

        return Response({
            'detail': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class AccountDeletionRequestAPIView(APIView):
    """
    DELETE /api/account/
    Soft delete user account (sends confirmation email).
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailOperationThrottle]

    def delete(self, request):
        user = request.user

        # Generate deletion token
        token = AccountDeletionTokenGenerator.generate_token(user)

        # Send deletion confirmation email
        send_deletion_confirmation(user, token)

        # Note: We don't create a separate model for deletion tokens,
        # they're validated via HMAC

        return Response({
            'detail': 'Account deletion confirmation sent. Please check your email.',
            'warning': 'Your account and all associated data will be permanently deleted in 30 days.'
        }, status=status.HTTP_200_OK)


class AccountDeletionConfirmAPIView(APIView):
    """
    POST /api/account/confirm-delete/
    Confirm account deletion with token from email link.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountDeletionConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        user_id = serializer.validated_data['user_id']

        # Verify user matches
        if str(request.user.id) != str(user_id):
            return Response(
                {'detail': 'You do not have permission to confirm this deletion.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate token
        if not AccountDeletionTokenGenerator.validate_token(token, request.user):
            return Response(
                {'detail': 'Invalid or expired deletion confirmation token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete user
        soft_delete_user(request.user)

        # Log operation
        log_account_operation(request.user, 'ACCOUNT_DELETED', request)

        # Calculate permanent deletion date (30 days)
        permanent_deletion_date = request.user.deleted_at + timedelta(days=30)

        return Response({
            'detail': 'Account deleted successfully. Your data will be permanently removed in 30 days.',
            'deleted_at': request.user.deleted_at.isoformat(),
            'permanent_deletion_date': permanent_deletion_date.isoformat()
        }, status=status.HTTP_200_OK)


class PseudonymValidationAPIView(APIView):
    """
    POST /api/account/validate-pseudonym/
    Validate pseudonym without saving (for frontend inline validation).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ValidationThrottle]

    def post(self, request):
        serializer = PseudonymValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pseudonym = serializer.validated_data['pseudonym']

        # Exclude current user if authenticated
        exclude_user_id = request.user.id if request.user.is_authenticated else None

        # Validate pseudonym
        result = validate_pseudonym(pseudonym, exclude_user_id=exclude_user_id)

        return Response(result, status=status.HTTP_200_OK)
