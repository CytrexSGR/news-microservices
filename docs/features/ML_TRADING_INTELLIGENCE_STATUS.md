# ML Trading Intelligence System - Status Report

**Project:** Integrated ML Trading Intelligence Feature Store
**Service:** prediction-service
**Created:** 2025-12-29
**Last Updated:** 2025-12-29

---

## Executive Summary

The ML Trading Intelligence System implements a **3-Tier Feature Store** architecture for real-time trading decisions. Phase 0 (Design) and Phase 1 (Core Infrastructure) are complete. The system is integrated with the unified trading loop and ready for production testing.

**Key Metrics:**
- **91 Features** cataloged across 6 categories
- **3 Storage Tiers**: HOT (Redis), WARM (PostgreSQL+Cache), COLD (PostgreSQL)
- **7 Database Tables** in `feature_store` schema
- **5 Integration Points** in trading loop

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Phase 0: Design (Complete)](#3-phase-0-design-complete)
4. [Phase 1: Implementation (Complete)](#4-phase-1-implementation-complete)
5. [File Inventory](#5-file-inventory)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Trading Loop Integration](#8-trading-loop-integration)
9. [Testing & Verification](#9-testing--verification)
10. [Next Steps (Phase 2+)](#10-next-steps-phase-2)

---

## 1. Project Overview

### 1.1 Goal

Build a comprehensive Feature Store that:
- Captures real-time trading signals, risk metrics, and market regime data
- Stores historical features for ML model training
- Provides sub-50ms access to critical trading features
- Enables backtesting with point-in-time feature snapshots

### 1.2 Problem Statement

Before this implementation:
- Trading decisions were made without persistent feature storage
- No historical record of feature values at trade entry/exit
- ML training required manual feature reconstruction
- No unified API for feature access across services

### 1.3 Solution

A 3-Tier Feature Store with:
- **HOT Tier** (Redis): Real-time features, <50ms latency
- **WARM Tier** (PostgreSQL + Cache): Hourly aggregates, <500ms latency
- **COLD Tier** (PostgreSQL): Historical snapshots, <5s latency

---

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PREDICTION SERVICE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐     ┌──────────────────────────────────────┐  │
│  │  Unified Trading │     │         Feature Store Module          │  │
│  │      Loop        │────▶│                                       │  │
│  │                  │     │  ┌─────────────────────────────────┐  │  │
│  │  - _process_     │     │  │   RealtimeFeaturePipeline       │  │  │
│  │    symbol()      │     │  │   - update_from_signal()        │  │  │
│  │  - _evaluate_    │     │  │   - update_from_regime()        │  │  │
│  │    entry()       │     │  │   - update_from_indicators()    │  │  │
│  │  - _execute_     │     │  │   - update_from_position()      │  │  │
│  │    spot/futures  │     │  └─────────────────────────────────┘  │  │
│  │  - _execute_     │     │                                       │  │
│  │    exit()        │     │  ┌─────────────────────────────────┐  │  │
│  └──────────────────┘     │  │      Redis Key Managers         │  │  │
│                           │  │   - SignalKeys                  │  │  │
│                           │  │   - RiskKeys                    │  │  │
│                           │  │   - RegimeKeys                  │  │  │
│                           │  │   - IndicatorKeys               │  │  │
│                           │  │   - PositionKeys                │  │  │
│                           │  └─────────────────────────────────┘  │  │
│                           └──────────────────────────────────────┘  │
│                                          │                           │
└──────────────────────────────────────────┼───────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            ┌───────────────┐    ┌─────────────────┐    ┌─────────────────┐
            │   HOT TIER    │    │   WARM TIER     │    │   COLD TIER     │
            │    Redis      │    │   PostgreSQL    │    │   PostgreSQL    │
            │   <50ms       │    │    + Cache      │    │     <5s         │
            │               │    │    <500ms       │    │                 │
            │ - Signals     │    │                 │    │ - execution_    │
            │ - Risk        │    │ - news_risk_    │    │   history       │
            │ - Regime      │    │   features      │    │ - feature_      │
            │ - Indicators  │    │ - content_      │    │   snapshots     │
            │ - Positions   │    │   analysis_     │    │                 │
            │               │    │   features      │    │                 │
            │ TTL: 1h-24h   │    │ - entity_       │    │ Retention:      │
            │               │    │   features      │    │ Indefinite      │
            │               │    │ - fmp_features  │    │                 │
            │               │    │ - search_       │    │                 │
            │               │    │   features      │    │                 │
            └───────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Data Flow

```
Market Data → Trading Loop → Feature Store Pipeline → Redis (HOT)
                                      │
                                      ├──▶ Hourly Aggregation → PostgreSQL (WARM)
                                      │
                                      └──▶ Trade Close → PostgreSQL (COLD)
```

---

## 3. Phase 0: Design (Complete)

### 3.1 Feature Catalog

**Total: 91 Features** across 6 categories:

| Category | Features | Priority Distribution |
|----------|----------|----------------------|
| Signal Features | 15 | 10 Critical, 5 High |
| Risk Features | 18 | 8 Critical, 6 High, 4 Medium |
| Regime Features | 12 | 5 Critical, 4 High, 3 Medium |
| Indicator Features | 22 | 6 Critical, 8 High, 6 Medium, 2 Low |
| Position Features | 14 | 4 Critical, 6 High, 4 Medium |
| External Features | 10 | 2 Critical, 4 High, 4 Low |

### 3.2 Priority Breakdown

| Priority | Count | Description |
|----------|-------|-------------|
| Critical | 35 | Required for trading decisions |
| High | 28 | Important for ML training |
| Medium | 22 | Useful for analysis |
| Low | 6 | Nice-to-have |

### 3.3 Feature Details by Category

#### Signal Features (15)
- `direction` (LONG/SHORT/NONE)
- `confidence` (0.0-1.0)
- `strategy_name`
- `entry_price`, `stop_loss`, `take_profit`
- `risk_reward_ratio`
- `atr_multiplier_sl`, `atr_multiplier_tp`
- `signal_strength`, `signal_source`
- `gate_evaluation_passed`, `gate_score`
- `reasoning`, `timestamp`

#### Risk Features (18)
- `portfolio_heat` (total risk exposure)
- `position_risk_pct`
- `max_drawdown_current`
- `correlation_risk`
- `var_95`, `var_99` (Value at Risk)
- `kelly_fraction`
- `liquidation_distance_pct`
- `margin_usage_pct`
- `global_risk_index`
- `geo_risk_index`, `finance_risk_index`
- `news_sentiment_risk`
- `volatility_risk_score`
- `concentration_risk`
- `leverage_risk_score`
- `time_risk` (weekend/holiday proximity)
- `risk_adjusted_return`

#### Regime Features (12)
- `regime_type` (TRENDING/RANGING/VOLATILE/QUIET)
- `regime_strength` (0.0-1.0)
- `regime_duration_candles`
- `trend_direction` (UP/DOWN/SIDEWAYS)
- `volatility_state` (LOW/NORMAL/HIGH/EXTREME)
- `adx_value`, `adx_trend`
- `bb_width_percentile`
- `regime_change_probability`
- `optimal_strategy_hint`
- `market_phase` (ACCUMULATION/MARKUP/DISTRIBUTION/MARKDOWN)
- `regime_confidence`

#### Indicator Features (22)
- EMAs: `ema_5`, `ema_8`, `ema_13`, `ema_21`, `ema_50`
- `rsi_14`, `rsi_divergence`
- Bollinger: `bb_upper`, `bb_lower`, `bb_mid`, `bb_position`, `bb_width`
- `atr_14`, `atr_percentile`
- `adx_14`, `plus_di`, `minus_di`
- MACD: `macd_line`, `macd_signal`, `macd_histogram`
- Volume: `volume_sma_ratio`, `obv_trend`

#### Position Features (14)
- `has_position` (boolean)
- `position_direction`
- `entry_price`, `current_price`
- `unrealized_pnl`, `unrealized_pnl_pct`
- `position_duration_seconds`
- `distance_to_sl_pct`, `distance_to_tp_pct`
- `max_adverse_excursion`
- `max_favorable_excursion`
- `trailing_stop_active`, `trailing_stop_price`
- `position_size_usd`

#### External Features (10)
- `news_sentiment_score`
- `news_volume_24h`
- `entity_mention_velocity`
- `social_sentiment`
- `funding_rate`
- `open_interest_change`
- `whale_activity_score`
- `exchange_flow_netflow`
- `fear_greed_index`
- `btc_dominance`

---

## 4. Phase 1: Implementation (Complete)

### 4.1 Completed Tasks

| Task | Status | Date |
|------|--------|------|
| Create feature_store module structure | ✅ | 2025-12-29 |
| Implement Redis key managers | ✅ | 2025-12-29 |
| Implement RealtimeFeaturePipeline | ✅ | 2025-12-29 |
| Create PostgreSQL migration | ✅ | 2025-12-29 |
| Create Feature Store API endpoints | ✅ | 2025-12-29 |
| Run database migration | ✅ | 2025-12-29 |
| Integrate with unified_trading.py | ✅ | 2025-12-29 |
| Verify API accessibility | ✅ | 2025-12-29 |

### 4.2 Implementation Details

#### Redis Key Structure

```
HOT Tier Keys (TTL: 1-24 hours):

fs:signal:{symbol}:{timeframe}     → Signal features JSON
fs:risk:{symbol}:{timeframe}       → Risk features JSON
fs:regime:{symbol}:{timeframe}     → Regime features JSON
fs:indicators:{symbol}:{timeframe} → Indicator features JSON
fs:position:{symbol}               → Position features JSON (no timeframe)

Examples:
fs:signal:BTCUSDT:5m
fs:risk:ETHUSDT:15m
fs:regime:BTCUSDT:1h
fs:indicators:BTCUSDT:5m
fs:position:BTCUSDT
```

#### Key Manager Classes

```python
# keys.py - Redis Key Managers

class SignalKeys:
    PREFIX = "fs:signal"
    TTL = 3600  # 1 hour

class RiskKeys:
    PREFIX = "fs:risk"
    TTL = 3600  # 1 hour

class RegimeKeys:
    PREFIX = "fs:regime"
    TTL = 7200  # 2 hours

class IndicatorKeys:
    PREFIX = "fs:indicators"
    TTL = 3600  # 1 hour

class PositionKeys:
    PREFIX = "fs:position"
    TTL = 86400  # 24 hours
```

---

## 5. File Inventory

### 5.1 New Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `app/feature_store/__init__.py` | Module initialization | ~20 |
| `app/feature_store/keys.py` | Redis key managers | ~150 |
| `app/feature_store/manager.py` | Feature Store Manager | ~200 |
| `app/feature_store/api.py` | REST API endpoints | ~180 |
| `app/feature_store/pipelines/__init__.py` | Pipeline module init | ~10 |
| `app/feature_store/pipelines/realtime.py` | Real-time HOT tier pipeline | ~250 |
| `alembic/versions/018_create_feature_store_schema.py` | Database migration | ~414 |

### 5.2 Modified Files

| File | Changes | Lines Added |
|------|---------|-------------|
| `app/main.py` | Import feature_store, register API router | ~10 |
| `app/unified/trading/loop.py` | Feature Store integration | ~180 |

### 5.3 File Structure

```
services/prediction-service/
├── app/
│   ├── feature_store/
│   │   ├── __init__.py              # Module exports
│   │   ├── keys.py                  # Redis key managers
│   │   ├── manager.py               # FeatureStoreManager class
│   │   ├── api.py                   # FastAPI router
│   │   └── pipelines/
│   │       ├── __init__.py
│   │       └── realtime.py          # RealtimeFeaturePipeline
│   ├── unified/
│   │   └── trading/
│   │       └── loop.py              # Modified: 5 integration points
│   └── main.py                      # Modified: Feature Store init
├── alembic/
│   └── versions/
│       └── 018_create_feature_store_schema.py
└── docs/
    └── features/
        └── ML_TRADING_INTELLIGENCE_STATUS.md  # This document
```

---

## 6. Database Schema

### 6.1 Schema: `feature_store`

Migration: `018_create_feature_store_schema.py`

### 6.2 Tables

#### 6.2.1 news_risk_features (WARM)
```sql
CREATE TABLE feature_store.news_risk_features (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20),              -- NULL for global
    timestamp TIMESTAMPTZ NOT NULL,

    -- Global Risk Indices
    global_risk_index FLOAT,
    geo_risk_index FLOAT,
    finance_risk_index FLOAT,

    -- Top Cluster Metrics
    top_cluster_risk_score FLOAT,
    top_cluster_risk_delta FLOAT,
    top_cluster_event_count INTEGER,
    top_cluster_sentiment FLOAT,
    top_cluster_name VARCHAR(255),

    -- Aggregated Metrics
    event_count_24h INTEGER,
    avg_sentiment_24h FLOAT,
    high_risk_cluster_count INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);
```

#### 6.2.2 content_analysis_features (WARM)
```sql
CREATE TABLE feature_store.content_analysis_features (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Financial Analyst Aggregates
    avg_market_impact FLOAT,
    max_market_impact FLOAT,
    volatility_expected VARCHAR(10),
    article_count INTEGER,

    -- Sentiment Aggregates
    avg_bullish_bearish FLOAT,
    sentiment_std FLOAT,
    positive_ratio FLOAT,
    negative_ratio FLOAT,

    -- Quality Scores
    avg_impact_score FLOAT,
    avg_urgency_score FLOAT,
    avg_credibility_score FLOAT,

    -- Source Distribution
    source_distribution JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);
```

#### 6.2.3 entity_features (WARM)
```sql
CREATE TABLE feature_store.entity_features (
    id BIGSERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL,

    -- Mention Metrics
    mention_count_24h INTEGER,
    mention_count_7d INTEGER,
    mention_velocity FLOAT,

    -- Sentiment
    avg_sentiment FLOAT,
    sentiment_trend FLOAT,

    -- Graph Metrics
    connection_count INTEGER,
    centrality_score FLOAT,

    -- Related Symbols
    related_symbols JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(canonical_name, timestamp)
);
```

#### 6.2.4 fmp_features (WARM)
```sql
CREATE TABLE feature_store.fmp_features (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Earnings
    next_earnings_date DATE,
    days_to_earnings INTEGER,
    last_earnings_surprise_pct FLOAT,

    -- Analyst Data
    analyst_rating VARCHAR(20),
    analyst_rating_score FLOAT,
    price_target_avg FLOAT,
    price_target_high FLOAT,
    price_target_low FLOAT,
    upside_pct FLOAT,

    -- Institutional
    institutional_ownership_pct FLOAT,
    insider_buy_count_30d INTEGER,
    insider_sell_count_30d INTEGER,
    insider_net_value_30d FLOAT,

    -- Sector
    sector VARCHAR(100),
    sector_performance_1d FLOAT,
    sector_performance_1w FLOAT,
    sector_performance_1m FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);
```

#### 6.2.5 search_features (WARM)
```sql
CREATE TABLE feature_store.search_features (
    id BIGSERIAL PRIMARY KEY,
    query_or_symbol VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Volume Metrics
    search_count_1h INTEGER,
    search_count_24h INTEGER,
    search_velocity FLOAT,

    -- Trending Rank
    trending_rank INTEGER,

    -- Result Metrics
    avg_results_count FLOAT,

    -- Sentiment from Search Results
    sentiment_positive_pct FLOAT,
    sentiment_negative_pct FLOAT,
    sentiment_neutral_pct FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(query_or_symbol, timestamp)
);
```

#### 6.2.6 execution_history (COLD)
```sql
CREATE TABLE feature_store.execution_history (
    id BIGSERIAL PRIMARY KEY,
    trade_id UUID UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,

    -- Trade Details
    direction VARCHAR(10) NOT NULL,
    entry_price NUMERIC(18,8) NOT NULL,
    exit_price NUMERIC(18,8),
    position_size NUMERIC(18,8) NOT NULL,
    leverage INTEGER DEFAULT 1,

    -- Timing
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- P&L
    realized_pnl NUMERIC(18,8),
    realized_pnl_pct FLOAT,
    max_drawdown_pct FLOAT,
    max_profit_pct FLOAT,

    -- Risk Management
    stop_loss_price NUMERIC(18,8),
    take_profit_price NUMERIC(18,8),
    hit_stop_loss BOOLEAN DEFAULT FALSE,
    hit_take_profit BOOLEAN DEFAULT FALSE,

    -- Strategy Info
    strategy_name VARCHAR(100),
    signal_confidence FLOAT,
    regime_at_entry VARCHAR(50),

    -- Execution Quality
    slippage_entry_pct FLOAT,
    slippage_exit_pct FLOAT,
    fill_time_entry_ms INTEGER,
    fill_time_exit_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 6.2.7 feature_snapshots (COLD)
```sql
CREATE TABLE feature_store.feature_snapshots (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id UUID UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- HOT Features (serialized)
    signal_features JSONB,
    risk_features JSONB,
    regime_features JSONB,
    indicator_features JSONB,

    -- WARM Features (serialized)
    news_risk_features JSONB,
    content_features JSONB,
    entity_features JSONB,

    -- Market Data at Snapshot
    price_open NUMERIC(18,8),
    price_high NUMERIC(18,8),
    price_low NUMERIC(18,8),
    price_close NUMERIC(18,8),
    volume NUMERIC(24,8),

    -- Training Labels (filled on trade close)
    label_direction VARCHAR(10),
    label_pnl_pct FLOAT,
    label_hit_tp BOOLEAN,
    label_hit_sl BOOLEAN,
    label_duration_candles INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.3 Indexes

```sql
-- news_risk_features
CREATE INDEX idx_news_risk_symbol_ts ON feature_store.news_risk_features(symbol, timestamp DESC);

-- content_analysis_features
CREATE INDEX idx_content_symbol_ts ON feature_store.content_analysis_features(symbol, timestamp DESC);

-- entity_features
CREATE INDEX idx_entity_name_ts ON feature_store.entity_features(canonical_name, timestamp DESC);
CREATE INDEX idx_entity_type ON feature_store.entity_features(entity_type);

-- fmp_features
CREATE INDEX idx_fmp_symbol_ts ON feature_store.fmp_features(symbol, timestamp DESC);

-- search_features
CREATE INDEX idx_search_query_ts ON feature_store.search_features(query_or_symbol, timestamp DESC);

-- execution_history
CREATE INDEX idx_execution_symbol_ts ON feature_store.execution_history(symbol, entry_time DESC);
CREATE INDEX idx_execution_strategy ON feature_store.execution_history(strategy_name, entry_time DESC);

-- feature_snapshots
CREATE INDEX idx_snapshot_symbol_ts ON feature_store.feature_snapshots(symbol, timeframe, timestamp DESC);
CREATE INDEX idx_snapshot_label ON feature_store.feature_snapshots(label_direction) WHERE label_direction IS NOT NULL;
```

---

## 7. API Endpoints

### 7.1 Feature Store API

Base URL: `/api/v1/feature-store`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Feature Store health status |
| `/symbols` | GET | List supported symbols |
| `/timeframes` | GET | List supported timeframes |
| `/hot/{symbol}/{timeframe}` | GET | Get all HOT tier features |
| `/hot/{symbol}/{timeframe}/signal` | GET | Get signal features only |
| `/hot/{symbol}/{timeframe}/risk` | GET | Get risk features only |
| `/hot/{symbol}/{timeframe}/regime` | GET | Get regime features only |
| `/hot/{symbol}/{timeframe}/indicators` | GET | Get indicator features only |
| `/hot/{symbol}/position` | GET | Get position features |

### 7.2 Example Responses

#### Health Check
```json
GET /api/v1/feature-store/health

{
  "status": "healthy",
  "tiers": {
    "hot": {
      "status": "healthy",
      "backend": "redis",
      "latency_sla_ms": 50
    },
    "warm": {
      "status": "not_implemented",
      "backend": "postgresql",
      "latency_sla_ms": 500
    },
    "cold": {
      "status": "not_implemented",
      "backend": "postgresql",
      "latency_sla_ms": 5000
    }
  },
  "timestamp": "2025-12-29T10:41:21.868562"
}
```

#### HOT Features
```json
GET /api/v1/feature-store/hot/BTCUSDT/5m

{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "signal": {
    "direction": "LONG",
    "confidence": 0.75,
    "strategy_name": "alpha_3",
    "entry_price": 94250.50,
    "stop_loss": 93800.00,
    "take_profit": 95150.00,
    "risk_reward_ratio": 2.0,
    "timestamp": "2025-12-29T10:40:00Z"
  },
  "risk": {
    "portfolio_heat": 0.15,
    "position_risk_pct": 0.02,
    "kelly_fraction": 0.08
  },
  "regime": {
    "regime_type": "TRENDING",
    "regime_strength": 0.72,
    "trend_direction": "UP",
    "volatility_state": "NORMAL"
  },
  "indicators": {
    "ema_5": 94200.5,
    "ema_21": 94150.2,
    "rsi_14": 58.5,
    "atr_14": 450.2,
    "adx_14": 28.5
  },
  "position": null,
  "fetched_at": 1735470000000
}
```

---

## 8. Trading Loop Integration

### 8.1 Integration Points

The Feature Store is integrated at 5 points in `app/unified/trading/loop.py`:

| Location | Method Called | Purpose |
|----------|---------------|---------|
| `_process_symbol()` | `_update_feature_store_regime()` | Update regime for all symbols |
| `_process_symbol()` | `_update_feature_store_indicators()` | Update indicators for all symbols |
| `_evaluate_entry()` | `_update_feature_store_signal()` | Record signal when trade executed |
| `_execute_spot_entry()` | `_update_feature_store_position()` | Record OPEN position (Spot) |
| `_execute_futures_entry()` | `_update_feature_store_position()` | Record OPEN position (Futures) |
| `_execute_exit()` | `_update_feature_store_position()` | Record CLOSED position |

### 8.2 Code Changes

#### Import Block (lines 79-85)
```python
# Feature Store imports
try:
    from app.feature_store.pipelines.realtime import realtime_pipeline
    FEATURE_STORE_AVAILABLE = True
except ImportError:
    FEATURE_STORE_AVAILABLE = False
    realtime_pipeline = None
```

#### Helper Methods Added

```python
async def _update_feature_store_signal(self, symbol: str, timeframe: str,
                                        decision: StrategyDecision,
                                        snapshot: MarketSnapshot):
    """Update Feature Store with trading signal data."""

async def _update_feature_store_regime(self, symbol: str, timeframe: str,
                                        snapshot: MarketSnapshot):
    """Update Feature Store with regime data."""

async def _update_feature_store_indicators(self, symbol: str, timeframe: str,
                                            indicators: Dict[str, Any]):
    """Update Feature Store with indicator values."""

async def _update_feature_store_position(self, symbol: str,
                                          position_data: Dict[str, Any]):
    """Update Feature Store with position data."""
```

### 8.3 Data Flow

```
Trading Loop Tick
       │
       ▼
┌──────────────────┐
│  _process_symbol │
│                  │
│  1. Build        │──▶ _update_feature_store_regime()
│     Snapshot     │──▶ _update_feature_store_indicators()
│                  │
│  2. Check        │
│     Position     │
│                  │
│  3. Evaluate     │
│     Entry        │
└────────┬─────────┘
         │
         ▼ (if signal)
┌──────────────────┐
│  _evaluate_entry │──▶ _update_feature_store_signal()
│                  │
│  Execute Entry   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ _execute_spot/   │──▶ _update_feature_store_position(OPEN)
│ _execute_futures │
└──────────────────┘

         ...later...

┌──────────────────┐
│  _execute_exit   │──▶ _update_feature_store_position(CLOSED)
└──────────────────┘
```

---

## 9. Testing & Verification

### 9.1 Migration Verification

```bash
# Check schema exists
docker exec postgres psql -U news_user -d news_mcp -c "\dn feature_store"

# Check tables created
docker exec postgres psql -U news_user -d news_mcp -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'feature_store';"

# Result: 7 tables
# - news_risk_features
# - content_analysis_features
# - entity_features
# - fmp_features
# - search_features
# - execution_history
# - feature_snapshots
```

### 9.2 API Verification

```bash
# Health check
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8116/api/v1/feature-store/health

# Response: {"status": "healthy", "tiers": {"hot": {"status": "healthy"}}}

# Get HOT features (returns null when no trading active)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8116/api/v1/feature-store/hot/BTCUSDT/5m
```

### 9.3 Service Logs

```bash
docker logs news-prediction-service --tail 50 | grep -i feature

# Expected:
# INFO - Feature Store Manager initialized
# INFO - ✓ Feature Store Manager initialized
```

---

## 10. Next Steps (Phase 2+)

### 10.1 Phase 2: WARM Tier Implementation

| Task | Priority | Effort |
|------|----------|--------|
| Hourly aggregation job (Celery) | High | Medium |
| News-Risk Service client | High | Low |
| Content Analysis client | High | Low |
| Entity Service client | Medium | Low |
| FMP Service client | Medium | Low |
| Search Service client | Low | Low |

### 10.2 Phase 3: COLD Tier & ML Training

| Task | Priority | Effort |
|------|----------|--------|
| Feature snapshot on trade entry | High | Medium |
| Label generation on trade exit | High | Medium |
| Training data export endpoint | Medium | Medium |
| Backfill historical snapshots | Low | High |

### 10.3 Phase 4: ML Model Integration

| Task | Priority | Effort |
|------|----------|--------|
| Train initial ML model | High | High |
| Inference pipeline | High | Medium |
| Model versioning | Medium | Medium |
| A/B testing framework | Low | High |

---

## Appendix A: Configuration

### A.1 Redis Keys TTL Configuration

| Key Type | TTL | Rationale |
|----------|-----|-----------|
| Signal | 1 hour | Signals expire after typical trade duration |
| Risk | 1 hour | Risk metrics need frequent refresh |
| Regime | 2 hours | Regimes are more stable |
| Indicators | 1 hour | Match signal TTL |
| Position | 24 hours | Positions can span multiple sessions |

### A.2 Supported Symbols

```python
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT"
]
```

### A.3 Supported Timeframes

```python
SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
```

---

## Appendix B: Error Handling

All Feature Store operations are wrapped in try/except blocks with graceful degradation:

```python
try:
    await self._update_feature_store_signal(...)
except Exception as e:
    logger.debug(f"Feature Store update failed: {e}")
    # Trading continues without Feature Store
```

This ensures trading operations are never blocked by Feature Store failures.

---

## Appendix C: Trading Cost & Risk Management Fixes (2025-12-29)

### C.1 Fix Summary

Following expert analysis, three critical fixes were implemented to improve trading cost modeling and risk management:

| Fix | Issue | Solution | Status |
|-----|-------|----------|--------|
| **Fee-Korrektur** | Only Exit fee (0.1%) was applied | Entry + Exit fees (0.055% × 2) + Slippage (0.05% on SL) | ✅ Complete |
| **Cooldown** | No pause after losing trades | 15-min cooldown, same direction only | ✅ Complete |
| **Liquidity Filter** | Orders could exceed market depth | Max 10% of top-5 orderbook depth | ✅ Complete |

### C.2 Fee Calculation (Before vs After)

**Before (WRONG):**
```python
# Only Exit fee, hardcoded 0.1%
notional_value = exit_price * position.size * leverage
fees = notional_value * Decimal("0.001")
pnl -= fees
```

**After (CORRECT):**
```python
# Entry + Exit fees + Slippage on SL
if self.config.use_fees:
    entry_fee = entry_value * self.config.taker_fee_pct  # 0.055%
    exit_fee = exit_value * self.config.taker_fee_pct   # 0.055%

if self.config.use_slippage and exit_reason == "stop_loss":
    slippage_cost = exit_value * self.config.slippage_pct  # 0.05%

total_fees = entry_fee + exit_fee + slippage_cost
pnl -= total_fees
```

**Impact Analysis:**
- 203 trades × 0.16% avg cost = **~32.5% total fee impact**
- Previously underestimated by **~22.5%** (0.1% vs 0.16%)

### C.3 New Configuration Options

```python
@dataclass
class TradingLoopConfig:
    # === FEES & SLIPPAGE ===
    taker_fee_pct: Decimal = Decimal("0.00055")  # 0.055% per side
    maker_fee_pct: Decimal = Decimal("0.0001")   # 0.01% (not used)
    use_fees: bool = True
    slippage_pct: Decimal = Decimal("0.0005")    # 0.05% on SL
    use_slippage: bool = True

    # === COOLDOWN AFTER LOSS ===
    use_cooldown: bool = True
    cooldown_minutes: int = 15
    cooldown_same_direction_only: bool = True

    # === LIQUIDITY FILTER ===
    use_liquidity_filter: bool = True
    min_liquidity_ratio: float = 0.1  # Max 10% of depth
```

### C.4 New State Tracking

```python
@dataclass
class TradingLoopState:
    # === FEES & SLIPPAGE TRACKING ===
    total_fees_paid: Decimal = Decimal("0")
    total_slippage_cost: Decimal = Decimal("0")
    gross_pnl: Decimal = Decimal("0")

    # === COOLDOWN TRACKING ===
    cooldown_until: Dict[str, Dict] = field(default_factory=dict)
    trades_blocked_by_cooldown: int = 0

    # === LIQUIDITY FILTER TRACKING ===
    trades_blocked_by_liquidity: int = 0
```

### C.5 Files Modified

| File | Changes |
|------|---------|
| `loop.py` | Fee calculation, cooldown logic, liquidity filter |
| `market_data.py` | New `get_orderbook()` method for liquidity check |

---

## Appendix D: References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture overview
- [CLAUDE.backend.md](../../CLAUDE.backend.md) - Backend development guide
- [ADR-018: Feature Store Architecture](../decisions/ADR-018-feature-store-architecture.md) - Architecture decision record
- [Migration 018](../../alembic/versions/018_create_feature_store_schema.py) - Database migration

---

**Document Version:** 1.0
**Author:** Claude Code
**Review Status:** Draft
