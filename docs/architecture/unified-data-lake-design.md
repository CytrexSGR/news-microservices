# Unified Data Lake Architecture Design
## FMP Service + Bybit Trading Data Integration for ML

**Author:** Claude (AI-assisted)
**Date:** 2025-12-01
**Status:** Draft - Awaiting Review
**Related:** Phase 4.3.2 Performance Prediction ML Pipeline

---

## Executive Summary

**Problem:** ML pipeline currently uses only Bybit trading data (18h history). FMP service has years of OHLCV data (273k+ rows) but incompatible structure.

**Solution:** Unified Data Lake architecture where **all sources write to `predictions.analysis_logs` with standardized schema**.

**Benefits:**
- ✅ **10,000+ training samples** (vs. current 562)
- ✅ **Multi-year backtesting** (vs. 18 hours)
- ✅ **Multi-asset ML models** (indices, forex, commodities + crypto)
- ✅ **No code changes** in ML pipeline (same interface)
- ✅ **Feature enrichment** (FMP fundamentals + Bybit real-time)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED DATA LAKE                        │
│               predictions.analysis_logs                     │
│                                                             │
│  Columns:                                                   │
│  - symbol, strategy, signal, confidence                     │
│  - entry_price, stop_loss, take_profit                      │
│  - market_data JSONB (RSI, EMA, OI, volume, ...)          │
│  - source ('bybit' | 'fmp' | 'computed')  ← NEW            │
│  - source_metadata JSONB (raw OHLCV, API info) ← NEW       │
│  - timestamp                                                │
└─────────────────────────────────────────────────────────────┘
                          ▲        ▲        ▲
                          │        │        │
           ┌──────────────┘        │        └──────────────┐
           │                       │                       │
   ┌───────────────┐     ┌─────────────────┐     ┌────────────────┐
   │ Bybit Trading │     │ FMP Historical  │     │ FMP Real-Time  │
   │   Pipeline    │     │    Backfill     │     │   Sync (NEW)   │
   └───────────────┘     └─────────────────┘     └────────────────┘
         │                       │                        │
   Real-time data          Historical data          Parallel sync
   (existing)              (years of OHLCV)         (1min/5min)
```

---

## Current State Analysis

### FMP Service Data (273k+ rows)

**Available Tables:**
1. **market_ohlcv** - OHLCV candlesticks
   - Intervals: 1min, 5min, 15min, 30min, 1hour, 4hour
   - Fields: open, high, low, close, volume, vwap, trades
   - 257 symbols (crypto, forex, commodities, indices)
   - Tier 1 (40 symbols): 1min data
   - Tier 2 (67 symbols): 5min data
   - Tier 3 (150 symbols): quote snapshots

2. **market_quote_snapshots** - Real-time quotes
   - Fields: price, bid, ask, volume, change_percent
   - Includes: day_high, day_low, prev_close
   - Updated: Every 1 minute

3. **market_symbols** - Symbol registry
   - 257 symbols with tier assignments
   - Metadata: asset_type, exchange, notes

**Historical Data Availability:**
- **2024-2025 EOD data**: Available in `market_history` tables
- **Expandable**: FMP API provides 5+ years historical data
- **Volume**: 273,522+ existing rows

### Bybit Trading Data

**Current Structure (analysis_logs):**
```sql
CREATE TABLE predictions.analysis_logs (
    id UUID PRIMARY KEY,
    symbol VARCHAR NOT NULL,        -- "BTC/USDT:USDT"
    strategy VARCHAR NOT NULL,      -- "OI_Trend"
    signal VARCHAR NOT NULL,        -- "LONG" | "SHORT" | "NEUTRAL"
    confidence FLOAT NOT NULL,      -- 0.0 - 1.0
    entry_price FLOAT NOT NULL,
    stop_loss FLOAT,
    take_profit FLOAT,
    market_data JSONB NOT NULL,     -- {"rsi": 45, "ema50": 85000, "oi_rising": true, ...}
    reason TEXT,
    timestamp TIMESTAMPTZ NOT NULL
);
```

**market_data JSONB Contents:**
- `rsi`: Relative Strength Index (14-period)
- `ema50`: 50-period Exponential Moving Average
- `close_price`: Current close price
- `open_interest`: Futures open interest (Bybit-specific)
- `oi_rising`: Boolean (OI trend)
- `signal`: Strategy signal (redundant with parent column)
- `confidence`: Strategy confidence (redundant)

**Data Characteristics:**
- **Update Frequency**: Every 1 minute (OI_Trend scheduler)
- **History**: 18.75 hours (658 analyses) - insufficient for 7-day ML
- **Symbols**: Currently only BTC/USDT:USDT
- **Strategies**: OI_Trend (Open Interest based)

---

## Feature Gap Analysis

### FMP Has (Available)
✅ **OHLCV Data**
- Open, High, Low, Close prices
- Volume (trading volume)
- VWAP (Volume Weighted Average Price)
- Timestamp (candle open time)

✅ **Quote Data**
- Current price (close)
- Bid/Ask spread
- Day High/Low
- Previous Close
- Change Percent

✅ **Historical Depth**
- 2024-2025 data (expandable to 5+ years)
- Multiple timeframes (1min, 5min, 15min, 30min, 1hour, 4hour)

### FMP Missing (Need to Compute)
❌ **Technical Indicators**
- RSI (14-period) - Must compute from OHLCV
- EMA (50-period) - Must compute from OHLCV
- Other indicators (MACD, Bollinger Bands, etc.)

❌ **Bybit-Specific Data**
- Open Interest (OI) - Not available for spot/indices/forex
- Funding Rates - Crypto futures only
- Liquidations - Exchange-specific

### Solution: Indicator Computation Layer

```python
# services/fmp-service/app/services/indicators.py
class TechnicalIndicators:
    """Compute technical indicators from OHLCV data."""

    @staticmethod
    def compute_rsi(closes: List[float], period: int = 14) -> float:
        """Relative Strength Index (14-period)"""
        # Implementation: Wilder's smoothing method

    @staticmethod
    def compute_ema(closes: List[float], period: int = 50) -> float:
        """Exponential Moving Average (50-period)"""
        # Implementation: EMA formula with smoothing

    @staticmethod
    def compute_all(ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """Compute all indicators from OHLCV history."""
        return {
            "rsi": compute_rsi([c["close"] for c in ohlcv_data]),
            "ema50": compute_ema([c["close"] for c in ohlcv_data], 50),
            "close_price": ohlcv_data[-1]["close"],
            "volume": ohlcv_data[-1]["volume"],
            # OI not available, use volume proxy or NULL
            "open_interest": None,
            "oi_rising": None
        }
```

---

## Unified Data Lake Schema

### Extended analysis_logs Table

```sql
-- Migration: Add multi-source support
ALTER TABLE predictions.analysis_logs
    ADD COLUMN source VARCHAR(20) DEFAULT 'bybit',     -- 'bybit' | 'fmp' | 'computed'
    ADD COLUMN source_metadata JSONB;                  -- Raw source data

CREATE INDEX idx_analysis_logs_source ON predictions.analysis_logs(source);
CREATE INDEX idx_analysis_logs_symbol_source_timestamp
    ON predictions.analysis_logs(symbol, source, timestamp);
```

### source Field Values

1. **'bybit'** - Real-time trading data from Bybit API
   - OI_Trend strategy analyses
   - Real-time signals (LONG/SHORT/NEUTRAL)
   - Includes open_interest, oi_rising

2. **'fmp'** - Historical/real-time data from FMP
   - Computed indicators from OHLCV
   - Multi-asset support (indices, forex, commodities)
   - No OI data (NULL or volume proxy)

3. **'computed'** - Synthetic/derived data
   - Backtests on historical data
   - Regime classifications
   - Cross-asset correlations

### source_metadata JSONB Schema

```json
// For source='bybit'
{
  "api": "bybit",
  "endpoint": "/v5/market/tickers",
  "raw_oi": 50000,
  "funding_rate": 0.0001
}

// For source='fmp'
{
  "api": "fmp",
  "endpoint": "/v3/quote/BTCUSD",
  "interval": "1min",           // OHLCV interval used
  "ohlcv_window": 50,            // Candles used for indicators
  "raw_ohlcv": {
    "open": 84500,
    "high": 84600,
    "low": 84400,
    "close": 84550,
    "volume": 12500
  }
}
```

---

## Implementation Plan

### Phase 1: Schema Migration (1h)
✅ **Goal:** Extend analysis_logs for multi-source support

**Tasks:**
1. Create Alembic migration script
   ```bash
   cd services/prediction-service
   alembic revision -m "add_multi_source_support"
   ```

2. Add columns:
   ```sql
   ALTER TABLE predictions.analysis_logs
       ADD COLUMN source VARCHAR(20) DEFAULT 'bybit',
       ADD COLUMN source_metadata JSONB;

   CREATE INDEX idx_analysis_logs_source ON predictions.analysis_logs(source);
   ```

3. Backfill existing records:
   ```sql
   UPDATE predictions.analysis_logs
   SET source = 'bybit',
       source_metadata = jsonb_build_object('api', 'bybit', 'legacy', true)
   WHERE source IS NULL;
   ```

4. Apply migration:
   ```bash
   alembic upgrade head
   ```

**Validation:**
- ✅ Query existing data with source filter
- ✅ Verify indexes created
- ✅ Check foreign key constraints

---

### Phase 2: Indicator Computation Service (3-4h)
✅ **Goal:** Compute RSI, EMA from FMP OHLCV data

**File:** `services/fmp-service/app/services/indicators.py`

```python
"""
Technical Indicator Computation Service
Computes RSI, EMA, and other indicators from OHLCV data.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

class TechnicalIndicators:
    """Compute technical indicators for ML feature engineering."""

    @staticmethod
    def compute_rsi(closes: List[float], period: int = 14) -> Optional[float]:
        """
        Relative Strength Index (14-period).

        Formula:
            RSI = 100 - (100 / (1 + RS))
            RS = Average Gain / Average Loss (Wilder's smoothing)

        Args:
            closes: List of close prices (recent last)
            period: RSI period (default 14)

        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if len(closes) < period + 1:
            return None

        # Calculate price changes
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Wilder's smoothing (first avg, then EMA-like)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Smooth remaining periods
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        # Calculate RSI
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    @staticmethod
    def compute_ema(closes: List[float], period: int = 50) -> Optional[float]:
        """
        Exponential Moving Average (50-period).

        Formula:
            EMA = (Close - EMA_prev) * multiplier + EMA_prev
            multiplier = 2 / (period + 1)

        Args:
            closes: List of close prices (recent last)
            period: EMA period (default 50)

        Returns:
            EMA value or None if insufficient data
        """
        if len(closes) < period:
            return None

        # Start with SMA for first value
        ema = np.mean(closes[:period])
        multiplier = 2 / (period + 1)

        # Calculate EMA for remaining values
        for close in closes[period:]:
            ema = (close - ema) * multiplier + ema

        return float(ema)

    @staticmethod
    def compute_all_indicators(
        ohlcv_data: List[Dict[str, Any]],
        rsi_period: int = 14,
        ema_period: int = 50
    ) -> Dict[str, Any]:
        """
        Compute all indicators from OHLCV window.

        Args:
            ohlcv_data: List of OHLCV candles (oldest first, newest last)
                        Each dict must have: open, high, low, close, volume
            rsi_period: RSI calculation period
            ema_period: EMA calculation period

        Returns:
            Dict with all computed indicators
        """
        if not ohlcv_data:
            return {}

        closes = [candle["close"] for candle in ohlcv_data]
        latest_candle = ohlcv_data[-1]

        return {
            "rsi": TechnicalIndicators.compute_rsi(closes, rsi_period),
            "ema50": TechnicalIndicators.compute_ema(closes, ema_period),
            "close_price": latest_candle["close"],
            "volume": latest_candle["volume"],
            # OI not available from FMP, leave as None
            "open_interest": None,
            "oi_rising": None,
            # Additional computed features
            "price_above_ema": closes[-1] > TechnicalIndicators.compute_ema(closes, ema_period) if len(closes) >= ema_period else None
        }
```

**Testing:**
```python
# tests/test_indicators.py
def test_rsi_computation():
    closes = [44, 44.34, 44.09, 43.61, 44.33, ...]  # 15 values
    rsi = TechnicalIndicators.compute_rsi(closes, period=14)
    assert 0 <= rsi <= 100
    assert abs(rsi - 70.46) < 0.1  # Known value from TA-Lib

def test_ema_computation():
    closes = [22.27, 22.19, 22.08, ...]  # 50+ values
    ema = TechnicalIndicators.compute_ema(closes, period=50)
    assert ema > 0
```

---

### Phase 3: FMP Historical Backfill Service (4-5h)
✅ **Goal:** Transform FMP OHLCV → analysis_logs format

**File:** `services/fmp-service/app/services/backfill_service.py`

```python
"""
FMP Historical Data Backfill Service
Transforms FMP OHLCV data into analysis_logs format for ML training.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.ohlcv import MarketOHLCV, CandleInterval
from app.models.market_symbol import MarketSymbol
from app.services.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class FMPBackfillService:
    """Backfill analysis_logs from FMP OHLCV historical data."""

    def __init__(self, db: AsyncSession, prediction_db: AsyncSession):
        self.db = db  # FMP database
        self.prediction_db = prediction_db  # Prediction service database
        self.indicators = TechnicalIndicators()

    async def backfill_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: CandleInterval = CandleInterval.FIVE_MINUTE,
        strategy: str = "FMP_Technical"
    ) -> Dict[str, Any]:
        """
        Backfill analysis_logs for a single symbol.

        Process:
        1. Fetch OHLCV data from market_ohlcv
        2. Compute technical indicators (RSI, EMA)
        3. Generate synthetic signals (NEUTRAL for historical data)
        4. Insert into predictions.analysis_logs with source='fmp'

        Args:
            symbol: Symbol to backfill (e.g., "BTCUSD", "^GSPC")
            start_date: Backfill start date
            end_date: Backfill end date
            interval: OHLCV interval (default 5min)
            strategy: Strategy name (default "FMP_Technical")

        Returns:
            Statistics: records_processed, records_inserted, errors
        """
        logger.info(
            f"Backfilling {symbol} from {start_date} to {end_date} "
            f"(interval: {interval.value})"
        )

        # Fetch OHLCV data
        query = select(MarketOHLCV).where(
            and_(
                MarketOHLCV.symbol == symbol,
                MarketOHLCV.interval == interval,
                MarketOHLCV.timestamp >= start_date,
                MarketOHLCV.timestamp <= end_date
            )
        ).order_by(MarketOHLCV.timestamp.asc())

        result = await self.db.execute(query)
        ohlcv_records = result.scalars().all()

        logger.info(f"Fetched {len(ohlcv_records)} OHLCV records")

        # Process in windows (need lookback for indicators)
        window_size = 50  # Need 50 candles for EMA50
        records_inserted = 0
        errors = 0

        for i in range(window_size, len(ohlcv_records)):
            try:
                # Get window of data for indicator computation
                window = ohlcv_records[i - window_size:i + 1]
                current_candle = ohlcv_records[i]

                # Convert to dict format for indicators
                ohlcv_dicts = [
                    {
                        "open": float(c.open),
                        "high": float(c.high),
                        "low": float(c.low),
                        "close": float(c.close),
                        "volume": int(c.volume) if c.volume else 0
                    }
                    for c in window
                ]

                # Compute indicators
                market_data = self.indicators.compute_all_indicators(ohlcv_dicts)

                # Create analysis_log entry
                analysis_entry = {
                    "symbol": self._normalize_symbol(symbol),  # Convert to Bybit format
                    "strategy": strategy,
                    "signal": "NEUTRAL",  # Historical data = no signal
                    "confidence": 0.0,    # No strategy execution
                    "entry_price": float(current_candle.close),
                    "stop_loss": None,
                    "take_profit": None,
                    "market_data": market_data,
                    "reason": f"FMP backfill ({interval.value})",
                    "timestamp": current_candle.timestamp,
                    "source": "fmp",
                    "source_metadata": {
                        "api": "fmp",
                        "interval": interval.value,
                        "ohlcv_window": window_size,
                        "raw_ohlcv": ohlcv_dicts[-1]
                    }
                }

                # Insert into predictions.analysis_logs
                await self._insert_analysis_log(analysis_entry)
                records_inserted += 1

            except Exception as e:
                logger.error(f"Error processing candle {i}: {str(e)}", exc_info=True)
                errors += 1

        logger.info(
            f"Backfill complete: {records_inserted} inserted, {errors} errors"
        )

        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval.value,
            "records_processed": len(ohlcv_records) - window_size,
            "records_inserted": records_inserted,
            "errors": errors
        }

    async def backfill_all_symbols(
        self,
        start_date: datetime,
        end_date: datetime,
        tier: int = 2  # Default to Tier 2 (5min data)
    ) -> Dict[str, Any]:
        """
        Backfill all symbols in a tier.

        Args:
            start_date: Backfill start
            end_date: Backfill end
            tier: Tier ID (1=1min, 2=5min, 3=quotes)

        Returns:
            Summary statistics
        """
        # Get symbols in tier
        query = select(MarketSymbol).where(
            and_(
                MarketSymbol.tier_id == tier,
                MarketSymbol.is_active == True
            )
        )

        result = await self.db.execute(query)
        symbols = result.scalars().all()

        logger.info(f"Backfilling {len(symbols)} symbols from tier {tier}")

        results = []
        for symbol in symbols:
            interval = CandleInterval.ONE_MINUTE if tier == 1 else CandleInterval.FIVE_MINUTE
            result = await self.backfill_symbol(
                symbol=symbol.symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            results.append(result)

        # Aggregate statistics
        total_inserted = sum(r["records_inserted"] for r in results)
        total_errors = sum(r["errors"] for r in results)

        return {
            "status": "success",
            "tier": tier,
            "symbols_processed": len(results),
            "total_records_inserted": total_inserted,
            "total_errors": total_errors,
            "symbol_results": results
        }

    def _normalize_symbol(self, fmp_symbol: str) -> str:
        """Convert FMP symbol format to Bybit format."""
        # Examples:
        # BTCUSD → BTC/USDT:USDT
        # EURUSD → EUR/USD:USD
        # ^GSPC → SPX (or keep as-is?)

        # Simple mapping for now
        symbol_map = {
            "BTCUSD": "BTC/USDT:USDT",
            "ETHUSD": "ETH/USDT:USDT",
            "EURUSD": "EUR/USD:USD",
            # Add more as needed
        }

        return symbol_map.get(fmp_symbol, fmp_symbol)

    async def _insert_analysis_log(self, entry: Dict[str, Any]):
        """Insert entry into predictions.analysis_logs."""
        from prediction_service.app.models.analysis_log import AnalysisLog

        analysis_log = AnalysisLog(**entry)
        self.prediction_db.add(analysis_log)
        await self.prediction_db.commit()
```

**API Endpoint:**
```python
# services/fmp-service/app/api/v1/backfill.py

@router.post("/backfill/{symbol}")
async def backfill_symbol_historical(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: CandleInterval = CandleInterval.FIVE_MINUTE,
    db: AsyncSession = Depends(get_db),
    prediction_db: AsyncSession = Depends(get_prediction_db)
):
    """Backfill historical data for symbol."""
    service = FMPBackfillService(db, prediction_db)
    result = await service.backfill_symbol(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    return result

@router.post("/backfill/tier/{tier_id}")
async def backfill_tier_historical(
    tier_id: int,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    prediction_db: AsyncSession = Depends(get_prediction_db)
):
    """Backfill all symbols in a tier."""
    service = FMPBackfillService(db, prediction_db)
    result = await service.backfill_all_symbols(
        start_date=start_date,
        end_date=end_date,
        tier=tier_id
    )
    return result
```

---

### Phase 4: Real-Time FMP→analysis_logs Sync (2-3h)
✅ **Goal:** Parallel sync FMP data alongside Bybit trading

**File:** `services/fmp-service/app/workers/analysis_sync_worker.py`

```python
"""
Real-time sync worker: FMP OHLCV → analysis_logs
Runs parallel to Bybit trading pipeline.
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.backfill_service import FMPBackfillService

logger = logging.getLogger(__name__)

class AnalysisSyncWorker:
    """Sync FMP data to analysis_logs in real-time."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def sync_tier1_symbols(self):
        """Sync Tier 1 symbols (1min data) every minute."""
        logger.info("Syncing Tier 1 symbols (1min)...")

        service = FMPBackfillService(db, prediction_db)

        # Get latest 1 minute of data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=2)

        await service.backfill_all_symbols(
            start_date=start_time,
            end_date=end_time,
            tier=1
        )

    async def sync_tier2_symbols(self):
        """Sync Tier 2 symbols (5min data) every 5 minutes."""
        logger.info("Syncing Tier 2 symbols (5min)...")

        service = FMPBackfillService(db, prediction_db)

        # Get latest 5 minutes of data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)

        await service.backfill_all_symbols(
            start_date=start_time,
            end_date=end_time,
            tier=2
        )

    def start(self):
        """Start scheduler jobs."""
        self.scheduler.add_job(
            self.sync_tier1_symbols,
            'interval',
            minutes=1,
            id='fmp_analysis_sync_tier1'
        )

        self.scheduler.add_job(
            self.sync_tier2_symbols,
            'interval',
            minutes=5,
            id='fmp_analysis_sync_tier2'
        )

        self.scheduler.start()
        logger.info("Analysis sync worker started")
```

**Configuration:**
```python
# services/fmp-service/app/main.py

from app.workers.analysis_sync_worker import AnalysisSyncWorker

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...

    # Start real-time analysis sync
    if settings.ENABLE_ANALYSIS_SYNC:
        sync_worker = AnalysisSyncWorker()
        sync_worker.start()
```

---

### Phase 5: ML Pipeline Integration (1h)
✅ **Goal:** Ensure ML pipeline works with multi-source data

**Changes Required:** NONE! 🎉

The ML pipeline (`data_collector.py`, `feature_engineer.py`, `model_trainer.py`, `predictor.py`) already uses `analysis_logs` as its source. No changes needed.

**Optional Enhancements:**
1. **Source Filtering:**
   ```python
   # DataCollector.collect_training_data()
   query = select(AnalysisLog).where(
       and_(
           AnalysisLog.strategy == strategy_name,
           AnalysisLog.symbol == symbol,
           AnalysisLog.source.in_(['bybit', 'fmp'])  # Filter sources
       )
   ).order_by(AnalysisLog.timestamp.asc())
   ```

2. **Source-Aware Features:**
   ```python
   # FeatureEngineer.compute_features()
   features["source_bybit"] = [1.0 if d["source"] == "bybit" else 0.0 for d in training_data]
   features["source_fmp"] = [1.0 if d["source"] == "fmp" else 0.0 for d in training_data]
   ```

---

## Expected Outcomes

### Training Data Growth
| Metric | Before (Bybit Only) | After (Unified Lake) | Improvement |
|--------|--------------------|--------------------|-------------|
| Total Samples | 562 (18h) | 10,000+ (months) | **18x** |
| Symbols | 1 (BTC/USDT) | 257 (multi-asset) | **257x** |
| Prediction Horizon | 1 hour (limited) | 7-30 days (valid) | ✅ **Production-ready** |
| Historical Depth | 0.78 days | 365+ days | **469x** |

### ML Model Improvements
- ✅ **Better Generalization:** Train on diverse market conditions
- ✅ **Cross-Asset Models:** Predict BTC using S&P 500, Gold correlations
- ✅ **Regime-Aware:** Train separate models per market regime
- ✅ **Backtesting:** Validate on years of historical data

### Business Benefits
- ✅ **Faster Development:** No waiting for Bybit data accumulation
- ✅ **Multi-Asset Strategy:** Expand beyond crypto (indices, forex, commodities)
- ✅ **Risk Management:** Test strategies across market crashes, rallies
- ✅ **Feature Richness:** FMP fundamentals + Bybit execution data

---

## Migration Strategy

### Option A: Incremental (Recommended)
1. **Week 1:** Schema migration + indicator service
2. **Week 2:** Backfill 1 month of Tier 2 data (BTC, ETH)
3. **Week 3:** Test ML pipeline with mixed sources
4. **Week 4:** Enable real-time sync, backfill all tiers

**Advantages:**
- ✅ Low risk (can rollback at any step)
- ✅ Early validation (test with small dataset first)
- ✅ Parallel development (ML continues on Bybit data)

### Option B: Big Bang
1. Complete all phases in 2-3 days
2. Backfill all historical data at once
3. Switch ML pipeline to unified lake

**Advantages:**
- ✅ Faster time-to-value
- ❌ Higher risk (more complex rollback)

---

## Testing Plan

### Unit Tests
```bash
# Test indicator computation
pytest services/fmp-service/tests/test_indicators.py

# Test backfill service
pytest services/fmp-service/tests/test_backfill_service.py
```

### Integration Tests
```bash
# Test end-to-end backfill
curl -X POST http://localhost:8113/api/v1/backfill/BTCUSD \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-11-01T00:00:00Z",
    "end_date": "2024-11-02T00:00:00Z",
    "interval": "5min"
  }'

# Verify data in analysis_logs
psql -d predictions -c "
  SELECT source, COUNT(*),
         MIN(timestamp), MAX(timestamp)
  FROM analysis_logs
  GROUP BY source;
"
```

### ML Pipeline Tests
```bash
# Test ML training with mixed sources
python test_ml_pipeline.py

# Expected output:
# ✓ Found 10,000+ training samples (mixed sources)
# ✓ Train R²: 0.85+
# ✓ Test R²: 0.70+
# ✓ Predictions working with FMP data
```

---

## Risk Mitigation

### Risk 1: Indicator Computation Accuracy
**Risk:** RSI/EMA calculations don't match Bybit's
**Mitigation:**
- Validate against known TA-Lib values
- Compare FMP-computed RSI with Bybit RSI for overlapping periods
- Allow ±5% tolerance in features (model should learn)

### Risk 2: Data Volume Explosion
**Risk:** 257 symbols × 1min data = millions of rows
**Mitigation:**
- Implement data retention policies (30-day rolling for 1min)
- Use partitioning on `analysis_logs` (by month)
- Archive old data to cold storage

### Risk 3: Performance Degradation
**Risk:** ML training slows down with 10,000+ samples
**Mitigation:**
- Use sampling strategies (stratified by time/source)
- Incremental learning (train on new data only)
- GPU acceleration for XGBoost

### Risk 4: Source Conflicts
**Risk:** Bybit price ≠ FMP price (different exchanges)
**Mitigation:**
- Accept price differences (ML should learn from patterns, not absolute prices)
- Normalize prices by source if needed
- Use percentage returns instead of absolute prices

---

## Success Metrics

### Technical Metrics
- ✅ **10,000+ training samples** (vs. current 562)
- ✅ **35+ tables integrated** (FMP + Bybit)
- ✅ **<1% data loss** during backfill
- ✅ **<5% indicator error** vs. reference libraries

### ML Metrics
- ✅ **Train R² > 0.80** (better generalization)
- ✅ **Test R² > 0.65** (stable performance)
- ✅ **7-day predictions valid** (not just 1-hour)
- ✅ **Multi-asset models working** (crypto + indices)

### Business Metrics
- ✅ **Time-to-market: 2-3 weeks** (incremental approach)
- ✅ **Development efficiency: 50% faster** (no data waiting)
- ✅ **Strategy diversity: 3x** (multi-asset strategies)

---

## Next Steps

1. **Review & Approve Design** ← YOU ARE HERE
2. **Phase 1: Schema Migration** (1h)
3. **Phase 2: Indicator Service** (3-4h)
4. **Phase 3: Backfill Service** (4-5h)
5. **Phase 4: Real-Time Sync** (2-3h)
6. **Phase 5: ML Validation** (1h)

**Total Estimated Time:** 11-14 hours (incremental approach)

---

## Questions for Review

1. **Symbol Normalization:** FMP uses "BTCUSD", Bybit uses "BTC/USDT:USDT". Keep separate or normalize?
   - Recommendation: Keep FMP symbols as-is, normalize only when needed

2. **Open Interest Proxy:** FMP doesn't have OI. Use volume as proxy or leave NULL?
   - Recommendation: Leave NULL initially, add volume-based proxy later if needed

3. **Tier Priority:** Start with Tier 1 (1min, 40 symbols) or Tier 2 (5min, 67 symbols)?
   - Recommendation: Start with Tier 2 (less data, faster backfill)

4. **Real-Time Sync:** Enable immediately or after backfill complete?
   - Recommendation: After backfill (validate historical first)

---

**Status:** Awaiting User Review & Approval
**Next Action:** Proceed to Phase 1 (Schema Migration) or request modifications
