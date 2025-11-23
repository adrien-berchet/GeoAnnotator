"""
Custom exception classes for GeoAnnotator.

Provides structured exception hierarchy for better error handling and debugging.
"""


class GeoAnnotatorError(Exception):
    """Base exception for all GeoAnnotator-specific errors."""

    pass


class ServiceError(GeoAnnotatorError):
    """Base exception for service layer errors."""

    pass


class PermissionError(GeoAnnotatorError):
    """Raised when user lacks required permissions."""

    pass


class ResourceNotFoundError(GeoAnnotatorError):
    """Raised when a requested resource doesn't exist."""

    pass


class ValidationError(GeoAnnotatorError):
    """Raised when data validation fails."""

    pass


class StorageError(ServiceError):
    """Raised when file storage operations fail."""

    pass


class QuotaExceededError(StorageError):
    """Raised when storage quota is exceeded."""

    def __init__(self, quota_limit: int, current_usage: int, additional_size: int):
        self.quota_limit = quota_limit
        self.current_usage = current_usage
        self.additional_size = additional_size
        message = (
            f"Storage quota exceeded: "
            f"{current_usage + additional_size} bytes "
            f"(limit: {quota_limit} bytes)"
        )
        super().__init__(message)


class ShareError(ServiceError):
    """Base exception for sharing operations."""

    pass


class AutoShareRuleError(ShareError):
    """Raised when auto-share rule application fails."""

    pass


class LockError(ServiceError):
    """Raised when editing lock operations fail."""

    pass


class LockAcquisitionError(LockError):
    """Raised when unable to acquire editing lock."""

    def __init__(self, point_id: str, locked_by: str):
        self.point_id = point_id
        self.locked_by = locked_by
        message = f"Point {point_id} is locked by {locked_by}"
        super().__init__(message)


class ExportError(ServiceError):
    """Raised when export operations fail."""

    pass


class ImportError(ServiceError):
    """Raised when import operations fail."""

    pass


class EmailError(ServiceError):
    """Raised when email operations fail."""

    pass
