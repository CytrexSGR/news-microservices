"""Base HTTP client with circuit breaker pattern."""

import logging
import time
from typing import Any, Dict, Optional
from enum import Enum

import httpx

from ..metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION,
    CIRCUIT_BREAKER_STATE,
    CIRCUIT_BREAKER_FAILURES,
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = 0  # Normal operation
    OPEN = 1  # Failing, reject requests
    HALF_OPEN = 2  # Testing recovery


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
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        CIRCUIT_BREAKER_STATE.labels(service=name).set(0)

    def record_success(self):
        """Record a successful call."""
        self.failures = 0
        self.state = CircuitState.CLOSED
        CIRCUIT_BREAKER_STATE.labels(service=self.name).set(0)

    def record_failure(self):
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        CIRCUIT_BREAKER_FAILURES.labels(service=self.name).inc()

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            CIRCUIT_BREAKER_STATE.labels(service=self.name).set(1)
            logger.warning(
                f"Circuit breaker OPEN for {self.name} after {self.failures} failures"
            )

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                CIRCUIT_BREAKER_STATE.labels(service=self.name).set(2)
                logger.info(f"Circuit breaker HALF-OPEN for {self.name}, testing...")
                return True
            return False

        # HALF_OPEN - allow one test request
        return True


class BaseClient:
    """Base HTTP client with circuit breaker and metrics."""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ):
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.circuit_breaker = CircuitBreaker(
            name=service_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP request with circuit breaker protection."""
        if not self.circuit_breaker.can_execute():
            return {
                "success": False,
                "data": None,
                "error": f"Circuit breaker open for {self.service_name}",
            }

        start_time = time.perf_counter()
        try:
            client = await self.get_client()
            response = await client.request(method, path, **kwargs)
            elapsed = time.perf_counter() - start_time

            HTTP_REQUEST_DURATION.labels(
                service=self.service_name,
                method=method,
            ).observe(elapsed)

            response.raise_for_status()

            HTTP_REQUESTS_TOTAL.labels(
                service=self.service_name,
                method=method,
                status="success",
            ).inc()

            self.circuit_breaker.record_success()

            return {
                "success": True,
                "data": response.json(),
                "error": None,
            }

        except httpx.HTTPStatusError as e:
            HTTP_REQUESTS_TOTAL.labels(
                service=self.service_name,
                method=method,
                status="error",
            ).inc()

            if e.response.status_code >= 500:
                self.circuit_breaker.record_failure()

            return {
                "success": False,
                "data": None,
                "error": str(e),
            }

        except Exception as e:
            HTTP_REQUESTS_TOTAL.labels(
                service=self.service_name,
                method=method,
                status="error",
            ).inc()

            self.circuit_breaker.record_failure()

            return {
                "success": False,
                "data": None,
                "error": str(e),
            }
