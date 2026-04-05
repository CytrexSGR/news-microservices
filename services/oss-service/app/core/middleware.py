"""
Request/Response Validation Middleware

Issue #2: Provides centralized validation for:
- Request size limits
- Content-Type validation
- Consistent error response format

Issue #10: Uses constants from central constants file.
"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.constants import MAX_REQUEST_SIZE_BYTES, ErrorMessages

logger = logging.getLogger(__name__)


# Configuration constants
ALLOWED_CONTENT_TYPES = ["application/json", "application/json; charset=utf-8"]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating incoming requests.

    Checks:
    - Content-Length for POST/PUT requests (max 1MB)
    - Content-Type header for JSON endpoints
    - Logs request timing for observability
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Skip validation for GET/DELETE/OPTIONS
        if request.method in ("GET", "DELETE", "OPTIONS", "HEAD"):
            response = await call_next(request)
            self._log_request(request, response, start_time)
            return response

        # Check Content-Length for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            # Validate Content-Length
            content_length = request.headers.get("content-length", "0")
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE_BYTES:
                    logger.warning(
                        f"Request too large: {size} bytes from {request.client.host}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": ErrorMessages.REQUEST_TOO_LARGE,
                            "max_size_bytes": MAX_REQUEST_SIZE_BYTES,
                            "received_bytes": size
                        }
                    )
            except ValueError:
                pass  # No Content-Length header, let FastAPI handle it

            # Validate Content-Type for endpoints expecting JSON
            if request.url.path.startswith("/api/"):
                content_type = request.headers.get("content-type", "")
                # Extract base content type (ignore charset)
                base_content_type = content_type.split(";")[0].strip().lower()

                if base_content_type and base_content_type != "application/json":
                    logger.warning(
                        f"Invalid Content-Type: {content_type} for {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=415,
                        content={
                            "detail": ErrorMessages.INVALID_CONTENT_TYPE,
                            "expected": "application/json",
                            "received": content_type
                        }
                    )

        # Process request
        response = await call_next(request)
        self._log_request(request, response, start_time)
        return response

    def _log_request(
        self, request: Request, response: Response, start_time: float
    ) -> None:
        """Log request details for observability."""
        duration_ms = (time.time() - start_time) * 1000

        # Only log slow requests or errors in production
        if duration_ms > 1000 or response.status_code >= 400:
            logger.info(
                f"{request.method} {request.url.path} "
                f"status={response.status_code} "
                f"duration={duration_ms:.2f}ms "
                f"client={request.client.host if request.client else 'unknown'}"
            )


class ResponseFormattingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for ensuring consistent response formatting.

    Adds standard headers and ensures JSON responses are properly formatted.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add standard headers
        response.headers["X-Service"] = settings.APP_NAME
        response.headers["X-Version"] = settings.APP_VERSION

        return response
