# FMP-Knowledge-Graph Integration - Implementation Guide

**Version:** 1.0.0
**Date:** 2025-11-16
**Status:** Implementation Ready

---

## Quick Start

This guide provides step-by-step instructions for implementing the FMP-Knowledge-Graph integration for Phase 1: Market Sync Foundation.

**Prerequisites:**
- ✅ FMP Service running on port 8113
- ✅ Knowledge-Graph Service running on port 8111
- ✅ Neo4j database accessible
- ✅ PostgreSQL database accessible
- ✅ RabbitMQ running (for Phase 3)

---

## Implementation Checklist

### Phase 1: Market Sync Foundation (2-3 days)

#### Day 1: Schema Setup & Core Services

- [ ] **1.1 Apply Neo4j Schema Migration**
  ```bash
  # Connect to Neo4j container
  docker exec -it news-microservices-neo4j-1 cypher-shell -u neo4j -p your_password

  # Run migration script
  :source /migrations/001_market_schema.cypher

  # Verify constraints and indexes
  SHOW CONSTRAINTS;
  SHOW INDEXES;
  ```

- [ ] **1.2 Create FMP Service Client**
  - Location: `services/knowledge-graph-service/app/clients/fmp_client.py`
  - Features: Circuit breaker, retry logic, rate limiting
  - Reference: Architecture doc Section 3.1

- [ ] **1.3 Create Market Sync Service**
  - Location: `services/knowledge-graph-service/app/services/market_sync_service.py`
  - Features: Batch processing, idempotent writes, error handling
  - Reference: Architecture doc Section 5.1

- [ ] **1.4 Create Pydantic Schemas**
  - Location: `services/knowledge-graph-service/app/schemas/markets.py`
  - Schemas: MarketSyncRequest, MarketSyncResponse, MarketNode, etc.
  - Reference: OpenAPI spec

#### Day 2: API Endpoints & Integration

- [ ] **2.1 Implement POST /api/v1/graph/markets/sync**
  - Location: `services/knowledge-graph-service/app/api/routes/markets.py`
  - Features: JWT auth, input validation, async processing
  - Reference: OpenAPI spec

- [ ] **2.2 Implement GET /api/v1/graph/markets**
  - Features: Filtering, pagination, text search
  - Performance target: < 100ms (p95)

- [ ] **2.3 Implement GET /api/v1/graph/markets/{symbol}**
  - Features: Graph traversal, relationship aggregation
  - Performance target: < 50ms (p95)

- [ ] **2.4 Implement GET /api/v1/graph/markets/{symbol}/history**
  - Features: FMP Service integration, data aggregation

#### Day 3: Testing & Deployment

- [ ] **3.1 Write Unit Tests**
  - Location: `services/knowledge-graph-service/tests/services/test_market_sync_service.py`
  - Coverage: 80%+ target
  - Test cases: Idempotency, error handling, rate limiting

- [ ] **3.2 Write Integration Tests**
  - Location: `services/knowledge-graph-service/tests/integration/test_fmp_kg_integration.py`
  - Test cases: Full sync workflow, concurrent requests, error scenarios

- [ ] **3.3 Initial Data Sync**
  ```bash
  # Sync all 40 assets
  curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"asset_types": ["STOCK", "FOREX", "COMMODITY", "CRYPTO"], "full_sync": true}'
  ```

- [ ] **3.4 Verify Data in Neo4j**
  ```cypher
  // Count MARKET nodes by type
  MATCH (m:MARKET)
  RETURN m.asset_type AS type, count(*) AS count
  ORDER BY count DESC;

  // Verify relationships
  MATCH (m:MARKET)-[r:BELONGS_TO_SECTOR]->(s:SECTOR)
  RETURN count(r) AS total_relationships;
  ```

- [ ] **3.5 Performance Testing**
  - Load test: 100 req/s on GET /markets
  - Verify response times meet SLAs
  - Monitor FMP API quota usage

---

## File Structure

```
services/knowledge-graph-service/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── markets.py                    # NEW: Market API endpoints
│   ├── clients/
│   │   └── fmp_client.py                     # NEW: FMP Service HTTP client
│   ├── services/
│   │   ├── market_sync_service.py            # NEW: Market sync orchestration
│   │   └── rate_limiter.py                   # NEW: FMP API rate limiting
│   ├── schemas/
│   │   └── markets.py                        # NEW: Pydantic schemas
│   └── core/
│       ├── circuit_breaker.py                # NEW: Circuit breaker pattern
│       └── cache.py                          # NEW: Redis caching
├── tests/
│   ├── services/
│   │   └── test_market_sync_service.py       # NEW: Unit tests
│   └── integration/
│       └── test_fmp_kg_integration.py        # NEW: Integration tests
└── migrations/
    └── neo4j/
        └── 001_market_schema.cypher          # ✅ Created
```

---

## Code Templates

### 1. FMP Service Client

```python
# services/knowledge-graph-service/app/clients/fmp_client.py

import httpx
import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.circuit_breaker import CircuitBreaker
from app.services.rate_limiter import RateLimiter
from app.schemas.markets import AssetMetadata, QuoteData
from app.config import settings

logger = logging.getLogger(__name__)


class FMPServiceClient:
    """HTTP client for FMP Service with resilience patterns."""

    def __init__(self):
        self.base_url = settings.FMP_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            service_name="fmp-service"
        )
        self.rate_limiter = RateLimiter(
            max_calls=300,
            period_seconds=86400  # 24 hours
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def get_asset_metadata(
        self,
        symbols: List[str],
        bypass_cache: bool = False
    ) -> List[AssetMetadata]:
        """
        Fetch metadata for multiple assets.

        Args:
            symbols: List of asset symbols (e.g., ["AAPL", "GOOGL"])
            bypass_cache: Force fresh data from FMP API

        Returns:
            List of AssetMetadata objects

        Raises:
            RateLimitExceededError: FMP API quota exceeded
            CircuitBreakerOpenError: FMP Service unavailable
            httpx.HTTPError: HTTP request failed
        """
        # Check rate limit
        await self.rate_limiter.acquire(cost=1)

        # Execute with circuit breaker
        return await self.circuit_breaker.call(
            self._fetch_metadata,
            symbols,
            bypass_cache
        )

    async def _fetch_metadata(
        self,
        symbols: List[str],
        bypass_cache: bool
    ) -> List[AssetMetadata]:
        """Internal method for metadata fetching."""
        logger.info(f"Fetching metadata for {len(symbols)} symbols from FMP Service")

        params = {
            "symbols": ",".join(symbols)
        }
        if bypass_cache:
            params["force_refresh"] = "true"

        response = await self.client.get(
            f"{self.base_url}/api/v1/metadata/bulk",
            params=params
        )
        response.raise_for_status()

        data = response.json()
        return [AssetMetadata(**item) for item in data]

    async def get_quotes_bulk(
        self,
        symbols: List[str]
    ) -> List[QuoteData]:
        """
        Fetch current quotes for multiple assets.

        Args:
            symbols: List of asset symbols

        Returns:
            List of QuoteData objects
        """
        await self.rate_limiter.acquire(cost=1)

        return await self.circuit_breaker.call(
            self._fetch_quotes,
            symbols
        )

    async def _fetch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        """Internal method for quote fetching."""
        logger.info(f"Fetching quotes for {len(symbols)} symbols")

        response = await self.client.get(
            f"{self.base_url}/api/v1/quotes/bulk",
            params={"symbols": ",".join(symbols)}
        )
        response.raise_for_status()

        data = response.json()
        return [QuoteData(**item) for item in data]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

### 2. Market Sync Service

```python
# services/knowledge-graph-service/app/services/market_sync_service.py

import logging
from typing import List, Optional, Dict
from datetime import datetime
from app.clients.fmp_client import FMPServiceClient
from app.services.neo4j_service import neo4j_service
from app.schemas.markets import (
    MarketSyncRequest,
    MarketSyncResponse,
    AssetMetadata,
    AssetType
)

logger = logging.getLogger(__name__)


class MarketSyncService:
    """Orchestrates market data sync from FMP Service to Neo4j."""

    def __init__(self):
        self.fmp_client = FMPServiceClient()

    async def sync_markets(
        self,
        request: MarketSyncRequest
    ) -> MarketSyncResponse:
        """
        Sync market data from FMP Service to Neo4j.

        Args:
            request: Sync request parameters

        Returns:
            MarketSyncResponse with sync statistics
        """
        sync_id = self._generate_sync_id()
        start_time = datetime.now()

        logger.info(f"Starting market sync: {sync_id}")

        # Determine symbols to sync
        symbols = await self._get_symbols_to_sync(request)

        # Fetch metadata from FMP Service
        try:
            metadata_list = await self.fmp_client.get_asset_metadata(
                symbols,
                bypass_cache=request.force_refresh
            )
        except Exception as e:
            logger.error(f"Failed to fetch metadata from FMP Service: {e}")
            return MarketSyncResponse(
                sync_id=sync_id,
                status="failed",
                assets_synced=0,
                assets_failed=len(symbols),
                nodes_created=0,
                nodes_updated=0,
                relationships_created=0,
                relationships_updated=0,
                duration_ms=0,
                fmp_api_calls_used=1,
                errors=[{"symbol": "ALL", "error": str(e)}],
                timestamp=datetime.now()
            )

        # Sync to Neo4j
        stats = await self._sync_to_neo4j(metadata_list, request.full_sync)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(
            f"Sync complete: {sync_id}, "
            f"synced={stats['assets_synced']}, "
            f"failed={stats['assets_failed']}, "
            f"duration={duration_ms}ms"
        )

        return MarketSyncResponse(
            sync_id=sync_id,
            status=self._determine_status(stats),
            assets_synced=stats["assets_synced"],
            assets_failed=stats["assets_failed"],
            nodes_created=stats["nodes_created"],
            nodes_updated=stats["nodes_updated"],
            relationships_created=stats["relationships_created"],
            relationships_updated=stats["relationships_updated"],
            duration_ms=duration_ms,
            fmp_api_calls_used=stats["fmp_api_calls"],
            errors=stats["errors"],
            timestamp=datetime.now()
        )

    async def _get_symbols_to_sync(
        self,
        request: MarketSyncRequest
    ) -> List[str]:
        """Determine which symbols to sync based on request."""
        if request.symbols:
            return request.symbols

        # Default: Sync all 40 assets
        default_symbols = {
            AssetType.STOCK: [
                "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
                "META", "NVDA", "JPM", "V", "WMT"
            ],
            AssetType.FOREX: [
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
            ],
            AssetType.COMMODITY: [
                "GC", "SI", "CL", "NG", "HG",
                "ZC", "ZW", "ZS", "KC", "CT"
            ],
            AssetType.CRYPTO: [
                "BTCUSD", "ETHUSD", "BNBUSD", "XRPUSD", "ADAUSD",
                "SOLUSD", "DOTUSD", "MATICUSD", "LINKUSD", "AVAXUSD"
            ]
        }

        symbols = []
        asset_types = request.asset_types or list(AssetType)

        for asset_type in asset_types:
            symbols.extend(default_symbols.get(asset_type, []))

        return symbols

    async def _sync_to_neo4j(
        self,
        metadata_list: List[AssetMetadata],
        full_sync: bool
    ) -> Dict:
        """
        Sync assets to Neo4j with idempotent MERGE operations.

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "assets_synced": 0,
            "assets_failed": 0,
            "nodes_created": 0,
            "nodes_updated": 0,
            "relationships_created": 0,
            "relationships_updated": 0,
            "fmp_api_calls": 1,  # Bulk metadata fetch
            "errors": []
        }

        for metadata in metadata_list:
            try:
                result = await self._sync_single_asset(metadata, full_sync)
                stats["assets_synced"] += 1
                stats["nodes_created"] += result["nodes_created"]
                stats["nodes_updated"] += result["nodes_updated"]
                stats["relationships_created"] += result["relationships_created"]
                stats["relationships_updated"] += result["relationships_updated"]

            except Exception as e:
                logger.error(f"Failed to sync {metadata.symbol}: {e}")
                stats["assets_failed"] += 1
                stats["errors"].append({
                    "symbol": metadata.symbol,
                    "error": str(e)
                })

        return stats

    async def _sync_single_asset(
        self,
        metadata: AssetMetadata,
        full_sync: bool
    ) -> Dict:
        """Sync single asset to Neo4j."""
        # Prepare Cypher query
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
            m.blockchain = $blockchain
        ON MATCH SET
            m.name = $name,
            m.sector = $sector,
            m.industry = $industry,
            m.last_updated = datetime()

        WITH m, $symbol AS symbol
        MATCH (s:SECTOR {sector_code: $sector_code})
        MERGE (m)-[r:BELONGS_TO_SECTOR]->(s)
        ON CREATE SET
            r.confidence = 1.0,
            r.classification_date = datetime()

        RETURN
            CASE WHEN m.first_seen = datetime() THEN 1 ELSE 0 END AS nodes_created,
            CASE WHEN m.first_seen < datetime() THEN 1 ELSE 0 END AS nodes_updated
        """

        parameters = {
            "symbol": metadata.symbol,
            "name": metadata.name,
            "asset_type": metadata.asset_type,
            "sector": metadata.sector,
            "industry": metadata.industry,
            "exchange": metadata.exchange,
            "currency": metadata.currency,
            "base_currency": getattr(metadata, "base_currency", None),
            "quote_currency": getattr(metadata, "quote_currency", None),
            "blockchain": getattr(metadata, "blockchain", None),
            "sector_code": self._map_sector_to_code(metadata.sector, metadata.asset_type)
        }

        result = await neo4j_service.execute_query(cypher, parameters)

        return {
            "nodes_created": result[0]["nodes_created"] if result else 0,
            "nodes_updated": result[0]["nodes_updated"] if result else 0,
            "relationships_created": 1,  # BELONGS_TO_SECTOR
            "relationships_updated": 0
        }

    def _map_sector_to_code(self, sector: Optional[str], asset_type: str) -> str:
        """Map sector name to sector code."""
        if asset_type == "FOREX":
            return "FOREX"
        elif asset_type == "COMMODITY":
            return "COMMODITY"
        elif asset_type == "CRYPTO":
            return "CRYPTO"

        # Stock sector mapping
        sector_map = {
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
            "Telecommunication Services": "TELECOM"
        }

        return sector_map.get(sector, "TECH")  # Default to TECH

    def _generate_sync_id(self) -> str:
        """Generate unique sync ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        short_id = str(uuid.uuid4())[:8]
        return f"sync_{timestamp}_{short_id}"

    def _determine_status(self, stats: Dict) -> str:
        """Determine overall sync status."""
        if stats["assets_failed"] == 0:
            return "completed"
        elif stats["assets_synced"] == 0:
            return "failed"
        else:
            return "partial"
```

### 3. API Router

```python
# services/knowledge-graph-service/app/api/routes/markets.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.services.market_sync_service import MarketSyncService
from app.schemas.markets import (
    MarketSyncRequest,
    MarketSyncResponse,
    MarketListResponse,
    MarketDetailResponse,
    AssetType
)
from app.middleware.auth import require_permissions, get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/api/v1/graph/markets/sync",
    response_model=MarketSyncResponse,
    status_code=200
)
@require_permissions(["markets:write"])
async def sync_markets(
    request: MarketSyncRequest,
    user: User = Depends(get_current_user)
):
    """
    Trigger market data sync from FMP Service to Neo4j.

    Requires `markets:write` permission.
    """
    logger.info(f"User {user.id} triggered market sync")

    sync_service = MarketSyncService()

    try:
        response = await sync_service.sync_markets(request)
        return response

    except RateLimitExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))

    except CircuitBreakerOpenError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.error(f"Market sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal sync error")


@router.get(
    "/api/v1/graph/markets",
    response_model=MarketListResponse
)
@require_permissions(["markets:read"])
async def get_markets(
    asset_type: Optional[AssetType] = Query(None),
    sector: Optional[str] = Query(None),
    is_active: bool = Query(True),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user)
):
    """
    Query MARKET nodes with filters and pagination.

    Requires `markets:read` permission.
    """
    # TODO: Implement Neo4j query with filters
    pass


@router.get(
    "/api/v1/graph/markets/{symbol}",
    response_model=MarketDetailResponse
)
@require_permissions(["markets:read"])
async def get_market_by_symbol(
    symbol: str,
    user: User = Depends(get_current_user)
):
    """
    Get detailed market data with relationships.

    Requires `markets:read` permission.
    """
    # TODO: Implement Neo4j graph traversal
    pass
```

---

## Testing Guide

### Unit Tests

```python
# tests/services/test_market_sync_service.py

import pytest
from app.services.market_sync_service import MarketSyncService
from app.schemas.markets import MarketSyncRequest, AssetType


@pytest.mark.asyncio
async def test_sync_single_stock():
    """Test syncing single stock symbol."""
    service = MarketSyncService()

    request = MarketSyncRequest(
        symbols=["AAPL"],
        full_sync=True
    )

    response = await service.sync_markets(request)

    assert response.status == "completed"
    assert response.assets_synced == 1
    assert response.assets_failed == 0
    assert response.nodes_created >= 1


@pytest.mark.asyncio
async def test_sync_idempotency():
    """Test that syncing same asset twice is idempotent."""
    service = MarketSyncService()

    request = MarketSyncRequest(symbols=["AAPL"], full_sync=True)

    # First sync (creates node)
    response1 = await service.sync_markets(request)
    assert response1.nodes_created == 1

    # Second sync (updates node)
    response2 = await service.sync_markets(request)
    assert response2.nodes_created == 0
    assert response2.nodes_updated == 1


@pytest.mark.asyncio
async def test_sync_all_asset_types():
    """Test syncing all 40 default assets."""
    service = MarketSyncService()

    request = MarketSyncRequest(
        asset_types=[
            AssetType.STOCK,
            AssetType.FOREX,
            AssetType.COMMODITY,
            AssetType.CRYPTO
        ],
        full_sync=True
    )

    response = await service.sync_markets(request)

    assert response.status == "completed"
    assert response.assets_synced == 40
    assert response.fmp_api_calls_used <= 5  # Should use batch requests
```

### Integration Tests

```python
# tests/integration/test_fmp_kg_integration.py

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_full_sync_workflow(auth_token):
    """Test complete sync workflow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Trigger sync
        response = await client.post(
            "/api/v1/graph/markets/sync",
            json={
                "symbols": ["AAPL", "GOOGL"],
                "full_sync": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["assets_synced"] == 2

        # 2. Query markets
        response = await client.get(
            "/api/v1/graph/markets",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        markets = response.json()["markets"]
        assert len(markets) >= 2

        # 3. Get specific market
        response = await client.get(
            "/api/v1/graph/markets/AAPL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        market = response.json()["market"]
        assert market["symbol"] == "AAPL"
        assert market["asset_type"] == "STOCK"
```

---

## Deployment

### Docker Compose Configuration

```yaml
# Add to docker-compose.yml (if not already present)

services:
  knowledge-graph-service:
    environment:
      - FMP_SERVICE_URL=http://fmp-service:8113
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URL=redis://redis:6379
```

### Environment Variables

```bash
# .env file additions
FMP_SERVICE_URL=http://fmp-service:8113
FMP_API_RATE_LIMIT=300  # Calls per day
MARKET_SYNC_CACHE_TTL=86400  # 24 hours
```

---

## Monitoring

### Prometheus Metrics

```python
# Add to app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Sync metrics
kg_market_sync_total = Counter(
    'kg_market_sync_total',
    'Total market sync operations',
    ['status']
)

kg_market_sync_duration_seconds = Histogram(
    'kg_market_sync_duration_seconds',
    'Market sync duration',
    buckets=[0.5, 1, 2, 5, 10, 30]
)

kg_fmp_quota_used = Gauge(
    'kg_fmp_quota_used',
    'FMP API quota used today'
)

kg_circuit_breaker_state = Gauge(
    'kg_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)
```

### Grafana Dashboard

Create dashboard with panels:
- Market sync success/failure rate
- FMP API quota usage (daily)
- Circuit breaker state (fmp-service)
- Neo4j write latency (p50, p95, p99)
- Market node count by asset type

---

## Troubleshooting

### Common Issues

**1. FMP Service Unavailable**
```
Error: Circuit breaker open
Solution: Check FMP Service health, wait for recovery timeout (30s)
```

**2. Rate Limit Exceeded**
```
Error: FMP API daily quota exceeded
Solution: Wait for quota reset (24h), implement incremental sync
```

**3. Duplicate MARKET Nodes**
```
Error: Constraint violation: market_symbol_unique
Solution: Verify UNIQUE constraint exists, use MERGE instead of CREATE
```

**4. Slow Neo4j Queries**
```
Error: Query timeout after 30s
Solution: Verify indexes exist, check query plan with EXPLAIN
```

---

## Next Steps

After Phase 1 completion:

1. **Phase 2: Incremental Updates**
   - Scheduled price updates (every 15 minutes)
   - Cache optimization
   - Bulk update queries

2. **Phase 3: Event-Driven Architecture**
   - RabbitMQ integration
   - Event-driven sync
   - Real-time updates

3. **Future Enhancements**
   - Historical price storage in Neo4j
   - Advanced graph analytics (centrality, communities)
   - Machine learning integration (price prediction)

---

## Support

For questions or issues:
- Architecture docs: `/docs/architecture/fmp-kg-integration-design.md`
- API spec: `/docs/api/kg-markets-api-spec.yaml`
- Neo4j schema: `/services/knowledge-graph-service/migrations/neo4j/001_market_schema.cypher`

**Last Updated:** 2025-11-16
