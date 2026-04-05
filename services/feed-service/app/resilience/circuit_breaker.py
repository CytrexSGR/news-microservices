"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by temporarily stopping calls to failing external services.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Requests blocked, circuit is "tripped"
- HALF_OPEN: Testing if service recovered, limited requests allowed

Transitions:
- CLOSED → OPEN: After failure_threshold consecutive failures
- OPEN → HALF_OPEN: After timeout_seconds elapsed
- HALF_OPEN → CLOSED: After success_threshold consecutive successes
- HALF_OPEN → OPEN: On any failure
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Callable, Any, Dict
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, REGISTRY

logger = logging.getLogger(__name__)

# Global registry to track created metrics (prevents duplicate registration)
_metrics_registry: dict = {}


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Open after N consecutive failures
    success_threshold: int = 2  # Close after N consecutive successes in HALF_OPEN
    timeout_seconds: int = 60  # Time before transitioning OPEN → HALF_OPEN
    enable_metrics: bool = True  # Enable Prometheus metrics
    name: str = "default"  # Circuit breaker identifier for metrics


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_rejections: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change_time: Optional[datetime] = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    opened_at: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit Breaker implementation for protecting external API calls.

    Usage:
        # Create circuit breaker
        cb = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=60,
        ))

        # Use as decorator
        @cb.call
        async def fetch_feed(url: str):
            async with httpx.AsyncClient() as client:
                return await client.get(url)

        # Use as context manager
        try:
            async with cb:
                result = await fetch_feed(url)
        except CircuitBreakerOpenError:
            logger.error("Circuit breaker is open")
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

        # Prometheus metrics (optional)
        if config.enable_metrics:
            self._init_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics (reuses existing if already registered)"""
        global _metrics_registry
        name = self.config.name

        # Use existing metrics if already registered for this circuit breaker name
        state_key = f"circuit_breaker_state_{name}"
        calls_key = f"circuit_breaker_calls_total_{name}"
        changes_key = f"circuit_breaker_state_changes_total_{name}"
        failures_key = f"circuit_breaker_consecutive_failures_{name}"

        if state_key in _metrics_registry:
            # Reuse existing metrics
            self.metrics_state = _metrics_registry[state_key]
            self.metrics_calls = _metrics_registry[calls_key]
            self.metrics_state_changes = _metrics_registry[changes_key]
            self.metrics_failure_count = _metrics_registry[failures_key]
            logger.debug(f"Reusing existing metrics for circuit breaker '{name}'")
            return

        # Create new metrics
        self.metrics_state = Gauge(
            state_key,
            f"Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
            ["name"],
        )

        self.metrics_calls = Counter(
            calls_key,
            f"Total circuit breaker calls",
            ["name", "result"],  # result: success, failure, rejected
        )

        self.metrics_state_changes = Counter(
            changes_key,
            f"Circuit breaker state transitions",
            ["name", "from_state", "to_state"],
        )

        self.metrics_failure_count = Gauge(
            failures_key,
            f"Consecutive failures",
            ["name"],
        )

        # Store in registry for reuse
        _metrics_registry[state_key] = self.metrics_state
        _metrics_registry[calls_key] = self.metrics_calls
        _metrics_registry[changes_key] = self.metrics_state_changes
        _metrics_registry[failures_key] = self.metrics_failure_count
        logger.debug(f"Registered new metrics for circuit breaker '{name}'")

    async def __aenter__(self):
        """Context manager entry"""
        if not await self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.config.name}' is {self.stats.state.value}"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            await self.record_success()
        else:
            await self.record_failure()
        return False  # Don't suppress exceptions

    def call(self, func: Callable):
        """
        Decorator for protecting async functions with circuit breaker.

        Usage:
            @circuit_breaker.call
            async def fetch_data():
                # ... external API call
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)
        return wrapper

    async def can_execute(self) -> bool:
        """Check if request can be executed"""
        async with self._lock:
            if self.stats.state == CircuitBreakerState.CLOSED:
                return True

            if self.stats.state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if self.stats.opened_at:
                    elapsed = datetime.now(timezone.utc) - self.stats.opened_at
                    if elapsed.total_seconds() >= self.config.timeout_seconds:
                        # Transition to HALF_OPEN
                        await self._transition_state(CircuitBreakerState.HALF_OPEN)
                        return True
                return False

            # HALF_OPEN: Allow single request to test recovery
            return True

    async def record_success(self):
        """Record successful operation"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = datetime.now(timezone.utc)
            self.stats.consecutive_failures = 0
            self.stats.failure_count = 0

            # Update metrics
            if self.config.enable_metrics:
                self.metrics_calls.labels(
                    name=self.config.name,
                    result="success"
                ).inc()
                self.metrics_failure_count.labels(
                    name=self.config.name
                ).set(0)

            # State-specific logic
            if self.stats.state == CircuitBreakerState.HALF_OPEN:
                self.stats.consecutive_successes += 1
                logger.info(
                    f"Circuit breaker '{self.config.name}' success in HALF_OPEN "
                    f"({self.stats.consecutive_successes}/{self.config.success_threshold})"
                )

                if self.stats.consecutive_successes >= self.config.success_threshold:
                    await self._transition_state(CircuitBreakerState.CLOSED)
                    logger.info(f"Circuit breaker '{self.config.name}' recovered and CLOSED")

    async def record_failure(self):
        """Record failed operation"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = datetime.now(timezone.utc)
            self.stats.consecutive_successes = 0
            self.stats.consecutive_failures += 1
            self.stats.failure_count += 1

            # Update metrics
            if self.config.enable_metrics:
                self.metrics_calls.labels(
                    name=self.config.name,
                    result="failure"
                ).inc()
                self.metrics_failure_count.labels(
                    name=self.config.name
                ).set(self.stats.consecutive_failures)

            # Check if threshold exceeded
            if self.stats.state == CircuitBreakerState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    await self._transition_state(CircuitBreakerState.OPEN)
                    logger.error(
                        f"Circuit breaker '{self.config.name}' OPENED after "
                        f"{self.stats.consecutive_failures} failures"
                    )

            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                # Any failure in HALF_OPEN → back to OPEN
                await self._transition_state(CircuitBreakerState.OPEN)
                logger.warning(
                    f"Circuit breaker '{self.config.name}' failed in HALF_OPEN, "
                    f"returning to OPEN"
                )

    async def record_rejection(self):
        """Record rejected call (circuit breaker open)"""
        async with self._lock:
            self.stats.total_rejections += 1

            if self.config.enable_metrics:
                self.metrics_calls.labels(
                    name=self.config.name,
                    result="rejected"
                ).inc()

    async def _transition_state(self, new_state: CircuitBreakerState):
        """Transition to new state"""
        old_state = self.stats.state

        if old_state == new_state:
            return

        self.stats.state = new_state
        self.stats.last_state_change_time = datetime.now(timezone.utc)

        # Reset counters on state change
        if new_state == CircuitBreakerState.CLOSED:
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self.stats.failure_count = 0
            self.stats.opened_at = None

        elif new_state == CircuitBreakerState.OPEN:
            self.stats.opened_at = datetime.now(timezone.utc)
            self.stats.consecutive_successes = 0

        elif new_state == CircuitBreakerState.HALF_OPEN:
            self.stats.consecutive_successes = 0
            self.stats.consecutive_failures = 0

        # Update metrics
        if self.config.enable_metrics:
            # Map states to numeric values for Gauge
            state_values = {
                CircuitBreakerState.CLOSED: 0,
                CircuitBreakerState.HALF_OPEN: 1,
                CircuitBreakerState.OPEN: 2,
            }
            self.metrics_state.labels(name=self.config.name).set(state_values[new_state])

            self.metrics_state_changes.labels(
                name=self.config.name,
                from_state=old_state.value,
                to_state=new_state.value,
            ).inc()

        logger.info(
            f"Circuit breaker '{self.config.name}' transitioned: "
            f"{old_state.value} → {new_state.value}"
        )

    async def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        async with self._lock:
            await self._transition_state(CircuitBreakerState.CLOSED)
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self.stats.failure_count = 0
            logger.info(f"Circuit breaker '{self.config.name}' manually reset to CLOSED")

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            "state": self.stats.state.value,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "total_calls": self.stats.total_calls,
            "total_successes": self.stats.total_successes,
            "total_failures": self.stats.total_failures,
            "total_rejections": self.stats.total_rejections,
            "failure_rate": (
                self.stats.total_failures / self.stats.total_calls
                if self.stats.total_calls > 0 else 0
            ),
            "last_failure_time": (
                self.stats.last_failure_time.isoformat()
                if self.stats.last_failure_time else None
            ),
            "last_success_time": (
                self.stats.last_success_time.isoformat()
                if self.stats.last_success_time else None
            ),
            "last_state_change_time": (
                self.stats.last_state_change_time.isoformat()
                if self.stats.last_state_change_time else None
            ),
            "opened_at": (
                self.stats.opened_at.isoformat()
                if self.stats.opened_at else None
            ),
        }
