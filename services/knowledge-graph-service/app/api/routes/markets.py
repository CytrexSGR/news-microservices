"""
Market Integration API Endpoints.

Provides REST API for syncing and querying financial market data
from FMP Service to Neo4j Knowledge Graph.

Endpoints:
- POST /api/v1/graph/markets/sync - Trigger market sync
- GET /api/v1/graph/markets - List markets with filters
- GET /api/v1/graph/markets/{symbol} - Get market details
- GET /api/v1/graph/markets/{symbol}/history - Get historical prices
- GET /api/v1/graph/markets/stats - Get market statistics
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.services.fmp_integration.market_sync_service import MarketSyncService
from app.services.neo4j_service import neo4j_service
from app.clients.fmp_service_client import (
    get_fmp_service_client,
    FMPServiceError,
    FMPServiceUnavailableError
)
from app.schemas.sync_results import SyncResult
from app.schemas.markets import (
    MarketNode,
    MarketListResponse,
    MarketDetailResponse,
    MarketStatsResponse,
    SectorNode
)
from app.models.neo4j_queries import QUERIES
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Schemas
# =============================================================================

class MarketSyncRequest(BaseModel):
    """Request schema for market sync operation."""

    asset_types: Optional[List[str]] = Field(
        None,
        description="Filter to specific asset types (STOCK, FOREX, COMMODITY, CRYPTO)"
    )
    symbols: Optional[List[str]] = Field(
        None,
        description="Specific symbols to sync (overrides asset_types, max 100)",
        max_items=100
    )
    force_refresh: bool = Field(
        default=False,
        description="Force fresh data from FMP API (bypass cache)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "asset_types": ["STOCK", "FOREX"],
                "symbols": None,
                "force_refresh": False
            }
        }


class MarketHistoryPoint(BaseModel):
    """Single historical price data point."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    adj_close: Optional[float] = Field(None, description="Adjusted close price")


class MarketHistoryResponse(BaseModel):
    """Historical price data response."""

    symbol: str
    history: List[MarketHistoryPoint]
    total_records: int
    data_source: str = "FMP"


# =============================================================================
# Dependency Injection
# =============================================================================

def get_market_sync_service() -> MarketSyncService:
    """Get MarketSyncService instance."""
    return MarketSyncService()


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/api/v1/graph/markets/sync",
    response_model=SyncResult,
    status_code=200,
    summary="Sync market data from FMP Service",
    description="""
    Trigger synchronous sync of market data from FMP Service to Neo4j.

    **Operation:**
    1. Fetches asset metadata from FMP Service (HTTP GET)
    2. Creates/updates MARKET nodes in Neo4j (idempotent MERGE)
    3. Creates SECTOR nodes if needed
    4. Establishes BELONGS_TO_SECTOR relationships

    **Rate Limiting:** FMP API has 300 calls/day limit.
    This endpoint uses batch requests to minimize API usage.

    **Permissions Required:** `markets:write`
    """,
    tags=["Markets"]
)
async def sync_markets(
    request: MarketSyncRequest
) -> SyncResult:
    """
    Trigger market metadata sync from FMP Service.

    Args:
        request: MarketSyncRequest with optional filters

    Returns:
        SyncResult with sync statistics and errors

    Raises:
        HTTPException 503: FMP Service unavailable
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Internal error
    """
    start_time = time.time()

    logger.info(
        f"Market sync requested: asset_types={request.asset_types}, "
        f"symbols={request.symbols}, force_refresh={request.force_refresh}"
    )

    try:
        # Get sync service and execute
        sync_service = get_market_sync_service()

        result = await sync_service.sync_all_markets(
            symbols=request.symbols,
            asset_types=request.asset_types,
            force_refresh=request.force_refresh
        )

        # Record metrics
        query_time_seconds = time.time() - start_time
        status = 'success' if result.status in ['completed', 'partial'] else 'error'
        kg_queries_total.labels(endpoint='markets_sync', status=status).inc()
        kg_query_duration_seconds.labels(endpoint='markets_sync').observe(query_time_seconds)

        logger.info(
            f"Market sync completed: sync_id={result.sync_id}, "
            f"status={result.status}, synced={result.synced}/{result.total_assets}, "
            f"duration={result.duration_seconds:.2f}s"
        )

        return result

    except FMPServiceUnavailableError as e:
        logger.error(f"FMP Service unavailable: {e}")
        kg_queries_total.labels(endpoint='markets_sync', status='error').inc()
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FMP Service unavailable",
                "detail": str(e),
                "retry_after": 30
            }
        )

    except FMPServiceError as e:
        logger.error(f"FMP Service error: {e}")
        kg_queries_total.labels(endpoint='markets_sync', status='error').inc()

        # Check if it's a rate limit error
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "detail": str(e),
                    "sync_id": None
                }
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "FMP Service error",
                "detail": str(e)
            }
        )

    except Exception as e:
        logger.error(f"Market sync failed: {e}", exc_info=True)
        kg_queries_total.labels(endpoint='markets_sync', status='error').inc()
        raise HTTPException(
            status_code=500,
            detail=f"Market sync failed: {str(e)}"
        )


@router.get(
    "/api/v1/graph/markets",
    response_model=MarketListResponse,
    status_code=200,
    summary="Query market nodes",
    description="""
    Query MARKET nodes from Neo4j graph with optional filters.

    **Performance:** Response time < 100ms (p95)
    **Pagination:** Max 1000 results per page

    **Permissions Required:** `markets:read`
    """,
    tags=["Markets"]
)
async def get_markets(
    asset_type: Optional[str] = Query(None, description="Filter by asset type (STOCK, FOREX, COMMODITY, CRYPTO)"),
    sector: Optional[str] = Query(None, description="Filter by sector code (e.g., TECH, FINANCE)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange (e.g., NASDAQ, NYSE)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Text search on name or symbol"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page (max 1000)")
) -> MarketListResponse:
    """
    List markets with filtering and pagination.

    Args:
        asset_type: Filter by asset type
        sector: Filter by sector code
        exchange: Filter by exchange
        is_active: Filter active/inactive
        search: Text search on symbol or name
        page: Page number (0-indexed)
        page_size: Items per page

    Returns:
        MarketListResponse with paginated results

    Raises:
        HTTPException 500: Query failed
    """
    start_time = time.time()

    logger.debug(
        f"Markets query: asset_type={asset_type}, sector={sector}, "
        f"exchange={exchange}, is_active={is_active}, search={search}, "
        f"page={page}, page_size={page_size}"
    )

    try:
        # Build query parameters
        skip = page * page_size
        asset_types = [asset_type] if asset_type else None

        # Query parameters for QUERIES.list_markets
        query_params = {
            "asset_types": asset_types,
            "is_active": is_active,
            "symbol_contains": search,
            "name_contains": search,
            "skip": skip,
            "limit": page_size
        }

        # Execute query
        markets_records = await neo4j_service.execute_query(
            QUERIES.list_markets,
            parameters=query_params
        )

        # Count total
        count_records = await neo4j_service.execute_query(
            QUERIES.count_markets,
            parameters=query_params
        )
        total = count_records[0]["total"] if count_records else 0

        # Transform results
        markets = []
        for record in markets_records:
            market_data = record["m"]
            markets.append(MarketNode(**market_data))

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='markets_list', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='markets_list').observe(query_time_seconds)

        logger.debug(
            f"Markets query completed: returned {len(markets)}/{total}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return MarketListResponse(
            markets=markets,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        kg_queries_total.labels(endpoint='markets_list', status='error').inc()
        logger.error(f"Markets query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query markets: {str(e)}"
        )


@router.get(
    "/api/v1/graph/markets/stats",
    response_model=MarketStatsResponse,
    status_code=200,
    summary="Get market statistics",
    description="""
    Get overall statistics for market nodes in the graph.

    **Permissions Required:** `markets:admin`
    """,
    tags=["Markets"]
)
async def get_market_stats() -> MarketStatsResponse:
    """
    Get aggregated market statistics.

    Returns:
        MarketStatsResponse with comprehensive statistics

    Raises:
        HTTPException 500: Query failed
    """
    start_time = time.time()

    logger.debug("Market stats query")

    try:
        # Get overall stats
        stats_results = await neo4j_service.execute_query(QUERIES.get_market_stats)

        if not stats_results:
            # No data - return empty stats
            return MarketStatsResponse(
                total_markets=0,
                active_markets=0,
                markets_by_asset_type={},
                markets_by_sector={},
                total_market_cap=None,
                avg_day_change=None
            )

        stats = stats_results[0]

        # Get asset type distribution
        asset_type_results = await neo4j_service.execute_query(
            QUERIES.get_markets_by_asset_type
        )
        markets_by_asset_type = {
            str(record["asset_type"] or "UNKNOWN"): record["count"]
            for record in asset_type_results
            if record.get("asset_type") is not None
        }

        # Get sector distribution
        sector_results = await neo4j_service.execute_query(
            QUERIES.get_markets_by_sector
        )
        markets_by_sector = {
            str(record["sector_code"] or "UNKNOWN"): record["count"]
            for record in sector_results
            if record.get("sector_code") is not None
        }

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='market_stats', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='market_stats').observe(query_time_seconds)

        logger.debug(
            f"Market stats query completed: total={stats.get('total_markets')}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return MarketStatsResponse(
            total_markets=stats.get("total_markets", 0),
            active_markets=stats.get("active_markets", 0),
            markets_by_asset_type=markets_by_asset_type,
            markets_by_sector=markets_by_sector,
            total_market_cap=stats.get("total_market_cap"),
            avg_day_change=stats.get("avg_day_change")
        )

    except Exception as e:
        kg_queries_total.labels(endpoint='market_stats', status='error').inc()
        logger.error(f"Market stats query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query market statistics: {str(e)}"
        )


@router.get(
    "/api/v1/graph/markets/{symbol}",
    response_model=MarketDetailResponse,
    status_code=200,
    summary="Get market details with relationships",
    description="""
    Get detailed market data including graph relationships.

    **Returns:**
    - MARKET node properties
    - ORGANIZATION entities with TICKER relationships
    - SECTOR classifications
    - Graph statistics (connection count)

    **Performance:** < 50ms (p95)

    **Permissions Required:** `markets:read`
    """,
    tags=["Markets"]
)
async def get_market_by_symbol(
    symbol: str = Path(..., description="Market symbol (e.g., AAPL, EURUSD, GC, BTCUSD)")
) -> MarketDetailResponse:
    """
    Get detailed market information with relationships.

    Args:
        symbol: Market symbol

    Returns:
        MarketDetailResponse with market data and relationships

    Raises:
        HTTPException 404: Market not found
        HTTPException 500: Query failed
    """
    start_time = time.time()

    logger.debug(f"Market detail query: symbol={symbol}")

    try:
        # Query market with relationships
        results = await neo4j_service.execute_query(
            QUERIES.get_market_with_relationships,
            parameters={"symbol": symbol.upper()}
        )

        if not results or not results[0].get("m"):
            kg_queries_total.labels(endpoint='market_detail', status='not_found').inc()
            logger.warning(f"Market not found: {symbol}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Market not found",
                    "detail": f"No MARKET node found with symbol: {symbol}"
                }
            )

        record = results[0]
        market_data = record["m"]
        sector_data = record.get("s")
        organizations = record.get("organizations", [])

        # Build response
        market = MarketNode(**market_data)

        sector_info = None
        if sector_data:
            sector_info = SectorNode(
                code=sector_data.get("sector_code"),
                name=sector_data.get("sector_name"),
                market_classification=sector_data.get("classification_system", "GICS")
            )

        # Get related markets in same sector
        related_markets = []
        if sector_data:
            related_query = """
            MATCH (m1:MARKET {symbol: $symbol})-[:BELONGS_TO_SECTOR]->(s:SECTOR)
            MATCH (s)<-[:BELONGS_TO_SECTOR]-(m2:MARKET)
            WHERE m1 <> m2
            RETURN m2.symbol AS symbol
            LIMIT 10
            """
            related_results = await neo4j_service.execute_query(
                related_query,
                parameters={"symbol": symbol.upper()}
            )
            related_markets = [r["symbol"] for r in related_results]

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='market_detail', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='market_detail').observe(query_time_seconds)

        logger.debug(
            f"Market detail query completed: symbol={symbol}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return MarketDetailResponse(
            **market.model_dump(),
            sector_info=sector_info,
            organizations=organizations,
            related_markets=related_markets
        )

    except HTTPException:
        raise
    except Exception as e:
        kg_queries_total.labels(endpoint='market_detail', status='error').inc()
        logger.error(f"Market detail query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query market details: {str(e)}"
        )


@router.get(
    "/api/v1/graph/markets/{symbol}/history",
    response_model=MarketHistoryResponse,
    status_code=200,
    summary="Get historical price data",
    description="""
    Get historical price data for a market symbol.

    **Note:** Historical data is fetched from FMP Service.

    **Permissions Required:** `markets:read`
    """,
    tags=["Markets"]
)
async def get_market_history(
    symbol: str = Path(..., description="Market symbol"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Max results")
) -> MarketHistoryResponse:
    """
    Get historical price data from FMP Service.

    Args:
        symbol: Market symbol
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        limit: Max results

    Returns:
        MarketHistoryResponse with historical data

    Raises:
        HTTPException 404: Market not found
        HTTPException 503: FMP Service unavailable
        HTTPException 500: Query failed
    """
    start_time = time.time()

    logger.debug(f"Market history query: symbol={symbol}, from={from_date}, to={to_date}")

    try:
        # First verify market exists in Neo4j
        market_check = await neo4j_service.execute_query(
            QUERIES.get_market_by_symbol,
            parameters={"symbol": symbol.upper()}
        )

        if not market_check or not market_check[0].get("m"):
            kg_queries_total.labels(endpoint='market_history', status='not_found').inc()
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Market not found",
                    "detail": f"No MARKET node found with symbol: {symbol}"
                }
            )

        # Fetch historical data from FMP Service
        fmp_client = get_fmp_service_client()
        history_data = await fmp_client.get_historical_prices(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date
        )

        # Limit results
        history_data = history_data[:limit]

        # Transform to response schema
        history_points = []
        for point in history_data:
            history_points.append(MarketHistoryPoint(
                date=point.get("date"),
                open=point.get("open"),
                high=point.get("high"),
                low=point.get("low"),
                close=point.get("close"),
                volume=point.get("volume"),
                adj_close=point.get("adjClose")
            ))

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='market_history', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='market_history').observe(query_time_seconds)

        logger.debug(
            f"Market history query completed: symbol={symbol}, "
            f"records={len(history_points)}, time={int(query_time_seconds * 1000)}ms"
        )

        return MarketHistoryResponse(
            symbol=symbol.upper(),
            history=history_points,
            total_records=len(history_points),
            data_source="FMP"
        )

    except HTTPException:
        raise
    except FMPServiceUnavailableError as e:
        kg_queries_total.labels(endpoint='market_history', status='error').inc()
        logger.error(f"FMP Service unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FMP Service unavailable",
                "detail": str(e)
            }
        )
    except Exception as e:
        kg_queries_total.labels(endpoint='market_history', status='error').inc()
        logger.error(f"Market history query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query market history: {str(e)}"
        )
