"""
Circuit breaker pattern implementation for resilient external API calls.

Based on feed-service implementation with improvements:
- Async/await support
- Context manager pattern
- Thread-safety with asyncio.Lock
- Type hints
- Prometheus metrics integration
- Optional Redis backend for distributed state
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Callable, Any, TypeVar, Awaitable
from dataclasses import dataclass, field

from .types import CircuitBreakerState
from .metrics import CircuitBreakerMetrics

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    """Number of failures before opening circuit."""

    success_threshold: int = 2
    """Number of successes in half-open before closing circuit."""

    timeout_seconds: int = 120
    """Seconds to wait before trying half-open state."""

    enable_metrics: bool = True
    """Enable Prometheus metrics tracking."""

    ignored_exceptions: tuple = ()
    """Exception types to ignore (not count as failures).
    Example: (RateLimitError, HTTPStatus429Error)"""


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_failures: int = 0
    total_successes: int = 0
    total_rejections: int = 0  # Requests blocked while OPEN


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: Service failing, block requests
    - HALF_OPEN: Testing recovery

    Usage:
        circuit_breaker = CircuitBreaker(name="openai-api")

        # Context manager (recommended)
        async with circuit_breaker:
            result = await call_external_api()

        # Manual control
        if circuit_breaker.can_execute():
            try:
                result = await call_external_api()
                circuit_breaker.record_success()
            except Exception as e:
                circuit_breaker.record_failure()
                raise
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        metrics: Optional[CircuitBreakerMetrics] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique identifier for this circuit breaker
            config: Configuration (uses defaults if None)
            metrics: Metrics collector (creates default if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.ignored_exceptions = config.ignored_exceptions if config else ()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

        # Metrics
        if self.config.enable_metrics:
            self.metrics = metrics or CircuitBreakerMetrics()
            self.metrics.register_circuit_breaker(self.name)
        else:
            self.metrics = None

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state."""
        return self.stats.state

    def can_execute(self) -> bool:
        """
        Check if operation can be executed.

        Returns:
            True if operation can proceed, False if blocked
        """
        if self.stats.state == CircuitBreakerState.CLOSED:
            return True

        if self.stats.state == CircuitBreakerState.OPEN:
            # Check if timeout expired -> move to half-open
            if self.stats.last_failure_time:
                elapsed = datetime.now(timezone.utc) - self.stats.last_failure_time
                if elapsed.total_seconds() > self.config.timeout_seconds:
                    self._transition_to_half_open()
                    return True

            # Still OPEN, block request
            self.stats.total_rejections += 1
            if self.metrics:
                self.metrics.record_rejection(self.name)
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting request")
            return False

        # HALF_OPEN: Allow request through for testing
        return self.stats.state == CircuitBreakerState.HALF_OPEN

    def record_success(self) -> None:
        """Record a successful operation."""
        self.stats.total_successes += 1
        self.stats.failure_count = 0  # Reset failure count

        if self.metrics:
            self.metrics.record_success(self.name)

        if self.stats.state == CircuitBreakerState.HALF_OPEN:
            self.stats.success_count += 1
            logger.info(
                f"Circuit breaker '{self.name}' success in HALF_OPEN: "
                f"{self.stats.success_count}/{self.config.success_threshold}"
            )

            if self.stats.success_count >= self.config.success_threshold:
                self._transition_to_closed()

    def record_failure(self, error: Optional[Exception] = None) -> None:
        """
        Record a failed operation.

        Args:
            error: Optional exception that caused the failure
        """
        self.stats.failure_count += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = datetime.now(timezone.utc)
        self.stats.success_count = 0  # Reset success count

        if self.metrics:
            self.metrics.record_failure(self.name, error)

        if self.stats.failure_count >= self.config.failure_threshold:
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        if self.stats.state != CircuitBreakerState.OPEN:
            self.stats.state = CircuitBreakerState.OPEN
            self.stats.last_state_change = datetime.now(timezone.utc)

            if self.metrics:
                self.metrics.record_state_change(self.name, CircuitBreakerState.OPEN)

            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self.stats.failure_count} failures. "
                f"Will retry in {self.config.timeout_seconds}s."
            )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        if self.stats.state != CircuitBreakerState.HALF_OPEN:
            self.stats.state = CircuitBreakerState.HALF_OPEN
            self.stats.last_state_change = datetime.now(timezone.utc)
            self.stats.success_count = 0

            if self.metrics:
                self.metrics.record_state_change(self.name, CircuitBreakerState.HALF_OPEN)

            logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state for recovery testing")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        if self.stats.state != CircuitBreakerState.CLOSED:
            previous_state = self.stats.state
            self.stats.state = CircuitBreakerState.CLOSED
            self.stats.last_state_change = datetime.now(timezone.utc)
            self.stats.success_count = 0
            self.stats.failure_count = 0

            if self.metrics:
                self.metrics.record_state_change(self.name, CircuitBreakerState.CLOSED)

            # Calculate recovery time if transitioning from OPEN
            if previous_state == CircuitBreakerState.OPEN and self.stats.last_failure_time:
                recovery_time = (
                    datetime.now(timezone.utc) - self.stats.last_failure_time
                ).total_seconds()
                if self.metrics:
                    self.metrics.record_recovery(self.name, recovery_time)
                logger.info(
                    f"Circuit breaker '{self.name}' closed (recovered in {recovery_time:.1f}s)"
                )
            else:
                logger.info(f"Circuit breaker '{self.name}' closed")

    @asynccontextmanager
    async def __call__(self):
        """
        Context manager for circuit breaker protection.

        Usage:
            async with circuit_breaker():
                result = await risky_operation()
        """
        # Check if we can execute
        if not self.can_execute():
            from .exceptions import CircuitBreakerOpenError
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )

        try:
            yield self
            # Success: record it
            async with self._lock:
                self.record_success()
        except Exception as e:
            # Check if this exception should be ignored (e.g., rate limit errors)
            should_ignore = False
            if self.ignored_exceptions:
                should_ignore = isinstance(e, self.ignored_exceptions)

            if should_ignore:
                logger.debug(
                    f"Circuit breaker '{self.name}' ignoring exception {type(e).__name__} "
                    f"(not counted as failure)"
                )
            else:
                # Failure: record it
                async with self._lock:
                    self.record_failure(e)

            # Re-raise regardless (ignored exceptions still propagate)
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.

        Returns:
            Dictionary with current stats
        """
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "total_rejections": self.stats.total_rejections,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_state_change": self.stats.last_state_change.isoformat(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            }
        }

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state (for testing/admin)."""
        async def _reset():
            async with self._lock:
                self._transition_to_closed()
                self.stats.failure_count = 0
                self.stats.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")

        # Run in event loop
        asyncio.create_task(_reset())


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Usage:
        registry = CircuitBreakerRegistry()

        # Get or create circuit breaker
        cb = registry.get_or_create("openai-api", config)

        # List all circuit breakers
        all_cbs = registry.list_all()
    """

    def __init__(self):
        """Initialize registry."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        metrics: Optional[CircuitBreakerMetrics] = None,
    ) -> CircuitBreaker:
        """
        Get existing circuit breaker or create new one.

        Args:
            name: Circuit breaker name
            config: Configuration (only used if creating new)
            metrics: Metrics collector

        Returns:
            Circuit breaker instance
        """
        async with self._lock:
            if name not in self._circuit_breakers:
                self._circuit_breakers[name] = CircuitBreaker(
                    name=name,
                    config=config,
                    metrics=metrics,
                )
                logger.info(f"Created circuit breaker '{name}'")

            return self._circuit_breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get circuit breaker by name.

        Args:
            name: Circuit breaker name

        Returns:
            Circuit breaker if exists, None otherwise
        """
        return self._circuit_breakers.get(name)

    def list_all(self) -> Dict[str, CircuitBreaker]:
        """
        List all circuit breakers.

        Returns:
            Dictionary of name -> CircuitBreaker
        """
        return dict(self._circuit_breakers)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get stats for all circuit breakers.

        Returns:
            Dictionary of name -> stats
        """
        return {
            name: cb.get_stats()
            for name, cb in self._circuit_breakers.items()
        }

    async def reset_all(self) -> None:
        """Reset all circuit breakers to CLOSED state."""
        async with self._lock:
            for cb in self._circuit_breakers.values():
                cb.reset()
        logger.info(f"Reset {len(self._circuit_breakers)} circuit breakers")
