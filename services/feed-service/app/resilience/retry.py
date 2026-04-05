"""
Retry logic with exponential backoff

Implements intelligent retry strategies for transient failures.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Callable, Optional, Type, Tuple, Any
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with retry logic and exponential backoff.

    Args:
        func: Async function to execute
        config: Retry configuration
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted

    Example:
        config = RetryConfig(max_retries=3, initial_delay=1.0)
        result = await retry_with_backoff(fetch_feed, config, feed_url)
    """
    last_exception = None
    delay = config.initial_delay

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_retries:
                logger.error(
                    f"All {config.max_retries} retry attempts exhausted for {func.__name__}: {e}"
                )
                raise

            # Calculate backoff delay
            if config.jitter:
                # Add random jitter (±25%) to prevent thundering herd
                jitter_factor = 0.75 + (random.random() * 0.5)
                actual_delay = min(delay * jitter_factor, config.max_delay)
            else:
                actual_delay = min(delay, config.max_delay)

            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                f"after {actual_delay:.2f}s delay. Error: {e}"
            )

            await asyncio.sleep(actual_delay)

            # Exponential backoff
            delay *= config.exponential_base

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to async functions.

    Usage:
        @with_retry(RetryConfig(max_retries=3))
        async def fetch_feed(url: str):
            # ... code that might fail
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator
