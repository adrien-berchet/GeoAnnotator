"""
Rate limiting decorators and utilities.

Provides wrappers around django-ratelimit for easier use with DRF views.
"""

from functools import wraps

from django_ratelimit.decorators import ratelimit as django_ratelimit
from rest_framework import status
from rest_framework.response import Response


def ratelimit(key="ip", rate="5/m", method=None, block=True):
    """
    Rate limit decorator for DRF views.

    Wrapper around django-ratelimit that returns proper DRF JSON responses
    when rate limit is exceeded.

    Args:
        key: What to rate limit by ('ip', 'user', callable)
        rate: Rate limit (e.g., '5/m' = 5 per minute, '100/h' = 100 per hour)
        method: HTTP method to rate limit (or None to use ALL methods)
        block: If True, block requests that exceed limit (default)

    Usage:
        @ratelimit(key='ip', rate='5/m', method='POST')
        def post(self, request):
            ...
    """

    def decorator(view_func):
        # Determine which HTTP methods to rate limit
        http_method = method if method is not None else "ALL"

        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            # Create a wrapper function that django-ratelimit can decorate
            # This function takes only request as first argument
            @django_ratelimit(key=key, rate=rate, method=http_method, block=block)
            def inner(request):
                return view_func(self, request, *args, **kwargs)

            # Execute the rate-limited function
            result = inner(request)

            # Check if request was rate limited
            if getattr(request, "limited", False):
                return Response(
                    {
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please try again later.",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            return result

        return wrapped_view

    return decorator


def get_user_or_ip(group, request):
    """
    Rate limit key function: Use user ID if authenticated, else IP.

    This ensures that authenticated users have separate rate limits
    from unauthenticated users.

    Usage:
        @ratelimit(key=get_user_or_ip, rate='100/h')
    """
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{request.META.get('REMOTE_ADDR', '')}"
