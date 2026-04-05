"""
Tests for Market and Sector Pydantic schemas.

Validates:
- Schema validation (field types, constraints)
- Field validators (symbol, currency, prices)
- Example data consistency
- Enum values
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.markets import (
    SectorNode,
    MarketBase,
    MarketCreate,
    MarketUpdate,
    MarketNode,
    MarketListResponse,
    MarketDetailResponse,
    MarketSearchQuery,
    MarketStatsResponse,
)
from app.models.enums import (
    AssetType,
    MarketSector,
    ExchangeType,
    MarketClassification,
)


class TestSectorNode:
    """Test SECTOR node schema."""

    def test_valid_sector(self):
        """Test creating valid sector."""
        sector = SectorNode(
            code="XLK",
            name="Information Technology",
            description="Technology companies",
            market_classification=MarketClassification.GICS
        )
        assert sector.code == "XLK"
        assert sector.name == "Information Technology"
        assert sector.market_classification == MarketClassification.GICS

    def test_sector_code_uppercase(self):
        """Test sector code is converted to uppercase."""
        sector = SectorNode(
            code="xlk",
            name="Information Technology"
        )
        assert sector.code == "XLK"

    def test_sector_code_validation(self):
        """Test invalid sector code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SectorNode(
                code="XLK@#$",  # Invalid characters
                name="Test"
            )
        assert "alphanumeric" in str(exc_info.value).lower()

    def test_sector_minimal(self):
        """Test sector with minimal required fields."""
        sector = SectorNode(
            code="XLF",
            name="Financials"
        )
        assert sector.code == "XLF"
        assert sector.description is None
        assert sector.market_classification == MarketClassification.GICS


class TestMarketCreate:
    """Test MarketCreate schema for creating new markets."""

    def test_valid_stock(self):
        """Test creating valid stock market."""
        market = MarketCreate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            sector="XLK",
            exchange=ExchangeType.NASDAQ,
            currency="USD",
            isin="US0378331005"
        )
        assert market.symbol == "AAPL"
        assert market.asset_type == AssetType.STOCK
        assert market.currency == "USD"
        assert market.is_active is True

    def test_symbol_uppercase(self):
        """Test symbol is converted to uppercase."""
        market = MarketCreate(
            symbol="aapl",
            name="Apple Inc.",
            asset_type=AssetType.STOCK
        )
        assert market.symbol == "AAPL"

    def test_valid_forex(self):
        """Test creating valid forex pair."""
        market = MarketCreate(
            symbol="EUR/USD",
            name="Euro vs US Dollar",
            asset_type=AssetType.FOREX,
            currency="USD"
        )
        assert market.symbol == "EUR/USD"
        assert "/" in market.symbol

    def test_valid_crypto(self):
        """Test creating valid crypto market."""
        market = MarketCreate(
            symbol="BTC-USD",
            name="Bitcoin",
            asset_type=AssetType.CRYPTO,
            currency="USD"
        )
        assert market.symbol == "BTC-USD"
        assert "-" in market.symbol

    def test_invalid_symbol(self):
        """Test invalid symbol characters raise error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketCreate(
                symbol="AAPL@#$",  # Invalid characters
                name="Test",
                asset_type=AssetType.STOCK
            )
        assert "must be alphanumeric" in str(exc_info.value).lower()

    def test_currency_uppercase(self):
        """Test currency code is converted to uppercase."""
        market = MarketCreate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            currency="usd"
        )
        assert market.currency == "USD"

    def test_isin_validation_valid(self):
        """Test valid ISIN passes validation."""
        market = MarketCreate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            isin="US0378331005"
        )
        assert market.isin == "US0378331005"

    def test_isin_validation_invalid_length(self):
        """Test invalid ISIN length raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketCreate(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK,
                isin="US037833"  # Too short
            )
        # Pydantic returns "at least 12 characters" message
        assert "12 characters" in str(exc_info.value).lower()

    def test_isin_validation_invalid_chars(self):
        """Test invalid ISIN characters raise error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketCreate(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK,
                isin="US037833100@"  # Invalid character
            )
        assert "12 alphanumeric characters" in str(exc_info.value).lower()

    def test_defaults(self):
        """Test default values."""
        market = MarketCreate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK
        )
        assert market.currency == "USD"
        assert market.is_active is True
        assert market.sector is None
        assert market.exchange is None


class TestMarketUpdate:
    """Test MarketUpdate schema for price updates."""

    def test_valid_price_update(self):
        """Test valid price update."""
        update = MarketUpdate(
            current_price=178.45,
            day_change_percent=1.23,
            market_cap=2800000000000,
            volume=52340000
        )
        assert update.current_price == 178.45
        assert update.day_change_percent == 1.23
        assert update.market_cap == 2800000000000
        assert update.volume == 52340000

    def test_full_ohlc_update(self):
        """Test full OHLC price update."""
        update = MarketUpdate(
            current_price=178.45,
            open_price=176.80,
            high_price=179.20,
            low_price=176.50,
            close_price=176.25,
            volume=52340000
        )
        assert update.open_price == 176.80
        assert update.high_price == 179.20
        assert update.low_price == 176.50
        assert update.close_price == 176.25

    def test_negative_price_fails(self):
        """Test negative prices raise error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketUpdate(current_price=-10.50)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_zero_price_fails(self):
        """Test zero price raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketUpdate(current_price=0.0)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_negative_volume_fails(self):
        """Test negative volume raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MarketUpdate(volume=-1000)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_zero_volume_allowed(self):
        """Test zero volume is allowed (no trading)."""
        update = MarketUpdate(volume=0)
        assert update.volume == 0

    def test_partial_update(self):
        """Test partial update with only some fields."""
        update = MarketUpdate(
            current_price=178.45,
            volume=52340000
        )
        assert update.current_price == 178.45
        assert update.volume == 52340000
        assert update.market_cap is None
        assert update.day_change_percent is None


class TestMarketNode:
    """Test MarketNode schema (full node representation)."""

    def test_complete_market_node(self):
        """Test complete market node with all fields."""
        node = MarketNode(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            sector="XLK",
            exchange="NASDAQ",
            currency="USD",
            is_active=True,
            isin="US0378331005",
            current_price=178.45,
            day_change_percent=1.23,
            market_cap=2800000000000,
            volume=52340000,
            open_price=176.80,
            high_price=179.20,
            low_price=176.50,
            close_price=176.25
        )
        assert node.symbol == "AAPL"
        assert node.current_price == 178.45
        assert node.market_cap == 2800000000000
        assert isinstance(node.created_at, datetime)
        assert isinstance(node.last_updated, datetime)

    def test_minimal_market_node(self):
        """Test market node with minimal fields."""
        node = MarketNode(
            symbol="BTC-USD",
            name="Bitcoin",
            asset_type=AssetType.CRYPTO
        )
        assert node.symbol == "BTC-USD"
        assert node.currency == "USD"
        assert node.is_active is True
        assert node.current_price is None


class TestMarketListResponse:
    """Test MarketListResponse for paginated lists."""

    def test_empty_list(self):
        """Test empty market list."""
        response = MarketListResponse(
            markets=[],
            total=0,
            page=0,
            page_size=20
        )
        assert len(response.markets) == 0
        assert response.total == 0

    def test_populated_list(self):
        """Test populated market list."""
        markets = [
            MarketNode(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK
            ),
            MarketNode(
                symbol="MSFT",
                name="Microsoft Corp.",
                asset_type=AssetType.STOCK
            )
        ]
        response = MarketListResponse(
            markets=markets,
            total=150,
            page=0,
            page_size=20
        )
        assert len(response.markets) == 2
        assert response.total == 150
        assert response.page == 0

    def test_negative_page_fails(self):
        """Test negative page number raises error."""
        with pytest.raises(ValidationError):
            MarketListResponse(
                markets=[],
                total=0,
                page=-1,
                page_size=20
            )

    def test_zero_page_size_fails(self):
        """Test zero page size raises error."""
        with pytest.raises(ValidationError):
            MarketListResponse(
                markets=[],
                total=0,
                page=0,
                page_size=0
            )

    def test_page_size_limit(self):
        """Test page size cannot exceed 100."""
        with pytest.raises(ValidationError):
            MarketListResponse(
                markets=[],
                total=0,
                page=0,
                page_size=101
            )


class TestMarketDetailResponse:
    """Test MarketDetailResponse with relationships."""

    def test_market_with_sector(self):
        """Test market with sector relationship."""
        response = MarketDetailResponse(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            sector_info=SectorNode(
                code="XLK",
                name="Information Technology"
            ),
            organizations=["Apple Inc."]
        )
        assert response.sector_info is not None
        assert response.sector_info.code == "XLK"
        assert len(response.organizations) == 1

    def test_market_without_relationships(self):
        """Test market without relationships."""
        response = MarketDetailResponse(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK
        )
        assert response.sector_info is None
        assert len(response.organizations) == 0
        assert len(response.related_markets) == 0


class TestMarketSearchQuery:
    """Test MarketSearchQuery filters."""

    def test_default_search(self):
        """Test search with defaults."""
        query = MarketSearchQuery()
        assert query.page == 0
        assert query.page_size == 20
        assert query.is_active is None

    def test_full_filters(self):
        """Test search with all filters."""
        query = MarketSearchQuery(
            symbol_contains="AA",
            name_contains="Apple",
            asset_types=[AssetType.STOCK],
            sectors=["XLK"],
            exchanges=[ExchangeType.NASDAQ],
            is_active=True,
            min_market_cap=1000000000,
            max_market_cap=5000000000000,
            page=2,
            page_size=50
        )
        assert query.symbol_contains == "AA"
        assert query.name_contains == "Apple"
        assert AssetType.STOCK in query.asset_types
        assert query.page == 2
        assert query.page_size == 50

    def test_negative_market_cap_fails(self):
        """Test negative market cap raises error."""
        with pytest.raises(ValidationError):
            MarketSearchQuery(min_market_cap=-1000)


class TestMarketStatsResponse:
    """Test MarketStatsResponse aggregations."""

    def test_complete_stats(self):
        """Test complete market statistics."""
        stats = MarketStatsResponse(
            total_markets=500,
            active_markets=485,
            markets_by_asset_type={
                "STOCK": 400,
                "FOREX": 50,
                "CRYPTO": 30,
                "COMMODITY": 20
            },
            markets_by_sector={
                "XLK": 80,
                "XLF": 60
            },
            total_market_cap=50000000000000,
            avg_day_change=0.45
        )
        assert stats.total_markets == 500
        assert stats.active_markets == 485
        assert stats.markets_by_asset_type["STOCK"] == 400
        assert stats.total_market_cap == 50000000000000

    def test_minimal_stats(self):
        """Test minimal statistics without optional fields."""
        stats = MarketStatsResponse(
            total_markets=100,
            active_markets=95,
            markets_by_asset_type={"STOCK": 100},
            markets_by_sector={}
        )
        assert stats.total_markets == 100
        assert stats.total_market_cap is None
        assert stats.avg_day_change is None


class TestEnums:
    """Test enum definitions."""

    def test_asset_type_values(self):
        """Test AssetType enum has expected values."""
        assert AssetType.STOCK.value == "STOCK"
        assert AssetType.FOREX.value == "FOREX"
        assert AssetType.COMMODITY.value == "COMMODITY"
        assert AssetType.CRYPTO.value == "CRYPTO"

    def test_exchange_type_values(self):
        """Test ExchangeType enum has major exchanges."""
        assert ExchangeType.NYSE.value == "NYSE"
        assert ExchangeType.NASDAQ.value == "NASDAQ"
        assert ExchangeType.LSE.value == "LSE"

    def test_market_classification_values(self):
        """Test MarketClassification enum."""
        assert MarketClassification.GICS.value == "GICS"
        assert MarketClassification.ICB.value == "ICB"

    def test_market_sector_values(self):
        """Test MarketSector enum has all 11 GICS sectors."""
        sectors = [sector.value for sector in MarketSector]
        assert "Information Technology" in sectors
        assert "Financials" in sectors
        assert "Health Care" in sectors
        assert len(sectors) == 11  # 11 GICS sectors


class TestSchemaExamples:
    """Test that schema examples are valid."""

    def test_sector_example(self):
        """Test SectorNode example is valid."""
        example = SectorNode.model_config['json_schema_extra']['example']
        sector = SectorNode(**example)
        assert sector.code == "XLK"

    def test_market_create_example(self):
        """Test MarketCreate example is valid."""
        example = MarketCreate.model_config['json_schema_extra']['example']
        market = MarketCreate(**example)
        assert market.symbol == "AAPL"

    def test_market_node_example(self):
        """Test MarketNode example is valid."""
        example = MarketNode.model_config['json_schema_extra']['example']
        # Remove datetime strings, use actual datetime objects
        example_copy = example.copy()
        example_copy.pop('created_at', None)
        example_copy.pop('last_updated', None)
        node = MarketNode(**example_copy)
        assert node.symbol == "AAPL"

    def test_market_list_example(self):
        """Test MarketListResponse example structure."""
        example = MarketListResponse.model_config['json_schema_extra']['example']
        assert 'markets' in example
        assert 'total' in example
        assert 'page' in example

    def test_market_stats_example(self):
        """Test MarketStatsResponse example is valid."""
        example = MarketStatsResponse.model_config['json_schema_extra']['example']
        stats = MarketStatsResponse(**example)
        assert stats.total_markets == 500
