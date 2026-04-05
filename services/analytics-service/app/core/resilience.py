"""
Resilience patterns for external service calls

Implements:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Timeout handling
- Error tracking and metrics
"""
import asyncio
import time
from enum import Enum
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import httpx
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60   # How long to stay open
    half_open_max_calls: int = 3  # Max concurrent calls in half-open


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


class CircuitBreaker:
    """
    Circuit breaker implementation

    Prevents cascading failures by stopping requests to failing services
    and allowing time for recovery.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_calls = 0
        self.metrics: Dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_transitions": []
        }

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        old_state = self.state
        self.state = new_state

        transition = {
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.metrics["state_transitions"].append(transition)

        logger.info(
            "circuit_breaker_transition",
            circuit=self.name,
            old_state=old_state.value,
            new_state=new_state.value
        )

        if new_state == CircuitState.OPEN:
            self.opened_at = datetime.utcnow()
            self.half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0

    def _should_attempt_reset(self) -> bool:
        """Check if we should try resetting from open state"""
        if self.state != CircuitState.OPEN or not self.opened_at:
            return False

        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.config.timeout_seconds

    def can_execute(self) -> bool:
        """Check if a call can be executed"""
        self.metrics["total_calls"] += 1

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            else:
                self.metrics["rejected_calls"] += 1
                return False

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            else:
                self.metrics["rejected_calls"] += 1
                return False

        return False

    def record_success(self):
        """Record a successful call"""
        self.metrics["successful_calls"] += 1
        self.last_failure_time = None

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self.failure_count = 0
                self.success_count = 0

        if self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record a failed call"""
        self.metrics["failed_calls"] += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            self.failure_count = 0
            self.success_count = 0

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            **self.metrics,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None
        }


class ResilientHttpClient:
    """
    HTTP client with retry logic and circuit breaker

    Usage:
        client = ResilientHttpClient("feed-service")
        result = await client.get("http://feed-service:8001/api/v1/feeds")
    """

    def __init__(
        self,
        service_name: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        timeout: float = 10.0
    ):
        self.service_name = service_name
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            name=f"{service_name}_circuit",
            config=circuit_breaker_config
        )
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100
                )
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter"""
        delay = self.retry_config.base_delay_seconds * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(delay, self.retry_config.max_delay_seconds)

        if self.retry_config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Execute HTTP request with retry logic"""
        last_exception = None

        for attempt in range(self.retry_config.max_attempts):
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.warning(
                    "circuit_breaker_open",
                    service=self.service_name,
                    url=url,
                    state=self.circuit_breaker.state.value
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker open for {self.service_name}"
                )

            try:
                client = await self._get_client()

                logger.debug(
                    "http_request_attempt",
                    service=self.service_name,
                    method=method,
                    url=url,
                    attempt=attempt + 1
                )

                response = await client.request(method, url, **kwargs)

                # Check if response is successful
                if response.status_code < 500:
                    self.circuit_breaker.record_success()
                    return response
                else:
                    # 5xx errors should trigger retry
                    last_exception = httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                    self.circuit_breaker.record_failure()

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                last_exception = e
                self.circuit_breaker.record_failure()

                logger.warning(
                    "http_request_failed",
                    service=self.service_name,
                    url=url,
                    attempt=attempt + 1,
                    error=str(e)
                )

            # Don't sleep after last attempt
            if attempt < self.retry_config.max_attempts - 1:
                delay = self._calculate_delay(attempt)
                logger.debug(
                    "retry_delay",
                    service=self.service_name,
                    attempt=attempt + 1,
                    delay_seconds=delay
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            "http_request_failed_all_retries",
            service=self.service_name,
            url=url,
            attempts=self.retry_config.max_attempts
        )
        raise last_exception or Exception("All retry attempts failed")

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Execute GET request with resilience"""
        return await self._execute_with_retry("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Execute POST request with resilience"""
        return await self._execute_with_retry("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Execute PUT request with resilience"""
        return await self._execute_with_retry("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Execute DELETE request with resilience"""
        return await self._execute_with_retry("DELETE", url, **kwargs)

    def get_circuit_breaker_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return self.circuit_breaker.get_metrics()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global registry of resilient clients
_client_registry: Dict[str, ResilientHttpClient] = {}


def get_resilient_client(
    service_name: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    timeout: float = 10.0
) -> ResilientHttpClient:
    """
    Get or create a resilient HTTP client for a service

    Args:
        service_name: Name of the service (e.g., "feed-service")
        retry_config: Optional retry configuration
        circuit_breaker_config: Optional circuit breaker configuration
        timeout: Request timeout in seconds

    Returns:
        ResilientHttpClient instance
    """
    if service_name not in _client_registry:
        _client_registry[service_name] = ResilientHttpClient(
            service_name=service_name,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config,
            timeout=timeout
        )

    return _client_registry[service_name]


async def close_all_clients():
    """Close all registered resilient clients"""
    for client in _client_registry.values():
        await client.close()
    _client_registry.clear()


def get_all_circuit_breaker_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics for all circuit breakers"""
    return {
        name: client.get_circuit_breaker_metrics()
        for name, client in _client_registry.items()
    }
