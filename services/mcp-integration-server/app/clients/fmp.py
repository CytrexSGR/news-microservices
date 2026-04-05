"""HTTP client for FMP (Financial Market Provider) service."""

import logging
from typing import Dict, Any, List, Optional

from ..config import settings
from .base import BaseClient, CircuitBreakerOpenError
from .symbol_aliases import resolve_symbol_alias

logger = logging.getLogger(__name__)


class FMPClient(BaseClient):
    """Client for FMP service (Port 8113)."""

    def __init__(self):
        super().__init__(
            name="fmp-service",
            base_url=settings.fmp_service_url,
            timeout=30.0,
        )

    # =========================================================================
    # Market Data
    # =========================================================================

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get current market quote for symbol.

        Args:
            symbol: Asset symbol (e.g., BTCUSD, AAPL, GOLD)
                   Supports human-readable aliases: GOLD->GCUSD, OIL->CLUSD

        Returns:
            Quote data with price, volume, change
        """
        # Resolve human-readable aliases to FMP symbols
        resolved_symbol = resolve_symbol_alias(symbol)

        response = await self.get(f"/api/v1/market/quotes/{resolved_symbol}")
        response.raise_for_status()
        return response.json()

    async def get_quotes_batch(
        self, symbols: List[str], asset_type: str
    ) -> Dict[str, Any]:
        """
        Get quotes for multiple symbols.

        Args:
            symbols: List of asset symbols
            asset_type: Asset type (crypto, forex, indices, commodities)

        Returns:
            Dict of symbol -> quote data
        """
        response = await self.get(
            "/api/v1/market/quotes",
            params={"symbols": ",".join(symbols), "asset_type": asset_type}
        )
        response.raise_for_status()
        return response.json()

    async def get_candles(
        self,
        symbol: str,
        interval: str = "1hour",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get OHLCV candles for symbol.

        Args:
            symbol: Asset symbol
            interval: Candle interval (1min, 5min, 15min, 30min, 1hour, 4hour)
            limit: Max candles to return

        Returns:
            OHLCV candle data
        """
        response = await self.get(
            f"/api/v1/market/candles/{symbol}",
            params={"interval": interval, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_candles_timerange(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1hour",
    ) -> Dict[str, Any]:
        """
        Get OHLCV candles for time range.

        Args:
            symbol: Asset symbol
            start: Start datetime (ISO format)
            end: End datetime (ISO format)
            interval: Candle interval (1min, 5min, 15min, 30min, 1hour, 4hour)

        Returns:
            OHLCV candle data for range
        """
        response = await self.get(
            f"/api/v1/market/candles/{symbol}/timerange",
            params={"start": start, "end": end, "interval": interval}
        )
        response.raise_for_status()
        return response.json()

    async def get_latest_candle(self, symbol: str, interval: str = "1hour") -> Dict[str, Any]:
        """
        Get latest candle for symbol.

        Args:
            symbol: Asset symbol
            interval: Candle interval (1min, 5min, 15min, 30min, 1hour, 4hour)

        Returns:
            Latest candle data
        """
        response = await self.get(
            f"/api/v1/market/candles/{symbol}/latest",
            params={"interval": interval}
        )
        response.raise_for_status()
        return response.json()

    async def get_market_status(self) -> Dict[str, Any]:
        """Get market status (open/closed for each market)."""
        response = await self.get("/api/v1/market/status")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Symbols & Metadata
    # =========================================================================

    async def list_symbols(
        self,
        asset_type: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List available symbols.

        Args:
            asset_type: Filter by asset type (crypto, stock, forex)
            limit: Max symbols to return

        Returns:
            List of symbols with metadata
        """
        params = {"limit": limit}
        if asset_type:
            params["asset_type"] = asset_type

        response = await self.get("/api/v1/market/symbols/list", params=params)
        response.raise_for_status()
        return response.json()

    async def search_symbols(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search for symbols by name or ticker.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Matching symbols
        """
        response = await self.get(
            "/api/v1/market/symbols/search",
            params={"q": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_asset_metadata(self, symbol: str) -> Dict[str, Any]:
        """
        Get metadata for asset.

        Args:
            symbol: Asset symbol

        Returns:
            Asset metadata (name, type, exchange, etc.)
        """
        response = await self.get(f"/api/v1/metadata/assets/{symbol}")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # News
    # =========================================================================

    async def get_news(
        self,
        limit: int = 20,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get financial news.

        Args:
            limit: Max articles
            symbol: Optional symbol filter

        Returns:
            News articles
        """
        if symbol:
            response = await self.get(
                f"/api/v1/news/by-symbol/{symbol}",
                params={"limit": limit}
            )
        else:
            response = await self.get("/api/v1/news", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    async def get_news_by_sentiment(
        self,
        sentiment: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get news filtered by sentiment.

        Args:
            sentiment: Sentiment filter (positive, negative, neutral)
            limit: Max articles

        Returns:
            News articles with matching sentiment
        """
        response = await self.get(
            f"/api/v1/news/sentiment/{sentiment}",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Macro Indicators
    # =========================================================================

    async def get_macro_indicators(self) -> Dict[str, Any]:
        """Get list of available macro economic indicators."""
        response = await self.get("/api/v1/macro/indicators")
        response.raise_for_status()
        return response.json()

    async def get_macro_indicator(self, indicator_name: str) -> Dict[str, Any]:
        """
        Get macro indicator data.

        Args:
            indicator_name: Indicator name (e.g., GDP, CPI, UNEMPLOYMENT)

        Returns:
            Indicator data with history
        """
        response = await self.get(f"/api/v1/macro/indicators/{indicator_name}")
        response.raise_for_status()
        return response.json()

    async def get_latest_macro(self) -> Dict[str, Any]:
        """Get latest values for all macro indicators."""
        response = await self.get("/api/v1/macro/latest")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Earnings
    # =========================================================================

    async def get_earnings_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get earnings calendar.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Earnings events
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = await self.get("/api/v1/earnings/calendar", params=params)
        response.raise_for_status()
        return response.json()

    async def get_earnings_history(self, symbol: str) -> Dict[str, Any]:
        """
        Get earnings history for symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Historical earnings data
        """
        response = await self.get(f"/api/v1/earnings/{symbol}/history")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Data Management
    # =========================================================================

    async def get_data_availability(self) -> Dict[str, Any]:
        """Get data availability overview."""
        response = await self.get("/api/v1/data-management/availability")
        response.raise_for_status()
        return response.json()

    async def get_data_inventory(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data inventory.

        Args:
            symbol: Optional symbol filter

        Returns:
            Data inventory with counts and date ranges
        """
        if symbol:
            response = await self.get(f"/api/v1/data-management/inventory/{symbol}")
        else:
            response = await self.get("/api/v1/data-management/inventory")
        response.raise_for_status()
        return response.json()

    async def get_data_gaps(self, symbol: str) -> Dict[str, Any]:
        """
        Get data gaps for symbol.

        Args:
            symbol: Asset symbol

        Returns:
            List of data gaps
        """
        response = await self.get(f"/api/v1/data-management/gaps/{symbol}")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # System
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check FMP service health."""
        response = await self.get("/api/v1/system/health")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # ETF Reference Data
    # =========================================================================

    async def search_etfs(
        self,
        sector: Optional[str] = None,
        theme: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search ETFs by sector, theme, or keyword.

        Args:
            sector: Filter by sector (Defense, Tech, Healthcare, etc.)
            theme: Filter by theme (AI, Rare Earth, NATO/Military, etc.)
            search: Full-text search in name/ticker/ISIN
            limit: Maximum results (default: 20)

        Returns:
            ETF search results with metadata
        """
        params = {"limit": limit}
        if sector:
            params["sector"] = sector
        if theme:
            params["theme"] = theme
        if search:
            params["search"] = search

        response = await self.get("/api/v1/etfs", params=params)
        response.raise_for_status()
        return response.json()

    async def get_etf(self, isin: str) -> Dict[str, Any]:
        """
        Get ETF details by ISIN.

        Args:
            isin: ISIN identifier (e.g., IE000YYE6WK5)

        Returns:
            ETF details including holdings and performance
        """
        response = await self.get(f"/api/v1/etfs/{isin}")
        response.raise_for_status()
        return response.json()
