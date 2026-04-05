"""
Market and Sector Pydantic schemas.

Defines data models for:
- MARKET nodes (stocks, forex, commodities, crypto)
- SECTOR nodes (industry classifications)
- API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.enums import AssetType, MarketSector, ExchangeType, MarketClassification


class SectorNode(BaseModel):
    """
    Represents SECTOR node in Neo4j.

    Sectors group markets by industry classification.
    Default system is GICS (Global Industry Classification Standard).
    """
    code: str = Field(
        ...,
        description="Sector code (e.g., XLC, XLF for SPDR sector ETFs)",
        min_length=2,
        max_length=10
    )
    name: str = Field(
        ...,
        description="Human-readable sector name",
        min_length=2,
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        description="Detailed sector description"
    )
    market_classification: MarketClassification = Field(
        default=MarketClassification.GICS,
        description="Classification system used"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "XLK",
                "name": "Information Technology",
                "description": "Companies that develop software, provide IT services, manufacture technology hardware and equipment, and semiconductor components",
                "market_classification": "GICS"
            }
        }
    )

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Ensure sector code is uppercase and alphanumeric."""
        v = v.upper().strip()
        if not v.replace('_', '').isalnum():
            raise ValueError('Sector code must be alphanumeric')
        return v


class MarketBase(BaseModel):
    """
    Base fields common to all market operations.
    """
    symbol: str = Field(
        ...,
        description="Ticker symbol (e.g., AAPL, EUR/USD, BTC-USD)",
        min_length=1,
        max_length=20
    )
    name: str = Field(
        ...,
        description="Full market name",
        min_length=1,
        max_length=200
    )
    asset_type: AssetType = Field(
        ...,
        description="Type of asset (STOCK, FOREX, COMMODITY, CRYPTO)"
    )

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """
        Ensure symbol is uppercase and contains valid characters.

        Allows: A-Z, 0-9, ^, /, -, . (common in tickers like BRK.B, ^VIX, EUR/USD)
        """
        v = v.upper().strip()
        allowed_special = {'^', '/', '-', '.'}
        if not all(c.isalnum() or c in allowed_special for c in v):
            raise ValueError(
                'Symbol must be alphanumeric or contain ^, /, -, .'
            )
        return v


class MarketCreate(MarketBase):
    """
    Schema for creating a new MARKET node.
    """
    sector: Optional[str] = Field(
        None,
        description="Sector code for BELONGS_TO_SECTOR relationship"
    )
    exchange: Optional[ExchangeType] = Field(
        None,
        description="Primary exchange where asset is traded"
    )
    currency: str = Field(
        default="USD",
        description="Currency for price denomination",
        min_length=3,
        max_length=3
    )
    is_active: bool = Field(
        default=True,
        description="Whether market is currently active for trading"
    )
    isin: Optional[str] = Field(
        None,
        description="International Securities Identification Number",
        min_length=12,
        max_length=12
    )
    description: Optional[str] = Field(
        None,
        description="Market description"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "STOCK",
                "sector": "XLK",
                "exchange": "NASDAQ",
                "currency": "USD",
                "is_active": True,
                "isin": "US0378331005",
                "description": "Technology company focusing on consumer electronics"
            }
        }
    )

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase ISO 4217."""
        return v.upper().strip()

    @field_validator('isin')
    @classmethod
    def validate_isin(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISIN format (12 characters, alphanumeric)."""
        if v is None:
            return v
        v = v.upper().strip()
        if len(v) != 12 or not v.isalnum():
            raise ValueError('ISIN must be exactly 12 alphanumeric characters')
        return v


class MarketUpdate(BaseModel):
    """
    Schema for updating MARKET price data.

    Used by market data providers to update real-time prices.
    """
    current_price: Optional[float] = Field(
        None,
        description="Current market price",
        gt=0
    )
    day_change_percent: Optional[float] = Field(
        None,
        description="Percentage change from previous close"
    )
    market_cap: Optional[int] = Field(
        None,
        description="Market capitalization in USD",
        gt=0
    )
    volume: Optional[int] = Field(
        None,
        description="Trading volume",
        ge=0
    )
    open_price: Optional[float] = Field(
        None,
        description="Opening price",
        gt=0
    )
    high_price: Optional[float] = Field(
        None,
        description="Day's high price",
        gt=0
    )
    low_price: Optional[float] = Field(
        None,
        description="Day's low price",
        gt=0
    )
    close_price: Optional[float] = Field(
        None,
        description="Previous closing price",
        gt=0
    )

    @field_validator('current_price', 'open_price', 'high_price', 'low_price', 'close_price')
    @classmethod
    def validate_positive_price(cls, v: Optional[float]) -> Optional[float]:
        """Ensure prices are positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class MarketNode(MarketBase):
    """
    Represents MARKET node from Neo4j with all fields.

    This is the complete node representation including
    price data and metadata.
    """
    # Metadata
    sector: Optional[str] = None
    exchange: Optional[str] = None
    currency: str = "USD"
    is_active: bool = True
    isin: Optional[str] = None
    description: Optional[str] = None

    # Price data
    current_price: Optional[float] = Field(None, gt=0)
    day_change_percent: Optional[float] = None
    market_cap: Optional[int] = Field(None, gt=0)
    volume: Optional[int] = Field(None, ge=0)
    open_price: Optional[float] = Field(None, gt=0)
    high_price: Optional[float] = Field(None, gt=0)
    low_price: Optional[float] = Field(None, gt=0)
    close_price: Optional[float] = Field(None, gt=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "STOCK",
                "sector": "XLK",
                "exchange": "NASDAQ",
                "currency": "USD",
                "is_active": True,
                "isin": "US0378331005",
                "current_price": 178.45,
                "day_change_percent": 1.23,
                "market_cap": 2800000000000,
                "volume": 52340000,
                "open_price": 176.80,
                "high_price": 179.20,
                "low_price": 176.50,
                "close_price": 176.25,
                "created_at": "2024-01-15T10:30:00Z",
                "last_updated": "2024-01-15T16:00:00Z"
            }
        }
    )


class MarketListResponse(BaseModel):
    """
    Paginated list of markets.
    """
    markets: List[MarketNode] = Field(
        default_factory=list,
        description="List of market nodes"
    )
    total: int = Field(
        ...,
        description="Total number of markets matching filters",
        ge=0
    )
    page: int = Field(
        ...,
        description="Current page number (0-indexed)",
        ge=0
    )
    page_size: int = Field(
        ...,
        description="Number of items per page",
        gt=0,
        le=100
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "markets": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "asset_type": "STOCK",
                        "current_price": 178.45,
                        "day_change_percent": 1.23
                    }
                ],
                "total": 150,
                "page": 0,
                "page_size": 20
            }
        }
    )


class MarketDetailResponse(MarketNode):
    """
    MARKET node with relationships and additional context.

    Includes sector information and related organizations.
    """
    sector_info: Optional[SectorNode] = Field(
        None,
        description="Full sector node if BELONGS_TO_SECTOR relationship exists"
    )
    organizations: List[str] = Field(
        default_factory=list,
        description="List of organization names that trade under this symbol"
    )
    related_markets: List[str] = Field(
        default_factory=list,
        description="Related market symbols (e.g., index constituents)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "STOCK",
                "current_price": 178.45,
                "sector_info": {
                    "code": "XLK",
                    "name": "Information Technology",
                    "market_classification": "GICS"
                },
                "organizations": ["Apple Inc."],
                "related_markets": ["QQQ", "SPY"]
            }
        }
    )


class MarketSearchQuery(BaseModel):
    """
    Search filters for markets.
    """
    symbol_contains: Optional[str] = Field(
        None,
        description="Filter by symbol substring (case-insensitive)"
    )
    name_contains: Optional[str] = Field(
        None,
        description="Filter by name substring (case-insensitive)"
    )
    asset_types: Optional[List[AssetType]] = Field(
        None,
        description="Filter by asset types"
    )
    sectors: Optional[List[str]] = Field(
        None,
        description="Filter by sector codes"
    )
    exchanges: Optional[List[ExchangeType]] = Field(
        None,
        description="Filter by exchanges"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Filter by active status"
    )
    min_market_cap: Optional[int] = Field(
        None,
        description="Minimum market cap in USD",
        ge=0
    )
    max_market_cap: Optional[int] = Field(
        None,
        description="Maximum market cap in USD",
        ge=0
    )
    page: int = Field(
        default=0,
        description="Page number (0-indexed)",
        ge=0
    )
    page_size: int = Field(
        default=20,
        description="Items per page",
        gt=0,
        le=100
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_types": ["STOCK"],
                "sectors": ["XLK", "XLF"],
                "is_active": True,
                "min_market_cap": 1000000000,
                "page": 0,
                "page_size": 20
            }
        }
    )


class MarketStatsResponse(BaseModel):
    """
    Aggregated statistics across markets.
    """
    total_markets: int
    active_markets: int
    markets_by_asset_type: Dict[str, int]
    markets_by_sector: Dict[str, int]
    total_market_cap: Optional[int] = None
    avg_day_change: Optional[float] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_markets": 500,
                "active_markets": 485,
                "markets_by_asset_type": {
                    "STOCK": 400,
                    "FOREX": 50,
                    "CRYPTO": 30,
                    "COMMODITY": 20
                },
                "markets_by_sector": {
                    "XLK": 80,
                    "XLF": 60,
                    "XLV": 50
                },
                "total_market_cap": 50000000000000,
                "avg_day_change": 0.45
            }
        }
    )
