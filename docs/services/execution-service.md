# Execution Service Documentation

## Overview

The execution-service is a custom-built trading execution layer designed to replace Freqtrade integration with a clean, tailored solution using CCXT (Async) and FastAPI. It provides trade execution, position management, portfolio analytics, and risk control for crypto trading via Bybit.

**Service Information:**
- **Port:** 8120
- **Technology:** Python 3.11, FastAPI, CCXT 4.2, SQLAlchemy (async)
- **Exchange:** Bybit (testnet/mainnet)
- **Database:** PostgreSQL
- **Cache:** Redis (DB 3)
- **Message Queue:** RabbitMQ
- **Status:** 🚧 Phase 1 - Foundation (Week 1, Day 1 complete)

## Architecture

### Service Structure

```
execution-service/
├── app/
│   ├── api/              # REST endpoints
│   │   └── endpoints/    # Position, Portfolio, Control, Analytics
│   ├── core/             # Config, events
│   ├── services/         # Business logic (Order Manager, Risk Guardian)
│   ├── adapters/         # CCXT, DB, RabbitMQ adapters
│   ├── models/           # SQLAlchemy models (Position, Order)
│   ├── utils/            # Logger, helpers
│   └── main.py           # FastAPI application
├── tests/
├── Dockerfile            # Python 3.11-slim
├── requirements.txt      # Dependencies
├── .env.example          # Configuration reference
└── README.md
```

### Development Phases

**Phase 1: Foundation ✅ (Week 1-2)**
- [x] Service skeleton (FastAPI, Docker)
- [x] Configuration management (Pydantic Settings)
- [x] JSON logging (Grafana-ready)
- [x] Health check endpoints
- [ ] Database schema (positions, orders, trades)
- [ ] RabbitMQ integration

**Phase 2: Core Execution (Weeks 3-6)**
- [ ] Signal consumer (validation, idempotency)
- [ ] Exchange adapter (CCXT Bybit)
- [ ] Order manager
- [ ] Execution orchestrator

**Phase 3: Risk & Safety (Weeks 7-8)**
- [ ] Risk guardian (pre-trade checks)
- [ ] Kill-switch (daily loss limit)
- [ ] Position tracker
- [ ] State manager (Redis + PostgreSQL)

**Phase 4: State Management (Weeks 9-10)**
- [ ] Reconciliation loop
- [ ] WebSocket integration
- [ ] Risk monitor (stop-loss, take-profit)

**Phase 5: Hardening (Weeks 11-12)**
- [ ] Stress testing
- [ ] Edge case testing
- [ ] Monitoring & alerts
- [ ] Testnet validation

## API Endpoints

### Position Management

#### GET /positions

List positions with optional status filter.

**Query Parameters:**
- `status_filter` (string, optional): Position status - `OPEN`, `CLOSED`, or `ALL` (default: `OPEN`)
- `limit` (integer, optional): Maximum number of positions to return (default: 100)

**Response:** `200 OK`

```json
{
  "count": 2,
  "status_filter": "OPEN",
  "positions": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "exchange": "bybit",
      "symbol": "BTC/USDT:USDT",
      "side": "long",
      "status": "open",
      "entry_price": 42500.00,
      "current_price": 43000.00,
      "quantity": 0.05,
      "notional_value": 2150.00,
      "unrealized_pnl": 25.00,
      "realized_pnl": 0.00,
      "stop_loss": 41500.00,
      "take_profit": 44500.00,
      "max_loss": 50.00,
      "signal_id": "sig_123456",
      "opened_at": "2025-12-22T10:30:00Z",
      "closed_at": null
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "exchange": "bybit",
      "symbol": "ETH/USDT:USDT",
      "side": "short",
      "status": "open",
      "entry_price": 2300.00,
      "current_price": 2280.00,
      "quantity": 1.0,
      "notional_value": 2280.00,
      "unrealized_pnl": 20.00,
      "realized_pnl": 0.00,
      "stop_loss": 2350.00,
      "take_profit": 2200.00,
      "max_loss": 50.00,
      "signal_id": "sig_123457",
      "opened_at": "2025-12-22T11:15:00Z",
      "closed_at": null
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid status filter
- `500 Internal Server Error`: Database error
- `503 Service Unavailable`: Database adapter not initialized

**Authentication:** Not required (internal service)

---

#### GET /positions/{position_id}

Get detailed information about a specific position.

**Path Parameters:**
- `position_id` (string, required): Position UUID

**Response:** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "exchange": "bybit",
  "symbol": "BTC/USDT:USDT",
  "side": "long",
  "status": "open",
  "entry_price": 42500.00,
  "current_price": 43000.00,
  "quantity": 0.05,
  "notional_value": 2150.00,
  "unrealized_pnl": 25.00,
  "realized_pnl": 0.00,
  "stop_loss": 41500.00,
  "take_profit": 44500.00,
  "max_loss": 50.00,
  "signal_id": "sig_123456",
  "opened_at": "2025-12-22T10:30:00Z",
  "closed_at": null
}
```

**Error Responses:**
- `404 Not Found`: Position not found
- `500 Internal Server Error`: Database error
- `503 Service Unavailable`: Database adapter not initialized

**Authentication:** Not required (internal service)

---

#### POST /positions/{position_id}/close

Manually close an open position.

**Path Parameters:**
- `position_id` (string, required): Position UUID

**Response:** `200 OK`

```json
{
  "message": "Position closed successfully",
  "position_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "order_id": "ord_987654321",
  "exchange_order_id": "bybit_123456789",
  "realized_pnl": 25.00,
  "exit_price": 43000.00,
  "closing_reason": "MANUAL"
}
```

**Error Responses:**
- `400 Bad Request`: Position already closed/liquidated
- `404 Not Found`: Position not found
- `500 Internal Server Error`: Order execution failed
- `503 Service Unavailable`: Exchange adapter not initialized

**Authentication:** Not required (internal service)

---

### Portfolio Management

#### GET /portfolio

Get portfolio summary including balance, equity, P&L, and exposure.

**Response:** `200 OK`

```json
{
  "timestamp": "2025-12-22T12:00:00Z",
  "balance": {
    "initial": 10000.00,
    "current": 10150.00,
    "note": "TODO: Fetch real balance from exchange"
  },
  "equity": 10195.00,
  "pnl": {
    "unrealized": 45.00,
    "realized_today": 150.00,
    "realized_all_time": 150.00,
    "daily_total": 195.00
  },
  "exposure": {
    "total": 4430.00,
    "long": 2150.00,
    "short": 2280.00,
    "net": -130.00
  },
  "positions": {
    "open": 2,
    "closed_today": 3,
    "long_count": 1,
    "short_count": 1
  },
  "breakdown": {
    "long": {
      "count": 1,
      "exposure": 2150.00,
      "pnl": 25.00
    },
    "short": {
      "count": 1,
      "exposure": 2280.00,
      "pnl": 20.00
    }
  }
}
```

**Field Descriptions:**
- `balance.initial`: Starting balance (placeholder - 10,000 USD)
- `balance.current`: Current balance (initial + realized P&L all-time)
- `balance.note`: TODO item for production
- `equity`: Balance + unrealized P&L
- `pnl.unrealized`: Sum of all open position unrealized P&L
- `pnl.realized_today`: Sum of closed positions P&L (today only)
- `pnl.realized_all_time`: Sum of all closed positions P&L
- `pnl.daily_total`: realized_today + unrealized
- `exposure.total`: Total notional value of open positions
- `exposure.long`: Notional value of long positions
- `exposure.short`: Notional value of short positions
- `exposure.net`: long - short (positive = net long, negative = net short)

**Error Responses:**
- `500 Internal Server Error`: Database error
- `503 Service Unavailable`: Database adapter not initialized

**Authentication:** Not required (internal service)

---

#### GET /portfolio/performance

Get performance metrics over a time period.

**Query Parameters:**
- `days` (integer, optional): Number of days to look back (default: 7)

**Response:** `200 OK`

```json
{
  "period_days": 7,
  "start_date": "2025-12-15T12:00:00Z",
  "end_date": "2025-12-22T12:00:00Z",
  "total_trades": 15,
  "total_pnl": 450.50,
  "win_rate": 66.67,
  "wins": {
    "count": 10,
    "average": 60.00,
    "largest": 120.00,
    "total": 600.00
  },
  "losses": {
    "count": 5,
    "average": -29.90,
    "largest": -50.00,
    "total": 149.50
  },
  "profit_factor": 4.01
}
```

**Field Descriptions:**
- `total_trades`: Number of closed positions in period
- `total_pnl`: Sum of realized P&L for all closed positions
- `win_rate`: Percentage of trades with positive P&L (0-100)
- `wins.count`: Number of winning trades
- `wins.average`: Average P&L per winning trade
- `wins.largest`: Largest single winning trade
- `wins.total`: Gross profit (sum of all winning trades)
- `losses.count`: Number of losing trades
- `losses.average`: Average P&L per losing trade (negative)
- `losses.largest`: Largest single losing trade (negative)
- `losses.total`: Gross loss (absolute value)
- `profit_factor`: Gross profit / Gross loss ratio (higher is better)

**No Data Response:** `200 OK`

```json
{
  "period_days": 7,
  "total_trades": 0,
  "message": "No closed positions in this period"
}
```

**Error Responses:**
- `500 Internal Server Error`: Database error
- `503 Service Unavailable`: Database adapter not initialized

**Authentication:** Not required (internal service)

---

### Trading Control

#### POST /control/stop

Emergency stop - Panic button. Halts all trading activities.

**Query Parameters:**
- `reason` (string, optional): Reason for emergency stop (default: "Manual emergency stop")

**Response:** `200 OK`

```json
{
  "message": "Emergency stop activated - trading halted",
  "halted_at": "2025-12-22T12:30:00Z",
  "reason": "Manual emergency stop",
  "note": "New positions will not be opened. Existing positions continue to be monitored."
}
```

**Already Halted Response:** `200 OK`

```json
{
  "message": "Trading already halted",
  "halted_at": "2025-12-22T12:00:00Z",
  "reason": "Manual emergency stop"
}
```

**Behavior:**
- Signal processing continues (to track signals)
- No new positions will be opened
- Existing positions continue to be monitored
- Risk monitor continues (to close positions if needed)

**Error Responses:**
- None (always succeeds)

**Authentication:** Not required (internal service)

**Use Cases:**
- Market volatility spikes
- Unexpected system behavior
- Manual intervention required
- External event (news, regulatory change)

---

#### POST /control/resume

Resume trading after emergency stop.

**Response:** `200 OK`

```json
{
  "message": "Trading resumed successfully",
  "resumed_at": "2025-12-22T13:00:00Z",
  "previous_halt": {
    "halted_at": "2025-12-22T12:30:00Z",
    "reason": "Manual emergency stop",
    "duration_seconds": 1800
  }
}
```

**Not Halted Response:** `200 OK`

```json
{
  "message": "Trading is not halted",
  "status": "active"
}
```

**Error Responses:**
- None (always succeeds)

**Authentication:** Not required (internal service)

---

#### GET /control/status

Get system control status (frontend-compatible).

**Response:** `200 OK`

```json
{
  "timestamp": "2025-12-22T12:00:00Z",
  "trading_enabled": true,
  "dry_run": true,
  "kill_switch_active": false,
  "daily_loss": 45.00,
  "max_daily_loss": 100.00,
  "open_positions": 2,
  "max_positions": 3,
  "exchange": "bybit",
  "mode": "testnet",
  "trading_halted": false,
  "halt_info": null
}
```

**Halted Status Response:** `200 OK`

```json
{
  "timestamp": "2025-12-22T12:00:00Z",
  "trading_enabled": false,
  "dry_run": true,
  "kill_switch_active": true,
  "daily_loss": -120.00,
  "max_daily_loss": 100.00,
  "open_positions": 1,
  "max_positions": 3,
  "exchange": "bybit",
  "mode": "testnet",
  "trading_halted": true,
  "halt_info": {
    "halted_at": "2025-12-22T11:30:00Z",
    "reason": "Daily loss limit exceeded",
    "duration_seconds": 1800
  }
}
```

**Field Descriptions:**
- `trading_enabled`: Inverse of trading_halted (true = trading active)
- `dry_run`: Whether service is in dry-run mode (no real orders)
- `kill_switch_active`: Manual halt OR daily loss exceeded
- `daily_loss`: Today's P&L (negative = loss)
- `max_daily_loss`: Maximum allowed daily loss (from config)
- `open_positions`: Current count of open positions
- `max_positions`: Maximum allowed open positions (from config)
- `exchange`: Exchange name (bybit)
- `mode`: testnet or live
- `trading_halted`: Legacy field (manual emergency stop flag)
- `halt_info`: Details if trading_halted is true

**Kill Switch Logic:**
Kill switch activates when:
1. Manual emergency stop (`trading_halted = true`), OR
2. Daily loss exceeds limit (`daily_pnl < -MAX_DAILY_LOSS_USD`)

**Error Responses:**
- None (always succeeds, returns default values on error)

**Authentication:** Not required (internal service)

---

#### POST /control/reset-kill-switch

Reset kill switch and resume trading (manual override).

**Response:** `200 OK`

```json
{
  "message": "Kill switch reset successfully",
  "kill_switch_active": false,
  "trading_enabled": true,
  "daily_loss": -80.00,
  "max_daily_loss": 100.00,
  "warning": null,
  "reset_info": {
    "was_manually_halted": true,
    "previous_halt_reason": "Manual emergency stop",
    "reset_at": "2025-12-22T13:00:00Z"
  }
}
```

**Loss Limit Still Exceeded Response:** `200 OK`

```json
{
  "message": "Kill switch reset successfully",
  "kill_switch_active": true,
  "trading_enabled": true,
  "daily_loss": -120.00,
  "max_daily_loss": 100.00,
  "warning": "⚠️ Daily loss limit exceeded! Trading enabled by manual override. Monitor carefully.",
  "reset_info": {
    "was_manually_halted": false,
    "previous_halt_reason": null,
    "reset_at": "2025-12-22T13:00:00Z"
  }
}
```

**Behavior:**
1. Clears emergency stop flag (`trading_halted = False`)
2. Clears halt reason and timestamp
3. Allows trading to resume EVEN IF daily loss limit is exceeded
4. Daily loss counter is NOT reset (real P&L data remains)

**⚠️ WARNING:**
- This will allow trading to continue even if daily loss limit is exceeded
- User takes conscious risk by resuming trading after kill switch
- Use with extreme caution

**Error Responses:**
- None (always succeeds)

**Authentication:** Not required (internal service)

**Use Cases:**
- Recover from false-positive kill switch trigger
- Manual override for controlled loss situations
- Testing/debugging kill switch behavior

---

#### GET /control/health

Health check endpoint for control system.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "timestamp": "2025-12-22T12:00:00Z",
  "trading_halted": false
}
```

**Error Responses:**
- None (always succeeds)

**Authentication:** Not required (internal service)

---

### Strategy Analytics

#### GET /analytics/strategies

Get strategy performance leaderboard (Multi-Strategy Arena Mode analytics).

**Response Model:** `StrategyLeaderboard`

**Response:** `200 OK`

```json
{
  "total_strategies": 3,
  "total_closed_trades": 15,
  "strategies": [
    {
      "strategy": "OITrend",
      "total_trades": 8,
      "win_rate": 0.75,
      "total_pnl": 450.50,
      "avg_pnl": 56.31,
      "profit_factor": 3.2,
      "winning_trades": 6,
      "losing_trades": 2,
      "gross_profit": 600.00,
      "gross_loss": 187.50
    },
    {
      "strategy": "MeanReversion",
      "total_trades": 5,
      "win_rate": 0.60,
      "total_pnl": 120.30,
      "avg_pnl": 24.06,
      "profit_factor": 1.8,
      "winning_trades": 3,
      "losing_trades": 2,
      "gross_profit": 220.00,
      "gross_loss": 122.22
    },
    {
      "strategy": "VolatilityBreakout",
      "total_trades": 2,
      "win_rate": 0.50,
      "total_pnl": -50.00,
      "avg_pnl": -25.00,
      "profit_factor": 0.67,
      "winning_trades": 1,
      "losing_trades": 1,
      "gross_profit": 100.00,
      "gross_loss": 150.00
    }
  ]
}
```

**Field Descriptions:**
- `total_strategies`: Number of strategies with closed positions
- `total_closed_trades`: Total closed trades across all strategies
- `strategies`: Array of strategy metrics (sorted by `total_pnl` descending)
  - `strategy`: Strategy name (extracted from `position.metadata.strategy`)
  - `total_trades`: Number of closed positions for this strategy
  - `win_rate`: Percentage of trades with positive P&L (0-1)
  - `total_pnl`: Sum of realized P&L (USD)
  - `avg_pnl`: Average P&L per trade (USD)
  - `profit_factor`: Gross profit / Gross loss ratio (null if no losses)
  - `winning_trades`: Count of profitable trades
  - `losing_trades`: Count of losing trades (includes break-even)
  - `gross_profit`: Sum of all winning trades
  - `gross_loss`: Sum of all losing trades (absolute value)

**No Data Response:** `200 OK`

```json
{
  "total_strategies": 0,
  "total_closed_trades": 0,
  "strategies": []
}
```

**Error Responses:**
- `500 Internal Server Error`: Database error
- `503 Service Unavailable`: Database adapter not initialized

**Authentication:** Not required (internal service)

**Use Cases:**
- Multi-Strategy Arena Mode: Compare which strategy performs best
- Forward testing: Track real-world strategy performance
- Risk management: Identify underperforming strategies
- Strategy rotation: Disable low-performing strategies

**Strategy Metadata:**
Strategy name is extracted from `Position.metadata_['strategy']`. Example:

```python
position.metadata_ = {
    "strategy": "OITrend",
    "signal_version": "v2.1",
    "model_id": "oi_lstm_20251201"
}
```

---

## Data Models

### Position Model

**Database Table:** `positions`

**Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | No | Primary key |
| `exchange` | string | No | Exchange name (bybit) |
| `symbol` | string | No | Trading pair (e.g., BTC/USDT:USDT) |
| `exchange_position_id` | string | Yes | Exchange-specific position ID (unique) |
| `side` | string | No | Position direction: `long` or `short` |
| `entry_price` | float | No | Average entry price |
| `current_price` | float | Yes | Latest market price |
| `quantity` | float | No | Position size (contracts/coins) |
| `notional_value` | float | Yes | quantity * current_price |
| `unrealized_pnl` | float | No | Unrealized profit/loss (default: 0.0) |
| `realized_pnl` | float | No | Realized profit/loss after closing (default: 0.0) |
| `stop_loss` | float | Yes | Stop loss price |
| `take_profit` | float | Yes | Take profit price |
| `max_loss` | float | Yes | Maximum allowed loss (from signal) |
| `status` | enum | No | Position status (see below) |
| `signal_id` | string | Yes | Reference to originating signal |
| `opened_at` | datetime | No | Position open timestamp |
| `closed_at` | datetime | Yes | Position close timestamp |
| `metadata_` | JSON | No | Arbitrary metadata (strategy, version, etc.) |

**Position Status Enum:**
- `OPEN`: Position is currently active
- `CLOSED`: Position closed normally
- `LIQUIDATED`: Position forcibly closed by exchange

**Indexes:**
- `idx_position_status_opened`: Composite index on (status, opened_at)
- `idx_position_symbol_status`: Composite index on (symbol, status)
- `exchange_position_id`: Unique index

**Example Metadata:**

```json
{
  "strategy": "OITrend",
  "signal_version": "v2.1",
  "model_id": "oi_lstm_20251201",
  "confidence": 0.85,
  "risk_reward_ratio": 3.5,
  "entry_reason": "OI divergence detected"
}
```

---

## Configuration

All configuration is managed via environment variables (see `.env.example`).

### Critical Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `BYBIT_TESTNET` | `true` | Use testnet (⚠️ false = live trading) |
| `BYBIT_API_KEY` | - | Bybit API key |
| `BYBIT_API_SECRET` | - | Bybit API secret |
| `DRY_RUN_MODE` | `true` | Simulate trades (no real orders) |
| `TRADING_ENABLED` | `true` | Enable/disable trading |
| `MAX_DAILY_LOSS_USD` | `100.0` | Daily loss limit (kill-switch) |
| `MAX_OPEN_POSITIONS` | `3` | Maximum concurrent positions |
| `MAX_POSITION_SIZE_USD` | `1000.0` | Maximum position size |
| `MIN_POSITION_SIZE_USD` | `50.0` | Minimum position size |
| `MAX_DRAWDOWN_PERCENT` | `10.0` | Maximum drawdown percentage |
| `MIN_SIGNAL_CONFIDENCE` | `0.70` | Minimum signal confidence (70%) |
| `MIN_RISK_REWARD_RATIO` | `2.0` | Minimum risk/reward ratio |
| `ALLOWED_SYMBOLS` | `["BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT"]` | Symbol whitelist |

### Service Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `execution-service` | Service name |
| `ENVIRONMENT` | `development` | Environment (development, staging, production) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/news_platform` | PostgreSQL connection string |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/3` | Redis connection string |
| `REDIS_DB` | `3` | Dedicated DB for execution-service |

### RabbitMQ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | RabbitMQ connection string |

### Exchange Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCHANGE` | `bybit` | Exchange name |
| `EXCHANGE_TIMEOUT` | `30000` | Exchange API timeout (ms) |
| `EXCHANGE_ENABLE_RATE_LIMIT` | `true` | Enable rate limiting (critical!) |

### Reconciliation Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RECONCILIATION_ENABLED` | `true` | Enable reconciliation loop |
| `RECONCILIATION_INTERVAL_SECONDS` | `60` | Reconciliation interval (seconds) |

### WebSocket Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSOCKET_ENABLED` | `true` | Enable WebSocket for real-time updates |
| `WEBSOCKET_PING_INTERVAL` | `30` | Heartbeat interval (seconds) |
| `WEBSOCKET_RECONNECT_DELAY` | `5` | Reconnect delay after disconnect (seconds) |

### Monitoring Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |
| `METRICS_PORT` | `9090` | Prometheus metrics port |

---

## Bybit Perpetual Futures Format

**Symbol Format:** `{BASE}/{QUOTE}:{SETTLE}`

**Examples:**
- `BTC/USDT:USDT` - BTC perpetual, USDT-margined
- `ETH/USDT:USDT` - ETH perpetual, USDT-margined
- `BNB/USDT:USDT` - BNB perpetual, USDT-margined

**Default Allowed Symbols:**
```python
ALLOWED_SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT"]
```

---

## Risk Management

### Kill-Switch

Automatically halts trading if:
- Daily realized loss > `MAX_DAILY_LOSS_USD` (default: $100)
- Max drawdown > `MAX_DRAWDOWN_PERCENT` (default: 10%)

**Behavior:**
- New positions will NOT be opened
- Existing positions continue to be monitored
- Risk monitor continues (can close positions)
- Signal processing continues (to track signals)

**Manual Override:** Use `POST /control/reset-kill-switch` to resume trading

### Position Limits

- Max open positions: 3 (configurable via `MAX_OPEN_POSITIONS`)
- Max positions per symbol: 1 (configurable via `MAX_POSITIONS_PER_SYMBOL`)
- Max position size: $1000 (configurable via `MAX_POSITION_SIZE_USD`)
- Min position size: $50 (configurable via `MIN_POSITION_SIZE_USD`)

### Signal Filtering

- Min confidence: 0.70 (70%, configurable via `MIN_SIGNAL_CONFIDENCE`)
- Min risk/reward ratio: 2:1 (configurable via `MIN_RISK_REWARD_RATIO`)

---

## Safety Guidelines

### Before Live Trading

- [ ] 3+ months testnet validation (MINIMUM)
- [ ] Zero critical bugs in last 4 weeks
- [ ] 100% reconciliation accuracy
- [ ] Kill-switch tested 10+ times
- [ ] Performance: Signal → Order < 500ms (p95)

### Production Checklist

- [ ] `BYBIT_TESTNET=false` (live mode)
- [ ] `DRY_RUN_MODE=false` (real orders)
- [ ] Secrets in vault (not .env)
- [ ] Monitoring alerts configured
- [ ] Backup & disaster recovery plan
- [ ] Initial capital: $1000 max (first 6 months)

---

## Monitoring & Observability

### Logs

Structured JSON logs for Grafana/Loki:

```bash
# View logs
docker logs -f news-execution-service

# Filter by level
docker logs news-execution-service 2>&1 | grep '"levelname":"ERROR"'

# Filter by endpoint
docker logs news-execution-service 2>&1 | grep '"endpoint":"/positions"'
```

**Log Fields:**
- `timestamp`: ISO 8601 timestamp
- `levelname`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message`: Human-readable message
- `service`: Service name (execution-service)
- `extra`: Contextual data (position_id, symbol, pnl, etc.)

### Metrics

Prometheus metrics endpoint (coming in Phase 5):
- `GET /metrics` - Prometheus metrics

**Planned Metrics:**
- `execution_positions_open_total`: Current open positions
- `execution_positions_closed_total`: Total closed positions
- `execution_daily_pnl_usd`: Daily P&L in USD
- `execution_kill_switch_active`: Kill switch status (0/1)
- `execution_order_duration_seconds`: Order execution latency
- `execution_api_errors_total`: Exchange API errors

### Grafana Dashboard

Custom dashboard for trading metrics (coming in Phase 5).

**Panels:**
- Open positions by symbol
- Daily P&L trend
- Win rate over time
- Kill-switch activations
- Order execution latency
- API error rate

---

## Error Handling

### HTTP Status Codes

| Code | Description | Typical Cause |
|------|-------------|---------------|
| `200 OK` | Request successful | - |
| `400 Bad Request` | Invalid request parameters | Invalid status filter, position already closed |
| `404 Not Found` | Resource not found | Position ID doesn't exist |
| `500 Internal Server Error` | Server error | Database error, order execution failed |
| `503 Service Unavailable` | Service dependency unavailable | Database/exchange adapter not initialized |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example:**

```json
{
  "detail": "Position a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found"
}
```

---

## Architecture Decisions

Based on analysis in `/home/cytrex/userdocs/crypto-lab/`:

1. **Custom vs Freqtrade**: Custom solution for architectural purity
   - Pros: Full control, clean integration with microservices
   - Cons: +50% dev time, +100% risk, extensive testing required

2. **Exchange**: Bybit (not Binance) for better API
   - Better WebSocket stability
   - Cleaner perpetual futures API
   - Lower latency (tested in testnet)

3. **State Management**: Redis (hot) + PostgreSQL (cold) + Reconciliation
   - Redis: Real-time position tracking
   - PostgreSQL: Permanent record, analytics
   - Reconciliation: Hourly sync with exchange

4. **Risk**: +50% dev time, +100% risk, extensive testnet required
   - 3+ months testnet validation before live trading
   - Comprehensive testing (unit, integration, stress)
   - Monitoring & alerting critical

**References:**
- `06-custom-execution-service-design.md` - Architecture review
- `07-custom-execution-implementation-plan.md` - Implementation plan

---

## Troubleshooting

### Service won't start

1. **Check logs:**
```bash
docker logs news-execution-service
```

2. **Verify credentials:**
```bash
curl http://localhost:8120/health | jq '.credentials_configured'
# Should return: true
```

3. **Check dependencies:**
```bash
# PostgreSQL healthy?
docker ps | grep postgres

# Redis healthy?
docker ps | grep redis

# RabbitMQ healthy?
docker ps | grep rabbitmq
```

### Exchange connection issues

1. **Testnet mode:**
```bash
curl http://localhost:8120/health | jq '.mode'
# Should return: "testnet"
```

2. **API credentials:**
- Testnet: https://testnet.bybit.com/app/user/api-management
- Mainnet: https://www.bybit.com/app/user/api-management

3. **IP whitelist** (if enabled):
- Add your server IP to Bybit API whitelist

### Credentials not configured

```bash
# Check environment variables in container
docker exec news-execution-service env | grep BYBIT

# Expected output:
# BYBIT_API_KEY=your_key
# BYBIT_API_SECRET=your_secret
# BYBIT_TESTNET=true
```

If missing, update `.env` and restart:
```bash
docker compose restart execution-service
```

### Kill switch won't reset

**Scenario:** Daily loss limit exceeded, kill switch active

**Solution:**
1. Verify daily P&L:
```bash
curl http://localhost:8120/control/status | jq '.daily_loss, .max_daily_loss'
```

2. Manual override (⚠️ use with caution):
```bash
curl -X POST http://localhost:8120/control/reset-kill-switch
```

3. Check warning in response:
```json
{
  "warning": "⚠️ Daily loss limit exceeded! Trading enabled by manual override. Monitor carefully."
}
```

### Position not closing

1. **Check position status:**
```bash
curl http://localhost:8120/positions/{position_id}
```

2. **Check exchange adapter status:**
```bash
curl http://localhost:8120/health | jq '.credentials_configured'
```

3. **Check logs for order errors:**
```bash
docker logs news-execution-service 2>&1 | grep "Error closing position"
```

---

## Testing

### Local Development (without Docker)

```bash
cd services/execution-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://..."
export REDIS_URL="redis://..."
export BYBIT_API_KEY="..."
export BYBIT_API_SECRET="..."

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# In container
docker exec -it news-execution-service pytest tests/ -v

# Local
pytest tests/ -v --cov=app
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8120/health

# List open positions
curl http://localhost:8120/positions?status_filter=OPEN

# Get portfolio summary
curl http://localhost:8120/portfolio

# Get performance metrics (last 7 days)
curl http://localhost:8120/portfolio/performance?days=7

# Get strategy leaderboard
curl http://localhost:8120/analytics/strategies

# Emergency stop
curl -X POST http://localhost:8120/control/stop?reason=Testing

# Resume trading
curl -X POST http://localhost:8120/control/resume

# Get control status
curl http://localhost:8120/control/status
```

---

## Security Considerations

### API Credentials

⚠️ **CRITICAL:**
- Never commit `.env` to git
- Use secrets management in production (Vault, AWS Secrets Manager)
- Rotate API keys regularly
- Use IP whitelisting on Bybit API keys

### Dry-Run Mode

**Default:** `DRY_RUN_MODE=true`

**Behavior:**
- Orders are simulated (not sent to exchange)
- Position tracking works normally
- P&L calculations are based on simulated fills

**Production:**
- Set `DRY_RUN_MODE=false` ONLY after extensive testnet validation
- Requires manual confirmation (not automated)

### Testnet vs Mainnet

**Default:** `BYBIT_TESTNET=true`

**⚠️ WARNING:**
- Setting `BYBIT_TESTNET=false` enables live trading
- Requires separate API credentials
- Financial risk - ALWAYS test on testnet first

---

## Performance Considerations

### Database Queries

**Optimized Queries:**
- Positions list: Indexed on (status, opened_at)
- Position lookup: Primary key (UUID)
- Portfolio metrics: Aggregated in memory (not DB)

**Expected Performance:**
- List positions: < 50ms (p95)
- Get position: < 20ms (p95)
- Portfolio summary: < 100ms (p95)
- Performance metrics: < 200ms (p95)

### Exchange API

**Rate Limiting:**
- `EXCHANGE_ENABLE_RATE_LIMIT=true` (critical!)
- CCXT handles rate limiting automatically
- Prevents nonce errors and API bans

**Expected Performance:**
- Order placement: < 500ms (p95)
- Position sync: < 300ms (p95)

---

## References

- **Documentation:** `/home/cytrex/userdocs/crypto-lab/`
- **Implementation Plan:** `07-custom-execution-implementation-plan.md`
- **Architecture Design:** `06-custom-execution-service-design.md`
- **Bybit API Docs:** https://bybit-exchange.github.io/docs/v5/intro
- **CCXT Documentation:** https://docs.ccxt.com/

---

## Contact

For questions about the execution-service:
- Check documentation in `/home/cytrex/userdocs/crypto-lab/`
- Review implementation plan
- Test on testnet first!

---

**⚠️ WARNING:** This service handles real money. Always test on testnet first. Never skip safety validations.

**🔐 SECURITY:** Keep API credentials secure. Never commit `.env` to git. Use secrets management in production.

**📊 MONITORING:** Enable comprehensive monitoring before live trading. Set up alerts for kill-switch activation.

---

**Last Updated:** 2025-12-22
**Version:** Phase 1 Foundation
**Status:** 🚧 In Development
