"""
Core middleware for request processing and monitoring.
"""

import uuid
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Middleware that adds a unique request ID to each request for request tracing.

    The request ID is:
    - Stored as request.id for use in views and services
    - Added to the response as X-Request-ID header
    - Included in all log messages for request correlation

    This enables tracing requests through logs and across service boundaries.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or reuse request ID from header (for distributed tracing)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.id = request_id

        # Add request ID to logging context
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record

        logging.setLogRecordFactory(record_factory)

        try:
            response = self.get_response(request)
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)

        # Add request ID to response headers
        response["X-Request-ID"] = request_id

        return response
