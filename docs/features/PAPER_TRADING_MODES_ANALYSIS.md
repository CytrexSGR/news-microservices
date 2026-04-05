# Paper Trading Modes - Analysis & Implementation Plan

**Date:** 2025-12-12
**Status:** Analysis Complete, Ready for Implementation

---

## Overview: Three Trading Modes

| Mode | Data Source | Price | Gate Logic | Purpose |
|------|-------------|-------|------------|---------|
| **1. LIVE** | Real-time API (Bybit) | Live Ticker | ML Models decide | Production Trading |
| **2. TEST** | Real-time API (Bybit) | Live Ticker | Bypass/Force Trades | Test Mechanics |
| **3. BACKTEST** | Historical DB | Historical | ML Models or Bypass | Validate Strategy |

---

## Current Problem: Why Strategy Never Trades

### Decision Logic (ml_lab_gatekeeper.py lines 138-174)

For ENTRY (no position):
1. `entry_signal` MUST be `"enter"`
2. `direction` MUST be `"bullish"` OR `"bearish"` (not `"neutral"`)
3. `regime` MUST be `"trending"`, `"ranging"` OR `"quiet"` (not `"volatile"`)
4. `risk_level` MUST NOT be `"high"`
5. `confidence` MUST be >= 0.6 (live_paper_trading.py line 356)

### What Logs Show

```
"No signal: regime=quiet, direction=neutral, entry=wait"
```

**Problem:** ML models return:
- `entry = "wait"` → No entry signal
- `direction = "neutral"` → No clear direction

Even if `entry = "enter"`, `direction = "neutral"` would block the trade!

### The 5 Blocking Points

| # | Gate | Current Value | Required for Trade |
|---|------|---------------|-------------------|
| 1 | **entry** | `wait` | `enter` |
| 2 | **direction** | `neutral` | `bullish` or `bearish` |
| 3 | **regime** | `quiet` | `trending`, `ranging`, `quiet` ✅ |
| 4 | **risk** | `medium` | not `high` ✅ |
| 5 | **confidence** | ~85% | >= 60% ✅ |

**→ 2 of 5 conditions fail: `entry` and `direction`**

---

## Mode 1: LIVE (Currently Implemented)

### Data Flow
```
Bybit API → OHLCV (last 500 candles) → ML Gates → Decision → Trade/Hold
     ↓
Live Price for Execution
```

### Characteristics
- Real-time data from Bybit API
- ML models make decisions
- Current market price for trades
- Problem: Never trades because `entry=wait`, `direction=neutral`

### Code Location
- `services/prediction-service/app/services/ml/live_paper_trading.py`
- `services/prediction-service/app/services/ml/ml_lab_gatekeeper.py`

---

## Mode 2: TEST (Force-Trade Mode)

### Purpose
Verify that position management, P&L calculation, DB persistence work correctly.

### Option A: Manual Force-Trades (Recommended)
```
POST /api/v1/ml/live-trading/force-trade
  ?symbol=XRPUSDT
  &action=enter_long   (or enter_short, exit)
```
- Ignores gates completely
- Opens/closes position immediately
- Uses current live price

### Option B: Auto-Test Mode with Rules
```
POST /api/v1/ml/live-trading/start?symbol=XRPUSDT&mode=test
```
Built-in test logic:
- Entry: If RSI < 30 → Long, RSI > 70 → Short (simple rule)
- Exit: After X ticks or at Y% P&L
- Ignores ML gate results

### Option C: Configurable Gate Overrides
```
POST /api/v1/ml/live-trading/start
  ?symbol=XRPUSDT
  &override_entry=enter
  &override_direction=bullish
```
- Gates are evaluated but results overwritten
- Looks like real trade flow

**Recommendation:** Option A (Force-Trade endpoint) + Option B (Auto-Test)

---

## Mode 3: BACKTEST (Historical Data)

### Purpose
Test strategy on past data, measure performance.

### Available Historical Data

| Symbol | Timeframe | Period | Candles |
|--------|-----------|--------|---------|
| XRPUSDT | 1min | 03.11 - 12.12.2025 | 56,573 |
| XRPUSDT | 5min | 03.11 - 10.12.2025 | 10,657 |
| XRPUSDT | 1H | 03.11 - 12.12.2025 | 943 |
| ETHUSDT | 1min | 09.12 - 12.12.2025 | 3,598 |
| ETHUSDT | 1H | 25.10.2024 - 12.12.2025 | 392 |
| BTCUSDT | 1min | 09.12 - 12.12.2025 | 3,598 |

### Concept
```
POST /api/v1/ml/live-trading/backtest
  {
    "symbol": "XRPUSDT",
    "timeframe": "5min",
    "date_from": "2025-11-15",
    "date_to": "2025-12-01",
    "use_ml_gates": false,  // true = ML decides, false = Force trades
    "initial_capital": 10000
  }
```

### Backtest Flow
```
1. Load historical data for period
2. Iterate through candles (simulated time)
3. Per candle:
   - Calculate features/indicators
   - Evaluate gates (or bypass in test mode)
   - Simulate trade execution at historical price
   - Track P&L
4. At end: Performance report
```

### Two Sub-Modes for Backtest
- **3a. Backtest + ML-Gates:** Tests if ML models would have worked historically
- **3b. Backtest + Force:** Tests trading mechanics with guaranteed trades

---

## Architecture Proposal

### Service Extension

```python
class TradingMode(str, Enum):
    LIVE = "live"
    TEST = "test"
    BACKTEST = "backtest"

class TestConfig(BaseModel):
    force_entry_every_n_ticks: int = 5
    force_exit_after_n_ticks: int = 10
    override_direction: str = "alternate"  # "bullish", "bearish", "alternate"

class BacktestConfig(BaseModel):
    date_from: datetime
    date_to: datetime
    speed_multiplier: int = 100
    use_ml_gates: bool = True

class MLLivePaperTradingService:
    mode: TradingMode = TradingMode.LIVE
    test_config: Optional[TestConfig] = None
    backtest_config: Optional[BacktestConfig] = None

    async def _execute_tick(self):
        if self.mode == TradingMode.LIVE:
            # Current code - ML gates decide
            pass
        elif self.mode == TradingMode.TEST:
            # Force-trade logic
            pass
        elif self.mode == TradingMode.BACKTEST:
            # Historical iteration
            pass
```

### API Endpoints

```python
# Mode 1: Live (unchanged)
POST /api/v1/ml/live-trading/start?symbol=XRPUSDT&mode=live

# Mode 2: Test
POST /api/v1/ml/live-trading/start?symbol=XRPUSDT&mode=test
POST /api/v1/ml/live-trading/force-trade?symbol=XRPUSDT&action=enter_long

# Mode 3: Backtest
POST /api/v1/ml/live-trading/backtest
  {
    "symbol": "XRPUSDT",
    "timeframe": "5min",
    "date_from": "2025-11-15",
    "date_to": "2025-12-01",
    "use_ml_gates": false,
    "initial_capital": 10000
  }

GET /api/v1/ml/live-trading/backtest/{job_id}/status
GET /api/v1/ml/live-trading/backtest/{job_id}/results
```

---

## Frontend Extension

### UI Structure

```
Paper Trading Tab
├── Mode Toggle: [LIVE] [TEST] [BACKTEST]
│
├── LIVE Mode:
│   └── Current UI (Sessions, Auto-Tick, etc.)
│
├── TEST Mode:
│   ├── Force Trade Buttons: [LONG] [SHORT] [EXIT]
│   ├── Auto-Test: [Start Auto-Test] with configurable rules
│   └── Sessions like LIVE, but with "TEST" badge
│
└── BACKTEST Mode:
    ├── Date Range Picker: [From] [To]
    ├── Symbol/Timeframe Selection
    ├── Toggle: [Use ML Gates] / [Force Trades]
    ├── [Run Backtest] Button
    └── Results:
        ├── Equity Curve Chart
        ├── Trade History Table
        └── Performance Metrics (Win Rate, Sharpe, Max DD, etc.)
```

---

## Implementation Order

### Phase 1: TEST Mode (Force-Trade)
1. Add `mode` parameter to start endpoint
2. Create `/force-trade` endpoint
3. Implement force-trade logic in service
4. Add TEST mode UI with force buttons
5. Test: Open/close positions manually, verify P&L

### Phase 2: BACKTEST Mode
1. Create backtest endpoint and schemas
2. Implement historical data iteration
3. Add backtest job management (async)
4. Create backtest results storage
5. Add BACKTEST mode UI with date picker and results
6. Test: Run backtests, verify equity curve

### Phase 3: Enhancements
1. Add more test strategies (RSI, EMA cross, etc.)
2. Add backtest comparison (multiple runs)
3. Add Monte Carlo simulation
4. Add walk-forward optimization

---

## Files to Modify

### Backend
- `services/prediction-service/app/services/ml/live_paper_trading.py` - Add modes
- `services/prediction-service/app/api/v1/ml_lab_router.py` - Add endpoints
- `services/prediction-service/app/schemas/ml_lab.py` - Add schemas

### Frontend
- `frontend/src/features/ml-lab/components/live/LivePaperTradingPanel.tsx` - Add mode toggle
- `frontend/src/features/ml-lab/api/mlLabApi.ts` - Add API calls
- `frontend/src/features/ml-lab/types/index.ts` - Add types

---

## Success Criteria

### TEST Mode
- [ ] Can force open a LONG position
- [ ] Can force open a SHORT position
- [ ] Can force close a position
- [ ] P&L is calculated correctly
- [ ] Trades are saved to database
- [ ] UI shows position and updates in real-time

### BACKTEST Mode
- [ ] Can run backtest on historical data
- [ ] Equity curve is generated
- [ ] Trade history is recorded
- [ ] Performance metrics calculated (Win Rate, Total P&L, Max DD)
- [ ] Results can be viewed in UI
- [ ] Can compare ML-gates vs Force-trades

---

**Next Step:** Implement Phase 1 (TEST Mode with Force-Trade endpoint)
