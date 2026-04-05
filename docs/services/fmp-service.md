# FMP Service - Financial Market Data Integration

**Service**: `fmp-service`
**Port**: `8113`
**Version**: `2.1.1` (Phase 1 + Phase 5 + Phase 6 Complete)
**Status**: Production
**Last Updated**: 2025-11-25

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
  - [Phase 0: Core Market Data](#phase-0-core-market-data)
  - [Phase 1: Company Intelligence](#phase-1-company-intelligence)
  - [Phase 5: Intermarket Analytics](#phase-5-intermarket-analytics)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Background Jobs](#background-jobs)
- [Event Publishing](#event-publishing)
- [Rate Limiting](#rate-limiting)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Recent Improvements](#recent-improvements-2025-11-25)
- [MCP Integration](#mcp-integration)

---

## MCP Integration

**MCP Server**: `mcp-integration-server`
**Port**: `9005`
**Prefix**: `integration:`

The FMP Service is accessible via the **mcp-integration-server** for AI/LLM integration. The following MCP tools are available:

### Market Data Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_market_quote` | Get current market quote for a symbol | `symbol` (required) |
| `get_market_quotes_batch` | Get quotes for multiple symbols | `symbols[]` (required) |
| `get_ohlcv_candles` | Get OHLCV candles for a symbol | `symbol`, `interval`, `limit` |
| `get_ohlcv_timerange` | Get OHLCV for a specific time range | `symbol`, `start`, `end`, `interval` |
| `get_market_status` | Get current market status (open/closed) | - |
| `list_symbols` | List available trading symbols | `asset_type`, `limit` |
| `search_symbols` | Search for symbols by name/ticker | `query`, `limit` |
| `get_asset_metadata` | Get metadata for an asset | `symbol` (required) |

### News Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_financial_news` | Get financial news articles | `symbol`, `limit` |
| `get_news_by_sentiment` | Get news filtered by sentiment | `sentiment` (positive/negative/neutral), `limit` |

### Macro & Earnings Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_macro_indicators` | List available macro indicators | - |
| `get_macro_indicator_data` | Get data for a specific indicator | `indicator_name` (required) |
| `get_latest_macro_data` | Get latest macro values | - |
| `get_earnings_calendar` | Get upcoming earnings | `start_date`, `end_date` |
| `get_earnings_history` | Get historical earnings | `symbol` (required) |

### Example Usage (Claude Desktop)

```
# Get Bitcoin quote
integration:get_market_quote symbol="BTCUSD"

# Get multiple quotes
integration:get_market_quotes_batch symbols=["BTCUSD", "ETHUSD", "AAPL"]

# Get financial news
integration:get_financial_news symbol="AAPL" limit=10
```

---

## Overview

The FMP Service is the **financial market data hub** for the News Microservices Platform. It integrates real-time and historical market data from the **Financial Modeling Prep (FMP) API** and provides comprehensive financial intelligence for correlation analysis between news events and market movements.

### Key Capabilities

**Phase 0: Core Market Data** (Production since 2024-10)
- Real-time quotes: Indices, Forex, Commodities, Crypto (40+ assets)
- Historical EOD data (2024-2025, expandable to 5+ years)
- Market news feed (35,802+ articles)
- Earnings calendar (140,178+ events)
- Macroeconomic indicators (11,484+ data points)

**Phase 1: Company Intelligence** ⭐ **NEW** (2025-11)
- Company profiles (executives, market cap, employees)
- SEC filings (8-K, 10-K, 10-Q)
- Insider trading (Form 4)
- Financial statements (income, balance sheet, cash flow)
- Key metrics (TTM - Trailing Twelve Months)

**Phase 5: Intermarket Analytics** ⭐ **NEW** (2025-11)
- Volatility tracking (VIX, VVIX, MOVE Index)
- Treasury yields (10Y, 2Y, yield curves)
- Inflation breakevens and real rates
- Dollar Index and carry trade dynamics
- Cross-asset correlations and regime detection

### System Integration

The FMP Service is deeply integrated with:
- **Knowledge Graph Service**: Links companies to stocks, price points, earnings events
- **Content Analysis Service**: Extracts stock mentions, enriches with company data
- **Analytics Service**: News-price correlation, earnings surprise impact, macro context
- **Frontend**: Admin dashboard, market data displays, asset metadata lookups

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      FMP Service (Port 8113)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  FastAPI     │  │  FMP Client  │  │  Data Scheduler    │  │
│  │  11 Routers  │──│ Rate Limited │◄─│  APScheduler 3.10  │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
│         │                  │                    │             │
│         │                  ▼                    │             │
│         │      ┌──────────────────────┐         │             │
│         └─────►│  Ingestion Service   │◄────────┘             │
│                │  + Event Publisher   │                       │
│                └──────────────────────┘                       │
│                         │                                     │
│         ┌───────────────┼───────────────┐                     │
│         ▼               ▼               ▼                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐             │
│  │  Redis   │   │ RabbitMQ │   │  PostgreSQL  │             │
│  │  (Usage) │   │ (Events) │   │  (35 Tables) │             │
│  └──────────┘   └──────────┘   └──────────────┘             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.109.0 |
| **Database** | PostgreSQL | 15+ (async via asyncpg) |
| **ORM** | SQLAlchemy | 2.0 (async) |
| **HTTP Client** | httpx | async |
| **Scheduler** | APScheduler | 3.10.4 |
| **Cache** | Redis | For rate limiting & usage tracking |
| **Message Queue** | RabbitMQ | Event publishing |
| **Container** | Docker | Python 3.11 |

### Database Architecture

**35 Tables** organized in 3 phases:

**Phase 0: Core (13 tables)**
- `index_quotes` (12,966 rows)
- `market_history` (1,731 rows)
- `forex_quotes` (25,560 rows)
- `forex_history` (3,578 rows)
- `commodity_quotes` (18,093 rows)
- `commodity_history` (3,811 rows)
- `crypto_quotes` (16,394 rows)
- `crypto_history` (3,925 rows)
- `fmp_news` (35,802 rows)
- `earnings_events` (140,178 rows)
- `macro_indicators` (11,484 rows)
- `api_rate_limits` (tracking)
- `asset_metadata` (40+ assets)

**Phase 1: Company Intelligence (14 tables)**
- `company_profiles`
- `key_executives`
- `market_cap_history`
- `employee_count`
- `merger_acquisitions`
- `sec_filings`
- `cik_search`
- `insider_trading`
- `income_statements`
- `balance_sheets`
- `cash_flow_statements`
- `financial_ratios`
- `financial_growth`
- `key_metrics_ttm`

**Phase 5: Intermarket Analytics (8 tables)**
- `vix_history`
- `treasury_yields`
- `inflation_breakevens`
- `real_rates`
- `dollar_index_history`
- `carry_trade_history`
- `asset_correlations`
- `regime_state`

**Total Storage**: 273,522+ rows

---

## Features

### Phase 0: Core Market Data

#### Real-time Quotes (40+ Assets)

**Stock Indices (6)**
- `^GSPC` - S&P 500
- `^DJI` - Dow Jones Industrial Average
- `^IXIC` - Nasdaq Composite
- `^NDX` - Nasdaq-100
- `^RUT` - Russell 2000
- `^VIX` - CBOE Volatility Index

**Forex Pairs (12)**
- Major: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD
- Crosses: EUR/GBP, EUR/JPY, GBP/JPY, AUD/JPY
- Emerging: NZD/USD, USD/CNY

**Commodities (12)**
- Precious Metals: GCUSD (Gold), SIUSD (Silver)
- Energy: CLUSD (Crude Oil), NGUSD (Natural Gas)
- Agricultural: ZCUSD (Corn), ZSUSD (Soybeans), KWUSD (Wheat)
- Industrial: HGUSD (Copper)

**Cryptocurrencies (10)**
- Major: BTCUSD (Bitcoin), ETHUSD (Ethereum)
- Altcoins: BNBUSD, ADAUSD, SOLUSD, DOTUSD, DOGUSD, XRPUSD

#### Historical Data
- **Coverage**: 2024-01-01 to present (expandable to 5+ years)
- **Frequency**: End-of-Day (EOD) prices
- **Storage**: ~13,000 records, ~1.6 MB
- **Access**: Query by symbol, date range, asset type

#### Market News
- **General News**: Latest financial news articles (35,802+)
- **Asset-Specific**: Filtered by stock, forex, or crypto symbol
- **Database + Live**: Historical (with analysis) + Real-time (from FMP)

#### Calendars
- **Earnings Calendar**: 140,178+ corporate earnings events
- **Economic Calendar**: Fed decisions, employment data, GDP releases (11,484+)

---

### Phase 1: Company Intelligence

#### Company Profiles
```python
CompanyProfile:
  - symbol: str
  - company_name: str
  - sector: str
  - industry: str
  - description: text
  - ceo: str
  - website: str
  - ipo_date: date
  - country: str
  - exchange: str
```

**Key Features:**
- Company metadata and leadership
- Market capitalization history
- Employee count tracking
- Merger & acquisition tracking
- CIK (Central Index Key) search for SEC lookups

#### SEC Filings
```python
SECFiling:
  - symbol: str
  - cik: str
  - filing_type: str  # 8-K, 10-K, 10-Q
  - filing_date: date
  - accepted_date: timestamp
  - filing_url: str
  - report_url: str
```

**Filing Types:**
- **8-K**: Current events, material changes
- **10-K**: Annual reports
- **10-Q**: Quarterly reports

**Sync Schedule**: Daily 7 AM EST

#### Insider Trading
```python
InsiderTrade:
  - symbol: str
  - reporting_name: str
  - transaction_type: str  # P-Buy, S-Sale, A-Award, D-Derivative
  - transaction_date: date
  - shares: int
  - price_per_share: decimal
  - total_value: decimal
  - shares_owned_after: int
```

**Use Cases:**
- Detect insider buying/selling patterns
- Correlation with stock price movements
- Sentiment indicators for specific companies

**Sync Schedule**: Daily 8 AM EST

#### Financial Statements
```python
IncomeStatement:
  - symbol: str
  - date: date
  - period: str  # FY, Q1, Q2, Q3, Q4
  - revenue: bigint
  - cost_of_revenue: bigint
  - gross_profit: bigint
  - operating_expenses: bigint
  - operating_income: bigint
  - net_income: bigint
  - eps: decimal
  - eps_diluted: decimal

BalanceSheet:
  - total_assets: bigint
  - total_liabilities: bigint
  - total_equity: bigint
  - cash: bigint
  - short_term_debt: bigint
  - long_term_debt: bigint

CashFlowStatement:
  - operating_cash_flow: bigint
  - investing_cash_flow: bigint
  - financing_cash_flow: bigint
  - free_cash_flow: bigint
  - capital_expenditure: bigint
```

**Sync Schedule**: Quarterly 9 AM EST (first day of quarter)

#### Key Metrics (TTM)
```python
KeyMetricsTTM:
  - symbol: str
  - revenue_ttm: bigint
  - net_income_ttm: bigint
  - earnings_per_share_ttm: decimal
  - pe_ratio_ttm: decimal
  - price_to_sales_ttm: decimal
  - price_to_book_ttm: decimal
  - debt_to_equity_ttm: decimal
  - return_on_equity_ttm: decimal
```

**TTM**: Trailing Twelve Months (most recent 4 quarters)

**Sync Schedule**: Daily 10 AM EST

---

### Phase 5: Intermarket Analytics

#### Volatility Tracking
```python
VIXHistory:
  - symbol: str  # VIX, VVIX, MOVE
  - date: date
  - open: decimal
  - high: decimal
  - low: decimal
  - close: decimal
  - timestamp: timestamp
```

**Tracked Indices:**
- **VIX**: S&P 500 Volatility (equity fear gauge)
- **VVIX**: VIX Volatility (volatility of volatility)
- **MOVE**: Bond Market Volatility (Merrill Lynch Option Volatility Estimate)

**Sync Schedule**: Every 5 minutes during market hours (9:30 AM - 4:00 PM EST)

#### Treasury Yields
```python
TreasuryYields:
  - date: date
  - month_1: decimal
  - month_3: decimal
  - month_6: decimal
  - year_1: decimal
  - year_2: decimal
  - year_5: decimal
  - year_10: decimal  # Benchmark
  - year_30: decimal
  - timestamp: timestamp
```

**Key Metrics Calculated:**
- **10Y-2Y Spread**: Recession indicator (inverted yield curve)
- **10Y-3M Spread**: Short-term economic outlook
- **Yield Curve Slope**: Economic growth expectations

**Sync Schedule**: Daily 5 PM EST

#### Inflation & Real Rates
```python
InflationBreakevens:
  - date: date
  - breakeven_5y: decimal
  - breakeven_10y: decimal
  - breakeven_30y: decimal

RealRates:
  - date: date
  - real_rate_5y: decimal
  - real_rate_10y: decimal
  - real_rate_30y: decimal
```

**Calculation**: Real Rate = Nominal Yield - Inflation Breakeven

**Use Case**: Purchasing power of bonds, inflation expectations

#### Dollar Index & Carry Trades
```python
DollarIndexHistory:
  - date: date
  - dxy_close: decimal  # DXY (US Dollar Index)
  - euro_weight: decimal
  - yen_weight: decimal

CarryTradeHistory:
  - date: date
  - pair: str  # e.g., AUD/JPY
  - interest_differential: decimal
  - risk_adjusted_return: decimal
```

**Carry Trade**: Borrow low-yield currency, invest in high-yield currency

#### Correlation Analysis
```python
AssetCorrelations:
  - date: date
  - asset_1: str
  - asset_2: str
  - correlation_30d: decimal
  - correlation_90d: decimal
  - correlation_180d: decimal
```

**Tracked Pairs:**
- Equities vs. Bonds (SPY vs. TLT)
- Gold vs. Real Rates
- Dollar vs. Emerging Market Currencies
- VIX vs. S&P 500

#### Regime Detection
```python
RegimeState:
  - date: date
  - regime_type: str  # risk_on, risk_off, transition
  - volatility_regime: str  # low, medium, high
  - correlation_regime: str  # diversified, concentrated
  - confidence_score: decimal
```

**Regime Types:**
- **Risk-On**: Equities up, VIX down, high-beta outperforms
- **Risk-Off**: Equities down, VIX up, defensive outperforms
- **Transition**: Mixed signals, regime shift in progress

**Sync Schedule**: Daily 6 PM EST

---

## Database Schema

### Phase 0: Core Tables

```sql
-- Real-time index quotes
CREATE TABLE index_quotes (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    price NUMERIC(20, 8) NOT NULL,
    change NUMERIC(20, 8),
    change_percent NUMERIC(10, 4),
    volume BIGINT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_symbol_timestamp (symbol, timestamp)
);

-- Forex quotes
CREATE TABLE forex_quotes (
    id UUID PRIMARY KEY,
    pair VARCHAR(10) NOT NULL,
    name VARCHAR(20) NOT NULL,
    bid NUMERIC(20, 8) NOT NULL,
    ask NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    change NUMERIC(20, 8),
    change_percent NUMERIC(10, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_pair_timestamp (pair, timestamp)
);

-- Similar tables for: commodity_quotes, crypto_quotes
-- Historical tables: market_history, forex_history, commodity_history, crypto_history

-- FMP news
CREATE TABLE fmp_news (
    id UUID PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(500) UNIQUE,
    published_at TIMESTAMP NOT NULL,
    source VARCHAR(100),
    symbols TEXT[],  -- PostgreSQL array
    sentiment VARCHAR(20),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_symbols USING GIN (symbols)
);

-- Earnings events
CREATE TABLE earnings_events (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(200),
    fiscal_date DATE NOT NULL,
    report_date TIMESTAMP NOT NULL,
    eps_actual NUMERIC(10, 4),
    eps_estimate NUMERIC(10, 4),
    revenue_actual BIGINT,
    revenue_estimate BIGINT,
    time VARCHAR(10),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Macro indicators
CREATE TABLE macro_indicators (
    id UUID PRIMARY KEY,
    indicator_name VARCHAR(50) NOT NULL,
    value NUMERIC(20, 4) NOT NULL,
    period VARCHAR(20),
    release_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Asset metadata
CREATE TABLE asset_metadata (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    asset_type VARCHAR(20) NOT NULL,  -- indices, forex, commodities, crypto
    category VARCHAR(50),
    display_name VARCHAR(100),
    short_name VARCHAR(50),
    icon_url VARCHAR(500),
    currency VARCHAR(10),
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_major BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 1: Company Intelligence Tables

```sql
-- Company profiles
CREATE TABLE company_profiles (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(200) NOT NULL,
    cik VARCHAR(20),
    sector VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    ceo VARCHAR(100),
    website VARCHAR(200),
    ipo_date DATE,
    country VARCHAR(50),
    exchange VARCHAR(50),
    currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- SEC filings
CREATE TABLE sec_filings (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    cik VARCHAR(20) NOT NULL,
    filing_type VARCHAR(10) NOT NULL,  -- 8-K, 10-K, 10-Q
    filing_date DATE NOT NULL,
    accepted_date TIMESTAMP NOT NULL,
    filing_url VARCHAR(500),
    report_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_symbol_filing (symbol, filing_type, filing_date)
);

-- Insider trading
CREATE TABLE insider_trading (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    reporting_name VARCHAR(200) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    transaction_date DATE NOT NULL,
    shares INT NOT NULL,
    price_per_share NUMERIC(20, 8),
    total_value NUMERIC(20, 2),
    shares_owned_after BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_symbol_transaction (symbol, transaction_date)
);

-- Financial statements (income, balance sheet, cash flow)
-- See app/models/financial_statements.py for full schemas

-- Key metrics TTM
CREATE TABLE key_metrics_ttm (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    revenue_ttm BIGINT,
    net_income_ttm BIGINT,
    earnings_per_share_ttm NUMERIC(10, 4),
    pe_ratio_ttm NUMERIC(10, 4),
    price_to_sales_ttm NUMERIC(10, 4),
    price_to_book_ttm NUMERIC(10, 4),
    debt_to_equity_ttm NUMERIC(10, 4),
    return_on_equity_ttm NUMERIC(10, 4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, date)
);
```

### Phase 5: Intermarket Analytics Tables

```sql
-- VIX history
CREATE TABLE vix_history (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,  -- VIX, VVIX, MOVE
    date DATE NOT NULL,
    open NUMERIC(10, 4),
    high NUMERIC(10, 4),
    low NUMERIC(10, 4),
    close NUMERIC(10, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, date)
);

-- Treasury yields
CREATE TABLE treasury_yields (
    id UUID PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    month_1 NUMERIC(10, 4),
    month_3 NUMERIC(10, 4),
    month_6 NUMERIC(10, 4),
    year_1 NUMERIC(10, 4),
    year_2 NUMERIC(10, 4),
    year_5 NUMERIC(10, 4),
    year_10 NUMERIC(10, 4),  -- Benchmark
    year_30 NUMERIC(10, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inflation breakevens
CREATE TABLE inflation_breakevens (
    id UUID PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    breakeven_5y NUMERIC(10, 4),
    breakeven_10y NUMERIC(10, 4),
    breakeven_30y NUMERIC(10, 4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Asset correlations
CREATE TABLE asset_correlations (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    asset_1 VARCHAR(20) NOT NULL,
    asset_2 VARCHAR(20) NOT NULL,
    correlation_30d NUMERIC(6, 4),
    correlation_90d NUMERIC(6, 4),
    correlation_180d NUMERIC(6, 4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, asset_1, asset_2)
);

-- Regime detection
CREATE TABLE regime_state (
    id UUID PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    regime_type VARCHAR(20) NOT NULL,  -- risk_on, risk_off, transition
    volatility_regime VARCHAR(20),  -- low, medium, high
    correlation_regime VARCHAR(20),  -- diversified, concentrated
    confidence_score NUMERIC(6, 4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

The FMP Service exposes **11 API router modules** under `/api/v1`:

### 1. Quotes (`/api/v1/quotes`)

```bash
GET  /api/v1/quotes/indices       # Get index quotes
GET  /api/v1/quotes/{symbol}      # Get specific quote
POST /api/v1/quotes/sync          # Manual sync
```

### 2. Forex (`/api/v1/forex`)

```bash
GET  /api/v1/forex/quotes         # Get forex quotes
POST /api/v1/forex/quotes/sync    # Manual sync
```

### 3. Commodities (`/api/v1/commodities`)

```bash
GET  /api/v1/commodities/quotes   # Get commodity quotes
POST /api/v1/commodities/quotes/sync
```

### 4. Crypto (`/api/v1/crypto`)

```bash
GET  /api/v1/crypto/quotes        # Get crypto quotes
POST /api/v1/crypto/quotes/sync
```

### 5. Historical Data (`/api/v1/historical`)

```bash
GET /api/v1/historical/{asset_type}/{symbol}
  ?from_date=2024-01-01
  &to_date=2024-12-31
  &limit=100

# asset_type: indices | forex | commodities | crypto
```

**Example:**
```bash
curl "http://localhost:8113/api/v1/historical/forex/EURUSD?from_date=2024-01-01&limit=10"
```

### 6. News (`/api/v1/news`)

**Database News** (Historical, with sentiment):
```bash
GET /api/v1/news                  # General news
GET /api/v1/news/stock            # Stock news
GET /api/v1/news/by-symbol/{symbol}?days=7&limit=50
```

**Live News** (Real-time from FMP):
```bash
GET /api/v1/news/live/general     # Latest general news
GET /api/v1/news/live/stock       # Stock market news
GET /api/v1/news/live/forex       # Forex news
GET /api/v1/news/live/crypto      # Crypto news
```

### 7. Earnings (`/api/v1/earnings`)

```bash
GET /api/v1/earnings/calendar
  ?from_date=2024-01-01
  &to_date=2024-01-31
  &symbol=AAPL

GET /api/v1/earnings/{symbol}/history?limit=10
POST /api/v1/earnings/sync
```

### 8. Macro Indicators (`/api/v1/macro`)

```bash
GET /api/v1/macro/indicators
  ?indicator=GDP,CPI,UNEMPLOYMENT_RATE
  &from_date=2023-01-01
```

### 9. Backfill (`/api/v1/backfill`)

```bash
POST /api/v1/backfill/indices?years=5
POST /api/v1/backfill/symbols
POST /api/v1/backfill/macro-indicators
GET  /api/v1/backfill/status
```

### 10. Metadata (`/api/v1/metadata`) ⭐ NEW

```bash
GET /api/v1/metadata/assets
  ?asset_type=forex
  &category=major_pairs
  &is_active=true
  &is_major=true

GET /api/v1/metadata/assets/{symbol}
GET /api/v1/metadata/stats
GET /api/v1/metadata/types
GET /api/v1/metadata/categories/{asset_type}
```

**Response Example:**
```json
{
  "total": 12,
  "assets": [
    {
      "id": "uuid",
      "symbol": "EURUSD",
      "name": "Euro / US Dollar",
      "display_name": "EUR/USD",
      "short_name": "Euro",
      "asset_type": "forex",
      "category": "major_pairs",
      "currency": "USD",
      "exchange": "FOREX",
      "is_active": true,
      "is_major": true,
      "icon_url": "https://..."
    }
  ],
  "asset_types": {
    "forex": 12
  }
}
```

### 11. Admin (`/api/v1/admin`) ⭐ EXTENSIVE

**Scheduler Management:**
```bash
GET  /api/v1/admin/scheduler/status
POST /api/v1/admin/scheduler/pause
POST /api/v1/admin/scheduler/resume
POST /api/v1/admin/scheduler/jobs/{job_id}/pause
POST /api/v1/admin/scheduler/jobs/{job_id}/resume
POST /api/v1/admin/trigger-market-sync
```

**Statistics & Monitoring:**
```bash
GET /api/v1/admin/stats/database
GET /api/v1/admin/stats/api-usage?days=7
GET /api/v1/admin/stats/data-quality
GET /api/v1/admin/stats/data-growth?days=30
GET /api/v1/admin/rate-limit/stats
GET /api/v1/admin/health
GET /api/v1/admin/cache/stats
```

**Data Management:**
```bash
POST /api/v1/admin/sync/historical
POST /api/v1/admin/cache/clear
```

**Example Scheduler Status Response:**
```json
{
  "running": true,
  "paused": false,
  "total_jobs": 8,
  "jobs": [
    {
      "id": "news_sync",
      "name": "Sync Financial News",
      "status": "running",
      "next_run": "2025-11-17T12:00:00",
      "trigger": "interval[0:05:00]",
      "success_rate": 99.8,
      "avg_duration": 2.34,
      "total_executions": 5234,
      "total_failures": 12
    }
  ]
}
```

---

## Background Jobs

The FMP Service runs **9 automated background jobs** via APScheduler:

### Core Market Data Jobs

| Job ID | Description | Interval | Target | Status |
|--------|-------------|----------|--------|--------|
| `news_sync` | Sync Financial News | 5 minutes | `fmp_news` | ✓ Active |
| `indices_sync` | Sync Index Quotes | 1 minute | `index_quotes` | ✓ Active |
| `forex_sync` | Sync Forex Quotes | 1 minute | `forex_quotes` | ✓ Active |
| `commodities_sync` | Sync Commodity Quotes | 5 minutes | `commodity_quotes` | ✓ Active |
| `crypto_sync` | Sync Crypto Quotes | 1 minute | `crypto_quotes` | ✓ Active |
| `earnings_sync` | Sync Earnings Calendar | 1 hour | `earnings_events` | ✓ Active |
| `macro_sync` | Sync Macro Indicators | 6 hours | `macro_indicators` | ✓ Active |
| `historical_backfill` | Weekly Historical Backfill | 7 days | All history tables | ✓ Active |

### Phase 1: Company Intelligence Jobs ⭐ NEW

| Job ID | Description | Schedule | Target | Status |
|--------|-------------|----------|--------|--------|
| `company_intelligence_sync` | Company profiles, executives, market cap | Daily 6 AM EST | `company_profiles` | ✓ Active |
| `sec_filings_sync` | SEC filings (8-K, 10-K, 10-Q) | Daily 7 AM EST | `sec_filings` | ✓ Active |
| `insider_trading_sync` | Insider trading (Form 4) | Daily 8 AM EST | `insider_trading` | ✓ Active |
| `financial_statements_sync` | Income, balance sheet, cash flow | Quarterly 9 AM EST | Financial tables | ✓ Active |
| `key_metrics_sync` | TTM key metrics | Daily 10 AM EST | `key_metrics_ttm` | ✓ Active |

### Phase 5: Intermarket Analytics Jobs ⭐ NEW

| Job ID | Description | Schedule | Target | Status |
|--------|-------------|----------|--------|--------|
| `volatility_indices_sync` | VIX, VVIX, MOVE tracking | Every 5 min (9:30 AM - 4 PM EST) | `vix_history` | ✓ Active |
| `treasury_inflation_sync` | Treasury yields + inflation | Daily 5 PM EST | `treasury_yields`, `inflation_breakevens` | ✓ Active |
| `correlation_regime` | Correlations + regime detection | Daily 6 PM EST | `asset_correlations`, `regime_state` | ✓ Active |

**Total: 15 Jobs** (8 core + 5 Phase 1 + 3 Phase 5) - Note: Some jobs registered but not in scheduler status yet

### Job Management

**Via Admin API:**
```bash
# Pause all jobs
curl -X POST http://localhost:8113/api/v1/admin/scheduler/pause

# Resume all jobs
curl -X POST http://localhost:8113/api/v1/admin/scheduler/resume

# Pause specific job
curl -X POST http://localhost:8113/api/v1/admin/scheduler/jobs/news_sync/pause

# Resume specific job
curl -X POST http://localhost:8113/api/v1/admin/scheduler/jobs/news_sync/resume
```

**Manual Triggers:**
```bash
# Trigger market sync immediately
curl -X POST http://localhost:8113/api/v1/admin/trigger-market-sync

# Trigger historical backfill
curl -X POST http://localhost:8113/api/v1/backfill/indices?years=5
```

---

## Event Publishing

The FMP Service publishes events to **RabbitMQ** exchange `finance` for consumption by other services.

### Event Types

#### `finance.quote.updated`
Published when real-time quotes are updated.

**Routing Key:** `finance.quote.updated`

```json
{
  "event_type": "finance.quote.updated",
  "symbol": "^GSPC",
  "price": 6791.69,
  "change_percent": 0.79,
  "volume": 3027308000,
  "timestamp": "2025-11-17T11:39:07",
  "_timestamp": "2025-11-17T11:39:07",
  "_source": "fmp-service"
}
```

#### `finance.earnings.announced`
Published when earnings events are ingested.

**Routing Key:** `finance.earnings.announced`

```json
{
  "event_type": "finance.earnings.announced",
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "report_date": "2025-01-30T16:30:00",
  "eps_actual": 2.18,
  "eps_estimate": 2.10,
  "eps_surprise_percent": 3.81
}
```

#### `finance.news.item`
Published when FMP financial news is ingested.

**Routing Key:** `finance.news.item`

```json
{
  "event_type": "finance.news.item",
  "title": "Apple Reports Record Q4 Earnings",
  "url": "https://example.com/article",
  "published_at": "2025-01-30T16:35:00",
  "symbols": ["AAPL"],
  "sentiment": "positive",
  "source": "Bloomberg"
}
```

### Event Consumers

**Knowledge Graph Service** consumes events to:
- Link organizations to stock symbols
- Create price points for articles
- Track earnings events

**Content Analysis Service** consumes events to:
- Extract stock mentions from articles
- Enrich with company data
- Run sentiment analysis on financial news

**Analytics Service** consumes events to:
- News-price correlation analysis
- Earnings surprise impact
- Macro context for research

---

## Rate Limiting

### FMP API Limits

**Current Plan**: 300 calls/minute (configurable)

### Implementation

**Token Bucket Algorithm** (in-memory):
```python
class FMPClient:
    async def _check_rate_limit(self) -> bool:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.rate_limit_window)

        # Remove old timestamps
        self._call_timestamps = [
            ts for ts in self._call_timestamps if ts > window_start
        ]

        # Check limit
        if len(self._call_timestamps) >= self.rate_limit_calls:
            return False  # Rate limit exceeded

        self._call_timestamps.append(now)
        return True
```

### Redis Usage Tracking ⭐ NEW

The service uses **Redis** to track FMP API usage across restarts:

**Connection**: On startup
```python
await redis_client.connect()
logger.info("✓ Redis connected for FMP usage tracking")
```

**Configuration:**
```env
FMP_RATE_LIMIT_CALLS=300
FMP_RATE_LIMIT_WINDOW=60  # 1 minute
REDIS_URL=redis://redis:6379/0
```

### Batch Optimization

To minimize API calls, the service uses **batch endpoints**:

```python
# ❌ BAD: Individual calls (6 API calls)
for symbol in ["^GSPC", "^DJI", "^IXIC", "^NDX", "^RUT", "^VIX"]:
    quote = await fmp_api.get_quote(symbol)

# ✅ GOOD: Batch call (1 API call)
symbols = "^GSPC,^DJI,^IXIC,^NDX,^RUT,^VIX"
quotes = await fmp_api.get_batch_quotes(symbols)
```

### Monitoring Rate Limits

```bash
# Check current usage
curl http://localhost:8113/api/v1/admin/rate-limit/stats

# Response:
{
  "current_calls": 42,
  "limit": 300,
  "window_seconds": 60,
  "remaining": 258,
  "percentage": 14.0,
  "status": "ok"
}
```

---

## Configuration

### Environment Variables

File: `services/fmp-service/.env`

```bash
# Service Configuration
SERVICE_NAME=fmp-service
SERVICE_PORT=8113
ENVIRONMENT=development

# FMP API
FMP_API_KEY=your_api_key_here
FMP_BASE_URL=https://financialmodelingprep.com/api
FMP_RATE_LIMIT_CALLS=300
FMP_RATE_LIMIT_WINDOW=60  # 1 minute

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=news_mcp
DATABASE_URL=postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Logging
LOG_LEVEL=INFO

# Background Jobs
MARKET_SYNC_INTERVAL_MINUTES=15
```

---

## Deployment

### Docker Compose

The service is integrated into the main `docker-compose.yml`:

```yaml
fmp-service:
  build:
    context: ./services/fmp-service
    dockerfile: Dockerfile.dev
  container_name: news-fmp-service
  restart: unless-stopped
  env_file:
    - ./services/fmp-service/.env
  environment:
    POSTGRES_HOST: postgres
    REDIS_HOST: redis
    RABBITMQ_HOST: rabbitmq
    FMP_API_KEY: ${FMP_API_KEY}
  ports:
    - "8113:8113"
  volumes:
    - ./services/fmp-service/app:/app/app  # Hot-reload
  networks:
    - news_network
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8113/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### Start/Stop

```bash
# Start service
docker compose up -d fmp-service

# View logs
docker logs news-fmp-service --tail 50 -f

# Restart service
docker compose restart fmp-service

# Stop service
docker compose stop fmp-service

# Rebuild after code changes
docker compose up -d --build fmp-service
```

### Hot Reload

The development Dockerfile mounts the `app/` directory:

```yaml
volumes:
  - ./services/fmp-service/app:/app/app
```

**Code changes are reflected instantly** without rebuild.

---

## Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8113/health

# Get index quotes
curl http://localhost:8113/api/v1/quotes/indices | jq .

# Get forex quotes
curl http://localhost:8113/api/v1/forex/quotes | jq .

# Get historical data
curl "http://localhost:8113/api/v1/historical/forex/EURUSD?from_date=2024-01-01&limit=10" | jq .

# Get asset metadata
curl http://localhost:8113/api/v1/metadata/assets?asset_type=forex | jq .

# Get scheduler status
curl http://localhost:8113/api/v1/admin/scheduler/status | jq .

# Trigger manual sync
curl -X POST http://localhost:8113/api/v1/admin/trigger-market-sync
```

### Database Verification

```bash
# Check ingested data
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT symbol, name, price, change_percent, timestamp
  FROM index_quotes
  ORDER BY timestamp DESC
  LIMIT 10;
"

# Count records by table
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT 'forex' as type, COUNT(*) as records FROM forex_quotes
  UNION ALL
  SELECT 'crypto', COUNT(*) FROM crypto_quotes
  UNION ALL
  SELECT 'news', COUNT(*) FROM fmp_news;
"

# Check Phase 1 data
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT COUNT(*) as profiles FROM company_profiles
  UNION ALL
  SELECT COUNT(*) FROM sec_filings
  UNION ALL
  SELECT COUNT(*) FROM insider_trading;
"
```

---

## Monitoring

### Metrics Endpoint

Prometheus metrics available at `/metrics` (if implemented):

```
# HELP fmp_api_calls_total Total FMP API calls
# TYPE fmp_api_calls_total counter
fmp_api_calls_total{endpoint="/v3/quote"} 12345

# HELP fmp_rate_limit_current Current rate limit usage
# TYPE fmp_rate_limit_current gauge
fmp_rate_limit_current 42
```

### Logging

Logs output to stdout/stderr (captured by Docker):

```bash
# View logs
docker logs news-fmp-service --tail 100 -f

# Filter by level
docker logs news-fmp-service 2>&1 | grep ERROR

# Filter by job
docker logs news-fmp-service 2>&1 | grep "news_sync"
```

**Log Format:**
```
2025-11-17 11:39:07,123 - app.services.data_scheduler - INFO - Scheduler started successfully
2025-11-17 11:39:07,456 - app.clients.fmp_client - INFO - FMP API Request: /v3/quote/^GSPC,^DJI
2025-11-17 11:39:07,789 - app.background_jobs.news_sync - INFO - Synced 50 news articles
```

### Health Checks

**Docker Health Check** (every 30s):
```bash
docker inspect news-fmp-service | grep -A10 Health
```

**Application Health Endpoint:**
```bash
curl http://localhost:8113/health

# Response:
{
  "status": "healthy",
  "service": "fmp-service",
  "version": "1.0.0",
  "environment": "development"
}
```

**Admin Health Endpoint:**
```bash
curl http://localhost:8113/api/v1/admin/health

# Response:
{
  "status": "healthy",
  "database_connected": true,
  "fmp_api_reachable": true,
  "scheduler_running": true,
  "last_check": "2025-11-17T11:47:05.750859"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Check logs:**
```bash
docker logs news-fmp-service --tail 50
```

**Common causes:**
1. Database connection failed → Verify postgres container is running
2. Invalid API key → Check `FMP_API_KEY` in `.env`
3. Port conflict → Check if port 8113 is already in use
4. Redis connection failed → Verify redis container is running

#### 2. Rate Limit Exceeded

**Symptom**: 429 errors or warnings in logs

**Check current usage:**
```bash
curl http://localhost:8113/api/v1/admin/rate-limit/stats
```

**Solutions:**
- Pause scheduler temporarily: `POST /api/v1/admin/scheduler/pause`
- Wait for rate limit window to reset (60 seconds)
- Pause specific high-frequency jobs

#### 3. Historical Data Missing

**Check database:**
```bash
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT 'forex' as type, COUNT(*) as records FROM forex_history
  UNION ALL
  SELECT 'crypto', COUNT(*) FROM crypto_history;
"
```

**Reload historical data:**
```bash
curl -X POST "http://localhost:8113/api/v1/backfill/indices?years=5"
```

#### 4. Scheduler Not Running

**Check status:**
```bash
curl http://localhost:8113/api/v1/admin/scheduler/status
```

**Resume if paused:**
```bash
curl -X POST http://localhost:8113/api/v1/admin/scheduler/resume
```

**Restart service:**
```bash
docker compose stop fmp-service && docker compose up -d fmp-service
```

#### 5. Background Jobs Failing

**Check job performance:**
```bash
curl http://localhost:8113/api/v1/admin/scheduler/status | jq '.jobs[] | {id, success_rate, total_failures}'
```

**View specific job logs:**
```bash
docker logs news-fmp-service 2>&1 | grep "news_sync"
```

**Common failures:**
- API rate limit exceeded → See #2
- Database connection timeout → Restart postgres
- Network issues → Check FMP API status

---

## Integration with Other Services

### Knowledge Graph Service

The Knowledge Graph Service consumes FMP events to:

1. **Link Organizations to Stock Symbols**
```cypher
// On finance.earnings.announced event
MATCH (org:Organization {name: "Apple Inc."})
MERGE (stock:Stock {symbol: "AAPL", name: "Apple Inc."})
MERGE (org)-[:HAS_STOCK]->(stock)

CREATE (event:EarningsEvent {
  date: $report_date,
  eps_actual: $eps_actual,
  eps_surprise: $eps_surprise_percent
})
CREATE (stock)-[:HAD_EARNINGS]->(event)
```

2. **Price Points for Articles**
```cypher
// When article mentions organization with stock
MATCH (article:Article)-[:MENTIONS]->(org:Organization)-[:HAS_STOCK]->(stock:Stock)

// Fetch price at publication time via FMP API
MERGE (price:PricePoint {
  symbol: stock.symbol,
  timestamp: article.published,
  price: $price_from_api
})
MERGE (article)-[:PRICE_AT_PUBLICATION]->(price)
```

### Content Analysis Service

The Content Analysis Service can:

1. **Extract Stock Mentions from Articles**
```python
# Detect stock symbols in text
symbols = extract_stock_symbols(article.text)

# Enrich with company data from FMP
for symbol in symbols:
    company = await fmp_api.get_company_profile(symbol)
```

2. **Consume FMP News Events**
```python
@consumer("finance.news.item")
async def process_fmp_news(message):
    # FMP news already has symbols tagged
    symbols = message['symbols']

    # Run sentiment analysis
    sentiment = await analyze_sentiment(message['title'])

    # Link to organizations in KG
    await link_to_organizations(symbols)
```

### Analytics Service

The Analytics Service uses FMP data for:

1. **News-Price Correlation**
```python
# Find articles mentioning stock
articles = db.query("""
    SELECT id, sentiment, published
    FROM articles
    WHERE symbols @> ARRAY['AAPL']
""")

# Get price changes from FMP data
for article in articles:
    price_before = db.query("""
        SELECT close FROM market_history
        WHERE symbol = 'AAPL'
        AND date = DATE(article.published) - INTERVAL '1 day'
    """)

    price_after = db.query("""
        SELECT close FROM market_history
        WHERE symbol = 'AAPL'
        AND date = DATE(article.published) + INTERVAL '3 days'
    """)

    impact = (price_after - price_before) / price_before
```

2. **Earnings Surprise Impact**
```python
# Get earnings with big surprises
earnings = db.query("""
    SELECT * FROM earnings_events
    WHERE ABS((eps_actual - eps_estimate) / eps_estimate) > 0.05
""")

# Analyze market reaction
for event in earnings:
    price_reaction = calculate_price_change(
        event.symbol,
        event.report_date,
        days=1
    )
```

---

## References

### FMP API Documentation

- **Main Docs**: https://site.financialmodelingprep.com/developer/docs
- **Endpoints Used**:
  - `/v3/quote/{symbols}` - Batch quotes
  - `/v3/historical-price-full/{symbol}` - Historical EOD
  - `/v3/earning_calendar` - Earnings calendar
  - `/v4/economic` - Macro indicators
  - `/v3/stock_news` - Financial news
  - `/v3/profile/{symbol}` - Company profiles (Phase 1)
  - `/v4/sec_filings` - SEC filings (Phase 1)
  - `/v4/insider-trading` - Insider trades (Phase 1)
  - `/v3/income-statement/{symbol}` - Income statements (Phase 1)
  - `/v3/historical-chart/5min/{symbol}` - Intraday data (Phase 5)

### Related Documentation

- [Architecture Decision Records](../decisions/)
- [Service README](../../services/fmp-service/README.md)
- [Knowledge Graph Integration](./knowledge-graph-service.md)
- [Analytics Service](./analytics-service.md)
- [API Contracts](../api/fmp-api.md)

---

## Support

For issues or questions:

1. **Check logs**: `docker logs news-fmp-service --tail 100`
2. **Verify FMP API status**: https://financialmodelingprep.com/status
3. **Review this documentation**
4. **Check POSTMORTEMS.md** for known issues
5. **Admin interface**: http://localhost:3000/admin/fmp-service (if available)

---

**Last Updated**: 2025-11-25
**Authors**: Claude Code, Andreas
**Status**: Production (Phase 0 + Phase 1 + Phase 5 + Phase 6)
**Next Phase**: Phase 2 (Options & Derivatives) or Phase 3 (Alternative Data)

---

## Phase 6: Unified Market Data Architecture ⭐ **NEW**

### Overview

Phase 6 introduces a **unified market data infrastructure** that consolidates FMP and Bybit data sources into a single, scalable architecture.

**Key Features:**
- **Single Source of Truth**: `market_ohlcv` table for all OHLCV data
- **Multi-Source Support**: FMP historical + Bybit real-time
- **Tiered Sync System**: Configurable symbol priorities (1min, 5min, quote)
- **Bandwidth Monitoring**: Real-time quota tracking with auto-pause
- **WebSocket Streaming**: Real-time price updates for Finance Terminal
- **Backfill Orchestration**: Automated gap detection and filling

---

### Phase 6.1: Bandwidth Monitoring System

#### Bandwidth Monitor Service

Tracks FMP API usage to prevent quota exhaustion.

**Tracking Metrics:**
- API call count (total, by endpoint, by tier)
- Data transferred (bytes, MB, GB)
- Daily quotas and remaining capacity
- Status levels (healthy/warning/critical/exhausted)

**Redis-Backed Persistence:**
```python
# Keys used
fmp:bandwidth:calls              # Total call count
fmp:bandwidth:bytes              # Total bytes transferred
fmp:bandwidth:calls_by_endpoint  # Hash: endpoint -> call count
fmp:bandwidth:bytes_by_endpoint  # Hash: endpoint -> bytes
fmp:bandwidth:calls_by_tier      # Hash: tier -> call count
fmp:bandwidth:bytes_by_tier      # Hash: tier -> bytes
fmp:bandwidth:reset_time         # Next quota reset time (UTC midnight)
```

**Quota Thresholds:**
- **80% (Warning)**: Logs warning, continues operation
- **95% (Critical)**: Auto-pauses workers to prevent exhaustion
- **100% (Exhausted)**: Blocks all API calls until reset

**API Endpoints:**

```bash
# Get current bandwidth status
GET /api/v1/admin/bandwidth/status

# Response:
{
  "total_calls": 1243,
  "total_mb": 50.0,
  "total_gb": 0.049,
  "daily_call_limit": 250000,
  "daily_bandwidth_limit_gb": 1000.0,
  "status": "healthy",
  "calls_remaining": 248757,
  "bandwidth_remaining_mb": 49950.0,
  "calls_percentage": 0.5,
  "bandwidth_percentage": 0.005,
  "reset_time": "2025-11-29T00:00:00Z",
  "next_reset_in_hours": 11.5,
  "alert": null  # Or warning/critical message
}

# Get bandwidth by endpoint
GET /api/v1/admin/bandwidth/endpoints

# Response:
{
  "endpoints": [
    {
      "endpoint": "/v3/historical-chart/5min/BTCUSD",
      "calls": 250,
      "mb": 10.0,
      "avg_bytes_per_call": 41943
    }
  ],
  "total_endpoints": 15,
  "total_mb": 50.0
}

# Get bandwidth by tier
GET /api/v1/admin/bandwidth/tiers

# Response:
{
  "tiers": [
    {
      "tier": "tier1",
      "calls": 720,
      "mb": 15.0,
      "percentage_of_total": 75.0
    }
  ]
}
```

**Configuration:**
```env
FMP_DAILY_CALL_LIMIT=500          # Free tier: 250-500 calls/day
FMP_DAILY_BANDWIDTH_GB=1.0        # Free tier: ~1 GB/month
```

---

### Phase 6.2: Unified Market Data Architecture

#### UnifiedDataService

Central service for accessing `market_ohlcv` table (Single Source of Truth).

**Features:**
- Symbol normalization (BTCUSD, BTCUSDT, BTC/USDT:USDT → internal format)
- Data inventory (available ranges per symbol/timeframe)
- Gap detection for missing data periods
- DataFrame output for backtesting compatibility

**Core Methods:**

```python
from app.services.unified_data_service import UnifiedDataService

# Get OHLCV data
df = await service.get_ohlcv(
    symbol="BTCUSDT",
    start_date="2024-01-01",
    end_date="2024-06-01",
    timeframe="1hour"
)
# Returns: DataFrame with columns [timestamp, open, high, low, close, volume]

# Get data inventory
inventory = await service.get_data_inventory("BTCUSDT")
# Returns:
{
  "symbol": "BTCUSDT",
  "timeframes": {
    "1min": {
      "earliest": "2024-01-01T00:00:00Z",
      "latest": "2024-06-01T23:59:00Z",
      "total_candles": 259200,
      "gaps": [],
      "sources": ["bybit"]
    }
  }
}

# Detect gaps
gaps = await service.detect_gaps(
    symbol="BTCUSDT",
    timeframe="1hour",
    start_date="2024-01-01",
    end_date="2024-06-01"
)
# Returns: List[DateRange] with missing periods

# Check data availability
availability = await service.check_data_availability(
    symbol="BTCUSDT",
    timeframe="1hour",
    start_date="2024-01-01",
    end_date="2024-06-01"
)
# Returns:
{
  "available": true,
  "candles_found": 4320,
  "candles_expected": 4344,
  "coverage_percent": 99.45,
  "gaps": [],
  "has_gaps": false
}
```

**Symbol Normalization:**

Uses `SymbolMapper` to convert between formats:
- **Internal**: BTCUSDT (database storage, unified format)
- **Bybit**: BTC/USDT:USDT (CCXT format)
- **FMP**: BTCUSD (FMP API format)

**Timeframe Support:**
- 1min, 5min, 15min, 30min, 1hour, 4hour, 1day

---

#### BackfillOrchestrator

Coordinates backfilling of historical market data from multiple sources.

**Features:**
- Priority-based backfill queue
- Source selection (FMP for history, Bybit for recent data)
- Gap detection and filling
- Progress tracking with callbacks
- Concurrent symbol processing

**Core Methods:**

```python
from app.services.backfill_orchestrator import BackfillOrchestrator

orchestrator = BackfillOrchestrator(db_session)

# Single symbol backfill
result = await orchestrator.backfill_symbol(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 1),
    source=BackfillSource.AUTO  # or BYBIT, FMP
)
# Returns:
{
  "job_id": "uuid",
  "symbol": "BTCUSDT",
  "status": "completed",
  "candles_fetched": 8760,
  "candles_inserted": 8760,
  "duration_seconds": 45.3,
  "source_used": "bybit"
}

# Fill detected gaps
gaps_filled = await orchestrator.fill_gaps(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date=datetime(2024, 1, 1),  # Optional
    end_date=datetime(2024, 12, 1)    # Optional
)
# Returns: List[BackfillResult] for each gap

# Backfill multiple symbols concurrently
results = await orchestrator.backfill_multiple(
    symbols=["BTCUSDT", "ETHUSD", "BNBUSDT"],
    timeframe="1h",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 1),
    max_concurrent=3
)

# Get active jobs
jobs = orchestrator.get_active_jobs()
# Returns: List[Dict] with job status and progress
```

**Source Selection Strategy:**
- **Recent data (< 30 days)**: Bybit (faster, more granular)
- **Historical data (> 30 days)**: FMP (longer history)
- **AUTO mode**: System decides based on date range

**PostgreSQL Upsert:**
```sql
-- Uses ON CONFLICT to handle duplicates gracefully
INSERT INTO market_ohlcv (symbol, interval, timestamp, open, high, low, close, volume, source)
VALUES (...)
ON CONFLICT (symbol, interval, timestamp)
DO UPDATE SET
  open = EXCLUDED.open,
  high = EXCLUDED.high,
  low = EXCLUDED.low,
  close = EXCLUDED.close,
  volume = EXCLUDED.volume,
  source = EXCLUDED.source,
  updated_at = NOW();
```

---

#### BybitFetcher

Fetches historical OHLCV data from Bybit exchange for backfilling.

**Features:**
- Automatic pagination (Bybit max 1000 candles per request)
- Rate limit handling with exponential backoff
- Symbol normalization via SymbolMapper
- Progress tracking for long-running backfills

**Core Methods:**

```python
from app.services.bybit_fetcher import BybitFetcher

async with BybitFetcher() as fetcher:
    # Fetch OHLCV data
    candles = await fetcher.fetch_ohlcv(
        symbol="BTCUSDT",
        timeframe="1h",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 1),
        progress_callback=lambda fetched, total: print(f"{fetched}/{total}")
    )
    # Returns: List[OHLCVCandle] (timestamp, OHLCV, volume)

    # Fetch recent candles
    recent = await fetcher.fetch_recent(
        symbol="BTCUSDT",
        timeframe="1h",
        limit=200
    )

    # Get stats
    stats = fetcher.get_stats()
    # Returns:
    {
      "request_count": 42,
      "rate_limit_delay": 0.2,
      "supported_timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
      "max_candles_per_request": 1000
    }
```

**Rate Limiting:**
- Default: 200ms between requests (5 req/sec)
- Exponential backoff on rate limit errors
- Network error retry with 2-second delay

**Data Deduplication:**
- Removes duplicate timestamps at batch boundaries
- Ensures sorted output (ascending timestamps)

---

### Phase 6.3: Finance Terminal API

#### Market Candles Endpoints

Provides intraday candlestick (OHLCV) data for all asset types.

```bash
# Get candles for a symbol
GET /api/v1/market/candles/{symbol}?interval=1min&limit=100
# Returns: Last 100 1-minute candles

# Get candles with date range
GET /api/v1/market/candles/BTCUSD?interval=5min&from_timestamp=2025-11-22T00:00:00Z&to_timestamp=2025-11-22T23:59:59Z
# Returns: All 5-minute candles for Nov 22

# Get latest candle
GET /api/v1/market/candles/BTCUSD/latest?interval=1min
# Returns: Most recent 1-minute candle

# Get candles by asset type
GET /api/v1/market/candles/asset-type/crypto?interval=1min&limit=10
# Returns: Latest 10 1-minute candles for ALL crypto symbols

# Get candles for time range
GET /api/v1/market/candles/BTCUSD/timerange?interval=1min&hours=1
# Returns: All 1-minute candles from last hour (60 candles)
```

**Supported Intervals:**
- 1min (1-minute)
- 5min (5-minute)
- 15min (15-minute)
- 30min (30-minute)
- 1hour (1-hour)
- 4hour (4-hour)

**Response Format:**
```json
{
  "symbol": "BTCUSD",
  "asset_type": "crypto",
  "interval": "1min",
  "candles": [
    {
      "timestamp": "2025-11-22T18:45:00Z",
      "open": 97250.5,
      "high": 97280.0,
      "low": 97200.0,
      "close": 97265.0,
      "volume": 1234567,
      "vwap": 97245.3,        // Optional
      "trades": 42            // Optional
    }
  ],
  "count": 100
}
```

**Data Availability:**
- **Tier 1 symbols (50)**: 1-minute candles, 30-day retention
- **Tier 2 symbols (100)**: 5-minute candles, 90-day retention
- **All symbols**: 15min+, 1-year retention

---

#### WebSocket Streaming

Real-time data streams for Finance Terminal.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8113/ws/finance');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case 'prices':
      // All market quotes (157 symbols)
      console.log('Price update:', msg.data.length, 'symbols');
      break;
    case 'status':
      // Market hours status for all asset types
      console.log('Market status:', msg.data);
      break;
    case 'health':
      // System health (DB, API quota, workers)
      console.log('System health:', msg.data.status);
      break;
  }
};
```

**Message Types:**

1. **prices** (1-second interval)
   ```json
   {
     "type": "prices",
     "data": [
       {
         "symbol": "BTCUSD",
         "asset_type": "crypto",
         "price": 97265.0,
         "change": 1250.5,
         "change_percent": 1.30,
         "volume": 1234567890,
         "timestamp": "2025-11-22T18:45:00Z"
       }
     ],
     "timestamp": "2025-11-22T18:45:01Z"
   }
   ```

2. **status** (60-second interval)
   ```json
   {
     "type": "status",
     "data": {
       "indices": {
         "status": "closed",
         "reason": "Weekend",
         "next_open": "2025-11-25T09:30:00-05:00"
       },
       "forex": { "status": "open", ... },
       "commodities": { "status": "closed", ... },
       "crypto": { "status": "open", "reason": "24/7 Market" }
     },
     "timestamp": "2025-11-22T18:45:00Z"
   }
   ```

3. **health** (30-second interval)
   ```json
   {
     "type": "health",
     "data": {
       "status": "healthy",
       "database": {
         "connected": true,
         "latency_ms": 2.5
       },
       "api_quota": {
         "daily_used": 1243,
         "daily_remaining": 248757,
         "usage_percentage": 0.5
       },
       "workers": [
         {
           "name": "tier1_worker",
           "status": "running",
           "last_heartbeat": "2025-11-22T18:45:00Z"
         }
       ]
     },
     "timestamp": "2025-11-22T18:45:00Z"
   }
   ```

**Performance:**
- Efficient: Only broadcasts when clients connected
- Concurrent: Handles multiple clients simultaneously
- Resilient: Auto-cleanup of dead connections

---

### Phase 6.4: Tier Management

#### JSON-Based Configuration (Legacy)

Original tier management via `config/symbol_tiers.json`.

**API Endpoints:**

```bash
# Get tier statistics
GET /api/v1/admin/tiers/statistics

# Get complete configuration
GET /api/v1/admin/tiers/config

# List symbols with filters
GET /api/v1/admin/tiers/symbols?tier=tier1&asset_type=crypto&limit=100

# Add symbol (validation only)
POST /api/v1/admin/tiers/symbols
{
  "symbol": "BTCUSD",
  "tier": "tier1",
  "asset_type": "crypto"
}

# Update symbol tier (validation only)
PUT /api/v1/admin/tiers/symbols/BTCUSD
{
  "new_tier": "tier2"
}

# Delete symbol (validation only)
DELETE /api/v1/admin/tiers/symbols/BTCUSD?delete_data=false

# Reload configuration
POST /api/v1/admin/tiers/reload
```

**Important:**
- These endpoints **validate** but **do not modify** the JSON config
- Manual config update required in `config/symbol_tiers.json`
- Service restart needed to reload configuration

---

#### Database-Based Tier Management (Phase 7)

New database-driven tier system (replaces JSON config).

**Features:**
- Dynamic tier management (no restart required)
- Sync configuration stored in `sync_configuration` table
- Worker state tracking
- Real-time config updates

**API Endpoints:**

```bash
# List all symbols (DB-based)
GET /api/v1/admin/db-tiers/symbols

# Get symbol details
GET /api/v1/admin/db-tiers/symbols/{symbol}

# Create new symbol sync config
POST /api/v1/admin/db-tiers/symbols
{
  "symbol": "BTCUSD",
  "asset_type": "crypto",
  "interval": "1min",
  "tier": 1,
  "is_active": true
}

# Update symbol config
PUT /api/v1/admin/db-tiers/symbols/{symbol}
{
  "interval": "5min",
  "tier": 2,
  "is_active": true
}

# Delete symbol (soft delete)
DELETE /api/v1/admin/db-tiers/symbols/{symbol}

# Bulk operations
POST /api/v1/admin/db-tiers/bulk/activate
POST /api/v1/admin/db-tiers/bulk/deactivate
POST /api/v1/admin/db-tiers/bulk/update-tier
```

**Database Schema:**
```sql
CREATE TABLE sync_configuration (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    asset_type VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    tier INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### Phase 6.5: Unified Backfill API

Backfilling for predictions service (ML training data).

**Purpose:** Transform FMP OHLCV data into `predictions.analysis_logs` format with technical indicators.

**API Endpoints:**

```bash
# Backfill single symbol
POST /api/v1/unified-backfill/symbol
{
  "symbol": "BTCUSD",
  "days_back": 365,
  "interval": "5min"
}

# Backfill entire tier
POST /api/v1/unified-backfill/tier
{
  "tier_id": 1,
  "days_back": 365,
  "interval": "5min"
}

# Check backfill status
GET /api/v1/unified-backfill/status/BTCUSD

# List available symbols
GET /api/v1/unified-backfill/symbols?tier_id=1

# Health check
GET /api/v1/unified-backfill/health
```

**Features:**
- Fetches FMP OHLCV data
- Computes RSI, EMA, and other indicators
- Transforms data into `analysis_logs` format
- Inserts into `predictions.analysis_logs` table

**Symbol Mapping:**
```python
SYMBOL_MAP = {
    "BTCUSD": "BTC/USDT:USDT",    # FMP -> Bybit
    "ETHUSD": "ETH/USDT:USDT",
    # ... 18 crypto symbols
}
```

---

## Recent Improvements (2025-11-25 to 2025-11-28)

### v2.2.0 Updates - Phase 6 Complete

#### Bandwidth Monitoring System
- Real-time API usage tracking (calls + bytes)
- Redis-backed persistence (survives restarts)
- Automatic quota enforcement (warning@80%, stop@95%)
- Daily reset at midnight UTC
- Detailed breakdown by endpoint and tier
- See [Phase 6.1](#phase-61-bandwidth-monitoring-system)

#### Unified Market Data Architecture
- **UnifiedDataService**: Single source of truth for OHLCV data
- **BackfillOrchestrator**: Automated gap detection and filling
- **BybitFetcher**: Historical data from Bybit exchange
- Symbol normalization (BTCUSD ↔ BTCUSDT ↔ BTC/USDT:USDT)
- Data inventory and gap detection
- See [Phase 6.2](#phase-62-unified-market-data-architecture)

#### Finance Terminal API
- WebSocket streaming (prices, status, health)
- Real-time price updates (1-second interval)
- Market status updates (60-second interval)
- System health monitoring (30-second interval)
- OHLCV candlestick endpoints (multiple intervals)
- See [Phase 6.3](#phase-63-finance-terminal-api)

#### Tier Management Enhancements
- JSON-based configuration (legacy, validation-only)
- Database-driven tier system (Phase 7, dynamic updates)
- Bulk operations (activate/deactivate/update)
- Sync configuration table
- Worker state tracking
- See [Phase 6.4](#phase-64-tier-management)

#### Unified Backfill API
- Single symbol backfill with technical indicators
- Tier-based bulk backfilling
- Status checking and progress tracking
- Symbol mapping (FMP ↔ Bybit)
- Integration with predictions service
- See [Phase 6.5](#phase-65-unified-backfill-api)

### v2.1.1 Updates (2025-11-25)

#### Configurable Rate Limiting
- Rate limit settings (calls/window) now configurable via environment variables
- `FMP_RATE_LIMIT_CALLS` and `FMP_RATE_LIMIT_WINDOW` in settings
- Token bucket algorithm supports dynamic configuration

#### Standardized Error Responses
- New `ErrorResponse` and `PaginatedResponse` schemas in `app/schemas/response.py`
- Generic typing support for type-safe paginated responses
- Consistent error format across all endpoints

#### DCC-GARCH Caching Layer
- In-memory caching for correlation matrix calculations
- Configurable TTL (default: 5 minutes)
- `use_cache` parameter for bypassing cache when needed
- Significant performance improvement for repeated calculations

#### Database Optimizations
- Added composite index `idx_fmp_news_source` on `(source, published_at)` for news queries
- Improved query performance for source-based filtering

#### Documentation Improvements
- Enhanced docstrings for model files (`quotes.py`, `news.py`)
- Added data source references and update frequency information
- Documented index usage and attribute descriptions
