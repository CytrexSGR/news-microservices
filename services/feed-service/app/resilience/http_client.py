"""
Resilient HTTP Client with Circuit Breaker and Retry Logic

Combines circuit breaker pattern and retry logic for robust HTTP calls.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
from .retry import RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


class ResilientHttpClient:
    """
    HTTP client with built-in resilience patterns.

    Features:
    - Circuit breaker to prevent cascading failures
    - Automatic retries with exponential backoff
    - Timeout handling
    - Connection pooling

    Usage:
        client = ResilientHttpClient(
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5),
            retry_config=RetryConfig(max_retries=3),
        )

        async with client:
            response = await client.get("https://example.com/feed")
    """

    def __init__(
        self,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.retry_config = retry_config or RetryConfig()
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.default_headers = headers or {}

        # Create circuit breaker
        self.circuit_breaker = CircuitBreaker(self.circuit_breaker_config)

        # HTTP client (will be created in __aenter__)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Create HTTP client on context entry"""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            headers=self.default_headers,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close HTTP client on context exit"""
        if self._client:
            await self._client.aclose()
        return False

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        HTTP GET request with resilience patterns.

        Args:
            url: Request URL
            headers: Additional headers
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            httpx.HTTPError: If request fails after retries
        """
        # Check circuit breaker
        if not await self.circuit_breaker.can_execute():
            await self.circuit_breaker.record_rejection()
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open, refusing to call {url}"
            )

        # Merge headers
        request_headers = {**self.default_headers, **(headers or {})}

        # Execute with retry logic
        try:
            response = await retry_with_backoff(
                self._execute_get,
                self.retry_config,
                url,
                request_headers,
                **kwargs
            )

            # Record success
            await self.circuit_breaker.record_success()
            return response

        except Exception as e:
            # Record failure
            await self.circuit_breaker.record_failure()
            raise

    async def _execute_get(
        self,
        url: str,
        headers: Dict[str, str],
        **kwargs
    ) -> httpx.Response:
        """Internal GET execution (called by retry logic)"""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        response = await self._client.get(url, headers=headers, **kwargs)
        # Don't raise for 304 Not Modified - it's a valid cache response
        # indicating the content hasn't changed since the last fetch
        if response.status_code != 304:
            response.raise_for_status()
        return response

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        HTTP POST request with resilience patterns.

        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            httpx.HTTPError: If request fails after retries
        """
        # Check circuit breaker
        if not await self.circuit_breaker.can_execute():
            await self.circuit_breaker.record_rejection()
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open, refusing to call {url}"
            )

        # Merge headers
        request_headers = {**self.default_headers, **(headers or {})}

        # Execute with retry logic
        try:
            response = await retry_with_backoff(
                self._execute_post,
                self.retry_config,
                url,
                request_headers,
                data,
                json,
                **kwargs
            )

            # Record success
            await self.circuit_breaker.record_success()
            return response

        except Exception as e:
            # Record failure
            await self.circuit_breaker.record_failure()
            raise

    async def _execute_post(
        self,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        **kwargs
    ) -> httpx.Response:
        """Internal POST execution (called by retry logic)"""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        response = await self._client.post(
            url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return self.circuit_breaker.get_stats()

    async def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        await self.circuit_breaker.reset()
