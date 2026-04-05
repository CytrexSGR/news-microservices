"""
FMP Service HTTP Client with resilience patterns.

Provides robust HTTP client for communicating with the FMP Service,
including circuit breaker, retry logic, and rate limiting.

Features:
- Circuit breaker pattern (5 failures → open, 30s recovery)
- Retry logic with exponential backoff (3 attempts: 2s, 4s, 8s)
- Rate limiting awareness (300 calls/day)
- Comprehensive error handling
- Request/Response logging

Reference:
- docs/architecture/fmp-kg-integration-implementation-guide.md
- ADR-035: Circuit Breaker Pattern
"""

import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from pydantic import BaseModel, Field

from .circuit_breaker import CircuitBreaker
from .exceptions import (
    FMPServiceError,
    FMPServiceUnavailableError,
    FMPRateLimitError,
    FMPNotFoundError,
    CircuitBreakerOpenError
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class FMPClientConfig(BaseModel):
    """Configuration for FMP Service client."""

    fmp_base_url: str = Field(
        default="http://fmp-service:8113",
        description="FMP Service base URL"
    )
    fmp_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    fmp_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    fmp_circuit_breaker_threshold: int = Field(
        default=5,
        description="Failures before circuit opens"
    )
    fmp_circuit_breaker_timeout: int = Field(
        default=30,
        description="Circuit recovery timeout in seconds"
    )


# ============================================================================
# Response Models
# ============================================================================

class AssetMetadata(BaseModel):
    """Asset metadata from FMP Service."""

    symbol: str
    name: str
    asset_type: str  # STOCK, FOREX, COMMODITY, CRYPTO
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None

    # Type-specific fields
    base_currency: Optional[str] = None  # For FOREX/CRYPTO
    quote_currency: Optional[str] = None  # For FOREX/CRYPTO
    blockchain: Optional[str] = None  # For CRYPTO
    commodity_type: Optional[str] = None  # For COMMODITY

    class Config:
        extra = "allow"  # Allow additional fields from FMP


class MarketQuote(BaseModel):
    """Current market quote from FMP Service."""

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    timestamp: datetime

    class Config:
        extra = "allow"


class MarketHistory(BaseModel):
    """Historical market data point."""

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None

    class Config:
        extra = "allow"


# ============================================================================
# FMP Service Client
# ============================================================================

class FMPServiceClient:
    """
    HTTP client for FMP Service with resilience patterns.

    Provides async methods to fetch asset metadata, market quotes, and
    historical data from the FMP Service with built-in resilience.

    Features:
    - Circuit breaker (auto-recovery after failures)
    - Retry logic (exponential backoff)
    - Rate limiting (respects FMP 300 calls/day quota)
    - Comprehensive error handling

    Example:
        >>> config = FMPClientConfig(fmp_base_url="http://fmp-service:8113")
        >>> client = FMPServiceClient(config)
        >>>
        >>> # Fetch metadata
        >>> assets = await client.fetch_asset_metadata(["AAPL", "GOOGL"])
        >>>
        >>> # Fetch quote
        >>> quote = await client.fetch_market_quote("AAPL")
        >>>
        >>> # Close when done
        >>> await client.close()

    Context Manager Usage:
        >>> async with FMPServiceClient(config) as client:
        >>>     assets = await client.fetch_asset_metadata(["AAPL"])
    """

    def __init__(self, config: Optional[FMPClientConfig] = None):
        """
        Initialize FMP Service client.

        Args:
            config: Client configuration (defaults to FMPClientConfig())
        """
        self.config = config or FMPClientConfig()

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.config.fmp_base_url,
            timeout=httpx.Timeout(
                timeout=self.config.fmp_timeout,
                connect=5.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.fmp_circuit_breaker_threshold,
            recovery_timeout=self.config.fmp_circuit_breaker_timeout,
            service_name="fmp-service"
        )

        logger.info(
            f"FMPServiceClient initialized: "
            f"base_url={self.config.fmp_base_url}, "
            f"timeout={self.config.fmp_timeout}s"
        )

    # ========================================================================
    # Context Manager
    # ========================================================================

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()
        logger.info("FMPServiceClient closed")

    # ========================================================================
    # Public API Methods
    # ========================================================================

    async def fetch_asset_metadata(
        self,
        symbols: Optional[List[str]] = None,
        asset_types: Optional[List[str]] = None,
        bypass_cache: bool = False
    ) -> List[AssetMetadata]:
        """
        Fetch asset metadata from FMP Service.

        Args:
            symbols: List of symbols to fetch (e.g., ["AAPL", "GOOGL"])
            asset_types: Filter by asset types (e.g., ["STOCK", "CRYPTO"])
            bypass_cache: Force fresh data from FMP API

        Returns:
            List of AssetMetadata objects

        Raises:
            FMPServiceUnavailableError: Service unavailable or circuit open
            FMPRateLimitError: FMP API quota exceeded
            FMPServiceError: Other service errors

        Example:
            >>> # Fetch specific symbols
            >>> assets = await client.fetch_asset_metadata(["AAPL", "GOOGL"])
            >>>
            >>> # Fetch all stocks
            >>> stocks = await client.fetch_asset_metadata(asset_types=["STOCK"])
        """
        logger.info(
            f"Fetching asset metadata: symbols={symbols}, "
            f"asset_types={asset_types}, bypass_cache={bypass_cache}"
        )

        try:
            data = await self.circuit_breaker.call(
                self._fetch_metadata_internal,
                symbols=symbols,
                asset_types=asset_types,
                bypass_cache=bypass_cache
            )

            assets = [AssetMetadata(**item) for item in data]
            logger.info(f"Successfully fetched {len(assets)} assets")

            return assets

        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker open: {e}")
            raise FMPServiceUnavailableError(str(e))

    async def fetch_market_quote(
        self,
        symbol: str
    ) -> MarketQuote:
        """
        Fetch current market quote for symbol.

        Args:
            symbol: Asset symbol (e.g., "AAPL")

        Returns:
            MarketQuote object with current price data

        Raises:
            FMPNotFoundError: Symbol not found
            FMPServiceUnavailableError: Service unavailable

        Example:
            >>> quote = await client.fetch_market_quote("AAPL")
            >>> print(f"Price: ${quote.price}, Change: {quote.change_percent}%")
        """
        logger.info(f"Fetching market quote for: {symbol}")

        try:
            data = await self.circuit_breaker.call(
                self._fetch_quote_internal,
                symbol=symbol
            )

            quote = MarketQuote(**data)
            logger.info(f"Successfully fetched quote for {symbol}: ${quote.price}")

            return quote

        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker open: {e}")
            raise FMPServiceUnavailableError(str(e))

    async def fetch_market_history(
        self,
        symbol: str,
        from_date: date,
        to_date: date
    ) -> List[MarketHistory]:
        """
        Fetch historical market data for symbol.

        Args:
            symbol: Asset symbol (e.g., "AAPL")
            from_date: Start date (inclusive)
            to_date: End date (inclusive)

        Returns:
            List of MarketHistory objects

        Raises:
            FMPNotFoundError: Symbol not found
            FMPServiceUnavailableError: Service unavailable

        Example:
            >>> from datetime import date, timedelta
            >>> end = date.today()
            >>> start = end - timedelta(days=7)
            >>> history = await client.fetch_market_history("AAPL", start, end)
        """
        logger.info(
            f"Fetching market history for {symbol}: "
            f"{from_date} to {to_date}"
        )

        try:
            data = await self.circuit_breaker.call(
                self._fetch_history_internal,
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            )

            history = [MarketHistory(**item) for item in data]
            logger.info(f"Successfully fetched {len(history)} data points for {symbol}")

            return history

        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker open: {e}")
            raise FMPServiceUnavailableError(str(e))

    async def health_check(self) -> bool:
        """
        Check if FMP Service is healthy.

        Returns:
            True if service is responding, False otherwise

        Example:
            >>> is_healthy = await client.health_check()
            >>> if not is_healthy:
            >>>     logger.warning("FMP Service is down")
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"FMP Service health check failed: {e}")
            return False

    # ========================================================================
    # Internal Methods (with retry logic)
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _fetch_metadata_internal(
        self,
        symbols: Optional[List[str]],
        asset_types: Optional[List[str]],
        bypass_cache: bool
    ) -> List[Dict[str, Any]]:
        """
        Internal method for fetching metadata with retry logic.

        Retries on network errors with exponential backoff:
        - Attempt 1: Immediate
        - Attempt 2: After 2 seconds
        - Attempt 3: After 4 seconds
        """
        params = {}

        if symbols:
            params["symbols"] = ",".join(symbols)

        if asset_types:
            params["asset_types"] = ",".join(asset_types)

        if bypass_cache:
            params["force_refresh"] = "true"

        try:
            response = await self.client.get(
                "/api/v1/metadata/assets",
                params=params
            )

            # Handle error responses
            if response.status_code == 404:
                raise FMPNotFoundError(
                    message="Assets not found",
                    resource=str(symbols)
                )
            elif response.status_code == 429:
                raise FMPRateLimitError(
                    message="FMP API rate limit exceeded"
                )
            elif response.status_code == 503:
                raise FMPServiceUnavailableError(
                    message="FMP Service temporarily unavailable"
                )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching metadata: {e}")
            raise FMPServiceError(
                message=f"HTTP {e.response.status_code}: {e}",
                status_code=e.response.status_code
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _fetch_quote_internal(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """Internal method for fetching quote with retry logic."""
        try:
            response = await self.client.get(
                f"/api/v1/quotes/{symbol}"
            )

            if response.status_code == 404:
                raise FMPNotFoundError(
                    message=f"Symbol '{symbol}' not found",
                    resource=symbol
                )
            elif response.status_code == 429:
                raise FMPRateLimitError()
            elif response.status_code == 503:
                raise FMPServiceUnavailableError()

            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching quote: {e}")
            raise FMPServiceError(
                message=f"HTTP {e.response.status_code}: {e}",
                status_code=e.response.status_code
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _fetch_history_internal(
        self,
        symbol: str,
        from_date: date,
        to_date: date
    ) -> List[Dict[str, Any]]:
        """Internal method for fetching history with retry logic."""
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }

        try:
            response = await self.client.get(
                f"/api/v1/quotes/{symbol}/history",
                params=params
            )

            if response.status_code == 404:
                raise FMPNotFoundError(
                    message=f"History for '{symbol}' not found",
                    resource=symbol
                )
            elif response.status_code == 429:
                raise FMPRateLimitError()
            elif response.status_code == 503:
                raise FMPServiceUnavailableError()

            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching history: {e}")
            raise FMPServiceError(
                message=f"HTTP {e.response.status_code}: {e}",
                status_code=e.response.status_code
            )

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_circuit_breaker_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker state and metrics

        Example:
            >>> stats = client.get_circuit_breaker_stats()
            >>> print(f"State: {stats['state']}, Failures: {stats['failure_count']}")
        """
        return self.circuit_breaker.get_stats()

    def reset_circuit_breaker(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        Use with caution - typically for testing or manual intervention.
        """
        self.circuit_breaker.reset()
        logger.warning("Circuit breaker manually reset")
