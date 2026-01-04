"""
Core utility views for system diagnostics.
"""

import logging
import time
from threading import Lock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.ratelimit import ratelimit

logger = logging.getLogger(__name__)
User = get_user_model()

# In-memory cache for database health check
# Cache duration: configurable via DB_HEALTH_CACHE_DURATION env var (default: 30 minutes)
DB_HEALTH_CACHE_DURATION = int(getattr(settings, "DB_HEALTH_CACHE_DURATION", 1800))
_db_health_cache = {"result": None, "timestamp": 0}
_db_health_cache_lock = Lock()


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


class HealthCheckView(APIView):
    """
    GET /api/health/
    Comprehensive health check endpoint for container orchestration and monitoring.

    Returns status of all critical services:
    - Database connectivity
    - Redis connectivity (if configured)
    - Overall application health

    Rate limited to 60 requests per minute per IP to prevent abuse while
    allowing legitimate monitoring tools and container orchestrators.

    Returns:
        200: All services healthy
        429: Rate limit exceeded
        503: One or more services unhealthy
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="60/m", method="GET")
    def get(self, request):
        checks = {
            "status": "healthy",
            "database": _check_database(),
            "redis": _check_redis(),
        }

        # Determine overall status
        all_healthy = all(
            check_result.get("healthy", False)
            for check_result in checks.values()
            if isinstance(check_result, dict)
        )

        if not all_healthy:
            checks["status"] = "unhealthy"
            return Response(checks, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(checks, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def metrics(request):
    """
    Application metrics endpoint for monitoring and observability.

    Returns key application statistics:
    - Total number of GPS points
    - Total number of users
    - Total number of annotations
    - Database connection status

    GET /api/metrics/

    Requires: Admin authentication
    """
    from apps.annotations.models import Annotation
    from apps.points.models import GPSPoint

    try:
        metrics_data = {
            "points_count": GPSPoint.objects.count(),
            "users_count": User.objects.count(),
            "annotations_count": Annotation.objects.count(),
            "database_healthy": _check_database()["healthy"],
        }

        return Response(metrics_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Failed to collect metrics", exc_info=True)
        return Response(
            {"error": "Failed to collect metrics", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _check_database():
    """
    Check database connectivity with caching.

    Database health is cached for 30 minutes to reduce load on free-tier database.
    Cache is per-process and thread-safe. Lock is held during the entire check
    to prevent multiple threads from querying the database simultaneously when
    the cache expires.
    """
    current_time = time.time()

    with _db_health_cache_lock:
        # Check if we have a valid cached result
        if _db_health_cache["result"] is not None and (
            current_time - _db_health_cache["timestamp"] < DB_HEALTH_CACHE_DURATION
            and _db_health_cache["result"].get("healthy", False)
        ):
            # Return cached result with indicator
            cached_result = _db_health_cache["result"].copy()
            cached_result["cached"] = True
            return cached_result

        # Cache is expired or invalid - perform actual database check
        # Lock is held to ensure only one thread performs this check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            result = {"healthy": True, "message": "Database connection successful", "cached": False}
        except Exception as e:
            logger.error("Database health check failed", exc_info=True)
            result = {"healthy": False, "message": f"Database error: {str(e)}", "cached": False}

        # Update cache with new result
        _db_health_cache["result"] = result.copy()
        _db_health_cache["timestamp"] = current_time

        return result


def _check_redis():
    """Check Redis connectivity (if Redis is configured)."""
    try:
        # Import redis module
        import redis

        # Try to get Redis configuration from settings
        redis_url = getattr(settings, "CELERY_BROKER_URL", None)

        if not redis_url:
            return {"healthy": True, "message": "Redis not configured (optional)"}

        # Try to connect to Redis
        # For rediss:// URLs, redis-py will automatically use SSL
        # Don't manually configure SSL parameters to avoid conflicts
        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()

        return {"healthy": True, "message": "Redis connection successful"}
    except ImportError:
        return {"healthy": True, "message": "Redis module not installed (optional)"}
    except Exception as e:
        logger.warning("Redis health check failed", exc_info=True)
        return {"healthy": False, "message": f"Redis error: {str(e)}"}
