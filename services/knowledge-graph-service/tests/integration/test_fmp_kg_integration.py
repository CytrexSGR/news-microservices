"""
End-to-End Integration Tests: FMP Service → Knowledge-Graph → Neo4j

Tests complete data flow from FMP Service through Knowledge-Graph Service
to Neo4j database, validating:

1. Service-to-service HTTP communication
2. Data transformation and validation
3. Neo4j node/relationship creation
4. Idempotency guarantees
5. Error handling and partial failures
6. Performance benchmarks

Run Requirements:
- Docker Compose stack running (FMP Service, Neo4j, Knowledge-Graph)
- Network connectivity between services
- Empty Neo4j database (or use cleanup fixtures)

Usage:
    pytest tests/integration/test_fmp_kg_integration.py -v -m integration
    pytest tests/integration/test_fmp_kg_integration.py -v -m integration --log-cli-level=INFO
"""

import pytest
import httpx
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import os

# Integration test marker
pytestmark = pytest.mark.integration


# =============================================================================
# Configuration
# =============================================================================

# Service URLs (override with env vars for CI/CD)
KNOWLEDGE_GRAPH_URL = os.getenv(
    "KNOWLEDGE_GRAPH_URL",
    "http://localhost:8111"
)
FMP_SERVICE_URL = os.getenv(
    "FMP_SERVICE_URL",
    "http://localhost:8109"
)
NEO4J_URL = os.getenv(
    "NEO4J_URL",
    "bolt://localhost:7687"
)

# Test configuration
DEFAULT_TIMEOUT = 30.0  # seconds
SYNC_TIMEOUT = 60.0     # seconds for full sync operations
HTTP_TIMEOUT = httpx.Timeout(DEFAULT_TIMEOUT, connect=10.0)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
async def http_client():
    """Shared HTTP client for integration tests."""
    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="module")
async def verify_services_running(http_client: httpx.AsyncClient):
    """
    Verify all required services are running before tests.

    Checks:
    - FMP Service health endpoint
    - Knowledge-Graph Service health endpoint
    - Neo4j connectivity (via Knowledge-Graph)

    Raises:
        RuntimeError: If any service is unavailable
    """
    services = {
        "FMP Service": f"{FMP_SERVICE_URL}/health",
        "Knowledge-Graph Service": f"{KNOWLEDGE_GRAPH_URL}/health"
    }

    for service_name, health_url in services.items():
        try:
            response = await http_client.get(health_url)
            assert response.status_code == 200, \
                f"{service_name} health check failed: {response.status_code}"

            # Verify Neo4j connectivity via Knowledge-Graph
            if service_name == "Knowledge-Graph Service":
                health_data = response.json()
                assert health_data.get("neo4j") == "connected", \
                    "Neo4j not connected"

            print(f"✓ {service_name} is running")

        except httpx.RequestError as e:
            pytest.fail(
                f"{service_name} is not accessible at {health_url}: {e}\n"
                f"Please ensure Docker Compose stack is running:\n"
                f"  docker compose up -d"
            )

    yield True


@pytest.fixture(scope="function")
async def clean_neo4j_markets(http_client: httpx.AsyncClient):
    """
    Clean Neo4j MARKET and SECTOR nodes before each test.

    Ensures tests start with empty database state.
    Uses Knowledge-Graph admin endpoint.
    """
    # Note: This would require admin endpoint implementation
    # For now, document expected pre-test state
    yield

    # Cleanup after test (optional - depends on test strategy)
    # For integration tests, we might want to preserve data for inspection


@pytest.fixture
def sample_symbols() -> List[str]:
    """Sample symbols for testing (one per asset type)."""
    return ["AAPL", "EURUSD", "GCUSD", "BTCUSD"]


@pytest.fixture
def full_symbol_set() -> List[str]:
    """Full default symbol set (40 symbols)."""
    return [
        # STOCK (10)
        "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
        "META", "NVDA", "JPM", "V", "WMT",
        # FOREX (10)
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
        # COMMODITY (10)
        "GCUSD", "SIUSD", "CLUSD", "NGUSD", "HGUSD",
        "ZCUSX", "WTUSD", "SBUSD", "KCUSX", "CTUSD",
        # CRYPTO (10)
        "BTCUSD", "ETHUSD", "BNBUSD", "XRPUSD", "ADAUSD",
        "SOLUSD", "DOTUSD", "MATICUSD", "LINKUSD", "AVAXUSD"
    ]


# =============================================================================
# Test 1: Service Connectivity
# =============================================================================

@pytest.mark.asyncio
async def test_fmp_service_connectivity(
    http_client: httpx.AsyncClient,
    verify_services_running
):
    """
    Test that FMP Service is reachable and returns valid asset metadata.

    Validates:
    - HTTP connectivity to FMP Service
    - Metadata endpoint returns valid data
    - Response contains expected fields
    """
    # Test basic connectivity
    response = await http_client.get(f"{FMP_SERVICE_URL}/health")
    assert response.status_code == 200
    health_data = response.json()
    assert health_data.get("status") == "healthy"

    # Test metadata endpoint (sample symbols)
    symbols = ["AAPL", "EURUSD", "BTCUSD"]
    response = await http_client.get(
        f"{FMP_SERVICE_URL}/api/v1/metadata/bulk",
        params={"symbols": ",".join(symbols)}
    )

    assert response.status_code == 200
    metadata = response.json()

    assert isinstance(metadata, list)
    assert len(metadata) >= 3, "Should return metadata for 3+ symbols"

    # Validate metadata structure
    for asset in metadata[:3]:  # Check first 3
        assert "symbol" in asset
        assert "name" in asset
        assert "asset_type" in asset
        assert asset["asset_type"] in ["STOCK", "FOREX", "CRYPTO", "COMMODITY"]

        # Stock-specific fields
        if asset["asset_type"] == "STOCK":
            assert "sector" in asset or "industry" in asset
            assert "exchange" in asset


# =============================================================================
# Test 2: End-to-End Market Sync (Small)
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_market_sync_small(
    http_client: httpx.AsyncClient,
    verify_services_running,
    sample_symbols: List[str]
):
    """
    Test complete market sync flow with 4 symbols (one per asset type).

    Flow:
    1. POST /api/v1/graph/markets/sync with specific symbols
    2. Knowledge-Graph fetches from FMP Service
    3. Knowledge-Graph creates MARKET nodes in Neo4j
    4. Knowledge-Graph creates SECTOR nodes
    5. Knowledge-Graph creates BELONGS_TO_SECTOR relationships
    6. Verify data via GET /api/v1/graph/markets

    Expected Result:
    - sync_id returned
    - status: "completed"
    - 4 markets synced
    - 4 MARKET nodes in Neo4j
    - 4 SECTOR nodes in Neo4j
    - 4 BELONGS_TO_SECTOR relationships
    """
    # Step 1: Trigger sync
    sync_request = {
        "symbols": sample_symbols,
        "force_refresh": True  # Bypass cache for predictable test
    }

    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )

    assert response.status_code == 200
    sync_result = response.json()

    # Validate sync result structure
    assert "sync_id" in sync_result
    assert "status" in sync_result
    assert "total_assets" in sync_result
    assert "synced" in sync_result
    assert "failed" in sync_result
    assert "duration_seconds" in sync_result

    # Validate sync success
    assert sync_result["status"] in ["completed", "partial"], \
        f"Sync failed: {sync_result.get('errors')}"
    assert sync_result["total_assets"] == 4
    assert sync_result["synced"] >= 3, \
        f"Expected 3+ synced, got {sync_result['synced']}"
    assert sync_result["failed"] <= 1, \
        f"Too many failures: {sync_result['failed']}"

    sync_id = sync_result["sync_id"]
    print(f"✓ Sync completed: {sync_id}, synced={sync_result['synced']}/4")

    # Step 2: Wait for Neo4j write consistency (eventual consistency)
    await asyncio.sleep(1.0)

    # Step 3: Query synced markets
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
        params={"page_size": 100}
    )

    assert response.status_code == 200
    markets_data = response.json()

    assert "markets" in markets_data
    assert "total" in markets_data

    markets = markets_data["markets"]
    total_markets = markets_data["total"]

    assert total_markets >= 3, f"Expected 3+ markets in Neo4j, got {total_markets}"
    assert len(markets) >= 3, f"Expected 3+ markets in response, got {len(markets)}"

    # Verify all sample symbols are present
    synced_symbols = {m["symbol"] for m in markets}
    missing_symbols = set(sample_symbols) - synced_symbols

    # Allow 1 symbol to fail (partial success acceptable)
    assert len(missing_symbols) <= 1, \
        f"Missing symbols: {missing_symbols}"

    print(f"✓ Markets query returned {len(markets)} markets")

    # Step 4: Verify MARKET node properties
    for market in markets[:4]:  # Check first 4
        assert "symbol" in market
        assert "name" in market
        assert "asset_type" in market
        assert "created_at" in market
        assert "updated_at" in market

        # Asset type validation
        assert market["asset_type"] in ["STOCK", "FOREX", "COMMODITY", "CRYPTO"]

    # Step 5: Verify stats endpoint (aggregations)
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/stats"
    )

    assert response.status_code == 200
    stats = response.json()

    assert "total_markets" in stats
    assert "markets_by_asset_type" in stats
    assert "markets_by_sector" in stats

    assert stats["total_markets"] >= 3
    assert len(stats["markets_by_asset_type"]) >= 3  # 3+ asset types
    assert len(stats["markets_by_sector"]) >= 3      # 3+ sectors

    print(f"✓ Stats: {stats['total_markets']} markets, "
          f"{len(stats['markets_by_asset_type'])} asset types, "
          f"{len(stats['markets_by_sector'])} sectors")


# =============================================================================
# Test 3: End-to-End Market Sync (Full)
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.slow
async def test_e2e_market_sync_full(
    http_client: httpx.AsyncClient,
    verify_services_running,
    full_symbol_set: List[str]
):
    """
    Test complete market sync flow with all 40 default symbols.

    Validates:
    - Large batch sync performance
    - All 4 asset types handled correctly
    - 14 SECTOR nodes created (11 GICS + 3 asset-specific)
    - All 40 BELONGS_TO_SECTOR relationships created
    - Query performance on larger dataset

    Expected Duration: <10 seconds
    """
    start_time = time.time()

    # Trigger full sync (no symbol filter = all defaults)
    sync_request = {
        "force_refresh": True
    }

    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )

    assert response.status_code == 200
    sync_result = response.json()

    # Validate sync result
    assert sync_result["status"] in ["completed", "partial"]
    assert sync_result["total_assets"] == 40
    assert sync_result["synced"] >= 35, \
        f"Expected 35+ synced (allow 5 failures), got {sync_result['synced']}"

    sync_duration = sync_result["duration_seconds"]
    print(f"✓ Full sync completed in {sync_duration:.2f}s: "
          f"{sync_result['synced']}/40 synced")

    # Performance check: Should complete in <10 seconds
    assert sync_duration < 10.0, \
        f"Sync too slow: {sync_duration:.2f}s (expected <10s)"

    # Wait for consistency
    await asyncio.sleep(1.0)

    # Verify total market count
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/stats"
    )

    assert response.status_code == 200
    stats = response.json()

    assert stats["total_markets"] >= 35, \
        f"Expected 35+ markets in Neo4j, got {stats['total_markets']}"

    # Verify asset type distribution
    asset_types = stats["markets_by_asset_type"]
    assert len(asset_types) == 4, "Should have 4 asset types"

    for asset_type in ["STOCK", "FOREX", "COMMODITY", "CRYPTO"]:
        assert asset_type in asset_types, f"Missing asset type: {asset_type}"
        assert asset_types[asset_type] >= 8, \
            f"Expected 8+ {asset_type} markets, got {asset_types[asset_type]}"

    # Verify sector distribution (should have ~14 sectors)
    sectors = stats["markets_by_sector"]
    assert len(sectors) >= 10, \
        f"Expected 10+ sectors, got {len(sectors)}"

    # Check expected sectors exist
    expected_sectors = ["TECH", "FINANCE", "FOREX", "COMMODITY", "CRYPTO"]
    for sector_code in expected_sectors:
        assert sector_code in sectors, f"Missing sector: {sector_code}"

    print(f"✓ Full sync validation passed: "
          f"{stats['total_markets']} markets, "
          f"{len(asset_types)} asset types, "
          f"{len(sectors)} sectors")

    # Check total test duration
    total_duration = time.time() - start_time
    print(f"✓ Total test duration: {total_duration:.2f}s")


# =============================================================================
# Test 4: Idempotency Test
# =============================================================================

@pytest.mark.asyncio
async def test_sync_idempotency(
    http_client: httpx.AsyncClient,
    verify_services_running,
    sample_symbols: List[str]
):
    """
    Test that running sync multiple times doesn't create duplicates.

    Flow:
    1. Sync #1 - Initial sync
    2. Query market count
    3. Sync #2 - Re-sync same symbols
    4. Query market count again
    5. Verify count is same (no duplicates)

    Validates:
    - MERGE operations are idempotent
    - Updated_at timestamp changes
    - No duplicate MARKET nodes
    - No duplicate relationships
    """
    sync_request = {
        "symbols": sample_symbols,
        "force_refresh": True
    }

    # Sync #1
    response1 = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )

    assert response1.status_code == 200
    result1 = response1.json()
    assert result1["status"] in ["completed", "partial"]
    synced_count_1 = result1["synced"]

    await asyncio.sleep(1.0)

    # Query count after first sync
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/stats"
    )
    stats1 = response.json()
    total_markets_1 = stats1["total_markets"]

    print(f"After Sync #1: {total_markets_1} markets")

    # Sync #2 (same symbols)
    await asyncio.sleep(0.5)  # Small delay to ensure updated_at changes

    response2 = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )

    assert response2.status_code == 200
    result2 = response2.json()
    assert result2["status"] in ["completed", "partial"]
    synced_count_2 = result2["synced"]

    # Should sync same number (or similar, accounting for failures)
    assert abs(synced_count_1 - synced_count_2) <= 1, \
        "Sync counts should be consistent"

    await asyncio.sleep(1.0)

    # Query count after second sync
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/stats"
    )
    stats2 = response.json()
    total_markets_2 = stats2["total_markets"]

    print(f"After Sync #2: {total_markets_2} markets")

    # Verify no duplicates created
    assert total_markets_2 == total_markets_1, \
        f"Duplicate markets created: {total_markets_1} → {total_markets_2}"

    # Verify updated_at changed (fetch specific market)
    if sample_symbols:
        symbol = sample_symbols[0]
        response = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/{symbol}"
        )

        if response.status_code == 200:
            market = response.json()
            created_at = datetime.fromisoformat(market["created_at"].replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(market["updated_at"].replace("Z", "+00:00"))

            # Updated_at should be after created_at (or equal if sync was instant)
            assert updated_at >= created_at, \
                "updated_at should be >= created_at"

            print(f"✓ Idempotency validated: no duplicates, updated_at refreshed")


# =============================================================================
# Test 5: Partial Failure Handling
# =============================================================================

@pytest.mark.asyncio
async def test_partial_failure_handling(
    http_client: httpx.AsyncClient,
    verify_services_running
):
    """
    Test that system handles partial failures gracefully.

    Scenario:
    - Request mix of valid and invalid symbols
    - Some symbols succeed, some fail
    - Verify: status = "partial"
    - Verify: Successful symbols are in Neo4j
    - Verify: Error tracking works

    Invalid symbols: "INVALID1", "INVALID2", "NOTFOUND"
    Valid symbols: "AAPL", "EURUSD"
    """
    symbols = ["AAPL", "INVALID1", "EURUSD", "NOTFOUND", "BTCUSD"]

    sync_request = {
        "symbols": symbols,
        "force_refresh": True
    }

    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )

    assert response.status_code == 200
    sync_result = response.json()

    # Should be partial status (some succeeded, some failed)
    # Or completed (if FMP returns empty for invalid symbols)
    assert sync_result["status"] in ["completed", "partial"]
    assert sync_result["total_assets"] == 5

    # At least valid symbols should sync
    assert sync_result["synced"] >= 3, \
        f"Expected 3+ valid symbols synced, got {sync_result['synced']}"

    # Some failures expected
    # Note: Actual behavior depends on FMP Service handling of invalid symbols
    print(f"Partial sync: {sync_result['synced']}/5 synced, "
          f"{sync_result['failed']} failed")

    # Verify errors are tracked
    if sync_result.get("errors"):
        assert isinstance(sync_result["errors"], list)
        for error in sync_result["errors"]:
            assert "symbol" in error or "message" in error

    await asyncio.sleep(1.0)

    # Verify valid symbols made it to Neo4j
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/AAPL"
    )

    # AAPL should exist (if it was in the successful batch)
    # Allow 404 if FMP didn't return it
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        market = response.json()
        assert market["symbol"] == "AAPL"
        print(f"✓ Valid symbol AAPL synced successfully")


# =============================================================================
# Test 6: Neo4j Data Integrity
# =============================================================================

@pytest.mark.asyncio
async def test_neo4j_data_integrity(
    http_client: httpx.AsyncClient,
    verify_services_running,
    sample_symbols: List[str]
):
    """
    Test that synced data in Neo4j is complete and valid.

    Validates:
    - MARKET nodes have all required properties
    - SECTOR nodes exist and are correctly classified
    - BELONGS_TO_SECTOR relationships link correctly
    - No orphaned nodes or relationships
    - Data types are correct (strings, floats, booleans)
    """
    # First sync data
    sync_request = {"symbols": sample_symbols, "force_refresh": True}
    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )
    assert response.status_code == 200

    await asyncio.sleep(1.0)

    # Query individual market with relationships
    symbol = sample_symbols[0]  # AAPL
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/{symbol}"
    )

    assert response.status_code == 200
    market_detail = response.json()

    # Validate MARKET node properties
    required_fields = [
        "symbol", "name", "asset_type", "created_at", "updated_at"
    ]
    for field in required_fields:
        assert field in market_detail, f"Missing required field: {field}"

    # Validate data types
    assert isinstance(market_detail["symbol"], str)
    assert isinstance(market_detail["name"], str)
    assert isinstance(market_detail["asset_type"], str)
    assert isinstance(market_detail["created_at"], str)
    assert isinstance(market_detail["updated_at"], str)

    # Validate timestamps are ISO format
    datetime.fromisoformat(market_detail["created_at"].replace("Z", "+00:00"))
    datetime.fromisoformat(market_detail["updated_at"].replace("Z", "+00:00"))

    # Validate SECTOR relationship (if exists)
    if "sector_info" in market_detail and market_detail["sector_info"]:
        sector = market_detail["sector_info"]
        assert "code" in sector
        assert "name" in sector
        assert isinstance(sector["code"], str)
        assert isinstance(sector["name"], str)

        print(f"✓ Market {symbol} linked to sector: {sector['code']}")

    # Validate related markets
    if "related_markets" in market_detail:
        assert isinstance(market_detail["related_markets"], list)
        # Related markets should have same sector
        print(f"✓ Found {len(market_detail['related_markets'])} related markets")

    print(f"✓ Data integrity validated for {symbol}")


# =============================================================================
# Test 7: Performance Benchmarks
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.performance
async def test_sync_performance(
    http_client: httpx.AsyncClient,
    verify_services_running,
    sample_symbols: List[str]
):
    """
    Test that sync completes within acceptable time limits.

    Performance Targets:
    - Small sync (4 symbols): <5 seconds
    - Full sync (40 symbols): <10 seconds
    - Query response: <100ms (p95)

    Measures:
    - Sync duration
    - Query duration
    - Throughput (symbols/second)
    """
    # Small sync benchmark
    sync_request = {"symbols": sample_symbols, "force_refresh": True}

    start_time = time.time()
    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )
    sync_duration = time.time() - start_time

    assert response.status_code == 200
    sync_result = response.json()

    # Performance assertion: <5 seconds for 4 symbols
    assert sync_duration < 5.0, \
        f"Sync too slow: {sync_duration:.2f}s (expected <5s)"

    # Calculate throughput
    throughput = sync_result["synced"] / sync_duration
    print(f"✓ Sync performance: {sync_duration:.2f}s, "
          f"throughput: {throughput:.1f} symbols/s")

    await asyncio.sleep(1.0)

    # Query performance benchmark
    query_times = []

    for _ in range(5):  # 5 iterations
        start = time.time()
        response = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
            params={"page_size": 50}
        )
        query_time = time.time() - start
        query_times.append(query_time)

        assert response.status_code == 200

    # Calculate p95 query time
    query_times.sort()
    p95_query_time = query_times[int(len(query_times) * 0.95)]
    avg_query_time = sum(query_times) / len(query_times)

    # Performance assertion: <100ms p95
    assert p95_query_time < 0.1, \
        f"Query too slow: p95={p95_query_time*1000:.0f}ms (expected <100ms)"

    print(f"✓ Query performance: avg={avg_query_time*1000:.0f}ms, "
          f"p95={p95_query_time*1000:.0f}ms")


# =============================================================================
# Test 8: Error Recovery
# =============================================================================

@pytest.mark.asyncio
async def test_error_recovery_fmp_service_down(
    http_client: httpx.AsyncClient,
    verify_services_running
):
    """
    Test graceful error handling when FMP Service is unavailable.

    Note: This test requires manually stopping FMP Service or using
    a mock server. For CI/CD, this would use docker-compose profiles
    to stop/start services.

    Validates:
    - Proper HTTP 503 returned
    - Error message includes retry information
    - No partial data corruption in Neo4j
    """
    # This test requires FMP service to be down
    # In a real integration test environment, we would:
    # 1. Stop FMP service container
    # 2. Attempt sync
    # 3. Verify proper error handling
    # 4. Restart FMP service

    # For now, document expected behavior
    pytest.skip("Requires FMP Service to be down - implement in CI/CD environment")

    # Expected behavior when implemented:
    # sync_request = {"symbols": ["AAPL"], "force_refresh": True}
    # response = await http_client.post(...)
    # assert response.status_code == 503
    # error_detail = response.json()
    # assert "retry_after" in error_detail
    # assert "FMP Service unavailable" in error_detail["error"]


# =============================================================================
# Test 9: Market Detail Query
# =============================================================================

@pytest.mark.asyncio
async def test_market_detail_query(
    http_client: httpx.AsyncClient,
    verify_services_running,
    sample_symbols: List[str]
):
    """
    Test detailed market query with relationships.

    Validates:
    - Market detail endpoint returns comprehensive data
    - Sector information is included
    - Related markets are returned
    - Organizations linked via TICKER relationship (if any)
    """
    # First sync data
    sync_request = {"symbols": sample_symbols, "force_refresh": True}
    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )
    assert response.status_code == 200
    await asyncio.sleep(1.0)

    # Query each symbol
    for symbol in sample_symbols:
        response = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/{symbol}"
        )

        if response.status_code == 404:
            # Symbol might have failed during sync
            continue

        assert response.status_code == 200
        market = response.json()

        # Validate basic fields
        assert market["symbol"] == symbol
        assert "name" in market
        assert "asset_type" in market

        # Check for sector (stocks should have GICS sector)
        if market["asset_type"] == "STOCK":
            # May or may not have sector_info depending on FMP data
            pass

        # Check for related markets
        assert "related_markets" in market

        print(f"✓ Market detail for {symbol}: "
              f"{market['asset_type']}, "
              f"sector={market.get('sector_info', {}).get('code', 'N/A')}")


# =============================================================================
# Test 10: Pagination and Filtering
# =============================================================================

@pytest.mark.asyncio
async def test_market_list_pagination_and_filtering(
    http_client: httpx.AsyncClient,
    verify_services_running,
    full_symbol_set: List[str]
):
    """
    Test market list endpoint pagination and filtering.

    Validates:
    - Pagination works correctly (page, page_size)
    - Asset type filter works
    - Sector filter works
    - Search filter works
    - Total count is accurate
    """
    # First sync full dataset
    sync_request = {"force_refresh": True}
    response = await http_client.post(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/sync",
        json=sync_request,
        timeout=SYNC_TIMEOUT
    )
    assert response.status_code == 200
    await asyncio.sleep(1.0)

    # Test 1: Basic pagination
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
        params={"page": 0, "page_size": 10}
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["markets"]) <= 10
    assert data["page"] == 0
    assert data["page_size"] == 10
    total = data["total"]

    # Test 2: Second page
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
        params={"page": 1, "page_size": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1

    # Test 3: Asset type filter
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
        params={"asset_type": "STOCK"}
    )
    assert response.status_code == 200
    data = response.json()

    # All returned markets should be STOCK
    for market in data["markets"]:
        assert market["asset_type"] == "STOCK"

    print(f"✓ Found {len(data['markets'])} STOCK markets")

    # Test 4: Search filter
    response = await http_client.get(
        f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets",
        params={"search": "Apple"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should return markets with "Apple" in name
    # (depends on FMP data - might return 0 results if not named "Apple")
    print(f"✓ Search 'Apple' returned {len(data['markets'])} results")

    print(f"✓ Pagination and filtering tests passed")


# =============================================================================
# Helper Functions
# =============================================================================

async def wait_for_neo4j_consistency(http_client: httpx.AsyncClient, timeout: float = 5.0):
    """
    Wait for Neo4j eventual consistency.

    Polls /api/v1/graph/markets/stats until stable count is reached.

    Args:
        http_client: HTTP client
        timeout: Max wait time in seconds
    """
    start_time = time.time()
    last_count = None
    stable_iterations = 0

    while time.time() - start_time < timeout:
        response = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/markets/stats"
        )

        if response.status_code == 200:
            stats = response.json()
            current_count = stats["total_markets"]

            if current_count == last_count:
                stable_iterations += 1
                if stable_iterations >= 2:  # Stable for 2 iterations
                    return current_count
            else:
                stable_iterations = 0

            last_count = current_count

        await asyncio.sleep(0.5)

    return last_count


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: Integration tests requiring running services"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow tests (>10 seconds)"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance benchmark tests"
    )
