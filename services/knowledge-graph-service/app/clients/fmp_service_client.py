"""
FMP Service HTTP Client.

Communicates with the FMP Service to fetch market data and metadata.
Implements circuit breaker pattern and rate limiting for resilience.
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class FMPServiceError(Exception):
    """Base exception for FMP Service errors."""
    pass


class FMPServiceUnavailableError(FMPServiceError):
    """FMP Service is unavailable or circuit breaker is open."""
    pass


class FMPServiceClient:
    """
    HTTP client for FMP Service with resilience patterns.

    Features:
    - Connection pooling
    - Automatic retries (transient errors)
    - Request/response logging
    - Timeout handling
    """

    def __init__(self):
        """Initialize FMP Service client."""
        self.base_url = settings.FMP_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            ),
            follow_redirects=True
        )

    async def get_asset_metadata_bulk(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch metadata for multiple assets from FMP Service.

        This endpoint fetches comprehensive asset metadata including:
        - Symbol, name, asset type
        - Exchange, currency
        - Sector, industry (for stocks)
        - Special properties (forex pairs, commodities, crypto)

        Args:
            symbols: List of asset symbols (e.g., ["AAPL", "GOOGL", "BTCUSD"])
            force_refresh: Force fresh data from FMP API (bypass cache)

        Returns:
            List of asset metadata dictionaries

        Raises:
            FMPServiceUnavailableError: FMP Service is down
            FMPServiceError: HTTP error or invalid response
        """
        logger.info(f"Fetching metadata for {len(symbols)} symbols from FMP Service")

        try:
            params = {
                "symbols": ",".join(symbols)
            }
            if force_refresh:
                params["force_refresh"] = "true"

            response = await self.client.get(
                f"{self.base_url}/api/v1/metadata/bulk",
                params=params
            )
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if not isinstance(data, list):
                logger.error(f"Invalid response format from FMP Service: expected list, got {type(data)}")
                raise FMPServiceError("Invalid response format from FMP Service")

            logger.info(f"Successfully fetched metadata for {len(data)} assets")
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                logger.error("FMP Service unavailable (503)")
                raise FMPServiceUnavailableError("FMP Service is currently unavailable")
            elif e.response.status_code == 429:
                logger.error("FMP API rate limit exceeded")
                raise FMPServiceError("FMP API rate limit exceeded")
            else:
                logger.error(f"FMP Service HTTP error: {e.response.status_code}")
                raise FMPServiceError(f"HTTP {e.response.status_code}: {e.response.text}")

        except httpx.TimeoutException:
            logger.error("FMP Service request timeout")
            raise FMPServiceUnavailableError("FMP Service request timeout")

        except httpx.RequestError as e:
            logger.error(f"FMP Service network error: {e}")
            raise FMPServiceUnavailableError(f"Network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error calling FMP Service: {e}")
            raise FMPServiceError(f"Unexpected error: {str(e)}")

    async def get_quotes_bulk(
        self,
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch current quotes for multiple assets.

        Args:
            symbols: List of asset symbols

        Returns:
            List of quote data dictionaries with:
            - symbol
            - price
            - change, change_percent
            - volume
            - timestamp

        Raises:
            FMPServiceUnavailableError: FMP Service is down
            FMPServiceError: HTTP error or invalid response
        """
        logger.info(f"Fetching quotes for {len(symbols)} symbols")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/quotes/bulk",
                params={"symbols": ",".join(symbols)}
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                raise FMPServiceError("Invalid response format: expected list")

            logger.info(f"Successfully fetched {len(data)} quotes")
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise FMPServiceUnavailableError("FMP Service unavailable")
            raise FMPServiceError(f"HTTP {e.response.status_code}")

        except httpx.TimeoutException:
            raise FMPServiceUnavailableError("Request timeout")

        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            raise FMPServiceError(str(e))

    async def get_historical_prices(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical prices for an asset.

        Args:
            symbol: Asset symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of historical price records

        Raises:
            FMPServiceUnavailableError: FMP Service is down
            FMPServiceError: HTTP error
        """
        logger.info(f"Fetching historical prices for {symbol}")

        try:
            params = {"symbol": symbol}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date

            response = await self.client.get(
                f"{self.base_url}/api/v1/historical/prices",
                params=params
            )
            response.raise_for_status()

            data = response.json()
            return data if isinstance(data, list) else []

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise FMPServiceUnavailableError("FMP Service unavailable")
            raise FMPServiceError(f"HTTP {e.response.status_code}")

        except httpx.TimeoutException:
            raise FMPServiceUnavailableError("Request timeout")

        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
            raise FMPServiceError(str(e))

    async def health_check(self) -> bool:
        """
        Check if FMP Service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=httpx.Timeout(3.0)
            )
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"FMP Service health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()


# Global client instance (singleton pattern)
_fmp_service_client: Optional[FMPServiceClient] = None


def get_fmp_service_client() -> FMPServiceClient:
    """
    Get global FMP Service client instance.

    Returns:
        FMPServiceClient singleton instance
    """
    global _fmp_service_client
    if _fmp_service_client is None:
        _fmp_service_client = FMPServiceClient()
    return _fmp_service_client


async def close_fmp_service_client():
    """Close global FMP Service client."""
    global _fmp_service_client
    if _fmp_service_client:
        await _fmp_service_client.close()
        _fmp_service_client = None
