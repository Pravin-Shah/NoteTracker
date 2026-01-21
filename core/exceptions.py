"""
Custom exceptions for the application.
"""


class AppException(Exception):
    """Base exception for the application."""
    pass


class DatabaseError(AppException):
    """Raised when database operation fails."""
    pass


class ValidationError(AppException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    pass


class NotificationError(AppException):
    """Raised when notification sending fails."""
    pass


class FileUploadError(AppException):
    """Raised when file upload fails."""
    pass


class NotFoundError(AppException):
    """Raised when requested resource is not found."""
    pass
