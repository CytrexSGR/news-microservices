# Prediction Service API Documentation

**Base URL:** `http://localhost:8116`
**Version:** v1
**OpenAPI:** http://localhost:8116/openapi.json
**Swagger UI:** http://localhost:8116/docs

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Info](#health--info)
3. [Feature Engineering](#feature-engineering)
4. [Predictions](#predictions)
5. [Trading Signals](#trading-signals)
6. [Event Impact](#event-impact)
7. [Portfolio Optimization](#portfolio-optimization)
8. [Backtesting](#backtesting)
9. [Performance](#performance)
10. [Error Responses](#error-responses)

---

## Authentication

**Current Status:** No authentication required (internal service)

**Future:** JWT tokens via auth-service

```http
Authorization: Bearer <token>
```

---

## Health & Info

### GET /health

Health check endpoint.

**Response:**
```json
{
  "service": "prediction-service",
  "version": "0.1.0",
  "status": "healthy"
}
```

### GET /

Service information and endpoints.

**Response:**
```json
{
  "service": "prediction-service",
  "version": "0.1.0",
  "description": "Predictive Analytics Service",
  "features": [
    "Multi-horizon forecasts (1D, 1W, 1M)",
    "Geopolitical event predictions",
    "ML ensemble models",
    "Backtest validation",
    "Paper trading signals"
  ],
  "endpoints": {
    "features": "/api/v1/features",
    "predictions": "/api/v1/predictions",
    "signals": "/api/v1/signals",
    "backtests": "/api/v1/backtests",
    "performance": "/api/v1/performance"
  }
}
```

---

## Feature Engineering

### GET /api/v1/features/{article_id}

Get extracted features for an article.

**Path Parameters:**
- `article_id` (UUID, required) - Article identifier

**Response:**
```json
{
  "feature_id": "uuid",
  "article_id": "uuid",
  "features": {
    "sentiment_score": 0.65,
    "bullish_ratio": 0.72,
    "topic_count": 5,
    "geographic_concentration": 0.45,
    "source_diversity": 0.88
  },
  "extracted_at": "2025-11-16T10:30:00Z"
}
```

### POST /api/v1/features/extract

Extract features from an article.

**Request Body:**
```json
{
  "article_id": "uuid"
}
```

**Response:**
```json
{
  "feature_id": "uuid",
  "article_id": "uuid",
  "features": {
    "sentiment_score": 0.65,
    "bullish_ratio": 0.72,
    "topic_count": 5
  },
  "extracted_at": "2025-11-16T10:30:00Z"
}
```

---

## Predictions

### POST /api/v1/predictions/predict

Generate a price forecast.

**Request Body:**
```json
{
  "article_id": "uuid",
  "symbol": "AAPL",
  "horizon": "1W",
  "model_name": "SentimentPredictor"
}
```

**Parameters:**
- `article_id` (UUID, required) - Article identifier
- `symbol` (string, required) - Stock symbol
- `horizon` (enum, required) - `1D` | `1W` | `1M`
- `model_name` (enum, required) - `SentimentPredictor` | `TopicVolumePredictor` | `ARIMAPredictor`

**Response:**
```json
{
  "forecast_id": "uuid",
  "symbol": "AAPL",
  "predicted_direction": "UP",
  "predicted_value": 0.025,
  "confidence": 0.72,
  "horizon": "1W",
  "model_name": "SentimentPredictor",
  "forecast_date": "2025-11-16",
  "target_date": "2025-11-23",
  "metadata": {
    "feature_count": 12,
    "data_quality": 0.95
  }
}
```

**Predicted Direction:**
- `UP` - Price expected to rise
- `DOWN` - Price expected to fall
- `FLAT` - No significant movement expected

### GET /api/v1/predictions/forecasts

List recent forecasts.

**Query Parameters:**
- `symbol` (string, optional) - Filter by symbol
- `horizon` (enum, optional) - Filter by horizon
- `model_name` (string, optional) - Filter by model
- `limit` (int, optional, default: 50) - Max results (1-200)

**Response:**
```json
{
  "forecasts": [
    {
      "forecast_id": "uuid",
      "symbol": "AAPL",
      "predicted_direction": "UP",
      "predicted_value": 0.025,
      "confidence": 0.72,
      "horizon": "1W",
      "model_name": "SentimentPredictor",
      "forecast_date": "2025-11-16"
    }
  ],
  "total": 156,
  "limit": 50
}
```

### GET /api/v1/predictions/forecasts/{forecast_id}

Get specific forecast.

**Path Parameters:**
- `forecast_id` (UUID, required) - Forecast identifier

**Response:**
```json
{
  "forecast_id": "uuid",
  "symbol": "AAPL",
  "predicted_direction": "UP",
  "predicted_value": 0.025,
  "confidence": 0.72,
  "horizon": "1W",
  "model_name": "SentimentPredictor",
  "forecast_date": "2025-11-16",
  "target_date": "2025-11-23",
  "metadata": {
    "features_used": ["sentiment_score", "bullish_ratio"],
    "data_quality": 0.95
  }
}
```

### POST /api/v1/predictions/batch-predict

Generate multiple forecasts.

**Request Body:**
```json
{
  "predictions": [
    {
      "article_id": "uuid1",
      "symbol": "AAPL",
      "horizon": "1W"
    },
    {
      "article_id": "uuid2",
      "symbol": "MSFT",
      "horizon": "1M"
    }
  ],
  "model_name": "SentimentPredictor"
}
```

**Response:**
```json
{
  "forecasts": [
    {
      "forecast_id": "uuid",
      "symbol": "AAPL",
      "predicted_direction": "UP",
      "confidence": 0.72
    },
    {
      "forecast_id": "uuid",
      "symbol": "MSFT",
      "predicted_direction": "DOWN",
      "confidence": 0.68
    }
  ],
  "total": 2,
  "failed": 0
}
```

---

## Trading Signals

### POST /api/v1/signals/generate

Generate trading signal from a forecast.

**Request Body:**
```json
{
  "forecast_id": "uuid",
  "strategy": "MOMENTUM",
  "current_price": 150.25
}
```

**Parameters:**
- `forecast_id` (UUID, required) - Forecast to convert to signal
- `strategy` (enum, required) - `MOMENTUM` | `MEAN_REVERSION` | `EVENT_DRIVEN`
- `current_price` (float, optional) - For stop-loss/take-profit calculation

**Strategy Behavior:**
| Strategy | UP Prediction | DOWN Prediction |
|----------|---------------|-----------------|
| MOMENTUM | BUY | SELL |
| MEAN_REVERSION | SELL | BUY |
| EVENT_DRIVEN | BUY | SELL |

**Response:**
```json
{
  "signal_id": "uuid",
  "symbol": "AAPL",
  "signal_type": "BUY",
  "signal_strength": 0.75,
  "confidence": 0.72,
  "strategy": "MOMENTUM",
  "expected_return": 0.025,
  "risk_reward_ratio": 3.0,
  "position_size": 0.08,
  "entry_price": 150.25,
  "stop_loss": 147.25,
  "take_profit": 159.27,
  "reasoning": "BUY signal based on momentum strategy. Model SentimentPredictor predicts UP direction (+2.50%) with 72% confidence."
}
```

**Signal Generation Rules:**
- Min. confidence: 60%
- Min. risk-reward: 2:1
- Position size: 5-10% (based on confidence)
- Stop-loss: 2% below entry
- Take-profit: 6% above entry (3:1 R/R)

**No Signal Cases:**
- Confidence < 60% → Returns 400 error
- Predicted direction = FLAT → Returns 400 error
- Risk-reward < 2:1 → Returns 400 error

### GET /api/v1/signals/

List active trading signals.

**Query Parameters:**
- `symbol` (string, optional) - Filter by symbol
- `strategy` (enum, optional) - Filter by strategy
- `limit` (int, optional, default: 50) - Max results (1-200)

**Response:**
```json
{
  "signals": [
    {
      "signal_id": "uuid",
      "symbol": "AAPL",
      "signal_type": "BUY",
      "signal_strength": 0.75,
      "confidence": 0.72,
      "strategy": "MOMENTUM",
      "expected_return": 0.025,
      "risk_reward_ratio": 3.0,
      "position_size": 0.08,
      "entry_price": 150.25,
      "stop_loss": 147.25,
      "take_profit": 159.27,
      "generated_at": "2025-11-16T10:30:00Z",
      "status": "ACTIVE"
    }
  ],
  "total": 12,
  "limit": 50
}
```

**Signal Status:**
- `ACTIVE` - Signal is active, position can be opened
- `CLOSED` - Position closed (profit/loss realized)
- `EXPIRED` - Signal expired (time limit reached)

---

## Event Impact

### POST /api/v1/signals/events/predict

Predict market impact of a geopolitical event.

**Request Body:**
```json
{
  "article_id": "uuid"
}
```

**Response:**
```json
{
  "impact_id": "uuid",
  "article_id": "uuid",
  "event_summary": "Ukraine conflict escalation near critical infrastructure",
  "impact_direction": "NEGATIVE",
  "impact_magnitude": "HIGH",
  "impact_duration": "LONG_TERM",
  "expected_market_move": -0.035,
  "volatility_increase": 0.025,
  "confidence": 0.72,
  "affected_sectors": ["Energy", "Defense"],
  "affected_symbols": [],
  "event_severity": 0.85,
  "event_topics": ["military_conflict"],
  "event_sentiment": -0.65
}
```

**Impact Direction:**
- `POSITIVE` - Market expected to rise
- `NEGATIVE` - Market expected to fall
- `NEUTRAL` - No significant directional impact
- `VOLATILE` - Increased volatility without clear direction

**Impact Magnitude:**
| Level | Market Move | Description |
|-------|-------------|-------------|
| NEGLIGIBLE | < 0.5% | Minimal reaction |
| LOW | 0.5-1% | Small correction |
| MODERATE | 1-2% | Notable movement |
| HIGH | 2-5% | Significant impact |
| SEVERE | > 5% | Major market event |

**Impact Duration:**
| Duration | Timeframe | Example Events |
|----------|-----------|----------------|
| IMMEDIATE | 1 day | Diplomatic statements |
| SHORT_TERM | 1 week | Political tensions |
| MEDIUM_TERM | 1 month | Economic sanctions |
| LONG_TERM | > 1 month | Military conflicts |

**Event Topics:**
- `military_conflict` (1.5x impact multiplier)
- `economic_sanctions` (1.3x)
- `political_crisis` (1.2x)
- `trade_dispute` (1.1x)
- `natural_disaster` (1.0x)
- `diplomatic_tension` (0.8x)

**No Prediction Cases:**
- Event severity < 0.3 → Returns 404 error
- Analysis not found → Returns 404 error

### GET /api/v1/signals/events/

List recent event impact predictions.

**Query Parameters:**
- `days` (int, optional, default: 7) - Lookback period (1-90)
- `limit` (int, optional, default: 50) - Max results (1-200)

**Response:**
```json
{
  "impacts": [
    {
      "impact_id": "uuid",
      "article_id": "uuid",
      "event_summary": "Ukraine conflict escalation...",
      "impact_direction": "NEGATIVE",
      "impact_magnitude": "HIGH",
      "impact_duration": "LONG_TERM",
      "expected_market_move": -0.035,
      "volatility_increase": 0.025,
      "confidence": 0.72,
      "affected_sectors": ["Energy", "Defense"],
      "created_at": "2025-11-16T10:30:00Z"
    }
  ],
  "total": 25,
  "limit": 50
}
```

---

## Portfolio Optimization

### POST /api/v1/signals/portfolio/optimize

Optimize portfolio allocation using Modern Portfolio Theory.

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"],
  "objective": "MAX_SHARPE",
  "risk_tolerance": "MODERATE",
  "current_weights": {
    "AAPL": 0.3,
    "MSFT": 0.3,
    "GOOGL": 0.2,
    "TSLA": 0.2
  },
  "min_weight": 0.0,
  "max_weight": 0.4,
  "lookback_days": 252
}
```

**Parameters:**
- `symbols` (array[string], required) - Symbols to include (2-50)
- `objective` (enum, required) - Optimization objective
- `risk_tolerance` (enum, required) - Risk tolerance level
- `current_weights` (dict, optional) - For rebalancing
- `min_weight` (float, optional, default: 0.0) - Min position size
- `max_weight` (float, optional, default: 0.3) - Max position size
- `lookback_days` (int, optional, default: 252) - Historical data period (30-1000)

**Optimization Objectives:**
| Objective | Description |
|-----------|-------------|
| MAX_SHARPE | Maximize (return - rf) / volatility |
| MIN_VARIANCE | Minimize portfolio variance |
| MAX_RETURN | Maximize expected return |
| RISK_PARITY | Equal risk contribution |
| MAX_DIVERSIFICATION | Maximize diversification ratio |

**Risk Tolerance Levels:**
| Level | Target Volatility | Investor Profile |
|-------|------------------|------------------|
| CONSERVATIVE | 10% annual | Capital preservation |
| MODERATE | 15% annual | Balanced growth |
| AGGRESSIVE | 25% annual | Growth seeking |

**Response:**
```json
{
  "weights": {
    "AAPL": 0.35,
    "MSFT": 0.40,
    "GOOGL": 0.15,
    "TSLA": 0.10
  },
  "expected_return": 0.125,
  "expected_volatility": 0.18,
  "sharpe_ratio": 0.47,
  "diversification_ratio": 1.23,
  "rebalancing_trades": {
    "AAPL": 0.05,
    "MSFT": 0.10,
    "GOOGL": -0.05,
    "TSLA": -0.10
  },
  "turnover": 0.15
}
```

**Metrics Explained:**
- `expected_return` - Annual expected return (from predictions)
- `expected_volatility` - Annual volatility (standard deviation)
- `sharpe_ratio` - (return - 4%) / volatility (higher is better)
- `diversification_ratio` - Weighted avg vol / portfolio vol (>1 means diversification benefit)
- `rebalancing_trades` - Position changes from current to optimal
- `turnover` - One-way turnover (sum(|trades|) / 2)

**Error Cases:**
- No predictions available → 400 error
- Insufficient historical data → 400 error
- Optimization did not converge → 500 error (warning logged)

### POST /api/v1/signals/portfolio/efficient-frontier

Calculate efficient frontier for visualization.

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "n_points": 50,
  "lookback_days": 252
}
```

**Parameters:**
- `symbols` (array[string], required) - Symbols to include (2-50)
- `n_points` (int, optional, default: 50) - Number of frontier points (10-200)
- `lookback_days` (int, optional, default: 252) - Historical data period (30-1000)

**Response:**
```json
{
  "frontier_points": [
    {
      "return": 0.08,
      "volatility": 0.12,
      "sharpe_ratio": 0.33
    },
    {
      "return": 0.10,
      "volatility": 0.14,
      "sharpe_ratio": 0.43
    },
    {
      "return": 0.12,
      "volatility": 0.18,
      "sharpe_ratio": 0.44
    }
    // ... 47 more points
  ],
  "n_points": 50,
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

**Use Case:**
Visualize risk-return tradeoff. Each point represents an optimal portfolio at a different return level. Plot volatility (x-axis) vs. return (y-axis) to see the efficient frontier curve.

---

## Backtesting

### POST /api/v1/backtests/run

Run historical backtest.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "horizon": "1W",
  "model_name": "SentimentPredictor",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

**Parameters:**
- `symbol` (string, required) - Stock symbol
- `horizon` (enum, required) - `1D` | `1W` | `1M`
- `model_name` (enum, required) - Model to backtest
- `start_date` (date, required) - Backtest start (YYYY-MM-DD)
- `end_date` (date, required) - Backtest end (YYYY-MM-DD)

**Response:**
```json
{
  "backtest_id": "uuid",
  "symbol": "AAPL",
  "horizon": "1W",
  "model_name": "SentimentPredictor",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "total_predictions": 156,
  "accuracy": 0.64,
  "sharpe_ratio": 0.85,
  "mae": 0.018,
  "rmse": 0.025,
  "mape": 0.021,
  "hit_rate": 0.68,
  "created_at": "2025-11-16T10:30:00Z"
}
```

**Metrics Explained:**
- `accuracy` - Directional accuracy (% correct UP/DOWN predictions)
- `sharpe_ratio` - Risk-adjusted return (higher is better)
- `mae` - Mean Absolute Error (lower is better)
- `rmse` - Root Mean Squared Error (lower is better)
- `mape` - Mean Absolute Percentage Error (lower is better)
- `hit_rate` - % of profitable predictions

### GET /api/v1/backtests/

List backtests.

**Query Parameters:**
- `symbol` (string, optional) - Filter by symbol
- `horizon` (enum, optional) - Filter by horizon
- `model_name` (string, optional) - Filter by model
- `limit` (int, optional, default: 50) - Max results (1-200)

**Response:**
```json
{
  "backtests": [
    {
      "backtest_id": "uuid",
      "symbol": "AAPL",
      "horizon": "1W",
      "model_name": "SentimentPredictor",
      "accuracy": 0.64,
      "sharpe_ratio": 0.85,
      "created_at": "2025-11-16T10:30:00Z"
    }
  ],
  "total": 48,
  "limit": 50
}
```

### GET /api/v1/backtests/{backtest_id}

Get specific backtest.

**Path Parameters:**
- `backtest_id` (UUID, required) - Backtest identifier

**Response:**
```json
{
  "backtest_id": "uuid",
  "symbol": "AAPL",
  "horizon": "1W",
  "model_name": "SentimentPredictor",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "total_predictions": 156,
  "accuracy": 0.64,
  "sharpe_ratio": 0.85,
  "mae": 0.018,
  "rmse": 0.025,
  "created_at": "2025-11-16T10:30:00Z"
}
```

### GET /api/v1/backtests/{backtest_id}/metrics

Get detailed metrics for a backtest.

**Response:**
```json
{
  "backtest_id": "uuid",
  "metrics": {
    "directional_accuracy": 0.64,
    "sharpe_ratio": 0.85,
    "mae": 0.018,
    "rmse": 0.025,
    "mape": 0.021,
    "hit_rate": 0.68,
    "max_drawdown": 0.12,
    "win_rate": 0.56,
    "avg_win": 0.032,
    "avg_loss": -0.018,
    "profit_factor": 1.78
  },
  "predictions": [
    {
      "date": "2024-01-08",
      "predicted": 0.025,
      "actual": 0.031,
      "error": -0.006,
      "correct_direction": true
    }
  ]
}
```

---

## Performance

### GET /api/v1/performance/metrics

Get overall model performance.

**Query Parameters:**
- `symbol` (string, optional) - Filter by symbol
- `horizon` (enum, optional) - Filter by horizon
- `model_name` (string, optional) - Filter by model
- `days` (int, optional, default: 30) - Lookback period (1-365)

**Response:**
```json
{
  "metrics": {
    "total_predictions": 1250,
    "avg_accuracy": 0.62,
    "avg_sharpe": 0.78,
    "avg_mae": 0.021,
    "avg_rmse": 0.029,
    "best_model": "SentimentPredictor",
    "best_horizon": "1W"
  },
  "by_model": {
    "SentimentPredictor": {
      "accuracy": 0.64,
      "sharpe": 0.85,
      "total": 450
    },
    "TopicVolumePredictor": {
      "accuracy": 0.58,
      "sharpe": 0.68,
      "total": 425
    },
    "ARIMAPredictor": {
      "accuracy": 0.65,
      "sharpe": 0.82,
      "total": 375
    }
  },
  "by_horizon": {
    "1D": {"accuracy": 0.58, "sharpe": 0.72},
    "1W": {"accuracy": 0.64, "sharpe": 0.85},
    "1M": {"accuracy": 0.61, "sharpe": 0.75}
  }
}
```

### GET /api/v1/performance/model-comparison

Compare model performance.

**Query Parameters:**
- `symbol` (string, optional) - Filter by symbol
- `horizon` (enum, optional) - Filter by horizon
- `days` (int, optional, default: 30) - Lookback period (1-365)

**Response:**
```json
{
  "comparison": [
    {
      "model_name": "SentimentPredictor",
      "accuracy": 0.64,
      "sharpe": 0.85,
      "mae": 0.018,
      "total_predictions": 450,
      "rank": 1
    },
    {
      "model_name": "ARIMAPredictor",
      "accuracy": 0.65,
      "sharpe": 0.82,
      "mae": 0.019,
      "total_predictions": 375,
      "rank": 2
    },
    {
      "model_name": "TopicVolumePredictor",
      "accuracy": 0.58,
      "sharpe": 0.68,
      "mae": 0.024,
      "total_predictions": 425,
      "rank": 3
    }
  ],
  "ranked_by": "sharpe_ratio"
}
```

---

## Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters, validation error |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error, database error |

### Common Errors

**400 Bad Request:**
```json
{
  "detail": "No signal generated (confidence too low or neutral prediction)"
}
```

**404 Not Found:**
```json
{
  "detail": "Forecast not found: uuid-here"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to calculate efficient frontier: unsupported operand type(s) for *: 'NoneType' and 'int'"
}
```

### Validation Errors

Pydantic validation errors include field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "symbols"],
      "msg": "ensure this value has at least 2 items",
      "type": "value_error.list.min_items"
    }
  ]
}
```

---

## Rate Limits

**Current:** No rate limits (internal service)

**Future:**
- 100 requests/minute per IP
- 1000 requests/hour per IP
- Burst: 20 requests/second

---

## Versioning

**Current Version:** v1
**Base Path:** `/api/v1`

**Future Versions:**
- v2: Enhanced with ensemble models
- v3: Real-time WebSocket streaming

**Deprecation Policy:**
- Versions supported for 6 months after new release
- Deprecation warnings 3 months in advance

---

## Changelog

### v0.1.0 (2025-11-16) - Phase 4 Complete

**Added:**
- Trading signals endpoints (2)
- Event impact endpoints (2)
- Portfolio optimization endpoints (2)
- Signal generation with 3 strategies
- Event impact prediction
- Modern Portfolio Theory optimization
- Efficient frontier calculation

**Changed:**
- N/A (first release)

**Deprecated:**
- N/A

### v0.0.3 (2025-11-15) - Phase 3 Complete

**Added:**
- Backtesting endpoints (4)
- Performance metrics endpoints (2)
- Outcome tracking
- Historical validation

### v0.0.2 (2025-11-14) - Phase 2 Complete

**Added:**
- Prediction endpoints (4)
- SentimentPredictor
- TopicVolumePredictor
- ARIMAPredictor
- Batch prediction support

### v0.0.1 (2025-11-13) - Phase 1 Complete

**Added:**
- Feature engineering endpoints (2)
- Health check
- Service info
- Database schema

---

## Support

**Swagger UI:** http://localhost:8116/docs
**OpenAPI Spec:** http://localhost:8116/openapi.json
**Service README:** `/services/prediction-service/README.md`

**Contact:**
- Email: andreas@test.com
- Issues: Create GitHub issue

---

**Last Updated:** 2025-11-16
**API Version:** v1
**Service Version:** 0.1.0
