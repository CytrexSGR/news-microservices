"""
Market Sync Service.

Orchestrates syncing market data from FMP Service to Neo4j Knowledge Graph.
Implements idempotent MERGE operations and batch processing.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.clients.fmp_service_client import get_fmp_service_client, FMPServiceError
from app.services.neo4j_service import neo4j_service
from app.schemas.sync_results import SyncResult, SyncError, QuoteUpdateResult, SectorSyncResult
from app.config import settings

logger = logging.getLogger(__name__)


# Default asset list (40 assets across 4 types)
DEFAULT_ASSETS = {
    "STOCK": [
        "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
        "META", "NVDA", "JPM", "V", "WMT"
    ],
    "FOREX": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
    ],
    "COMMODITY": [
        "GCUSD", "SIUSD", "CLUSD", "NGUSD", "HGUSD",
        "ZCUSX", "WTUSD", "SBUSD", "KCUSX", "CTUSD"
    ],
    "CRYPTO": [
        "BTCUSD", "ETHUSD", "BNBUSD", "XRPUSD", "ADAUSD",
        "SOLUSD", "DOTUSD", "MATICUSD", "LINKUSD", "AVAXUSD"
    ]
}

# Sector mapping: sector name -> sector code
SECTOR_MAPPING = {
    "Technology": "TECH",
    "Financials": "FINANCE",
    "Healthcare": "HEALTHCARE",
    "Energy": "ENERGY",
    "Consumer Discretionary": "CONSUMER_DISC",
    "Consumer Staples": "CONSUMER_STAPLES",
    "Industrials": "INDUSTRIALS",
    "Materials": "MATERIALS",
    "Utilities": "UTILITIES",
    "Real Estate": "REAL_ESTATE",
    "Telecommunication Services": "TELECOM",
    # Asset-type specific sectors
    "FOREX": "FOREX",
    "COMMODITY": "COMMODITY",
    "CRYPTO": "CRYPTO"
}

# 14 standard sectors (11 GICS + 3 asset-specific)
STANDARD_SECTORS = [
    {"code": "TECH", "name": "Technology", "system": "GICS"},
    {"code": "FINANCE", "name": "Financials", "system": "GICS"},
    {"code": "HEALTHCARE", "name": "Healthcare", "system": "GICS"},
    {"code": "ENERGY", "name": "Energy", "system": "GICS"},
    {"code": "CONSUMER_DISC", "name": "Consumer Discretionary", "system": "GICS"},
    {"code": "CONSUMER_STAPLES", "name": "Consumer Staples", "system": "GICS"},
    {"code": "INDUSTRIALS", "name": "Industrials", "system": "GICS"},
    {"code": "MATERIALS", "name": "Materials", "system": "GICS"},
    {"code": "UTILITIES", "name": "Utilities", "system": "GICS"},
    {"code": "REAL_ESTATE", "name": "Real Estate", "system": "GICS"},
    {"code": "TELECOM", "name": "Telecommunication Services", "system": "GICS"},
    {"code": "FOREX", "name": "Foreign Exchange", "system": "FMP"},
    {"code": "COMMODITY", "name": "Commodities", "system": "FMP"},
    {"code": "CRYPTO", "name": "Cryptocurrency", "system": "FMP"},
]


class MarketSyncService:
    """
    Market Sync Service.

    Orchestrates fetching FMP data and syncing to Neo4j with:
    - Idempotent MERGE operations
    - Batch processing
    - Partial failure tolerance
    - Comprehensive error tracking
    """

    def __init__(self):
        """Initialize Market Sync Service."""
        self.fmp_client = get_fmp_service_client()

    async def sync_all_markets(
        self,
        symbols: Optional[List[str]] = None,
        asset_types: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> SyncResult:
        """
        Sync all markets from FMP Service to Neo4j.

        Args:
            symbols: Specific symbols to sync (overrides asset_types)
            asset_types: Asset types to sync (STOCK, FOREX, COMMODITY, CRYPTO)
            force_refresh: Force fresh data from FMP API (bypass cache)

        Returns:
            SyncResult with statistics and errors
        """
        sync_id = self._generate_sync_id()
        start_time = datetime.utcnow()

        logger.info(f"Starting market sync: {sync_id}")

        # Determine which symbols to sync
        symbols_to_sync = symbols or self._get_default_symbols(asset_types)
        total_assets = len(symbols_to_sync)

        # Initialize metrics
        synced = 0
        failed = 0
        nodes_created = 0
        nodes_updated = 0
        relationships_created = 0
        relationships_updated = 0
        errors = []

        # Fetch metadata from FMP Service
        try:
            logger.info(f"Fetching metadata for {total_assets} symbols")
            metadata_list = await self.fmp_client.get_asset_metadata_bulk(
                symbols_to_sync,
                force_refresh=force_refresh
            )
            logger.info(f"Received metadata for {len(metadata_list)} assets")

        except FMPServiceError as e:
            # Total failure - FMP Service unavailable
            logger.error(f"FMP Service error: {e}")
            duration_seconds = (datetime.utcnow() - start_time).total_seconds()

            return SyncResult(
                sync_id=sync_id,
                status="failed",
                total_assets=total_assets,
                synced=0,
                failed=total_assets,
                nodes_created=0,
                nodes_updated=0,
                relationships_created=0,
                relationships_updated=0,
                duration_seconds=duration_seconds,
                fmp_api_calls_used=0,
                errors=[SyncError(symbol="ALL", error=str(e))],
                timestamp=datetime.utcnow()
            )

        # Sync each asset to Neo4j (partial failure tolerance)
        for metadata in metadata_list:
            symbol = metadata.get("symbol", "UNKNOWN")

            try:
                result = await self._sync_single_asset(metadata)

                synced += 1
                nodes_created += result["nodes_created"]
                nodes_updated += result["nodes_updated"]
                relationships_created += result["relationships_created"]
                relationships_updated += result["relationships_updated"]

                logger.debug(f"Synced {symbol}: created={result['nodes_created']}, updated={result['nodes_updated']}")

            except Exception as e:
                failed += 1
                error_msg = f"Failed to sync {symbol}: {str(e)}"
                logger.error(error_msg)
                errors.append(SyncError(symbol=symbol, error=str(e)))

        # Calculate metrics
        duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        status = self._determine_status(synced, failed)

        logger.info(
            f"Sync complete: {sync_id}, "
            f"synced={synced}/{total_assets}, "
            f"failed={failed}, "
            f"duration={duration_seconds:.2f}s"
        )

        return SyncResult(
            sync_id=sync_id,
            status=status,
            total_assets=total_assets,
            synced=synced,
            failed=failed,
            nodes_created=nodes_created,
            nodes_updated=nodes_updated,
            relationships_created=relationships_created,
            relationships_updated=relationships_updated,
            duration_seconds=duration_seconds,
            fmp_api_calls_used=1,  # Bulk metadata fetch
            errors=errors,
            timestamp=datetime.utcnow()
        )

    async def sync_market_quotes(
        self,
        symbols: List[str]
    ) -> QuoteUpdateResult:
        """
        Sync current quotes (prices) for specified symbols.

        Updates price fields in existing MARKET nodes.

        Args:
            symbols: List of symbols to update

        Returns:
            QuoteUpdateResult with update statistics
        """
        start_time = datetime.utcnow()

        logger.info(f"Updating quotes for {len(symbols)} symbols")

        # Fetch quotes from FMP Service
        try:
            quotes = await self.fmp_client.get_quotes_bulk(symbols)
        except FMPServiceError as e:
            logger.error(f"Failed to fetch quotes: {e}")
            return QuoteUpdateResult(
                symbols_requested=symbols,
                symbols_updated=0,
                symbols_failed=len(symbols),
                errors=[SyncError(symbol="ALL", error=str(e))],
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )

        # Update prices in Neo4j
        updated = 0
        failed = 0
        errors = []

        for quote in quotes:
            symbol = quote.get("symbol")
            price = quote.get("price")

            if not symbol or price is None:
                continue

            try:
                # Update MARKET node price
                cypher = """
                MATCH (m:MARKET {symbol: $symbol})
                SET m.current_price = $price,
                    m.last_updated = datetime()
                RETURN m
                """

                result = await neo4j_service.execute_write(
                    cypher,
                    {"symbol": symbol, "price": price}
                )

                if result.get("properties_set", 0) > 0:
                    updated += 1
                else:
                    failed += 1
                    errors.append(SyncError(symbol=symbol, error="Node not found"))

            except Exception as e:
                failed += 1
                errors.append(SyncError(symbol=symbol, error=str(e)))

        duration_seconds = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"Quote update complete: updated={updated}, failed={failed}")

        return QuoteUpdateResult(
            symbols_requested=symbols,
            symbols_updated=updated,
            symbols_failed=failed,
            errors=errors,
            duration_seconds=duration_seconds,
            timestamp=datetime.utcnow()
        )

    async def sync_single_market(
        self,
        market_data: Dict[str, Any]
    ) -> bool:
        """
        Sync single market to Neo4j.

        Used by event consumer to sync individual market updates.

        Args:
            market_data: Market data dict with symbol, name, asset_type, etc.

        Returns:
            True if sync successful (regardless of changes made), False on error
        """
        try:
            result = await self._sync_single_asset(market_data)
            symbol = market_data.get('symbol')

            # Log based on what happened
            if result["nodes_created"] > 0 or result["nodes_updated"] > 0:
                logger.info(
                    f"Synced {symbol}: "
                    f"created={result['nodes_created']}, "
                    f"updated={result['nodes_updated']}"
                )
            else:
                logger.debug(f"No changes for {symbol} (already synced)")

            # Success regardless of whether changes were made
            return True

        except Exception as e:
            logger.error(f"Failed to sync single market {market_data.get('symbol')}: {e}", exc_info=True)
            return False

    async def sync_sectors(self) -> SectorSyncResult:
        """
        Ensure all 14 standard SECTOR nodes exist in Neo4j.

        Creates missing sectors using idempotent MERGE.

        Returns:
            SectorSyncResult with sector count and statistics
        """
        start_time = datetime.utcnow()

        logger.info("Syncing SECTOR nodes to Neo4j")

        created = 0
        verified = 0
        sector_codes = []

        for sector in STANDARD_SECTORS:
            try:
                # Idempotent MERGE operation
                cypher = """
                MERGE (s:SECTOR {sector_code: $code})
                ON CREATE SET
                    s.sector_name = $name,
                    s.classification_system = $system,
                    s.created_at = datetime(),
                    s.updated_at = datetime()
                ON MATCH SET
                    s.updated_at = datetime()
                RETURN
                    CASE WHEN s.created_at = datetime() THEN 1 ELSE 0 END AS was_created
                """

                result = await neo4j_service.execute_query(
                    cypher,
                    {
                        "code": sector["code"],
                        "name": sector["name"],
                        "system": sector["system"]
                    }
                )

                sector_codes.append(sector["code"])

                if result and result[0].get("was_created", 0) == 1:
                    created += 1
                    logger.debug(f"Created SECTOR: {sector['code']}")
                else:
                    verified += 1

            except Exception as e:
                logger.error(f"Failed to sync sector {sector['code']}: {e}")

        duration_seconds = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Sector sync complete: created={created}, verified={verified}, total={len(sector_codes)}"
        )

        return SectorSyncResult(
            total_sectors=len(sector_codes),
            sectors_created=created,
            sectors_verified=verified,
            sector_codes=sector_codes,
            duration_seconds=duration_seconds,
            timestamp=datetime.utcnow()
        )

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    async def _sync_single_asset(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Sync single asset to Neo4j using idempotent MERGE.

        Args:
            metadata: Asset metadata from FMP Service

        Returns:
            Dict with nodes_created, nodes_updated, relationships_created, relationships_updated
        """
        symbol = metadata.get("symbol")
        name = metadata.get("name")
        asset_type = metadata.get("type") or metadata.get("asset_type", "STOCK")
        exchange = metadata.get("exchange")
        currency = metadata.get("currency", "USD")

        # Optional fields
        sector = metadata.get("sector")
        industry = metadata.get("industry")
        base_currency = metadata.get("base_currency")
        quote_currency = metadata.get("quote_currency")
        blockchain = metadata.get("blockchain")

        # Map sector to sector code
        sector_code = self._map_sector_to_code(sector, asset_type)

        # Cypher query: MERGE MARKET node and BELONGS_TO_SECTOR relationship
        cypher = """
        MERGE (m:MARKET {symbol: $symbol})
        ON CREATE SET
            m.name = $name,
            m.asset_type = $asset_type,
            m.sector = $sector,
            m.industry = $industry,
            m.exchange = $exchange,
            m.currency = $currency,
            m.is_active = true,
            m.first_seen = datetime(),
            m.data_source = 'FMP',
            m.base_currency = $base_currency,
            m.quote_currency = $quote_currency,
            m.blockchain = $blockchain,
            m.last_updated = datetime()
        ON MATCH SET
            m.name = $name,
            m.sector = $sector,
            m.industry = $industry,
            m.exchange = $exchange,
            m.currency = $currency,
            m.last_updated = datetime()

        WITH m
        MATCH (s:SECTOR {sector_code: $sector_code})
        MERGE (m)-[r:BELONGS_TO_SECTOR]->(s)
        ON CREATE SET
            r.confidence = 1.0,
            r.classification_date = datetime()
        ON MATCH SET
            r.classification_date = datetime()

        RETURN
            CASE WHEN m.first_seen = datetime() THEN 1 ELSE 0 END AS nodes_created,
            CASE WHEN m.first_seen < datetime() THEN 1 ELSE 0 END AS nodes_updated,
            1 AS relationships_checked
        """

        parameters = {
            "symbol": symbol,
            "name": name,
            "asset_type": asset_type,
            "sector": sector,
            "industry": industry,
            "exchange": exchange,
            "currency": currency,
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "blockchain": blockchain,
            "sector_code": sector_code
        }

        result = await neo4j_service.execute_query(cypher, parameters)

        # Parse result
        if result and len(result) > 0:
            record = result[0]
            return {
                "nodes_created": record.get("nodes_created", 0),
                "nodes_updated": record.get("nodes_updated", 0),
                "relationships_created": 1,  # BELONGS_TO_SECTOR always created/matched
                "relationships_updated": 0
            }

        return {
            "nodes_created": 0,
            "nodes_updated": 0,
            "relationships_created": 0,
            "relationships_updated": 0
        }

    def _map_sector_to_code(
        self,
        sector: Optional[str],
        asset_type: str
    ) -> str:
        """
        Map sector name to sector code.

        Args:
            sector: Sector name (e.g., "Technology")
            asset_type: Asset type (STOCK, FOREX, COMMODITY, CRYPTO)

        Returns:
            Sector code (e.g., "TECH")
        """
        # Asset-specific sectors
        if asset_type in ["FOREX", "COMMODITY", "CRYPTO"]:
            return asset_type

        # Stock sectors
        if sector and sector in SECTOR_MAPPING:
            return SECTOR_MAPPING[sector]

        # Default fallback
        return "TECH"

    def _get_default_symbols(
        self,
        asset_types: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get default symbols to sync based on asset types.

        Args:
            asset_types: List of asset types (STOCK, FOREX, COMMODITY, CRYPTO)

        Returns:
            List of symbols
        """
        if not asset_types:
            asset_types = ["STOCK", "FOREX", "COMMODITY", "CRYPTO"]

        symbols = []
        for asset_type in asset_types:
            symbols.extend(DEFAULT_ASSETS.get(asset_type, []))

        return symbols

    def _generate_sync_id(self) -> str:
        """Generate unique sync operation ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"sync_{timestamp}_{short_uuid}"

    def _determine_status(
        self,
        synced: int,
        failed: int
    ) -> str:
        """
        Determine overall sync status.

        Args:
            synced: Number of successfully synced assets
            failed: Number of failed assets

        Returns:
            Status string: "completed", "partial", "failed"
        """
        if failed == 0:
            return "completed"
        elif synced == 0:
            return "failed"
        else:
            return "partial"
