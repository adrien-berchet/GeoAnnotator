"""Custom pagination classes for points app."""

from rest_framework.pagination import CursorPagination
from rest_framework.pagination import PageNumberPagination


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination class that allows clients to request large page sizes.

    Default page size is 25, but clients can request up to 10000 items
    using the page_size query parameter.

    Note: For datasets larger than 10k items, consider using PointsCursorPagination instead.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 10000


class PointsCursorPagination(CursorPagination):
    """
    Cursor-based pagination for GPS points.

    Benefits over PageNumberPagination:
    - More efficient for large datasets (no COUNT query needed)
    - Consistent results even when data is being added/removed
    - No possibility of duplicate/missing items across pages
    - Scales to millions of records

    Ordering:
    - Primary: created_at (descending) - newest points first
    - Secondary: id - ensures stable ordering for points created at the same time

    Usage:
        GET /api/points/?cursor=<encoded_cursor>&page_size=100

    Response format:
        {
            "next": "http://api/points/?cursor=cD0yMDIz...",
            "previous": "http://api/points/?cursor=cj0xJnA9Mg...",
            "results": [...]
        }
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
    ordering = "-created_at"  # Newest first

    # Cursor is encoded, so clients don't need to understand the ordering
    cursor_query_param = "cursor"

    # Use id as tie-breaker for stable ordering when created_at is identical
    # This prevents inconsistent results when multiple points have same timestamp
    ordering_fields = ["created_at", "id"]
