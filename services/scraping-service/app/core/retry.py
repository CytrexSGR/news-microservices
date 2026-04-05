"""
Exponential Backoff Retry Logic for HTTP Requests.

Implements retry mechanism with:
- Maximum 3 retry attempts
- Exponential backoff delays (1s, 2s, 4s)
- Detailed logging of retry attempts
- Configurable for different scraping methods
"""

import asyncio
import logging
import random
from typing import TypeVar, Callable, Awaitable, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Enum):
    """Types of errors that should trigger retries."""
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"  # 5xx
    RATE_LIMIT = "rate_limit"      # 429


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0  # First retry after 1s
    max_delay: float = 4.0   # Cap at 4s
    exponential_base: float = 2.0  # Delay multiplier (1s, 2s, 4s)


def calculate_backoff_with_jitter(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff with full jitter.

    Full jitter prevents "thundering herd" problem where many
    clients retry at the same time after a service recovers.

    Formula: random(0.5 * delay, delay) where delay = min(max_delay, base_delay * 2^attempt)

    Args:
        attempt: Current retry attempt (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds with jitter applied
    """
    # Calculate exponential delay
    exp_delay = config.base_delay * (config.exponential_base ** attempt)

    # Cap at max_delay
    capped_delay = min(exp_delay, config.max_delay)

    # Apply full jitter: random value between 50% and 100% of capped delay
    # This prevents synchronized retries while maintaining backoff pressure
    jittered_delay = capped_delay * (0.5 + random.random() * 0.5)

    return jittered_delay


class RetryHandler:
    """
    Handles retry logic with exponential backoff.

    Usage:
        retry_handler = RetryHandler()

        result = await retry_handler.execute_with_retry(
            func=scraper.scrape,
            args=(url,),
            kwargs={"method": "httpx"},
            config=RetryConfig(max_retries=3)
        )
    """

    def __init__(self):
        self.retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0
        }

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T]],
        args: tuple = (),
        kwargs: dict = None,
        config: Optional[RetryConfig] = None,
        context: str = "operation"
    ) -> T:
        """
        Execute async function with exponential backoff retry.

        Args:
            func: Async function to execute
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            config: Retry configuration (uses default if None)
            context: Description for logging (e.g., "scrape https://example.com")

        Returns:
            Result from successful function execution

        Raises:
            Last exception if all retries exhausted
        """
        if kwargs is None:
            kwargs = {}

        if config is None:
            config = RetryConfig()

        last_exception = None

        for attempt in range(config.max_retries + 1):
            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Log successful retry
                if attempt > 0:
                    logger.info(
                        f"✅ Retry successful for {context} "
                        f"(attempt {attempt + 1}/{config.max_retries + 1})"
                    )
                    self.retry_stats["successful_retries"] += 1

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if not self._should_retry(e, attempt, config):
                    logger.warning(
                        f"❌ No retry for {context}: {str(e)} "
                        f"(attempt {attempt + 1}/{config.max_retries + 1})"
                    )
                    self.retry_stats["failed_retries"] += 1
                    raise

                # Calculate delay with jittered exponential backoff
                delay = calculate_backoff_with_jitter(attempt, config)

                logger.warning(
                    f"🔄 Retrying {context} after {delay:.2f}s (jittered) "
                    f"(attempt {attempt + 1}/{config.max_retries + 1}): {str(e)}"
                )

                self.retry_stats["total_retries"] += 1

                # Wait before retry
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            f"❌ All retries exhausted for {context} "
            f"(tried {config.max_retries + 1} times)"
        )
        self.retry_stats["failed_retries"] += 1
        raise last_exception

    def _should_retry(
        self,
        exception: Exception,
        attempt: int,
        config: RetryConfig
    ) -> bool:
        """
        Determine if exception should trigger retry.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-indexed)
            config: Retry configuration

        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if max attempts reached
        if attempt >= config.max_retries:
            return False

        exception_name = type(exception).__name__
        exception_msg = str(exception).lower()

        # Retry on timeout errors
        if "timeout" in exception_name.lower() or "timeout" in exception_msg:
            return True

        # Retry on connection errors
        if "connection" in exception_msg or "refused" in exception_msg:
            return True

        # Retry on server errors (5xx)
        if "500" in exception_msg or "502" in exception_msg or "503" in exception_msg:
            return True

        # Retry on rate limiting (429)
        if "429" in exception_msg or "rate limit" in exception_msg:
            return True

        # Check for specific exception types
        retryable_exceptions = [
            "TimeoutError",
            "ConnectTimeout",
            "ReadTimeout",
            "HTTPStatusError",
            "ConnectError",
            "NetworkError",
            "RemoteProtocolError",
        ]

        if any(exc in exception_name for exc in retryable_exceptions):
            return True

        # Don't retry on other errors (e.g., validation, 404, 403)
        return False

    def get_stats(self) -> dict:
        """
        Get retry statistics.

        Returns:
            dict: Retry statistics including total, successful, and failed retries
        """
        return {
            **self.retry_stats,
            "success_rate": (
                self.retry_stats["successful_retries"] / self.retry_stats["total_retries"]
                if self.retry_stats["total_retries"] > 0
                else 0.0
            )
        }

    def reset_stats(self):
        """Reset retry statistics."""
        self.retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0
        }


# Global retry handler instance
retry_handler = RetryHandler()
