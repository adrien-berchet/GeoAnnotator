"""
Core utility views for system diagnostics.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAdminUser])
def email_config_status(request):
    """
    Diagnostic endpoint to check email configuration.

    Returns current email backend and configuration status.
    Only accessible by admin users for security.

    GET /api/v1/system/email-config/
    """
    config = {
        "email_backend": settings.EMAIL_BACKEND,
        "default_from_email": settings.DEFAULT_FROM_EMAIL,
        "django_settings_module": settings.SETTINGS_MODULE,
    }

    # Check Mailjet-specific configuration
    if "mailjet" in settings.EMAIL_BACKEND.lower():
        config["backend_type"] = "Mailjet HTTP API"
        config["mailjet_api_key_configured"] = bool(getattr(settings, "MAILJET_API_KEY", None))
        config["mailjet_secret_key_configured"] = bool(
            getattr(settings, "MAILJET_SECRET_KEY", None)
        )
        config["default_from_name"] = getattr(settings, "DEFAULT_FROM_NAME", "Not set")

        # Mask API key for security (show first 8 chars only)
        if config["mailjet_api_key_configured"]:
            api_key = getattr(settings, "MAILJET_API_KEY", "")
            config["mailjet_api_key_preview"] = f"{api_key[:8]}..." if len(api_key) > 8 else "***"

    # Check SMTP configuration
    elif "smtp" in settings.EMAIL_BACKEND.lower():
        config["backend_type"] = "SMTP"
        config["email_host"] = getattr(settings, "EMAIL_HOST", "Not set")
        config["email_port"] = getattr(settings, "EMAIL_PORT", "Not set")
        config["email_use_tls"] = getattr(settings, "EMAIL_USE_TLS", False)
        config["email_host_user_configured"] = bool(getattr(settings, "EMAIL_HOST_USER", None))

    # Check console backend (development)
    elif "console" in settings.EMAIL_BACKEND.lower():
        config["backend_type"] = "Console (development only)"

    # Unknown backend
    else:
        config["backend_type"] = "Unknown"

    # Overall configuration status
    if "mailjet" in settings.EMAIL_BACKEND.lower():
        config["status"] = (
            "configured"
            if (config["mailjet_api_key_configured"] and config["mailjet_secret_key_configured"])
            else "missing_credentials"
        )
    elif "smtp" in settings.EMAIL_BACKEND.lower():
        config["status"] = (
            "configured" if config["email_host_user_configured"] else "missing_credentials"
        )
    else:
        config["status"] = "unknown"

    return Response(config, status=status.HTTP_200_OK)
