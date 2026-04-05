"""
Standardized Error Handling for Feed Service

Provides consistent error responses across all API endpoints.

Task 406: Error Handling Standardization
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, DataError
from pydantic import ValidationError

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================

class FeedServiceError(Exception):
    """Base exception for Feed Service errors"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundError(FeedServiceError):
    """Resource not found (404)"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with ID '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ValidationError(FeedServiceError):
    """Validation error (422)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DuplicateResourceError(FeedServiceError):
    """Duplicate resource (409)"""
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_RESOURCE",
            details={"resource": resource, "field": field, "value": str(value)},
        )


class CircuitBreakerOpenError(FeedServiceError):
    """Circuit breaker open (503)"""
    def __init__(self, service: str):
        super().__init__(
            message=f"Service '{service}' is currently unavailable (circuit breaker open)",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="CIRCUIT_BREAKER_OPEN",
            details={"service": service},
        )


class ExternalServiceError(FeedServiceError):
    """External service error (502)"""
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class RateLimitExceededError(FeedServiceError):
    """Rate limit exceeded (429)"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after} if retry_after else {},
        )


class AuthorizationError(FeedServiceError):
    """Authorization error (403)"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


# =============================================================================
# Error Response Models
# =============================================================================

def error_response(
    message: str,
    status_code: int,
    error_code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Create standardized error response.

    Format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "status": 400,
            "details": {...},
            "request_id": "uuid",
            "timestamp": "2025-11-24T10:00:00.000Z"
        }
    }
    """
    from datetime import datetime

    error_data = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }

    if details:
        error_data["error"]["details"] = details

    if request_id:
        error_data["error"]["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=error_data,
    )


# =============================================================================
# Exception Handlers
# =============================================================================

async def feed_service_error_handler(request: Request, exc: FeedServiceError):
    """Handle FeedServiceError and subclasses"""
    logger.error(
        f"FeedServiceError: {exc.error_code} - {exc.message}",
        extra={"details": exc.details},
    )

    return error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details,
        request_id=request.headers.get("X-Request-ID"),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")

    return error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        error_code=f"HTTP_{exc.status_code}",
        request_id=request.headers.get("X-Request-ID"),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error: {errors}")

    return error_response(
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors},
        request_id=request.headers.get("X-Request-ID"),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (duplicates, foreign keys)"""
    logger.error(f"Database integrity error: {exc}", exc_info=True)

    # Parse error message to provide better feedback
    error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    if "unique constraint" in error_message.lower() or "duplicate key" in error_message.lower():
        return error_response(
            message="Resource already exists",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_RESOURCE",
            details={"database_error": error_message[:200]},
            request_id=request.headers.get("X-Request-ID"),
        )
    elif "foreign key" in error_message.lower():
        return error_response(
            message="Referenced resource does not exist",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FOREIGN_KEY_VIOLATION",
            details={"database_error": error_message[:200]},
            request_id=request.headers.get("X-Request-ID"),
        )
    else:
        return error_response(
            message="Database integrity error",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DATABASE_INTEGRITY_ERROR",
            details={"database_error": error_message[:200]},
            request_id=request.headers.get("X-Request-ID"),
        )


async def data_error_handler(request: Request, exc: DataError):
    """Handle database data errors (invalid data types, etc.)"""
    logger.error(f"Database data error: {exc}", exc_info=True)

    error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    return error_response(
        message="Invalid data provided",
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="INVALID_DATA",
        details={"database_error": error_message[:200]},
        request_id=request.headers.get("X-Request-ID"),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return error_response(
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        details={
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:200],
        } if logger.level == logging.DEBUG else {},
        request_id=request.headers.get("X-Request-ID"),
    )


# =============================================================================
# Utility Functions
# =============================================================================

def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    from fastapi.exceptions import RequestValidationError as FastAPIValidationError

    app.add_exception_handler(FeedServiceError, feed_service_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(DataError, data_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Registered exception handlers")
