"""
Rate limiting decorators and utilities.

Provides wrappers around django-ratelimit for easier use with DRF views.
"""

from functools import wraps

from django_ratelimit.decorators import ratelimit as django_ratelimit
from rest_framework.response import Response
from rest_framework import status


def ratelimit(key="ip", rate="5/m", method="POST", block=True):
    """
    Rate limit decorator for DRF views.

    Wrapper around django-ratelimit that returns proper DRF JSON responses
    when rate limit is exceeded.

    Args:
        key: What to rate limit by ('ip', 'user', callable)
        rate: Rate limit (e.g., '5/m' = 5 per minute, '100/h' = 100 per hour)
        method: HTTP method to rate limit (or 'ALL' for all methods)
        block: If True, block requests that exceed limit (default)

    Usage:
        @ratelimit(key='ip', rate='5/m', method='POST')
        def post(self, request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @django_ratelimit(key=key, rate=rate, method=method, block=block)
        def wrapped_view(self, request, *args, **kwargs):
            # Check if request was rate limited
            if getattr(request, "limited", False):
                return Response(
                    {
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests. Please try again later.",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            return view_func(self, request, *args, **kwargs)

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
