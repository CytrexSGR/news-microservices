"""
Error Handling for Narrative Service
Standardized error responses and retry logic
"""
from typing import Optional, Callable, Any
from functools import wraps
import asyncio
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class NarrativeServiceError(Exception):
    """Base exception for narrative service errors"""
    pass


class TextTooShortError(NarrativeServiceError):
    """Raised when input text is too short for analysis"""
    pass


class AnalysisFailedError(NarrativeServiceError):
    """Raised when narrative analysis fails"""
    pass


class CacheError(NarrativeServiceError):
    """Raised when cache operations fail"""
    pass


class DatabaseError(NarrativeServiceError):
    """Raised when database operations fail"""
    pass


def validate_text_length(text: str, min_length: int = 50, max_length: int = 50000) -> None:
    """
    Validate text length for analysis

    Args:
        text: Text to validate
        min_length: Minimum required length
        max_length: Maximum allowed length

    Raises:
        HTTPException: If text length is invalid
    """
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )

    text_len = len(text)

    if text_len < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text must be at least {min_length} characters (got {text_len})"
        )

    if text_len > max_length:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Text must not exceed {max_length} characters (got {text_len})"
        )


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for async retry logic with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


def handle_analysis_error(
    error: Exception,
    context: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> HTTPException:
    """
    Convert analysis errors to HTTP exceptions

    Args:
        error: Original exception
        context: Context description (e.g., "frame detection")
        status_code: HTTP status code to return

    Returns:
        HTTPException with appropriate message
    """
    error_msg = str(error)

    # Log the error
    logger.error(f"{context} failed: {error_msg}", exc_info=True)

    # Map specific errors to status codes
    if isinstance(error, TextTooShortError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(error, CacheError):
        # Cache errors are non-fatal, log but don't fail request
        logger.warning(f"Cache error in {context}: {error_msg}")
        return None
    elif isinstance(error, DatabaseError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Create user-friendly error message
    if "timeout" in error_msg.lower():
        detail = f"{context} timed out. Please try again."
    elif "connection" in error_msg.lower():
        detail = f"Service temporarily unavailable. Please try again later."
    else:
        detail = f"{context} failed: {error_msg}"

    return HTTPException(
        status_code=status_code,
        detail={
            "error": context,
            "message": detail,
            "type": type(error).__name__
        }
    )


async def safe_analysis(
    func: Callable,
    *args,
    context: str = "Analysis",
    default_on_error: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Safely execute analysis function with error handling

    Args:
        func: Async function to execute
        args: Positional arguments for func
        context: Error context description
        default_on_error: Default value to return on error
        kwargs: Keyword arguments for func

    Returns:
        Function result or default value on error
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{context} error: {e}", exc_info=True)

        if default_on_error is not None:
            logger.info(f"Returning default value for {context}")
            return default_on_error

        raise handle_analysis_error(e, context)
