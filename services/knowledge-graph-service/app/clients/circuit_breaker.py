"""
Circuit Breaker pattern implementation for service resilience.

Prevents cascading failures by detecting when a service is failing
and temporarily blocking requests to give it time to recover.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service failing, requests blocked
- HALF_OPEN: Testing if service recovered

Reference: ADR-035 Circuit Breaker Pattern
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, TypeVar
from .exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait before attempting recovery (default: 30)
        service_name: Name of the protected service (for logging)

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        >>>
        >>> async def fetch_data():
        >>>     async with httpx.AsyncClient() as client:
        >>>         response = await client.get("http://api.example.com/data")
        >>>         return response.json()
        >>>
        >>> try:
        >>>     result = await breaker.call(fetch_data)
        >>> except CircuitBreakerOpenError:
        >>>     # Circuit is open, service unavailable
        >>>     logger.warning("Service unavailable, using fallback")
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        service_name: str = "external-service"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.service_name = service_name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._success_count_half_open = 0

        logger.info(
            f"CircuitBreaker initialized for '{service_name}': "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: Circuit is open, request blocked
            Exception: Original exception from func if circuit is closed
        """
        # Check if we should attempt recovery
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    service_name=self.service_name,
                    recovery_timeout=self.recovery_timeout
                )

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Record success
            self._record_success()

            return result

        except Exception as e:
            # Record failure
            self._record_failure(e)

            # Re-raise original exception
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count_half_open += 1

            # After one success in HALF_OPEN, transition to CLOSED
            if self._success_count_half_open >= 1:
                self._transition_to_closed()

        # In CLOSED state, reset failure count on success
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def _record_failure(self, exception: Exception) -> None:
        """Record failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        logger.warning(
            f"CircuitBreaker '{self.service_name}': Failure recorded "
            f"({self._failure_count}/{self.failure_threshold}). "
            f"Error: {type(exception).__name__}: {str(exception)}"
        )

        # Transition to OPEN if threshold exceeded
        if self._failure_count >= self.failure_threshold:
            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery attempt
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                # Normal operation failures exceeded threshold
                self._transition_to_open()

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state (normal operation)."""
        previous_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count_half_open = 0

        logger.info(
            f"CircuitBreaker '{self.service_name}': "
            f"{previous_state} -> CLOSED (service recovered)"
        )

    def _transition_to_open(self) -> None:
        """Transition to OPEN state (blocking requests)."""
        previous_state = self._state
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()

        logger.error(
            f"CircuitBreaker '{self.service_name}': "
            f"{previous_state} -> OPEN (threshold exceeded: "
            f"{self._failure_count} failures)"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state (testing recovery)."""
        previous_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._success_count_half_open = 0

        logger.info(
            f"CircuitBreaker '{self.service_name}': "
            f"{previous_state} -> HALF_OPEN (attempting recovery)"
        )

    def reset(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        Use with caution - typically for testing or manual intervention.
        """
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count_half_open = 0
        self._last_failure_time = None

        logger.warning(
            f"CircuitBreaker '{self.service_name}': Manually reset to CLOSED"
        )

    def get_stats(self) -> dict:
        """
        Get current circuit breaker statistics.

        Returns:
            Dictionary with state, failure_count, and last_failure_time
        """
        return {
            "service_name": self.service_name,
            "state": self._state,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout,
            "is_open": self.is_open
        }
