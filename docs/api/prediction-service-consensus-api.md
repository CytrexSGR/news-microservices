# Prediction Service - Consensus API

## Overview

The Consensus API provides access to **multi-strategy aggregated trading signals** using weighted voting across all strategies.

**Base URL:** `http://localhost:8116/api/v1/consensus`

**Purpose:** Combine individual strategy signals into consensus signals with confidence levels and alert priorities to prevent missed trading opportunities.

---

## Endpoints

### 1. GET /latest

Get latest aggregated consensus signal for each trading pair.

**Use Case:** Dashboard overview showing current market consensus

**Request:**
```bash
curl -X GET "http://localhost:8116/api/v1/consensus/latest"
```

**Response:**
```json
{
  "signals": {
    "BTC/USDT:USDT": {
      "id": 23,
      "signal_id": "e0d383e4-2605-4e27-9918-bb3a7ad06629",
      "consensus": "NEUTRAL",
      "confidence": 0.0,
      "normalized_score": 0.0,
      "alert_level": "LOW",
      "num_active_strategies": 4,
      "strategies": [
        {
          "name": "OI_Trend",
          "signal": "NEUTRAL",
          "confidence": 0.0,
          "weight": 0.35,
          "contribution_score": 0.0,
          "reason": "NEUTRAL: RSI too low for SHORT (28.48 <= 30)"
        },
        {
          "name": "VolatilityBreakout",
          "signal": "NEUTRAL",
          "confidence": 0.0,
          "weight": 0.2,
          "contribution_score": 0.0,
          "reason": "NEUTRAL: No recent squeeze detected"
        },
        {
          "name": "GoldenPocket",
          "signal": "NEUTRAL",
          "confidence": 0.0,
          "weight": 0.2,
          "contribution_score": 0.0,
          "reason": "NEUTRAL: Price not in Golden Pocket zone"
        },
        {
          "name": "MeanReversion",
          "signal": "NEUTRAL",
          "confidence": 0.0,
          "weight": 0.25,
          "contribution_score": 0.0,
          "reason": "NEUTRAL: RSI not oversold"
        }
      ],
      "reason": "NEUTRAL: No significant contributions",
      "metadata": {
        "thresholds": {
          "long": 0.3,
          "short": -0.3
        },
        "total_active_weight": 1.0,
        "total_weighted_score": 0.0
      },
      "timestamp": "2025-12-01T09:13:20.259255+00:00",
      "created_at": "2025-12-01T09:13:20.261561+00:00"
    },
    "ETH/USDT:USDT": {
      "id": 24,
      "consensus": "NEUTRAL",
      "confidence": 0.0,
      "normalized_score": 0.0,
      "alert_level": "LOW",
      "num_active_strategies": 4,
      "strategies": [...],
      "timestamp": "2025-12-01T09:13:22.923456+00:00"
    }
  },
  "last_updated": "2025-12-01T09:13:22.923456+00:00",
  "total_symbols": 2
}
```

**Response Fields:**
- `signals` - Dictionary of latest consensus per symbol
- `consensus` - LONG, SHORT, or NEUTRAL
- `confidence` - Overall confidence (0.0 - 1.0)
- `normalized_score` - Signal strength (-1.0 to +1.0)
- `alert_level` - CRITICAL, HIGH, MEDIUM, or LOW
- `num_active_strategies` - Number of strategies that provided signals
- `strategies` - Individual strategy contributions with weights

---

### 2. GET /history

Get historical aggregated consensus signals for a specific symbol.

**Use Case:** Chart historical consensus signals for analysis

**Query Parameters:**
- `symbol` (required) - Trading symbol (e.g., "BTC/USDT:USDT")
- `hours` (optional) - Hours of history (1-168, default: 24)
- `limit` (optional) - Max results (1-1000, default: 100)

**Request:**
```bash
curl -X GET "http://localhost:8116/api/v1/consensus/history?symbol=BTC/USDT:USDT&hours=24&limit=10"
```

**Response:**
```json
{
  "symbol": "BTC/USDT:USDT",
  "signals": [
    {
      "id": 23,
      "signal_id": "e0d383e4-2605-4e27-9918-bb3a7ad06629",
      "consensus": "NEUTRAL",
      "confidence": 0.0,
      "normalized_score": 0.0,
      "alert_level": "LOW",
      "num_active_strategies": 4,
      "strategies": [...],
      "timestamp": "2025-12-01T09:13:20.259255+00:00"
    },
    {
      "id": 21,
      "consensus": "NEUTRAL",
      "confidence": 0.12,
      "normalized_score": 0.12,
      "alert_level": "LOW",
      "timestamp": "2025-12-01T09:00:30.952870+00:00"
    }
  ],
  "total_count": 10,
  "time_range": {
    "start": "2025-11-30T09:13:20+00:00",
    "end": "2025-12-01T09:13:20+00:00"
  }
}
```

---

### 3. GET /alerts

Get high-priority consensus alerts (CRITICAL and HIGH by default).

**Use Case:** Alert dashboard showing critical trading opportunities

**Query Parameters:**
- `hours` (optional) - Hours of history (1-168, default: 24)
- `alert_level` (optional) - Filter by specific level (CRITICAL, HIGH, MEDIUM, LOW)

**Request:**
```bash
# Get all HIGH and CRITICAL alerts (default)
curl -X GET "http://localhost:8116/api/v1/consensus/alerts?hours=24"

# Get only CRITICAL alerts
curl -X GET "http://localhost:8116/api/v1/consensus/alerts?hours=24&alert_level=CRITICAL"
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 42,
      "symbol": "BTC/USDT:USDT",
      "consensus": "SHORT",
      "confidence": 0.75,
      "normalized_score": -0.75,
      "alert_level": "CRITICAL",
      "num_active_strategies": 4,
      "strategies": [...],
      "timestamp": "2025-12-01T10:30:00+00:00"
    }
  ],
  "total_count": 1,
  "breakdown": {
    "CRITICAL": 1,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0
  },
  "time_range": {
    "start": "2025-11-30T10:30:00+00:00",
    "end": "2025-12-01T10:30:00+00:00"
  }
}
```

---

### 4. GET /stats

Get consensus signal statistics over a time period.

**Use Case:** Dashboard statistics panel

**Query Parameters:**
- `hours` (optional) - Hours for statistics (1-168, default: 24)

**Request:**
```bash
curl -X GET "http://localhost:8116/api/v1/consensus/stats?hours=24"
```

**Response:**
```json
{
  "total_signals": 22,
  "by_consensus": {
    "LONG": 0,
    "SHORT": 0,
    "NEUTRAL": 22
  },
  "by_alert_level": {
    "CRITICAL": 0,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 22
  },
  "avg_confidence": 0.054,
  "avg_strategies_per_signal": 4.0,
  "time_range": {
    "start": "2025-11-30T09:00:00+00:00",
    "end": "2025-12-01T09:00:00+00:00"
  }
}
```

---

## Consensus Aggregation Logic

### Strategy Weights
- **OI_Trend**: 0.35 (35%) - Highest weight
- **MeanReversion**: 0.25 (25%)
- **VolatilityBreakout**: 0.20 (20%)
- **GoldenPocket**: 0.20 (20%)

### Calculation Formula
```
contribution = weight × signal_value × confidence

normalized_score = Σ(contributions) / Σ(active_weights)

where:
  signal_value = -1.0 (SHORT), 0.0 (NEUTRAL), +1.0 (LONG)
  confidence = 0.0 - 1.0
```

### Consensus Thresholds
- `score ≤ -0.3` → **SHORT**
- `score ≥ 0.3` → **LONG**
- `otherwise` → **NEUTRAL**

### Alert Levels
- **CRITICAL** - ≥70% confidence + 3+ strategies agreeing
- **HIGH** - ≥50% confidence + 2+ strategies agreeing
- **MEDIUM** - ≥40% confidence
- **LOW** - Otherwise

### Actionable Signals
A signal is considered actionable if:
- Consensus is LONG or SHORT (not NEUTRAL)
- Confidence ≥ 0.4 (40%)
- Alert level is HIGH or CRITICAL

---

## Examples

### Example 1: Strong LONG Consensus
```json
{
  "consensus": "LONG",
  "confidence": 0.75,
  "normalized_score": 0.75,
  "alert_level": "CRITICAL",
  "strategies": [
    {"name": "OI_Trend", "signal": "LONG", "confidence": 0.8, "weight": 0.35, "contribution_score": 0.28},
    {"name": "MeanReversion", "signal": "LONG", "confidence": 0.75, "weight": 0.25, "contribution_score": 0.19},
    {"name": "VolatilityBreakout", "signal": "LONG", "confidence": 0.7, "weight": 0.20, "contribution_score": 0.14},
    {"name": "GoldenPocket", "signal": "LONG", "confidence": 0.7, "weight": 0.20, "contribution_score": 0.14}
  ]
}
```

**Interpretation:**
- All 4 strategies agree on LONG
- Average confidence 75%
- Normalized score +0.75 (strong bullish)
- CRITICAL alert (≥70% conf + 3+ strategies)
- **Actionable signal** → Published to execution-service

### Example 2: Weak Mixed Signals
```json
{
  "consensus": "NEUTRAL",
  "confidence": 0.12,
  "normalized_score": 0.12,
  "alert_level": "LOW",
  "strategies": [
    {"name": "OI_Trend", "signal": "NEUTRAL", "confidence": 0.0, "weight": 0.35, "contribution_score": 0.0},
    {"name": "MeanReversion", "signal": "NEUTRAL", "confidence": 0.0, "weight": 0.25, "contribution_score": 0.0},
    {"name": "VolatilityBreakout", "signal": "NEUTRAL", "confidence": 0.0, "weight": 0.20, "contribution_score": 0.0},
    {"name": "GoldenPocket", "signal": "LONG", "confidence": 0.6, "weight": 0.20, "contribution_score": 0.12}
  ]
}
```

**Interpretation:**
- Only GoldenPocket has a signal (LONG with 60% confidence)
- Normalized score +0.12 (below +0.3 threshold)
- Consensus: NEUTRAL (not strong enough for LONG)
- LOW alert
- **Not actionable** → Not published

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Not Found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to fetch consensus signals: <error message>"
}
```

---

## Related Documentation
- [Multi-Strategy Aggregation Design](../../services/prediction-service/README.md#multi-strategy-aggregation)
- [Prediction Service Architecture](../../services/prediction-service/README.md)
- [Trading Scheduler](../../services/prediction-service/README.md#trading-scheduler)
- [Strategy Weights Rationale](../../services/prediction-service/README.md#strategy-weights)

---

**Last Updated:** 2025-12-01
**Version:** 1.0.0
**Status:** Production-ready
