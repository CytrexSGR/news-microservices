"""Circuit breaker and resilience patterns for HTTP clients."""

import time
import logging
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx


logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60  # Time before trying half-open
    enable_metrics: bool = True


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: Dict[str, int] = field(default_factory=lambda: {
        "closed_to_open": 0,
        "open_to_half_open": 0,
        "half_open_to_closed": 0,
        "half_open_to_open": 0,
    })


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN."""

    pass


class HTTPCircuitBreakerError(Exception):
    """Raised when HTTP request fails due to circuit breaker."""

    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"[{service}] {message}")


class CircuitBreaker:
    """Circuit breaker for HTTP clients."""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.metrics = CircuitBreakerMetrics()

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        self.metrics.total_requests += 1

        # Check if circuit is OPEN
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker [{self.name}] transitioning to HALF_OPEN")
                self._transition_to_half_open()
            else:
                self.metrics.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker [{self.name}] is OPEN. "
                    f"Will retry after {self.config.timeout_seconds}s timeout."
                )

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.timeout_seconds

    def _on_success(self):
        """Handle successful request."""
        self.metrics.successful_requests += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit breaker [{self.name}] CLOSED after recovery")
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed request."""
        self.metrics.failed_requests += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker [{self.name}] failed in HALF_OPEN, reopening")
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker [{self.name}] OPEN after "
                    f"{self.failure_count} failures"
                )
                self._transition_to_open()

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.metrics.state_changes["half_open_to_closed"] += 1

    def _transition_to_open(self):
        """Transition to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.success_count = 0
        if old_state == CircuitState.CLOSED:
            self.metrics.state_changes["closed_to_open"] += 1
        elif old_state == CircuitState.HALF_OPEN:
            self.metrics.state_changes["half_open_to_open"] += 1

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.metrics.state_changes["open_to_half_open"] += 1

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "rejected_requests": self.metrics.rejected_requests,
            "state_changes": self.metrics.state_changes,
        }


class ResilientHTTPClient:
    """HTTP client with circuit breaker protection."""

    def __init__(
        self,
        name: str,
        base_url: str,
        config: CircuitBreakerConfig,
        timeout: int = 30,
    ):
        self.name = name
        self.base_url = base_url
        self.circuit_breaker = CircuitBreaker(name, config)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request with circuit breaker."""
        return await self.circuit_breaker.call(self.client.get, path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request with circuit breaker."""
        return await self.circuit_breaker.call(self.client.post, path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        """PUT request with circuit breaker."""
        return await self.circuit_breaker.call(self.client.put, path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request with circuit breaker."""
        return await self.circuit_breaker.call(self.client.delete, path, **kwargs)

    async def aclose(self):
        """Close HTTP client."""
        await self.client.aclose()

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics."""
        return self.circuit_breaker.get_metrics()
