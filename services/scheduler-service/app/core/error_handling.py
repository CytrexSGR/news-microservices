"""
Standardized Error Handling for Scheduler Service.

Provides:
- Exponential backoff retry logic
- Circuit breaker pattern
- Error categorization (transient vs permanent)
- Comprehensive error logging
- Dead letter queue support
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCategory(Enum):
    """Error categories for different handling strategies"""
    TRANSIENT = "transient"  # Retry with backoff
    PERMANENT = "permanent"  # Don't retry
    RATE_LIMIT = "rate_limit"  # Retry with longer backoff
    TIMEOUT = "timeout"  # Retry with same/shorter timeout


class RetryConfig:
    """Configuration for retry logic"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.

        Args:
            attempt: Current retry attempt (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    def record_success(self):
        """Record successful request"""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.success_count = 0
                logger.info("Circuit breaker CLOSED (service recovered)")

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.success_count = 0
            logger.warning("Circuit breaker OPEN (service still failing)")

        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPEN (threshold {self.failure_threshold} exceeded)")

    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) >= self.timeout:
                self.state = "HALF_OPEN"
                self.success_count = 0
                logger.info("Circuit breaker HALF_OPEN (testing recovery)")
                return True
            return False

        # HALF_OPEN state
        return True

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time
        }


def categorize_error(error: Exception) -> ErrorCategory:
    """
    Categorize error for appropriate handling.

    Args:
        error: Exception to categorize

    Returns:
        ErrorCategory enum value
    """
    import httpx

    error_str = str(error).lower()

    # Timeout errors
    if isinstance(error, (asyncio.TimeoutError, httpx.TimeoutException)):
        return ErrorCategory.TIMEOUT

    # HTTP errors
    if isinstance(error, httpx.HTTPError):
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code

            # Rate limiting
            if status_code == 429:
                return ErrorCategory.RATE_LIMIT

            # Permanent client errors
            if 400 <= status_code < 500:
                return ErrorCategory.PERMANENT

            # Transient server errors
            if 500 <= status_code < 600:
                return ErrorCategory.TRANSIENT

        # Connection errors are transient
        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return ErrorCategory.TRANSIENT

    # Database connection errors are transient
    if "connection" in error_str or "timeout" in error_str:
        return ErrorCategory.TRANSIENT

    # Default to permanent for unknown errors
    return ErrorCategory.PERMANENT


def with_retry(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """
    Decorator for retry logic with exponential backoff and circuit breaker.

    Args:
        config: Retry configuration
        circuit_breaker: Optional circuit breaker instance

    Usage:
        @with_retry(config=RetryConfig(max_retries=3))
        async def my_function():
            # Function that might fail
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(config.max_retries + 1):
                try:
                    # Check circuit breaker
                    if circuit_breaker and not circuit_breaker.can_execute():
                        raise Exception(f"Circuit breaker is {circuit_breaker.state}")

                    # Execute function
                    result = await func(*args, **kwargs)

                    # Record success
                    if circuit_breaker:
                        circuit_breaker.record_success()

                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt} retries")

                    return result

                except Exception as e:
                    last_error = e
                    error_category = categorize_error(e)

                    # Record failure
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    # Don't retry permanent errors
                    if error_category == ErrorCategory.PERMANENT:
                        logger.error(f"{func.__name__} failed with permanent error: {e}")
                        raise

                    # Last attempt
                    if attempt == config.max_retries:
                        logger.error(
                            f"{func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise

                    # Calculate delay
                    delay = config.calculate_delay(attempt)
                    if error_category == ErrorCategory.RATE_LIMIT:
                        delay *= 2  # Longer delay for rate limiting

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed ({error_category.value}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)

            raise last_error

        return wrapper

    return decorator


class ErrorHandler:
    """
    Centralized error handling for scheduler service.

    Provides consistent error logging and categorization.
    """

    def __init__(self):
        self.error_counts: Dict[str, int] = {}

    def handle_error(
        self,
        error: Exception,
        context: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorCategory:
        """
        Handle error with logging and categorization.

        Args:
            error: Exception that occurred
            context: Context where error occurred (e.g., "job_processing")
            metadata: Additional metadata for logging

        Returns:
            ErrorCategory for handling decision
        """
        category = categorize_error(error)

        # Track error counts
        error_key = f"{context}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Log with appropriate level
        log_data = {
            "context": context,
            "error_type": type(error).__name__,
            "error_category": category.value,
            "error_count": self.error_counts[error_key],
            "error_message": str(error),
            **(metadata or {})
        }

        if category == ErrorCategory.PERMANENT:
            logger.error(f"Permanent error in {context}", extra=log_data)
        elif category == ErrorCategory.TRANSIENT:
            logger.warning(f"Transient error in {context}", extra=log_data)
        elif category == ErrorCategory.TIMEOUT:
            logger.warning(f"Timeout error in {context}", extra=log_data)
        elif category == ErrorCategory.RATE_LIMIT:
            logger.warning(f"Rate limit error in {context}", extra=log_data)

        return category

    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()

    def reset_stats(self):
        """Reset error statistics"""
        self.error_counts.clear()


# Global error handler instance
error_handler = ErrorHandler()
