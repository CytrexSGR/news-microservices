"""
Prometheus metrics for circuit breaker pattern.

Provides metrics tracking for circuit breaker state, failures, successes, and recovery.
"""

import logging
from typing import Optional, Dict
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime, timezone

from .types import CircuitBreakerState

logger = logging.getLogger(__name__)


class CircuitBreakerMetrics:
    """
    Prometheus metrics for circuit breakers.

    Metrics:
    - circuit_breaker_state: Current state (0=closed, 1=half-open, 2=open)
    - circuit_breaker_failures_total: Total failure count
    - circuit_breaker_successes_total: Total success count
    - circuit_breaker_rejections_total: Total blocked requests (while OPEN)
    - circuit_breaker_state_changes_total: State transition count
    - circuit_breaker_recovery_time_seconds: Time to recover from OPEN to CLOSED
    """

    # Class-level metrics (singleton) to avoid duplicate registration
    _state_gauge: Optional[Gauge] = None
    _failures_counter: Optional[Counter] = None
    _successes_counter: Optional[Counter] = None
    _rejections_counter: Optional[Counter] = None
    _state_changes_counter: Optional[Counter] = None
    _recovery_time_histogram: Optional[Histogram] = None
    _previous_states: Dict[str, CircuitBreakerState] = {}

    def __init__(self):
        """Initialize metrics collectors (singleton pattern)."""
        # Initialize metrics only once at class level
        if CircuitBreakerMetrics._state_gauge is None:
            CircuitBreakerMetrics._state_gauge = Gauge(
                "circuit_breaker_state",
                "Current circuit breaker state (0=closed, 1=half-open, 2=open)",
                ["name"],
            )

            CircuitBreakerMetrics._failures_counter = Counter(
                "circuit_breaker_failures_total",
                "Total number of circuit breaker failures",
                ["name", "error_type"],
            )

            CircuitBreakerMetrics._successes_counter = Counter(
                "circuit_breaker_successes_total",
                "Total number of circuit breaker successes",
                ["name"],
            )

            CircuitBreakerMetrics._rejections_counter = Counter(
                "circuit_breaker_rejections_total",
                "Total number of rejected requests while circuit is open",
                ["name"],
            )

            CircuitBreakerMetrics._state_changes_counter = Counter(
                "circuit_breaker_state_changes_total",
                "Total number of state changes",
                ["name", "from_state", "to_state"],
            )

            CircuitBreakerMetrics._recovery_time_histogram = Histogram(
                "circuit_breaker_recovery_time_seconds",
                "Time taken to recover from OPEN to CLOSED state",
                ["name"],
                buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
            )

        # Use class-level references
        self.state_gauge = CircuitBreakerMetrics._state_gauge
        self.failures_counter = CircuitBreakerMetrics._failures_counter
        self.successes_counter = CircuitBreakerMetrics._successes_counter
        self.rejections_counter = CircuitBreakerMetrics._rejections_counter
        self.state_changes_counter = CircuitBreakerMetrics._state_changes_counter
        self.recovery_time_histogram = CircuitBreakerMetrics._recovery_time_histogram
        self._previous_states = CircuitBreakerMetrics._previous_states

    def register_circuit_breaker(self, name: str) -> None:
        """
        Register a circuit breaker for metrics tracking.

        Args:
            name: Circuit breaker name
        """
        # Initialize state to CLOSED
        self.state_gauge.labels(name=name).set(0)
        self._previous_states[name] = CircuitBreakerState.CLOSED
        logger.debug(f"Registered circuit breaker metrics for '{name}'")

    def record_success(self, name: str) -> None:
        """
        Record a successful operation.

        Args:
            name: Circuit breaker name
        """
        self.successes_counter.labels(name=name).inc()

    def record_failure(self, name: str, error: Optional[Exception] = None) -> None:
        """
        Record a failed operation.

        Args:
            name: Circuit breaker name
            error: Exception that caused the failure
        """
        error_type = type(error).__name__ if error else "unknown"
        self.failures_counter.labels(name=name, error_type=error_type).inc()

    def record_rejection(self, name: str) -> None:
        """
        Record a rejected request (circuit is open).

        Args:
            name: Circuit breaker name
        """
        self.rejections_counter.labels(name=name).inc()

    def record_state_change(self, name: str, new_state: CircuitBreakerState) -> None:
        """
        Record a state transition.

        Args:
            name: Circuit breaker name
            new_state: New state
        """
        # Update state gauge
        state_value = {
            CircuitBreakerState.CLOSED: 0,
            CircuitBreakerState.HALF_OPEN: 1,
            CircuitBreakerState.OPEN: 2,
        }[new_state]
        self.state_gauge.labels(name=name).set(state_value)

        # Track state change
        previous_state = self._previous_states.get(name, CircuitBreakerState.CLOSED)
        if previous_state != new_state:
            self.state_changes_counter.labels(
                name=name,
                from_state=previous_state.value,
                to_state=new_state.value,
            ).inc()
            self._previous_states[name] = new_state
            logger.debug(f"Circuit breaker '{name}' state: {previous_state.value} → {new_state.value}")

    def record_recovery(self, name: str, recovery_time_seconds: float) -> None:
        """
        Record recovery time (OPEN → CLOSED transition).

        Args:
            name: Circuit breaker name
            recovery_time_seconds: Time taken to recover
        """
        self.recovery_time_histogram.labels(name=name).observe(recovery_time_seconds)
        logger.info(f"Circuit breaker '{name}' recovered in {recovery_time_seconds:.1f}s")
