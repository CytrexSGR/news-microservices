"""
Retry Logic with Exponential Backoff for Resilient HTTP Requests.

Implements retry pattern with exponential backoff to handle transient failures
like timeouts, temporary service unavailability, etc.
"""

import asyncio
import logging
from typing import Callable, Any, TypeVar, Coroutine
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    initial_backoff: float = 1.0  # Seconds
    max_backoff: float = 32.0  # Seconds
    backoff_multiplier: float = 2.0
    retryable_status_codes: set = None  # Status codes to retry on

    def __post_init__(self):
        if self.retryable_status_codes is None:
            # Retry on these HTTP status codes
            self.retryable_status_codes = {408, 429, 500, 502, 503, 504}


class RetryableError(Exception):
    """Raised when retry attempt fails after exhausting retries"""
    pass


async def retry_with_backoff(
    func: Callable[..., Coroutine[Any, Any, T]],
    config: RetryConfig,
    *args,
    **kwargs
) -> T:
    """
    Execute async function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        config: Retry configuration
        *args: Function positional arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        RetryableError: If all retries exhausted
    """
    attempt = 0
    backoff = config.initial_backoff

    while attempt <= config.max_retries:
        try:
            return await func(*args, **kwargs)

        except httpx.HTTPStatusError as e:
            # Check if status code is retryable
            if e.response.status_code not in config.retryable_status_codes:
                # Not retryable, raise immediately
                logger.debug(
                    f"Non-retryable HTTP error {e.response.status_code}, "
                    f"not retrying"
                )
                raise

            # Retryable error
            if attempt >= config.max_retries:
                logger.error(
                    f"Max retries ({config.max_retries}) exhausted. "
                    f"Last error: HTTP {e.response.status_code}"
                )
                raise RetryableError(
                    f"Failed after {config.max_retries} retries: "
                    f"HTTP {e.response.status_code}"
                ) from e

            logger.warning(
                f"HTTP {e.response.status_code} (attempt {attempt + 1}/{config.max_retries}). "
                f"Retrying in {backoff}s..."
            )

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # Network errors are always retryable
            if attempt >= config.max_retries:
                logger.error(
                    f"Max retries ({config.max_retries}) exhausted. "
                    f"Last error: {type(e).__name__}: {e}"
                )
                raise RetryableError(
                    f"Failed after {config.max_retries} retries: {type(e).__name__}"
                ) from e

            logger.warning(
                f"{type(e).__name__} (attempt {attempt + 1}/{config.max_retries}). "
                f"Retrying in {backoff}s..."
            )

        except Exception as e:
            # Unexpected errors are not retryable
            logger.debug(f"Non-retryable error: {type(e).__name__}: {e}")
            raise

        # Wait before retry (exponential backoff)
        await asyncio.sleep(backoff)
        backoff = min(backoff * config.backoff_multiplier, config.max_backoff)
        attempt += 1

    # Should not reach here
    raise RetryableError(f"Failed after {config.max_retries} retries")
