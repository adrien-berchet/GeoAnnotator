"""Custom pagination classes for points app."""

from rest_framework.pagination import PageNumberPagination


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination class that allows clients to request large page sizes.

    Default page size is 25, but clients can request up to 10000 items
    using the page_size query parameter.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 10000
