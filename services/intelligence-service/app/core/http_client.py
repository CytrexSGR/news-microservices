"""
Resilient HTTP Client for Inter-Service Communication.

Combines circuit breaker pattern and retry logic for robust calls to other
microservices. Handles transient failures gracefully.

Features:
- Circuit breaker to prevent cascading failures
- Exponential backoff retry on transient errors
- Configurable timeouts
- Connection pooling
- Automatic error recovery
"""

import httpx
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
from .retry import RetryConfig, retry_with_backoff, RetryableError
from .config import settings

logger = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    """Raised when service is unavailable (circuit breaker open)"""
    pass


class ResilientHttpClient:
    """
    HTTP client with built-in resilience patterns for inter-service communication.

    Features:
    - Circuit breaker to prevent cascading failures
    - Automatic retries with exponential backoff
    - Timeout handling
    - Connection pooling

    Usage:
        client = ResilientHttpClient(
            service_name="feed-service",
            base_url="http://feed-service:8101"
        )

        async with client:
            response = await client.get("/api/v1/feeds")
    """

    def __init__(
        self,
        service_name: str,
        base_url: str,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout: float = settings.HTTP_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout
        self.default_headers = headers or {}

        # Circuit breaker config
        if circuit_breaker_config is None:
            circuit_breaker_config = CircuitBreakerConfig(
                failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                success_threshold=settings.CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
                timeout=settings.CIRCUIT_BREAKER_TIMEOUT,
                name=service_name,
            )
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)

        # Retry config
        if retry_config is None:
            retry_config = RetryConfig(
                max_retries=settings.MAX_RETRIES,
                initial_backoff=settings.INITIAL_BACKOFF,
                max_backoff=settings.MAX_BACKOFF,
                backoff_multiplier=settings.BACKOFF_MULTIPLIER,
            )
        self.retry_config = retry_config

        # HTTP client (created in __aenter__)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Create HTTP client on context entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
            headers=self.default_headers,
        )
        logger.debug(f"ResilientHttpClient for {self.service_name} initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close HTTP client on context exit"""
        if self._client:
            await self._client.aclose()
        return False

    @asynccontextmanager
    async def _with_client(self):
        """Context manager for client operations"""
        if not self._client:
            raise RuntimeError(
                f"Client not initialized. Use 'async with' context manager "
                f"for {self.service_name}"
            )
        yield self._client

    async def get(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        HTTP GET request with resilience patterns.

        Args:
            path: Request path (relative to base_url)
            headers: Additional headers
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response

        Raises:
            ServiceUnavailableError: If circuit breaker is open
            RetryableError: If all retries exhausted
            httpx.HTTPError: Other HTTP errors
        """
        try:
            response = await self.circuit_breaker.call(
                self._execute_get,
                path,
                headers,
                **kwargs
            )
            return response
        except CircuitBreakerOpenError as e:
            logger.error(
                f"Circuit breaker OPEN for {self.service_name}. Service unavailable."
            )
            raise ServiceUnavailableError(
                f"{self.service_name} is currently unavailable"
            ) from e

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        HTTP POST request with resilience patterns.

        Args:
            path: Request path (relative to base_url)
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional httpx request parameters

        Returns:
            HTTP response

        Raises:
            ServiceUnavailableError: If circuit breaker is open
            RetryableError: If all retries exhausted
            httpx.HTTPError: Other HTTP errors
        """
        try:
            response = await self.circuit_breaker.call(
                self._execute_post,
                path,
                data,
                json,
                headers,
                **kwargs
            )
            return response
        except CircuitBreakerOpenError as e:
            logger.error(
                f"Circuit breaker OPEN for {self.service_name}. Service unavailable."
            )
            raise ServiceUnavailableError(
                f"{self.service_name} is currently unavailable"
            ) from e

    async def _execute_get(
        self,
        path: str,
        headers: Optional[Dict[str, str]],
        **kwargs
    ) -> httpx.Response:
        """Internal GET execution with retry logic"""
        async with self._with_client() as client:
            request_headers = {**self.default_headers, **(headers or {})}
            response = await retry_with_backoff(
                self._do_get,
                self.retry_config,
                client,
                path,
                request_headers,
                **kwargs
            )
            response.raise_for_status()
            return response

    async def _execute_post(
        self,
        path: str,
        data: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        **kwargs
    ) -> httpx.Response:
        """Internal POST execution with retry logic"""
        async with self._with_client() as client:
            request_headers = {**self.default_headers, **(headers or {})}
            response = await retry_with_backoff(
                self._do_post,
                self.retry_config,
                client,
                path,
                data,
                json,
                request_headers,
                **kwargs
            )
            response.raise_for_status()
            return response

    @staticmethod
    async def _do_get(
        client: httpx.AsyncClient,
        path: str,
        headers: Dict[str, str],
        **kwargs
    ) -> httpx.Response:
        """Actual GET execution"""
        return await client.get(path, headers=headers, **kwargs)

    @staticmethod
    async def _do_post(
        client: httpx.AsyncClient,
        path: str,
        data: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        **kwargs
    ) -> httpx.Response:
        """Actual POST execution"""
        return await client.post(
            path,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return self.circuit_breaker.get_stats()

    async def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        await self.circuit_breaker.reset()


# Factory for creating clients for different services
class HttpClientFactory:
    """Factory for creating ResilientHttpClient instances for different services"""

    _clients: Dict[str, ResilientHttpClient] = {}

    @classmethod
    def get_client(
        cls,
        service_name: str,
        base_url: Optional[str] = None,
    ) -> ResilientHttpClient:
        """
        Get or create a ResilientHttpClient for a service.

        Args:
            service_name: Name of the service (e.g., "feed-service")
            base_url: Base URL for the service (if None, uses config defaults)

        Returns:
            ResilientHttpClient instance
        """
        if service_name not in cls._clients:
            # Determine base URL from config
            if base_url is None:
                base_url = cls._get_service_url(service_name)

            if not base_url:
                raise ValueError(f"Unknown service: {service_name}")

            cls._clients[service_name] = ResilientHttpClient(
                service_name=service_name,
                base_url=base_url,
            )

        return cls._clients[service_name]

    @staticmethod
    def _get_service_url(service_name: str) -> Optional[str]:
        """Get base URL for service from config"""
        service_urls = {
            "feed-service": settings.FEED_SERVICE_URL,
            "analytics-service": settings.ANALYTICS_SERVICE_URL,
            "research-service": settings.RESEARCH_SERVICE_URL,
            "osint-service": settings.OSINT_SERVICE_URL,
            "auth-service": settings.AUTH_SERVICE_URL,
        }
        return service_urls.get(service_name)

    @classmethod
    async def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all clients"""
        stats = {}
        for service_name, client in cls._clients.items():
            stats[service_name] = client.get_stats()
        return stats

    @classmethod
    async def reset_all_circuit_breakers(cls):
        """Reset all circuit breakers"""
        for service_name, client in cls._clients.items():
            await client.reset_circuit_breaker()
            logger.info(f"Circuit breaker reset for {service_name}")
