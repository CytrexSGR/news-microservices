"""
HTTP Circuit Breaker for external API calls.

Wraps httpx AsyncClient with circuit breaker protection.
Prevents cascading failures and excessive costs from API outages.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import httpx

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class HTTPCircuitBreakerError(Exception):
    """Base exception for HTTP circuit breaker errors."""
    pass


class ResilientHTTPClient:
    """
    HTTP client with circuit breaker protection.

    Wraps httpx.AsyncClient and provides automatic circuit breaking
    for failed API calls.

    Usage:
        config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60,
        )

        async with ResilientHTTPClient(
            name="perplexity-api",
            base_url="https://api.perplexity.ai",
            config=config,
        ) as client:
            response = await client.post("/chat/completions", json={...})
    """

    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        config: Optional[CircuitBreakerConfig] = None,
        timeout: float = 30.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize resilient HTTP client.

        Args:
            name: Circuit breaker name (for metrics/logging)
            base_url: Optional base URL for all requests
            config: Circuit breaker configuration
            timeout: Request timeout in seconds
            circuit_breaker: Optional pre-configured circuit breaker
        """
        self.name = name
        self.base_url = base_url
        self.timeout = timeout

        # Create or use provided circuit breaker
        if circuit_breaker:
            self.circuit_breaker = circuit_breaker
        else:
            cb_config = config or CircuitBreakerConfig(
                failure_threshold=5,  # Open after 5 failures
                success_threshold=2,  # Close after 2 successes
                timeout_seconds=60,   # Retry after 60s
                enable_metrics=True,
            )
            self.circuit_breaker = CircuitBreaker(
                name=name,
                config=cb_config,
            )

        # HTTP client (created in __aenter__)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry - create HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Make GET request with circuit breaker protection.

        Args:
            url: Request URL
            **kwargs: Additional httpx request arguments

        Returns:
            httpx.Response

        Raises:
            CircuitBreakerOpenError: If circuit is open
            httpx.HTTPStatusError: If request fails
        """
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """
        Make POST request with circuit breaker protection.

        Args:
            url: Request URL
            **kwargs: Additional httpx request arguments

        Returns:
            httpx.Response

        Raises:
            CircuitBreakerOpenError: If circuit is open
            httpx.HTTPStatusError: If request fails
        """
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make PUT request with circuit breaker protection."""
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make DELETE request with circuit breaker protection."""
        return await self._request("DELETE", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Internal request method with circuit breaker protection.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request arguments

        Returns:
            httpx.Response

        Raises:
            CircuitBreakerOpenError: If circuit is open
            httpx.HTTPStatusError: If request fails
        """
        if not self._client:
            raise HTTPCircuitBreakerError("Client not initialized. Use 'async with' context manager.")

        # Try request with circuit breaker
        async with self.circuit_breaker():
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                # Log and re-raise
                logger.error(
                    f"HTTP {method} {url} failed: {e.response.status_code}"
                )
                raise
            except httpx.RequestError as e:
                # Network errors, timeouts, etc.
                logger.error(f"HTTP {method} {url} error: {e}")
                raise

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return self.circuit_breaker.get_stats()

    @property
    def state(self):
        """Get current circuit breaker state."""
        return self.circuit_breaker.state

    def reset(self) -> None:
        """Reset circuit breaker (for testing/admin)."""
        self.circuit_breaker.reset()


# Convenience factory function
def create_resilient_http_client(
    name: str,
    base_url: Optional[str] = None,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout_seconds: int = 60,
    request_timeout: float = 30.0,
) -> ResilientHTTPClient:
    """
    Create resilient HTTP client with default configuration.

    Args:
        name: Circuit breaker name
        base_url: Optional base URL
        failure_threshold: Failures before opening circuit
        success_threshold: Successes before closing circuit
        timeout_seconds: Time before retrying from OPEN
        request_timeout: HTTP request timeout

    Returns:
        ResilientHTTPClient instance
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout_seconds=timeout_seconds,
        enable_metrics=True,
    )

    return ResilientHTTPClient(
        name=name,
        base_url=base_url,
        config=config,
        timeout=request_timeout,
    )
