# Market Models & Schemas Guide

## Overview

This guide covers the Pydantic schemas and Neo4j query templates for the Market integration in the Knowledge Graph Service.

**Created:** 2025-11-16
**Status:** ✅ Complete - All tests passing (44/44)

---

## 📁 File Structure

```
services/knowledge-graph-service/
├── app/
│   ├── models/
│   │   ├── __init__.py                # Package exports
│   │   ├── enums.py                   # Asset types, sectors, exchanges
│   │   └── neo4j_queries.py           # Cypher query templates
│   └── schemas/
│       ├── __init__.py                # Package exports
│       ├── markets.py                 # Market & Sector schemas
│       └── sync_results.py            # Sync operation results
└── tests/
    └── test_market_models.py          # 44 comprehensive tests
```

---

## 🎯 Quick Start

### Import Schemas

```python
from app.schemas.markets import (
    SectorNode,
    MarketCreate,
    MarketUpdate,
    MarketNode,
    MarketListResponse,
    MarketDetailResponse,
    MarketSearchQuery,
    MarketStatsResponse,
)
from app.models.enums import AssetType, MarketSector, ExchangeType
from app.models.neo4j_queries import QUERIES, QueryParamBuilder
```

### Create a Market

```python
from app.schemas.markets import MarketCreate
from app.models.enums import AssetType, ExchangeType

# Create stock market
market = MarketCreate(
    symbol="AAPL",
    name="Apple Inc.",
    asset_type=AssetType.STOCK,
    sector="XLK",
    exchange=ExchangeType.NASDAQ,
    currency="USD",
    isin="US0378331005"
)

# Create forex pair
forex = MarketCreate(
    symbol="EUR/USD",
    name="Euro vs US Dollar",
    asset_type=AssetType.FOREX,
    currency="USD"
)

# Create crypto
crypto = MarketCreate(
    symbol="BTC-USD",
    name="Bitcoin",
    asset_type=AssetType.CRYPTO,
    currency="USD"
)
```

### Update Market Prices

```python
from app.schemas.markets import MarketUpdate

# Partial update
update = MarketUpdate(
    current_price=178.45,
    day_change_percent=1.23,
    volume=52340000
)

# Full OHLC update
update_full = MarketUpdate(
    current_price=178.45,
    open_price=176.80,
    high_price=179.20,
    low_price=176.50,
    close_price=176.25,
    volume=52340000,
    market_cap=2800000000000
)
```

### Query Neo4j

```python
from app.models.neo4j_queries import QUERIES, QueryParamBuilder

# Create/update market
result = session.run(
    QUERIES.merge_market,
    **QueryParamBuilder.market_create_params(market.dict())
)

# Update prices
result = session.run(
    QUERIES.update_market_price,
    **QueryParamBuilder.market_update_params("AAPL", update.dict())
)

# Get market by symbol
result = session.run(
    QUERIES.get_market_by_symbol,
    symbol="AAPL"
)

# Search markets
search = MarketSearchQuery(
    asset_types=[AssetType.STOCK],
    sectors=["XLK"],
    is_active=True,
    page=0,
    page_size=20
)
result = session.run(
    QUERIES.list_markets,
    **QueryParamBuilder.search_params(search.dict())
)
```

---

## 📊 Schema Reference

### 1. SectorNode

Represents a market sector (e.g., Technology, Financials).

**Fields:**
- `code: str` - Sector code (e.g., "XLK", "XLF")
- `name: str` - Sector name (e.g., "Information Technology")
- `description: Optional[str]` - Detailed description
- `market_classification: MarketClassification` - Default: GICS

**Validation:**
- Code is auto-converted to uppercase
- Code must be alphanumeric

**Example:**
```python
sector = SectorNode(
    code="XLK",
    name="Information Technology",
    description="Tech companies",
    market_classification=MarketClassification.GICS
)
```

---

### 2. MarketCreate

Schema for creating new MARKET nodes.

**Required Fields:**
- `symbol: str` - Ticker symbol (1-20 chars)
- `name: str` - Full market name
- `asset_type: AssetType` - STOCK, FOREX, COMMODITY, or CRYPTO

**Optional Fields:**
- `sector: Optional[str]` - Sector code
- `exchange: Optional[ExchangeType]` - Trading exchange
- `currency: str` - Default: "USD"
- `is_active: bool` - Default: True
- `isin: Optional[str]` - 12-char ISIN code
- `description: Optional[str]`

**Validation:**
- Symbol: uppercase, allows A-Z, 0-9, ^, /, -, .
- Currency: uppercase, 3 characters
- ISIN: exactly 12 alphanumeric characters

---

### 3. MarketUpdate

Schema for updating market prices.

**All Fields Optional:**
- `current_price: Optional[float]` - Current price (> 0)
- `day_change_percent: Optional[float]` - % change
- `market_cap: Optional[int]` - Market cap in USD (> 0)
- `volume: Optional[int]` - Trading volume (≥ 0)
- `open_price: Optional[float]` - Opening price (> 0)
- `high_price: Optional[float]` - Day's high (> 0)
- `low_price: Optional[float]` - Day's low (> 0)
- `close_price: Optional[float]` - Previous close (> 0)

**Validation:**
- All prices must be > 0
- Volume can be 0 (no trading)

---

### 4. MarketNode

Complete MARKET node from Neo4j (extends MarketCreate with price data).

**Additional Fields:**
- All fields from MarketCreate
- All fields from MarketUpdate
- `created_at: datetime` - Auto-generated
- `last_updated: datetime` - Auto-updated

**Use Case:** Representing full market data from database.

---

### 5. MarketListResponse

Paginated list of markets.

**Fields:**
- `markets: List[MarketNode]` - List of market nodes
- `total: int` - Total count matching filters (≥ 0)
- `page: int` - Current page (0-indexed, ≥ 0)
- `page_size: int` - Items per page (1-100)

**Validation:**
- page_size max: 100
- page must be ≥ 0

---

### 6. MarketDetailResponse

MARKET node with relationships (extends MarketNode).

**Additional Fields:**
- `sector_info: Optional[SectorNode]` - Full sector object
- `organizations: List[str]` - Related organization names
- `related_markets: List[str]` - Related market symbols

**Use Case:** API response with full market context.

---

### 7. MarketSearchQuery

Search filters for markets.

**Filter Fields:**
- `symbol_contains: Optional[str]` - Case-insensitive substring
- `name_contains: Optional[str]` - Case-insensitive substring
- `asset_types: Optional[List[AssetType]]` - Filter by types
- `sectors: Optional[List[str]]` - Filter by sector codes
- `exchanges: Optional[List[ExchangeType]]` - Filter by exchanges
- `is_active: Optional[bool]` - Active/inactive filter
- `min_market_cap: Optional[int]` - Minimum market cap (≥ 0)
- `max_market_cap: Optional[int]` - Maximum market cap (≥ 0)

**Pagination:**
- `page: int` - Default: 0
- `page_size: int` - Default: 20, max: 100

---

### 8. MarketStatsResponse

Aggregated market statistics.

**Fields:**
- `total_markets: int` - Total market count
- `active_markets: int` - Active market count
- `markets_by_asset_type: Dict[str, int]` - Count per asset type
- `markets_by_sector: Dict[str, int]` - Count per sector
- `total_market_cap: Optional[int]` - Sum of all market caps
- `avg_day_change: Optional[float]` - Average % change

---

## 🔢 Enumerations

### AssetType

```python
class AssetType(str, Enum):
    STOCK = "STOCK"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"
    CRYPTO = "CRYPTO"
```

### MarketSector (GICS)

11 sectors based on Global Industry Classification Standard:

```python
class MarketSector(str, Enum):
    COMMUNICATION_SERVICES = "Communication Services"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    ENERGY = "Energy"
    FINANCIALS = "Financials"
    HEALTH_CARE = "Health Care"
    INDUSTRIALS = "Industrials"
    INFORMATION_TECHNOLOGY = "Information Technology"
    MATERIALS = "Materials"
    REAL_ESTATE = "Real Estate"
    UTILITIES = "Utilities"
```

### ExchangeType

```python
class ExchangeType(str, Enum):
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"      # London
    TSE = "TSE"      # Tokyo
    HKEX = "HKEX"    # Hong Kong
    SSE = "SSE"      # Shanghai
    EURONEXT = "EURONEXT"
    TSX = "TSX"      # Toronto
    ASX = "ASX"      # Australia
    OTHER = "OTHER"
```

### MarketClassification

```python
class MarketClassification(str, Enum):
    GICS = "GICS"    # Global Industry Classification Standard
    ICB = "ICB"      # Industry Classification Benchmark
    NAICS = "NAICS"  # North American Industry Classification
    SIC = "SIC"      # Standard Industrial Classification
```

---

## 🔍 Neo4j Queries

### QUERIES Collection

All query templates are available via `QUERIES` class:

```python
from app.models.neo4j_queries import QUERIES

# Market operations
QUERIES.merge_market                    # Create/update MARKET
QUERIES.merge_market_with_sector        # Create MARKET + SECTOR relationship
QUERIES.update_market_price             # Update price fields
QUERIES.get_market_by_symbol            # Fetch single market
QUERIES.get_market_with_relationships   # Fetch with relationships
QUERIES.list_markets                    # List with filters
QUERIES.count_markets                   # Count matching filters
QUERIES.search_markets_by_sector        # Filter by sector
QUERIES.get_markets_by_market_cap       # Filter by market cap
QUERIES.delete_market                   # Delete market
QUERIES.get_market_stats                # Aggregate statistics
QUERIES.get_markets_by_asset_type       # Group by asset type
QUERIES.get_markets_by_sector           # Group by sector

# Sector operations
QUERIES.merge_sector                    # Create/update SECTOR
QUERIES.get_sector_by_code              # Fetch sector
QUERIES.get_sector_with_markets         # Fetch with markets
QUERIES.list_sectors                    # List all sectors
QUERIES.delete_sector                   # Delete sector

# Relationship operations
QUERIES.create_market_sector_relationship
QUERIES.delete_market_sector_relationship
QUERIES.get_market_relationships

# Graph traversals
QUERIES.find_related_markets            # Find related markets
QUERIES.get_sector_performance          # Sector performance metrics
QUERIES.get_top_movers                  # Top gainers/losers
```

### QueryParamBuilder

Helper to build query parameters:

```python
from app.models.neo4j_queries import QueryParamBuilder

# Create parameters
params = QueryParamBuilder.market_create_params(market_data)

# Update parameters
params = QueryParamBuilder.market_update_params(symbol, update_data)

# Search parameters
params = QueryParamBuilder.search_params(search_query)
```

---

## ✅ Validation Rules

### Symbol
- **Format:** Uppercase, alphanumeric + special chars (^, /, -, .)
- **Length:** 1-20 characters
- **Examples:** AAPL, EUR/USD, BTC-USD, ^VIX, BRK.B

### Prices
- **Type:** float
- **Constraint:** Must be > 0 (strictly positive)
- **Fields:** current_price, open_price, high_price, low_price, close_price

### Volume
- **Type:** int
- **Constraint:** Must be ≥ 0 (zero allowed for no trading)

### Market Cap
- **Type:** int
- **Constraint:** Must be > 0

### Currency
- **Format:** Uppercase, 3 characters (ISO 4217)
- **Examples:** USD, EUR, GBP, JPY

### ISIN
- **Format:** Exactly 12 alphanumeric characters
- **Example:** US0378331005

### Asset Type
- **Constraint:** Must be one of: STOCK, FOREX, COMMODITY, CRYPTO

---

## 🧪 Testing

### Run All Tests

```bash
# In Docker
cd /home/cytrex/news-microservices
docker compose exec knowledge-graph-service pytest tests/test_market_models.py -v

# Expected: 44 passed
```

### Test Coverage

- ✅ Schema validation (field types, constraints)
- ✅ Field validators (symbol, currency, prices, ISIN)
- ✅ Enum values
- ✅ Example data consistency
- ✅ Edge cases (negative values, zero, invalid formats)
- ✅ Pagination limits
- ✅ Optional vs. required fields

### Test Categories

1. **SectorNode** (4 tests)
   - Valid sector creation
   - Code uppercase conversion
   - Code validation
   - Minimal fields

2. **MarketCreate** (10 tests)
   - Stock, forex, crypto creation
   - Symbol validation
   - Currency validation
   - ISIN validation
   - Defaults

3. **MarketUpdate** (7 tests)
   - Price updates (partial, full)
   - OHLC data
   - Negative/zero validation
   - Volume validation

4. **MarketNode** (2 tests)
   - Complete node
   - Minimal node

5. **MarketListResponse** (5 tests)
   - Empty/populated lists
   - Pagination validation

6. **MarketDetailResponse** (2 tests)
   - With/without relationships

7. **MarketSearchQuery** (3 tests)
   - Default values
   - Full filters
   - Validation

8. **MarketStatsResponse** (2 tests)
   - Complete/minimal stats

9. **Enums** (4 tests)
   - AssetType, ExchangeType, MarketClassification, MarketSector values

10. **Schema Examples** (5 tests)
    - Verify all example data is valid

---

## 📝 Common Patterns

### Pattern 1: Create Market with Sector

```python
from app.schemas.markets import MarketCreate
from app.models.enums import AssetType, ExchangeType
from app.models.neo4j_queries import QUERIES

# Create market schema
market = MarketCreate(
    symbol="AAPL",
    name="Apple Inc.",
    asset_type=AssetType.STOCK,
    sector="XLK",
    exchange=ExchangeType.NASDAQ
)

# Insert into Neo4j
result = session.run(
    QUERIES.merge_market_with_sector,
    symbol=market.symbol,
    name=market.name,
    asset_type=market.asset_type.value,
    sector_code="XLK",
    sector_name="Information Technology",
    market_classification="GICS",
    currency=market.currency,
    is_active=market.is_active
)
```

### Pattern 2: Batch Price Update

```python
from app.schemas.markets import MarketUpdate
from app.models.neo4j_queries import QUERIES

# Price data from external API
prices = {
    "AAPL": {"current_price": 178.45, "volume": 52340000},
    "MSFT": {"current_price": 415.20, "volume": 28910000},
    "GOOGL": {"current_price": 142.85, "volume": 35420000}
}

# Update each market
with driver.session() as session:
    for symbol, data in prices.items():
        update = MarketUpdate(**data)
        session.run(
            QUERIES.update_market_price,
            symbol=symbol,
            **update.dict(exclude_none=True)
        )
```

### Pattern 3: Search and Paginate

```python
from app.schemas.markets import MarketSearchQuery, MarketListResponse
from app.models.enums import AssetType
from app.models.neo4j_queries import QUERIES, QueryParamBuilder

# Build search query
search = MarketSearchQuery(
    asset_types=[AssetType.STOCK],
    sectors=["XLK", "XLF"],
    is_active=True,
    min_market_cap=1000000000,
    page=0,
    page_size=20
)

# Execute query
with driver.session() as session:
    # Get results
    result = session.run(
        QUERIES.list_markets,
        **QueryParamBuilder.search_params(search.dict())
    )
    markets = [MarketNode(**record["m"]) for record in result]

    # Get total count
    count_result = session.run(
        QUERIES.count_markets,
        **QueryParamBuilder.search_params(search.dict())
    )
    total = count_result.single()["total"]

    # Build response
    response = MarketListResponse(
        markets=markets,
        total=total,
        page=search.page,
        page_size=search.page_size
    )
```

---

## 🚨 Common Pitfalls

### 1. Forgetting to Exclude None Values

```python
# ❌ WRONG - sends null values to database
update = MarketUpdate(current_price=178.45)
session.run(QUERIES.update_market_price, **update.dict())

# ✅ RIGHT - only sends provided values
session.run(QUERIES.update_market_price, **update.dict(exclude_none=True))
```

### 2. Not Converting Enum Values

```python
# ❌ WRONG - sends Enum object
market = MarketCreate(symbol="AAPL", name="Apple", asset_type=AssetType.STOCK)
session.run(QUERIES.merge_market, asset_type=market.asset_type)

# ✅ RIGHT - converts to string
session.run(QUERIES.merge_market, asset_type=market.asset_type.value)
```

### 3. Invalid Symbol Characters

```python
# ❌ WRONG - will raise ValidationError
market = MarketCreate(symbol="AAPL@#$", ...)

# ✅ RIGHT - only valid characters
market = MarketCreate(symbol="AAPL", ...)
market = MarketCreate(symbol="EUR/USD", ...)  # OK
market = MarketCreate(symbol="BTC-USD", ...)  # OK
market = MarketCreate(symbol="^VIX", ...)     # OK
```

### 4. Page Size Exceeding Limit

```python
# ❌ WRONG - exceeds max page_size
search = MarketSearchQuery(page_size=200)

# ✅ RIGHT - within limits
search = MarketSearchQuery(page_size=100)  # Max allowed
```

---

## 🔗 Related Documentation

- **Neo4j Schema:** `services/knowledge-graph-service/migrations/neo4j/001_market_schema.cypher`
- **API Endpoints:** `services/knowledge-graph-service/app/api/v1/markets.py` (to be created)
- **FMP Integration:** `services/fmp/` (market data provider)
- **Main README:** `services/knowledge-graph-service/README.md`

---

## 📊 Statistics

- **Total Tests:** 44
- **Test Coverage:** 100% of schemas
- **Validation Rules:** 15+
- **Enum Values:** 30+
- **Query Templates:** 25+

**Last Updated:** 2025-11-16
**Maintainer:** Knowledge Graph Service Team
