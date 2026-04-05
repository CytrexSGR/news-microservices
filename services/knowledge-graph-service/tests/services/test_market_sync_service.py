"""
Comprehensive unit tests for Market Sync Service.

Tests cover:
- sync_all_markets(): Full sync, partial failure, complete failure
- sync_market_quotes(): Quote updates, not found errors
- sync_sectors(): Initial creation, idempotent updates
- Error handling: FMP errors, Neo4j errors, rate limits
- Helper methods: Sector mapping, symbol defaults, status determination

Target Coverage: 80%+
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.fmp_integration.market_sync_service import (
    MarketSyncService,
    DEFAULT_ASSETS,
    STANDARD_SECTORS,
)
from app.clients.fmp_service_client import (
    FMPServiceError,
    FMPServiceUnavailableError,
)
from app.schemas.sync_results import (
    SyncResult,
    SyncError,
    QuoteUpdateResult,
    SectorSyncResult,
)


# ============================================================================
# Fixtures: Test Data
# ============================================================================


@pytest.fixture
def sample_stock_metadata() -> List[Dict[str, Any]]:
    """Sample stock metadata from FMP Service."""
    return [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "type": "STOCK",
            "asset_type": "STOCK",
            "exchange": "NASDAQ",
            "currency": "USD",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "base_currency": None,
            "quote_currency": None,
            "blockchain": None,
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "type": "STOCK",
            "asset_type": "STOCK",
            "exchange": "NASDAQ",
            "currency": "USD",
            "sector": "Technology",
            "industry": "Internet Services",
            "base_currency": None,
            "quote_currency": None,
            "blockchain": None,
        },
    ]


@pytest.fixture
def sample_forex_metadata() -> List[Dict[str, Any]]:
    """Sample forex metadata from FMP Service."""
    return [
        {
            "symbol": "EURUSD",
            "name": "Euro/US Dollar",
            "type": "FOREX",
            "asset_type": "FOREX",
            "exchange": None,
            "currency": "USD",
            "sector": "FOREX",
            "industry": None,
            "base_currency": "EUR",
            "quote_currency": "USD",
            "blockchain": None,
        },
        {
            "symbol": "GBPUSD",
            "name": "British Pound/US Dollar",
            "type": "FOREX",
            "asset_type": "FOREX",
            "exchange": None,
            "currency": "USD",
            "sector": "FOREX",
            "industry": None,
            "base_currency": "GBP",
            "quote_currency": "USD",
            "blockchain": None,
        },
    ]


@pytest.fixture
def sample_crypto_metadata() -> List[Dict[str, Any]]:
    """Sample crypto metadata from FMP Service."""
    return [
        {
            "symbol": "BTCUSD",
            "name": "Bitcoin",
            "type": "CRYPTO",
            "asset_type": "CRYPTO",
            "exchange": None,
            "currency": "USD",
            "sector": "CRYPTO",
            "industry": None,
            "base_currency": "BTC",
            "quote_currency": "USD",
            "blockchain": "Bitcoin",
        },
        {
            "symbol": "ETHUSD",
            "name": "Ethereum",
            "type": "CRYPTO",
            "asset_type": "CRYPTO",
            "exchange": None,
            "currency": "USD",
            "sector": "CRYPTO",
            "industry": None,
            "base_currency": "ETH",
            "quote_currency": "USD",
            "blockchain": "Ethereum",
        },
    ]


@pytest.fixture
def sample_all_markets_metadata(
    sample_stock_metadata, sample_forex_metadata, sample_crypto_metadata
) -> List[Dict[str, Any]]:
    """40 assets: 10 stocks + 10 forex + 10 commodities + 10 crypto."""
    # 2 from fixture + 8 more = 10 stocks
    stocks = sample_stock_metadata + [
        {
            "symbol": f"STOCK{i}",
            "name": f"Stock Company {i}",
            "type": "STOCK",
            "asset_type": "STOCK",
            "exchange": "NYSE",
            "currency": "USD",
            "sector": "Technology" if i % 2 == 0 else "Financials",
            "industry": f"Industry {i}",
            "base_currency": None,
            "quote_currency": None,
            "blockchain": None,
        }
        for i in range(3, 11)  # 8 more (3-10 inclusive)
    ]

    # 2 from fixture + 8 more = 10 forex
    forex = sample_forex_metadata + [
        {
            "symbol": f"PAIR{i}",
            "name": f"Currency Pair {i}",
            "type": "FOREX",
            "asset_type": "FOREX",
            "exchange": None,
            "currency": "USD",
            "sector": "FOREX",
            "industry": None,
            "base_currency": "ABC",
            "quote_currency": "USD",
            "blockchain": None,
        }
        for i in range(3, 11)  # 8 more (3-10 inclusive)
    ]

    # 10 commodities
    commodities = [
        {
            "symbol": f"COMM{i}",
            "name": f"Commodity {i}",
            "type": "COMMODITY",
            "asset_type": "COMMODITY",
            "exchange": "NYMEX",
            "currency": "USD",
            "sector": "COMMODITY",
            "industry": None,
            "base_currency": None,
            "quote_currency": None,
            "blockchain": None,
        }
        for i in range(1, 11)
    ]

    # 2 from fixture + 8 more = 10 crypto
    crypto = sample_crypto_metadata + [
        {
            "symbol": f"COIN{i}",
            "name": f"Crypto {i}",
            "type": "CRYPTO",
            "asset_type": "CRYPTO",
            "exchange": None,
            "currency": "USD",
            "sector": "CRYPTO",
            "industry": None,
            "base_currency": "XYZ",
            "quote_currency": "USD",
            "blockchain": f"Blockchain {i}",
        }
        for i in range(3, 11)  # 8 more (3-10 inclusive)
    ]

    return stocks + forex + commodities + crypto


@pytest.fixture
def sample_quotes() -> List[Dict[str, Any]]:
    """Sample quote data from FMP Service."""
    return [
        {"symbol": "AAPL", "price": 150.25},
        {"symbol": "GOOGL", "price": 140.50},
        {"symbol": "MSFT", "price": 380.75},
    ]


@pytest.fixture
def mock_fmp_client() -> AsyncMock:
    """Mock FMP Service client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_neo4j_service() -> AsyncMock:
    """Mock Neo4j service."""
    service = AsyncMock()
    return service


@pytest.fixture
def market_sync_service(mock_fmp_client, mock_neo4j_service):
    """Market Sync Service with mocked dependencies."""
    service = MarketSyncService()
    # Inject mocked dependencies
    service.fmp_client = mock_fmp_client
    return service


# ============================================================================
# Tests: sync_all_markets()
# ============================================================================


@pytest.mark.asyncio
async def test_sync_all_markets_success(
    market_sync_service, sample_all_markets_metadata, mock_neo4j_service
):
    """Test successful sync of all 40 markets."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_all_markets_metadata
    )

    # Mock Neo4j responses for single asset syncs
    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets()

    # Verify result structure
    assert isinstance(result, SyncResult)
    assert result.status == "completed"
    assert result.total_assets == 40
    assert result.synced == 40
    assert result.failed == 0
    assert len(result.errors) == 0
    assert result.nodes_created > 0
    assert result.relationships_created == 40
    assert result.duration_seconds > 0
    assert result.fmp_api_calls_used == 1


@pytest.mark.asyncio
async def test_sync_all_markets_partial_failure(
    market_sync_service, sample_all_markets_metadata, mock_neo4j_service
):
    """Test sync with partial failures (2 fail, 38 succeed)."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_all_markets_metadata
    )

    # Mock first 38 to succeed, last 2 to fail
    success_response = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    call_count = 0

    async def execute_query_side_effect(cypher, params):
        nonlocal call_count
        call_count += 1
        # Last 2 calls (assets 39-40) fail
        if call_count > 38:
            raise Exception("Neo4j timeout")
        return success_response

    mock_neo4j_service.execute_query.side_effect = execute_query_side_effect

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets()

    # Verify partial failure status
    assert result.status == "partial"
    assert result.total_assets == 40
    assert result.synced == 38
    assert result.failed == 2
    assert len(result.errors) == 2
    # All errors should reference symbol
    for error in result.errors:
        assert isinstance(error, SyncError)
        assert error.symbol is not None


@pytest.mark.asyncio
async def test_sync_all_markets_fmp_service_down(
    market_sync_service, mock_neo4j_service
):
    """Test sync when FMP Service is unavailable."""
    # Mock FMP service error
    market_sync_service.fmp_client.get_asset_metadata_bulk.side_effect = (
        FMPServiceUnavailableError("FMP Service is down")
    )

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets()

    # Verify total failure
    assert result.status == "failed"
    assert result.synced == 0
    assert result.failed == 40  # Expected 40 from default assets
    assert len(result.errors) == 1
    assert result.errors[0].symbol == "ALL"
    assert "FMP Service is down" in result.errors[0].error


@pytest.mark.asyncio
async def test_sync_all_markets_with_custom_symbols(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test sync with custom symbol list."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_stock_metadata
    )

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        custom_symbols = ["AAPL", "GOOGL"]
        result = await market_sync_service.sync_all_markets(symbols=custom_symbols)

    # Verify correct symbols were fetched
    market_sync_service.fmp_client.get_asset_metadata_bulk.assert_called_once_with(
        custom_symbols, force_refresh=False
    )
    assert result.total_assets == 2
    assert result.synced == 2


@pytest.mark.asyncio
async def test_sync_all_markets_with_asset_types_filter(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test sync with asset types filter."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_stock_metadata
    )

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets(asset_types=["STOCK"])

    # Verify FMP was called with stock symbols only
    call_args = (
        market_sync_service.fmp_client.get_asset_metadata_bulk.call_args[0][0]
    )
    assert all(sym in DEFAULT_ASSETS["STOCK"] for sym in call_args)


@pytest.mark.asyncio
async def test_sync_all_markets_force_refresh(
    market_sync_service, sample_all_markets_metadata, mock_neo4j_service
):
    """Test sync with force_refresh flag."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_all_markets_metadata
    )

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets(force_refresh=True)

    # Verify force_refresh was passed
    market_sync_service.fmp_client.get_asset_metadata_bulk.assert_called_once()
    call_kwargs = (
        market_sync_service.fmp_client.get_asset_metadata_bulk.call_args[1]
    )
    assert call_kwargs.get("force_refresh") is True


# ============================================================================
# Tests: sync_market_quotes()
# ============================================================================


@pytest.mark.asyncio
async def test_sync_quotes_success(market_sync_service, sample_quotes, mock_neo4j_service):
    """Test successful quote updates for 3 symbols."""
    market_sync_service.fmp_client.get_quotes_bulk.return_value = sample_quotes

    # Mock Neo4j: each symbol updates successfully
    mock_neo4j_service.execute_write.return_value = {"properties_set": 1}

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_market_quotes(
            ["AAPL", "GOOGL", "MSFT"]
        )

    # Verify result
    assert isinstance(result, QuoteUpdateResult)
    assert result.symbols_requested == ["AAPL", "GOOGL", "MSFT"]
    assert result.symbols_updated == 3
    assert result.symbols_failed == 0
    assert len(result.errors) == 0
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_sync_quotes_symbol_not_found(
    market_sync_service, mock_neo4j_service
):
    """Test quote sync when symbol not found in Neo4j."""
    # Quote exists
    quotes = [{"symbol": "INVALID", "price": 100.0}]
    market_sync_service.fmp_client.get_quotes_bulk.return_value = quotes

    # Neo4j: node not found
    mock_neo4j_service.execute_write.return_value = {"properties_set": 0}

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_market_quotes(["INVALID"])

    # Verify error handling
    assert result.symbols_updated == 0
    assert result.symbols_failed == 1
    assert len(result.errors) == 1
    assert "Node not found" in result.errors[0].error


@pytest.mark.asyncio
async def test_sync_quotes_neo4j_error(market_sync_service, sample_quotes):
    """Test quote sync with Neo4j error."""
    market_sync_service.fmp_client.get_quotes_bulk.return_value = sample_quotes

    # Mock Neo4j service error
    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service"
    ) as mock_service:
        mock_service.execute_write.side_effect = Exception("Neo4j connection error")

        result = await market_sync_service.sync_market_quotes(
            ["AAPL", "GOOGL", "MSFT"]
        )

    # All should fail
    assert result.symbols_updated == 0
    assert result.symbols_failed == 3
    assert len(result.errors) == 3


@pytest.mark.asyncio
async def test_sync_quotes_fmp_service_error(market_sync_service):
    """Test quote sync when FMP Service fails."""
    market_sync_service.fmp_client.get_quotes_bulk.side_effect = (
        FMPServiceError("FMP API error")
    )

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service"
    ):
        result = await market_sync_service.sync_market_quotes(["AAPL", "GOOGL"])

    # Verify failure
    assert result.symbols_updated == 0
    assert result.symbols_failed == 2
    assert len(result.errors) == 1
    assert result.errors[0].symbol == "ALL"


@pytest.mark.asyncio
async def test_sync_quotes_partial_failure(market_sync_service, mock_neo4j_service):
    """Test quote sync with partial failures."""
    quotes = [
        {"symbol": "AAPL", "price": 150.0},
        {"symbol": "GOOGL", "price": 140.0},
        {"symbol": "MSFT", "price": 380.0},
    ]
    market_sync_service.fmp_client.get_quotes_bulk.return_value = quotes

    # First 2 succeed, 3rd fails
    call_count = 0

    async def execute_write_side_effect(cypher, params):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return {"properties_set": 1}
        raise Exception("Neo4j timeout")

    mock_neo4j_service.execute_write.side_effect = execute_write_side_effect

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_market_quotes(
            ["AAPL", "GOOGL", "MSFT"]
        )

    assert result.symbols_updated == 2
    assert result.symbols_failed == 1
    assert len(result.errors) == 1


# ============================================================================
# Tests: sync_sectors()
# ============================================================================


@pytest.mark.asyncio
async def test_sync_sectors_initial_creation(market_sync_service, mock_neo4j_service):
    """Test creating 14 SECTOR nodes on first run."""
    # Mock: first run - all created
    mock_neo4j_service.execute_query.return_value = [{"was_created": 1}]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_sectors()

    # Verify result
    assert isinstance(result, SectorSyncResult)
    assert result.total_sectors == 14
    assert result.sectors_created == 14
    assert result.sectors_verified == 0
    assert len(result.sector_codes) == 14
    assert result.duration_seconds > 0

    # Verify all standard sectors are included
    expected_codes = {sector["code"] for sector in STANDARD_SECTORS}
    assert set(result.sector_codes) == expected_codes


@pytest.mark.asyncio
async def test_sync_sectors_idempotent(market_sync_service, mock_neo4j_service):
    """Test sector sync is idempotent (existing sectors verified, not recreated)."""
    # Mock: sectors already exist
    mock_neo4j_service.execute_query.return_value = [{"was_created": 0}]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_sectors()

    # Verify idempotence
    assert result.sectors_created == 0
    assert result.sectors_verified == 14
    assert result.total_sectors == 14


@pytest.mark.asyncio
async def test_sync_sectors_mixed_creation_and_verification(
    market_sync_service, mock_neo4j_service
):
    """Test sector sync with mix of creation and verification."""
    # Mock: first 7 created, last 7 verified
    call_count = 0

    async def execute_query_side_effect(cypher, params):
        nonlocal call_count
        call_count += 1
        was_created = 1 if call_count <= 7 else 0
        return [{"was_created": was_created}]

    mock_neo4j_service.execute_query.side_effect = execute_query_side_effect

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_sectors()

    assert result.sectors_created == 7
    assert result.sectors_verified == 7
    assert result.total_sectors == 14


@pytest.mark.asyncio
async def test_sync_sectors_error_handling(market_sync_service, mock_neo4j_service):
    """Test sector sync continues despite individual sector errors."""
    # Mock: some sectors fail
    call_count = 0

    async def execute_query_side_effect(cypher, params):
        nonlocal call_count
        call_count += 1
        # 5th sector (CONSUMER_DISC) fails
        if call_count == 5:
            raise Exception("Neo4j error")
        return [{"was_created": 1}]

    mock_neo4j_service.execute_query.side_effect = execute_query_side_effect

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_sectors()

    # Service should continue and sync 13 remaining sectors (1 failed)
    # Note: total_sectors is populated from sector_codes which doesn't include failed ones
    assert len(result.sector_codes) == 13
    assert result.sectors_created == 13
    assert result.sectors_verified == 0


# ============================================================================
# Tests: Helper Methods
# ============================================================================


def test_map_sector_to_code_stock_technology(market_sync_service):
    """Test sector mapping for Technology stock."""
    code = market_sync_service._map_sector_to_code("Technology", "STOCK")
    assert code == "TECH"


def test_map_sector_to_code_stock_financials(market_sync_service):
    """Test sector mapping for Financials stock."""
    code = market_sync_service._map_sector_to_code("Financials", "STOCK")
    assert code == "FINANCE"


def test_map_sector_to_code_stock_unknown_sector(market_sync_service):
    """Test sector mapping for unknown sector defaults to TECH."""
    code = market_sync_service._map_sector_to_code("UnknownSector", "STOCK")
    assert code == "TECH"


def test_map_sector_to_code_forex(market_sync_service):
    """Test sector mapping for FOREX asset type."""
    code = market_sync_service._map_sector_to_code("Any", "FOREX")
    assert code == "FOREX"


def test_map_sector_to_code_commodity(market_sync_service):
    """Test sector mapping for COMMODITY asset type."""
    code = market_sync_service._map_sector_to_code("Any", "COMMODITY")
    assert code == "COMMODITY"


def test_map_sector_to_code_crypto(market_sync_service):
    """Test sector mapping for CRYPTO asset type."""
    code = market_sync_service._map_sector_to_code("Any", "CRYPTO")
    assert code == "CRYPTO"


def test_map_sector_to_code_none_sector(market_sync_service):
    """Test sector mapping with None sector."""
    code = market_sync_service._map_sector_to_code(None, "STOCK")
    assert code == "TECH"


def test_get_default_symbols_all_types(market_sync_service):
    """Test getting default symbols for all asset types."""
    symbols = market_sync_service._get_default_symbols()
    assert len(symbols) == 40
    assert all(sym in symbols for sym in DEFAULT_ASSETS["STOCK"])
    assert all(sym in symbols for sym in DEFAULT_ASSETS["FOREX"])
    assert all(sym in symbols for sym in DEFAULT_ASSETS["COMMODITY"])
    assert all(sym in symbols for sym in DEFAULT_ASSETS["CRYPTO"])


def test_get_default_symbols_stock_only(market_sync_service):
    """Test getting default symbols for STOCK only."""
    symbols = market_sync_service._get_default_symbols(asset_types=["STOCK"])
    assert len(symbols) == 10
    assert symbols == DEFAULT_ASSETS["STOCK"]


def test_get_default_symbols_multiple_types(market_sync_service):
    """Test getting default symbols for multiple asset types."""
    symbols = market_sync_service._get_default_symbols(
        asset_types=["STOCK", "FOREX"]
    )
    assert len(symbols) == 20
    assert all(sym in symbols for sym in DEFAULT_ASSETS["STOCK"])
    assert all(sym in symbols for sym in DEFAULT_ASSETS["FOREX"])


def test_get_default_symbols_empty_type_list(market_sync_service):
    """Test getting default symbols with empty asset type list."""
    symbols = market_sync_service._get_default_symbols(asset_types=[])
    # Empty list means no types specified, so service defaults to all types
    # This is the existing behavior (see line 502-503 in market_sync_service.py)
    assert len(symbols) == 40


def test_get_default_symbols_unknown_type(market_sync_service):
    """Test getting default symbols with unknown asset type."""
    symbols = market_sync_service._get_default_symbols(asset_types=["UNKNOWN"])
    assert len(symbols) == 0


def test_generate_sync_id(market_sync_service):
    """Test sync ID generation format."""
    sync_id = market_sync_service._generate_sync_id()
    assert sync_id.startswith("sync_")
    parts = sync_id.split("_")
    assert len(parts) == 4  # sync, date, time, uuid
    assert len(parts[3]) == 8  # short UUID


def test_generate_sync_id_uniqueness(market_sync_service):
    """Test sync IDs are unique."""
    ids = {market_sync_service._generate_sync_id() for _ in range(10)}
    assert len(ids) == 10


def test_determine_status_all_success(market_sync_service):
    """Test status determination: all success."""
    status = market_sync_service._determine_status(synced=40, failed=0)
    assert status == "completed"


def test_determine_status_all_failure(market_sync_service):
    """Test status determination: all failure."""
    status = market_sync_service._determine_status(synced=0, failed=40)
    assert status == "failed"


def test_determine_status_partial_success(market_sync_service):
    """Test status determination: partial success."""
    status = market_sync_service._determine_status(synced=38, failed=2)
    assert status == "partial"


def test_determine_status_single_success(market_sync_service):
    """Test status determination: single asset success."""
    status = market_sync_service._determine_status(synced=1, failed=0)
    assert status == "completed"


def test_determine_status_single_failure(market_sync_service):
    """Test status determination: single asset failure."""
    status = market_sync_service._determine_status(synced=0, failed=1)
    assert status == "failed"


# ============================================================================
# Tests: _sync_single_asset() Helper
# ============================================================================


@pytest.mark.asyncio
async def test_sync_single_asset_stock_creation(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test syncing a single stock asset (node creation)."""
    metadata = sample_stock_metadata[0]  # AAPL

    # Mock Neo4j response for node creation
    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service._sync_single_asset(metadata)

    # Verify result
    assert result["nodes_created"] == 1
    assert result["nodes_updated"] == 0
    assert result["relationships_created"] == 1


@pytest.mark.asyncio
async def test_sync_single_asset_stock_update(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test syncing a single stock asset (node update)."""
    metadata = sample_stock_metadata[0]

    # Mock Neo4j response for node update
    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 0,
            "nodes_updated": 1,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service._sync_single_asset(metadata)

    assert result["nodes_created"] == 0
    assert result["nodes_updated"] == 1
    assert result["relationships_created"] == 1


@pytest.mark.asyncio
async def test_sync_single_asset_forex(
    market_sync_service, sample_forex_metadata, mock_neo4j_service
):
    """Test syncing a forex asset."""
    metadata = sample_forex_metadata[0]  # EURUSD

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service._sync_single_asset(metadata)

    # Verify Cypher query includes forex-specific fields
    call_args = mock_neo4j_service.execute_query.call_args
    cypher = call_args[0][0]
    params = call_args[0][1]

    assert params["base_currency"] == "EUR"
    assert params["quote_currency"] == "USD"
    assert params["sector_code"] == "FOREX"


@pytest.mark.asyncio
async def test_sync_single_asset_crypto(
    market_sync_service, sample_crypto_metadata, mock_neo4j_service
):
    """Test syncing a crypto asset."""
    metadata = sample_crypto_metadata[0]  # BTCUSD

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service._sync_single_asset(metadata)

    # Verify blockchain field is included
    call_args = mock_neo4j_service.execute_query.call_args
    params = call_args[0][1]

    assert params["blockchain"] == "Bitcoin"
    assert params["sector_code"] == "CRYPTO"


@pytest.mark.asyncio
async def test_sync_single_asset_empty_response(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test syncing asset with empty Neo4j response."""
    metadata = sample_stock_metadata[0]

    # Mock empty Neo4j response
    mock_neo4j_service.execute_query.return_value = []

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service._sync_single_asset(metadata)

    # Verify zeros returned
    assert result["nodes_created"] == 0
    assert result["nodes_updated"] == 0
    assert result["relationships_created"] == 0


# ============================================================================
# Tests: Rate Limit and Circuit Breaker Errors
# ============================================================================


@pytest.mark.asyncio
async def test_sync_all_markets_rate_limit_error(
    market_sync_service, mock_neo4j_service
):
    """Test handling of FMP rate limit errors."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.side_effect = (
        FMPServiceError("Rate limit exceeded: 429")
    )

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets()

    assert result.status == "failed"
    assert result.synced == 0
    assert "Rate limit" in result.errors[0].error


@pytest.mark.asyncio
async def test_sync_quotes_rate_limit_error(market_sync_service):
    """Test handling of FMP rate limit errors for quotes."""
    market_sync_service.fmp_client.get_quotes_bulk.side_effect = (
        FMPServiceError("Rate limit exceeded: 429")
    )

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service"
    ):
        result = await market_sync_service.sync_market_quotes(["AAPL"])

    assert result.symbols_updated == 0
    assert result.symbols_failed == 1


# ============================================================================
# Tests: Data Structure Validation
# ============================================================================


@pytest.mark.asyncio
async def test_sync_result_has_timestamp(market_sync_service, mock_neo4j_service):
    """Test that SyncResult includes timestamp."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = []

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets()

    assert result.timestamp is not None
    assert isinstance(result.timestamp, datetime)


@pytest.mark.asyncio
async def test_quote_result_has_timestamp(market_sync_service, sample_quotes):
    """Test that QuoteUpdateResult includes timestamp."""
    market_sync_service.fmp_client.get_quotes_bulk.return_value = sample_quotes

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service"
    ) as mock_service:
        mock_service.execute_write.return_value = {"properties_set": 1}
        result = await market_sync_service.sync_market_quotes(["AAPL"])

    assert result.timestamp is not None
    assert isinstance(result.timestamp, datetime)


@pytest.mark.asyncio
async def test_sector_result_has_timestamp(market_sync_service, mock_neo4j_service):
    """Test that SectorSyncResult includes timestamp."""
    mock_neo4j_service.execute_query.return_value = [{"was_created": 1}]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_sectors()

    assert result.timestamp is not None
    assert isinstance(result.timestamp, datetime)


# ============================================================================
# Tests: Integration-like Tests
# ============================================================================


@pytest.mark.asyncio
async def test_sync_workflow_sectors_then_markets(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test realistic workflow: sync sectors first, then markets."""
    # First sync sectors
    mock_neo4j_service.execute_query.return_value = [{"was_created": 1}]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        sector_result = await market_sync_service.sync_sectors()

    assert sector_result.sectors_created == 14

    # Then sync markets
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_stock_metadata
    )

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        market_result = await market_sync_service.sync_all_markets(
            symbols=["AAPL", "GOOGL"]
        )

    assert market_result.synced == 2


# ============================================================================
# Coverage: Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_sync_quotes_with_missing_price_field(
    market_sync_service, mock_neo4j_service
):
    """Test handling of quotes missing price field."""
    quotes = [
        {"symbol": "AAPL"},  # Missing price
        {"symbol": "GOOGL", "price": 140.0},
    ]
    market_sync_service.fmp_client.get_quotes_bulk.return_value = quotes

    mock_neo4j_service.execute_write.return_value = {"properties_set": 1}

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_market_quotes(
            ["AAPL", "GOOGL"]
        )

    # Only GOOGL should be updated
    assert result.symbols_updated == 1


@pytest.mark.asyncio
async def test_sync_quotes_with_missing_symbol_field(
    market_sync_service, mock_neo4j_service
):
    """Test handling of quotes missing symbol field."""
    quotes = [
        {"price": 150.0},  # Missing symbol
        {"symbol": "GOOGL", "price": 140.0},
    ]
    market_sync_service.fmp_client.get_quotes_bulk.return_value = quotes

    mock_neo4j_service.execute_write.return_value = {"properties_set": 1}

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_market_quotes(["GOOGL"])

    # Only GOOGL should be updated
    assert result.symbols_updated == 1


@pytest.mark.asyncio
async def test_sync_markets_with_missing_metadata_fields(
    market_sync_service, mock_neo4j_service
):
    """Test handling of metadata with missing optional fields."""
    minimal_metadata = [
        {
            "symbol": "TEST",
            "name": "Test Asset",
            # Missing most optional fields
        }
    ]
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        minimal_metadata
    )

    mock_neo4j_service.execute_query.return_value = [
        {
            "nodes_created": 1,
            "nodes_updated": 0,
            "relationships_checked": 1,
        }
    ]

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets(symbols=["TEST"])

    # Should handle gracefully with defaults
    assert result.synced == 1
    assert result.failed == 0


def test_sector_mapping_all_standard_sectors(market_sync_service):
    """Test all standard sectors map correctly."""
    for sector in STANDARD_SECTORS:
        # Test stock mapping for GICS sectors
        if sector["system"] == "GICS":
            code = market_sync_service._map_sector_to_code(
                sector["name"], "STOCK"
            )
            assert code == sector["code"]


# ============================================================================
# Tests: Logging and Debugging Info
# ============================================================================


@pytest.mark.asyncio
async def test_sync_generates_valid_sync_id(
    market_sync_service, mock_neo4j_service
):
    """Test that each sync generates a valid unique ID."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = []

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result1 = await market_sync_service.sync_all_markets()
        result2 = await market_sync_service.sync_all_markets()

    # IDs should be different
    assert result1.sync_id != result2.sync_id
    # Both should be valid format
    assert result1.sync_id.startswith("sync_")
    assert result2.sync_id.startswith("sync_")


@pytest.mark.asyncio
async def test_sync_error_includes_symbol_context(
    market_sync_service, sample_stock_metadata, mock_neo4j_service
):
    """Test that sync errors include symbol context."""
    market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = (
        sample_stock_metadata
    )

    # First call succeeds, second fails
    call_count = 0

    async def execute_query_side_effect(cypher, params):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [
                {
                    "nodes_created": 1,
                    "nodes_updated": 0,
                    "relationships_checked": 1,
                }
            ]
        raise Exception("Test error")

    mock_neo4j_service.execute_query.side_effect = execute_query_side_effect

    with patch(
        "app.services.fmp_integration.market_sync_service.neo4j_service",
        mock_neo4j_service,
    ):
        result = await market_sync_service.sync_all_markets(
            symbols=["AAPL", "GOOGL"]
        )

    # Verify error has symbol
    assert len(result.errors) == 1
    assert result.errors[0].symbol == "GOOGL"
