from typing import Any, Optional, Dict


class AppException(Exception):
    """
    Base application exception for OWNIT.
    Provides structured error codes and messages for clean JSON responses.
    """
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details
        )


class ValidationException(AppException):
    """Raised when request payload or business logic validation fails."""
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class UnauthorizedException(AppException):
    """Raised when authentication credentials are missing or invalid."""
    def __init__(self, message: str = "Unauthorized access", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details
        )


class ConflictException(AppException):
    """Raised when a resource state conflict occurs (e.g. duplicate item)."""
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )
