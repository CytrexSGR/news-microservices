"""Base HTTP client with circuit breaker protection."""

import httpx
import logging
import time
from typing import Dict, Any, Optional

from ..config import settings
from ..metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION,
    HTTP_REQUEST_ERRORS,
    HTTP_TIMEOUTS,
    SERVICE_HEALTH,
)

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    """Simple circuit breaker state."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time: Optional[float] = None

    def record_success(self):
        """Record successful call."""
        self.failures = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info(f"Circuit breaker {self.name}: CLOSED (recovered)")

    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {self.name}: OPEN (failures={self.failures})")

    def can_execute(self) -> bool:
        """Check if call can proceed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN (trying recovery)")
                return True
            return False

        # HALF_OPEN: allow one request
        return True


class BaseClient:
    """Base HTTP client with circuit breaker and metrics."""

    def __init__(self, name: str, base_url: str, timeout: float = 30.0):
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
        )
        self.circuit_breaker = CircuitBreaker(
            name=name,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with circuit breaker and metrics."""
        if not self.circuit_breaker.can_execute():
            HTTP_REQUEST_ERRORS.labels(service=self.name, error_type="circuit_breaker_open").inc()
            raise CircuitBreakerOpenError(f"Circuit breaker is OPEN for {self.name}")

        start_time = time.time()
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            elapsed = time.time() - start_time

            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                service=self.name,
                method=method,
                endpoint=endpoint,
                status=str(response.status_code),
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                service=self.name,
                method=method,
                endpoint=endpoint,
            ).observe(elapsed)

            if response.is_success:
                self.circuit_breaker.record_success()
                SERVICE_HEALTH.labels(service=self.name).set(1)
            else:
                self.circuit_breaker.record_failure()
                SERVICE_HEALTH.labels(service=self.name).set(0)

            return response

        except httpx.TimeoutException as e:
            self.circuit_breaker.record_failure()
            HTTP_TIMEOUTS.labels(service=self.name).inc()
            SERVICE_HEALTH.labels(service=self.name).set(0)
            logger.error(f"Request timeout for {self.name} {endpoint}: {e}")
            raise

        except httpx.HTTPError as e:
            self.circuit_breaker.record_failure()
            HTTP_REQUEST_ERRORS.labels(service=self.name, error_type=type(e).__name__).inc()
            SERVICE_HEALTH.labels(service=self.name).set(0)
            logger.error(f"HTTP error for {self.name} {endpoint}: {e}")
            raise

    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self._request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self._request("DELETE", endpoint, **kwargs)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
