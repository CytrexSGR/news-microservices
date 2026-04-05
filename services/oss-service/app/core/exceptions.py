"""
Custom Exception Handlers

Issue #2: Provides consistent error response format across all endpoints.
Issue #9: Uses standardized error messages from constants.
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import json

from app.core.constants import ErrorMessages

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI request validation errors.

    Returns consistent error format instead of default FastAPI format.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "unknown")
        })

    logger.warning(
        f"Validation error on {request.method} {request.url.path}: "
        f"{len(errors)} error(s)"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
            "path": str(request.url.path)
        }
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    These occur when response models fail validation.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "unknown")
        })

    logger.error(
        f"Pydantic validation error on {request.method} {request.url.path}: "
        f"{len(errors)} error(s)"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Response validation failed",
            "errors": errors,
            "path": str(request.url.path)
        }
    )


async def json_decode_exception_handler(
    request: Request, exc: json.JSONDecodeError
) -> JSONResponse:
    """
    Handle JSON decode errors.

    These occur when request body is not valid JSON.
    Issue #9: Uses standardized error message.
    """
    logger.warning(
        f"JSON decode error on {request.method} {request.url.path}: {exc.msg}"
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": ErrorMessages.INVALID_JSON,
            "error": exc.msg,
            "position": exc.pos,
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle uncaught exceptions.

    Returns consistent error format and logs full traceback.
    Issue #9: Uses standardized error message.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": ErrorMessages.INTERNAL_ERROR,
            "type": type(exc).__name__,
            "path": str(request.url.path)
        }
    )


async def connection_error_handler(
    request: Request, exc: ConnectionError
) -> JSONResponse:
    """
    Handle connection errors (e.g., Neo4j, external APIs).

    Issue #9: Uses standardized error message.
    """
    logger.error(
        f"Connection error on {request.method} {request.url.path}: {exc}"
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": ErrorMessages.SERVICE_UNAVAILABLE,
            "message": ErrorMessages.NEO4J_CONNECTION_FAILED,
            "path": str(request.url.path)
        }
    )
