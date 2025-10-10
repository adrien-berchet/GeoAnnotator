"""
Custom exception handlers for DRF.

Formats all error responses to match OpenAPI Error schema:
{
    "error": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...}  // Optional validation details
}
"""

from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats errors to match OpenAPI spec.

    Converts DRF's default error format to:
    {
        "error": "ERROR_CODE",
        "message": "Description",
        "details": {field: [errors]}  // For validation errors
    }
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {}

        # Check if exception already has custom format (error + message)
        if isinstance(response.data, dict) and 'error' in response.data and 'message' in response.data:
            # Exception already formatted (e.g., from serializer), use as-is
            return response

        # Determine error code based on status code or exception type
        if isinstance(exc, AuthenticationFailed):
            # AuthenticationFailed may have custom detail
            if isinstance(response.data, dict) and 'error' in response.data:
                custom_response_data = response.data
            else:
                custom_response_data['error'] = 'INVALID_CREDENTIALS'
                custom_response_data['message'] = str(response.data.get('detail', 'Invalid credentials'))

        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['error'] = 'VALIDATION_ERROR'
            custom_response_data['message'] = 'Invalid request data'

            # Check if it's a validation error with field-level errors
            if isinstance(response.data, dict):
                # If all keys are field names (not 'detail'), it's field validation
                if not ('detail' in response.data):
                    custom_response_data['details'] = response.data
                else:
                    custom_response_data['message'] = str(response.data.get('detail', 'Invalid request data'))

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['error'] = 'UNAUTHORIZED'
            custom_response_data['message'] = str(response.data.get('detail', 'Authentication required'))

        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['error'] = 'ACCESS_DENIED'
            custom_response_data['message'] = str(response.data.get('detail', 'Access denied'))

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            # Check if it's a point-related 404 based on URL path
            request = context.get('request')
            if request and '/points/' in request.path:
                custom_response_data['error'] = 'POINT_NOT_FOUND'
            else:
                custom_response_data['error'] = 'NOT_FOUND'
            custom_response_data['message'] = str(response.data.get('detail', 'Resource not found'))

        elif response.status_code == status.HTTP_409_CONFLICT:
            custom_response_data['error'] = 'CONFLICT'
            custom_response_data['message'] = str(response.data.get('detail', 'Resource conflict'))

        elif response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
            custom_response_data['error'] = 'FILE_TOO_LARGE'
            custom_response_data['message'] = str(response.data.get('detail', 'Request entity too large'))

        elif response.status_code >= 500:
            custom_response_data['error'] = 'SERVER_ERROR'
            custom_response_data['message'] = 'Internal server error'

        else:
            # Fallback for other status codes
            custom_response_data['error'] = 'ERROR'
            custom_response_data['message'] = str(response.data.get('detail', 'An error occurred'))

        # Replace response data
        response.data = custom_response_data

    return response
