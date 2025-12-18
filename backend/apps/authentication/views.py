"""
Authentication views for user registration, login, token refresh, profile management,
and account management (username, email, password, deletion).
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from apps.core.ratelimit import ratelimit

from .models import User
from .serializers import AccountDeletionConfirmSerializer
from .serializers import AccountSerializer
from .serializers import EmailChangeSerializer
from .serializers import EmailConfirmSerializer
from .serializers import LoginSerializer
from .serializers import PasswordChangeSerializer
from .serializers import PasswordResetConfirmSerializer
from .serializers import PasswordResetRequestSerializer
from .serializers import RefreshTokenSerializer
from .serializers import RegisterSerializer
from .serializers import UsernameUpdateSerializer
from .serializers import UsernameValidationSerializer
from .serializers import UserSerializer
from .services import AccountDeletionTokenGenerator
from .services import AuthenticationService
from .services import EmailConfirmationService
from .services import log_account_operation
from .services import PasswordResetService
from .services import send_deletion_confirmation
from .services import soft_delete_user
from .services import validate_username


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register
    Register a new user account.

    Rate limit: 5 registrations per hour per IP address
    """

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @ratelimit(key="ip", rate="5/h", method="POST")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user via serializer
        user = serializer.save()

        # Import EmailConfirmation for type constant
        from .models import EmailConfirmation

        # Generate confirmation token
        token = EmailConfirmationService.generate_confirmation_token(
            user, EmailConfirmation.REGISTRATION
        )

        # Send confirmation email
        EmailConfirmationService.send_confirmation_email(
            user, token, EmailConfirmation.REGISTRATION
        )

        # Return success message instead of JWT tokens
        response_data = {
            "message": "Registration successful! Please check your email to confirm your account.",
            "email": str(user.email),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class ConfirmEmailView(APIView):
    """
    POST /api/auth/confirm-email
    Confirm user email with token from confirmation link.

    Rate limit: 10 confirmations per hour per IP address
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="10/h", method="POST")
    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirm email
        success, error_message = EmailConfirmationService.confirm_email(token)

        if not success:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Email confirmed successfully! You can now log in."},
            status=status.HTTP_200_OK,
        )


class ResendConfirmationView(APIView):
    """
    POST /api/auth/resend-confirmation
    Resend confirmation email to unverified user.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resend confirmation email
        success, error_message = EmailConfirmationService.resend_confirmation_email(email)

        if not success:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Confirmation email sent! Please check your inbox."},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    POST /api/auth/login
    Authenticate user and return JWT tokens.

    Rate limit: 5 login attempts per minute per IP address
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="5/m", method="POST")
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # User is already authenticated by the serializer
        user = serializer.validated_data["user"]

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

    Rate limit: 30 refresh requests per minute per IP address
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="30/m", method="POST")
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
            email_hash = User.hash_email(email)
            user = User.objects.get(email_hash=email_hash)
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

    rate = "10/min"
    scope = "account"


class EmailOperationThrottle(UserRateThrottle):
    """Custom throttle for email operations (3 requests per hour)."""

    rate = "3/hour"
    scope = "email"


class ValidationThrottle(AnonRateThrottle):
    """Custom throttle for validation endpoint (30 requests per minute)."""

    rate = "30/min"
    scope = "validation"


class AccountRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/account/
    Retrieve current authenticated user's account information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    def get_object(self):
        user = self.request.user
        # Block soft-deleted users from accessing their account
        if hasattr(user, "deleted_at") and user.deleted_at is not None:
            raise NotFound("User account not found.")
        return user


class AccountUpdateAPIView(generics.UpdateAPIView):
    """
    PATCH /api/account/
    Update account username.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountOperationThrottle]
    serializer_class = UsernameUpdateSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        old_username = user.username
        new_username = serializer.validated_data["username"]

        # Update username
        user.username = new_username
        user.save(update_fields=["username"])

        # Log operation
        log_account_operation(
            user,
            "USERNAME_CHANGED",
            request,
            details={"old_username": old_username, "new_username": new_username},
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
        from .models import EmailConfirmation

        serializer = EmailChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data["new_email"]

        # Generate token using unified service
        token = EmailConfirmationService.generate_confirmation_token(
            user, EmailConfirmation.EMAIL_CHANGE, new_email=new_email
        )

        # Send confirmation email using unified service
        EmailConfirmationService.send_confirmation_email(
            user, token, EmailConfirmation.EMAIL_CHANGE, new_email=new_email
        )

        # Log operation
        log_account_operation(
            user, "EMAIL_CHANGE_REQUESTED", request, details={"new_email": new_email}
        )

        # Calculate expiration time (30 minutes)
        expires_at = timezone.now() + timedelta(minutes=30)

        return Response(
            {
                "detail": f"Confirmation email sent to {new_email}. Please check your inbox.",
                "expires_at": expires_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class EmailConfirmAPIView(APIView):
    """
    POST /api/account/confirm-email/
    Confirm email change with token from email link.

    Note: This endpoint is for email changes on existing authenticated accounts.
    For registration email confirmation, use ConfirmEmailView (no auth required).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import EmailConfirmation

        serializer = EmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user_id = serializer.validated_data["user_id"]

        # Verify user matches (security check)
        if str(request.user.id) != str(user_id):
            return Response(
                {"detail": "You do not have permission to confirm this email change."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate token and get confirmation
        is_valid, error_message, confirmation = (
            EmailConfirmationService.validate_confirmation_token(token)
        )

        if not is_valid:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify confirmation belongs to authenticated user
        if confirmation.user.id != request.user.id:
            return Response(
                {"detail": "You do not have permission to confirm this email change."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify this is an email change confirmation (not registration)
        if confirmation.confirmation_type != EmailConfirmation.EMAIL_CHANGE:
            return Response(
                {
                    "detail": (
                        "This endpoint is for email changes only. Registration confirmations "
                        "should use /api/auth/confirm-email/"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirm email change using unified service
        success, error_message = EmailConfirmationService.confirm_email(token)

        if not success:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refresh user to get updated email
        request.user.refresh_from_db()

        return Response(
            {"detail": "Email address updated successfully.", "new_email": str(request.user.email)},
            status=status.HTTP_200_OK,
        )


class PasswordChangeAPIView(APIView):
    """
    POST /api/account/password-change/
    Change user password (requires old password verification).

    Sends security notification email after successful password change.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountOperationThrottle]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data["new_password"]

        # Update password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Log operation
        log_account_operation(user, "PASSWORD_CHANGED", request)

        # Send security notification email
        self._send_password_change_notification(user, request)

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

    def _send_password_change_notification(self, user, request):
        """Send security notification email after password change."""
        from django.conf import settings
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils import timezone

        from .tasks import send_email_async

        # Get request details for security audit
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR", "Unknown")

        user_agent = request.headers.get("user-agent", "")

        # Get frontend URL from settings
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        reset_password_url = f"{frontend_url}/reset-password"

        # Email context
        context = {
            "user": user,
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "ip_address": ip_address,
            "user_agent": user_agent[:100] if user_agent else None,  # Truncate long user agents
            "reset_password_url": reset_password_url,
        }

        # Render email templates
        html_message = render_to_string(
            "emails/password_changed_notification.html", context
        )
        text_message = render_to_string("emails/password_changed_notification.txt", context)

        # Send email (async if Celery available)
        subject = "Password Changed - GeoAnnotator"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = str(user.email)

        try:
            # Try async email sending via Celery
            send_email_async.delay(
                subject=subject,
                message=text_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
            )
        except Exception:
            # Fallback to synchronous email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=True,  # Don't fail password change if email fails
            )


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

        return Response(
            {
                "detail": "Account deletion confirmation sent. Please check your email.",
                "warning": "Your account and all associated data will be permanently deleted in 30 days.",
            },
            status=status.HTTP_200_OK,
        )


class AccountDeletionConfirmAPIView(APIView):
    """
    POST /api/account/confirm-delete/
    Confirm account deletion with token from email link.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountDeletionConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user_id = serializer.validated_data["user_id"]

        # Verify user matches
        if str(request.user.id) != str(user_id):
            return Response(
                {"detail": "You do not have permission to confirm this deletion."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate token
        if not AccountDeletionTokenGenerator.validate_token(token, request.user):
            return Response(
                {"detail": "Invalid or expired deletion confirmation token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Soft delete user
        soft_delete_user(request.user)

        # Log operation
        log_account_operation(request.user, "ACCOUNT_DELETED", request)

        # Calculate permanent deletion date (30 days)
        permanent_deletion_date = request.user.deleted_at + timedelta(days=30)

        return Response(
            {
                "detail": "Account deleted successfully. Your data will be permanently removed in 30 days.",
                "deleted_at": request.user.deleted_at.isoformat(),
                "permanent_deletion_date": permanent_deletion_date.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class UsernameValidationAPIView(APIView):
    """
    POST /api/account/validate-username/
    Validate username without saving (for frontend inline validation).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ValidationThrottle]

    def post(self, request):
        serializer = UsernameValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]

        # Exclude current user if authenticated
        exclude_user_id = request.user.id if request.user.is_authenticated else None

        # Validate username
        result = validate_username(username, exclude_user_id=exclude_user_id)

        # Transform errors list to single error message for API response
        response_data = {"valid": result["valid"], "available": result["available"]}
        if result.get("errors"):
            response_data["error"] = result["errors"][0]  # Return first error

        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Request password reset by email.

    Rate limit: 3 requests per hour per IP address
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @ratelimit(key="ip", rate="3/h", method="POST")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Find user by email_hash
        email_hash = User.hash_email(email)
        try:
            user = User.objects.get(email_hash=email_hash)

            # Generate reset token
            token = PasswordResetService.generate_reset_token(user, request)

            # Send reset email
            PasswordResetService.send_reset_email(user, token)

            # Log the request
            log_account_operation(
                user=user,
                operation="PASSWORD_RESET_REQUESTED",
                request=request,
                details={"email": email},
            )

        except User.DoesNotExist:
            # Don't reveal whether email exists (security best practice)
            # Return success message regardless
            pass

        # Always return success to prevent email enumeration
        return Response(
            {
                "message": "If an account with that email exists, "
                "a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/
    Confirm password reset with token and new password.

    Rate limit: 5 confirmations per hour per IP address
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @ratelimit(key="ip", rate="5/h", method="POST")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        # Confirm password reset
        success, error_message = PasswordResetService.confirm_password_reset(
            token, new_password, request
        )

        if not success:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Password has been reset successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )
