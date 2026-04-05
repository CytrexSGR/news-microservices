# Indicators API Documentation

**API Version:** 1.0
**Base URL:** `http://localhost:8116/api/v1` (development) or your production endpoint
**Authentication:** Bearer Token (JWT)
**Content-Type:** `application/json`

---

## Table of Contents

1. [Overview](#overview)
2. [Timeframe Parameter](#timeframe-parameter)
3. [Endpoints](#endpoints)
4. [Request Examples](#request-examples)
5. [Response Schema](#response-schema)
6. [Error Handling](#error-handling)
7. [Usage Guidelines](#usage-guidelines)
8. [Code Examples](#code-examples)
9. [Backwards Compatibility](#backwards-compatibility)

---

## Overview

The Indicators API provides real-time and historical technical analysis indicators for trading symbols. All indicators are calculated **on-demand from live market data** (cached 60 seconds) to ensure accuracy.

### Supported Indicators

**Core Indicators (9):**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average) - Multi-period support (10, 20, 50, 200)
- Volume & Volume Moving Average
- Bollinger Bands
- ATR (Average True Range)
- ADX (Average Directional Index)
- Stochastic RSI
- OBV (On Balance Volume)

**Advanced Indicators (5):**
- Fair Value Gaps (FVG)
- Liquidity Sweeps (Stop-Hunt Detection)
- Volume Profile (POC, VAH, VAL)
- Funding Rate (Perpetual Futures Sentiment)
- Open Interest (Leverage & Positioning)

---

## Timeframe Parameter

### Introduction

The `timeframe` query parameter allows you to request indicator calculations across different time windows. This enables analysis from ultra-short-term scalping to long-term position trading.

### Supported Timeframes

| Timeframe | Duration | Candles for EMA200 | Use Case | Data Points |
|-----------|----------|-------------------|----------|------------|
| `15m` | 15 Minutes | 800 (8.3 days) | Scalping, high-frequency trading | Requires sufficient historical data |
| `1h` | 1 Hour | 200 (8.3 days) | Day trading, default for most use cases | Recommended starting point |
| `4h` | 4 Hours | 200 (33 days) | Swing trading, trend confirmation | Good for medium-term analysis |
| `1d` | 1 Day | 200 (200 days) | Position trading, long-term analysis | Best for supply/demand analysis |

### Default Behavior

If the `timeframe` parameter is **not provided**, it defaults to `1h` for **backwards compatibility**.

```bash
# Both requests are equivalent
GET /api/v1/indicators/BTC/USDT:USDT/current
GET /api/v1/indicators/BTC/USDT:USDT/current?timeframe=1h
```

### Validation

The timeframe parameter is validated using the regex pattern: `^(15m|1h|4h|1d)$`

Any invalid timeframe will return a **422 Unprocessable Entity** error:

```json
{
  "detail": [
    {
      "loc": ["query", "timeframe"],
      "msg": "string should match regex '^(15m|1h|4h|1d)$'",
      "type": "value_error.str.regex"
    }
  ]
}
```

---

## Endpoints

### 1. Get Current Indicators

**Endpoint:** `GET /api/v1/indicators/{symbol}/current`

**Description:** Get the most recent technical indicators snapshot for a symbol at a specified timeframe.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `symbol` | path | Yes | - | Trading pair symbol (e.g., `BTC/USDT:USDT`, `ETH/USDT:USDT`) |
| `timeframe` | query | No | `1h` | Timeframe: `15m`, `1h`, `4h`, `1d` |

**Response:** `IndicatorsSnapshot` object

**Status Codes:**
- `200` - Success
- `400` - Insufficient historical data (not enough candles for timeframe)
- `404` - Symbol not found
- `422` - Invalid timeframe parameter
- `500` - Internal server error

---

### 2. Get Historical Indicators

**Endpoint:** `GET /api/v1/indicators/{symbol}/historical`

**Description:** Get historical indicator values for charting and trend analysis (data points over time).

**Parameters:**

| Name | Type | Required | Default | Range | Description |
|------|------|----------|---------|-------|-------------|
| `symbol` | path | Yes | - | - | Trading pair symbol |
| `hours` | query | No | `24` | 1-168 | Number of hours of historical data |

**Response:** Array of `HistoricalIndicator` objects

**Status Codes:**
- `200` - Success
- `400` - Invalid hours parameter
- `404` - Symbol not found or insufficient data
- `500` - Internal server error

---

### 3. List Available Symbols

**Endpoint:** `GET /api/v1/indicators/symbols`

**Description:** List all symbols with indicator data available.

**Response:** Array of symbol strings

**Status Codes:**
- `200` - Success
- `500` - Internal server error

---

## Request Examples

### Example 1: Default (1h Timeframe)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 2: Explicit 15m Timeframe (Scalping)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=15m" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 3: 4h Timeframe (Swing Trading)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=4h" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 4: Daily Timeframe (Position Trading)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1d" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 5: Invalid Timeframe (Error Case)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=5m" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Returns 422 Unprocessable Entity
```

### Example 6: Historical Data (24-hour chart)

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/historical?hours=24" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 7: List Available Symbols

```bash
curl -X GET "http://localhost:8116/api/v1/indicators/symbols" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Response: ["BTC/USDT:USDT", "ETH/USDT:USDT", "AAPL", ...]
```

---

## Response Schema

### IndicatorsSnapshot (Current Indicators Response)

```json
{
  "symbol": "BTC/USDT:USDT",
  "timeframe": "1h",
  "timestamp": "2025-12-07T16:00:00Z",
  "rsi": {
    "value": 65.23,
    "signal": "NEUTRAL",
    "interpretation": "RSI at 65.2 indicates NEUTRAL conditions"
  },
  "macd": {
    "macd": 1250.45,
    "signal": 1200.30,
    "histogram": 50.15,
    "interpretation": "Bullish crossover"
  },
  "ema": {
    "ema10": 89125.56,
    "ema20": 89261.69,
    "ema50": 89702.05,
    "ema200": 90311.87,
    "current_price": 89500.00,
    "position": "BELOW",
    "trend": "BEARISH",
    "price_above_ema10": false,
    "ema10_above_ema20": false,
    "ema20_above_ema50": true,
    "ema50_above_ema200": true,
    "trend_hierarchy_score": 2
  },
  "volume": {
    "current_volume": 1250000,
    "volume_ma": 950000,
    "ratio": 1.32,
    "signal": "HIGH"
  },
  "bollinger_bands": {
    "upper": 91500.00,
    "middle": 89750.00,
    "lower": 88000.00,
    "width": 0.0386,
    "position": "BETWEEN",
    "interpretation": "Price within bands - normal range"
  },
  "atr": {
    "value": 1250.50,
    "percentage": 1.39,
    "volatility": "NORMAL",
    "stop_loss_suggestion": 87999.00
  },
  "adx": {
    "adx": 28.45,
    "plus_di": 22.10,
    "minus_di": 15.30,
    "trend_strength": "STRONG",
    "market_phase": "TRENDING"
  },
  "stochastic_rsi": {
    "k": 75.30,
    "d": 70.45,
    "signal": "OVERBOUGHT",
    "interpretation": "Stoch RSI overbought - potential pullback"
  },
  "obv": {
    "value": 2500000000,
    "trend": "RISING",
    "divergence": null
  },
  "funding_rate": {
    "rate": 0.00008,
    "rate_percent": 0.008,
    "signal": "BULLISH",
    "sentiment": "Positive sentiment - longs paying shorts",
    "next_funding_time": "2025-12-07T20:00:00Z"
  },
  "open_interest": {
    "value": 150000000,
    "value_usd": 1350000000,
    "trend": "RISING",
    "signal": "STRONG_BULLISH",
    "interpretation": "Rising OI + Rising Price - New longs entering"
  },
  "fair_value_gaps": {
    "gaps": [
      {
        "type": "bullish",
        "upper": 89200.00,
        "lower": 88900.00,
        "timestamp": "2025-12-07T14:00:00Z",
        "candles_ago": 2,
        "filled": false
      }
    ],
    "recent_unfilled_bullish": 2,
    "recent_unfilled_bearish": 1,
    "signal": "BULLISH",
    "interpretation": "2 unfilled bullish gaps acting as support"
  },
  "liquidity_sweeps": {
    "sweeps": [
      {
        "type": "bullish",
        "sweep_level": 88500.00,
        "sweep_price": 88300.00,
        "reversal_close": 88800.00,
        "timestamp": "2025-12-07T15:30:00Z",
        "candles_ago": 1,
        "strength": "STRONG"
      }
    ],
    "recent_bullish_sweeps": 2,
    "recent_bearish_sweeps": 0,
    "signal": "BULLISH",
    "interpretation": "2 bullish sweeps (2 strong) - shorts stopped out"
  },
  "volume_profile": {
    "poc": 89600.00,
    "vah": 90200.00,
    "val": 89000.00,
    "current_position": "IN_VALUE_AREA",
    "signal": "NEUTRAL",
    "interpretation": "Price in Value Area, below POC ($89,600) - balanced, slight bearish bias",
    "volume_nodes": 30
  },
  "consensus": "BULLISH",
  "confidence": 0.71
}
```

### HistoricalIndicator (Historical Data Point)

```json
{
  "timestamp": "2025-12-07T15:00:00Z",
  "rsi": 62.45,
  "macd_histogram": 45.30,
  "price_vs_ema200": 0.991,
  "volume_ratio": 1.28,
  "bb_width": 0.0380,
  "atr_percentage": 1.35,
  "adx": 26.50,
  "stoch_rsi_k": 68.20,
  "obv_normalized": 65.40,
  "fvg_bullish_count": 2,
  "fvg_bearish_count": 1,
  "sweep_bullish_count": 1,
  "sweep_bearish_count": 0
}
```

### Field Descriptions

#### RSI (Relative Strength Index)
- **value**: 0-100 scale indicating momentum
- **signal**: OVERSOLD (<30), NEUTRAL (30-70), OVERBOUGHT (>70)
- **interpretation**: Human-readable explanation

#### MACD
- **macd**: MACD line value (12-26 EMA difference)
- **signal**: Signal line (9-period EMA of MACD)
- **histogram**: MACD - Signal (convergence/divergence indicator)
- **interpretation**: Bullish or Bearish crossover

#### EMA (Extended Multi-Period)
- **ema10**, **ema20**, **ema50**: Short to medium-term trend indicators
- **ema200**: Long-term trend indicator
- **trend_hierarchy_score**: 0-4 indicating how many EMAs are in correct bullish order
  - 4: All EMAs in perfect bullish alignment (strongest signal)
  - 3: Price > EMA10 > EMA20 > EMA50 > EMA200
  - 2: Most EMAs aligned
  - 1: Partial alignment
  - 0: All bearish or misaligned

#### Volume
- **current_volume**: Current candle volume
- **volume_ma**: 20-period moving average
- **ratio**: current_volume / volume_ma (1.0 = average)
- **signal**: HIGH (>1.5x), NORMAL, LOW (<0.5x)

#### Bollinger Bands
- **upper/middle/lower**: Band values
- **width**: Volatility measure (band width / middle)
- **position**: Price location relative to bands
- **interpretation**: Volatility assessment

#### ATR (Average True Range)
- **value**: Absolute volatility measure
- **percentage**: ATR as % of current price
- **volatility**: LOW (<1%), NORMAL (1-3%), HIGH (>3%)
- **stop_loss_suggestion**: 2x ATR below current price (risk management)

#### ADX (Average Directional Index)
- **adx**: 0-100 trend strength indicator
- **plus_di**: Directional indicator for uptrends
- **minus_di**: Directional indicator for downtrends
- **trend_strength**: WEAK (<20), MODERATE (20-25), STRONG (25-40), VERY_STRONG (>40)
- **market_phase**: TRENDING (ADX >= 25) or CONSOLIDATION

#### Fair Value Gaps (FVG)
- **gaps**: Array of detected price imbalances
  - **type**: bullish (gap up) or bearish (gap down)
  - **upper/lower**: Gap boundaries
  - **filled**: Whether current price is within the gap
- **signal**: BULLISH (more unfilled bullish gaps), BEARISH, NEUTRAL

#### Liquidity Sweeps
- **sweeps**: Array of detected stop-hunts
  - **type**: bullish (low swept) or bearish (high swept)
  - **strength**: WEAK, MODERATE, STRONG (based on reversal magnitude)
- **signal**: BULLISH (more bullish sweeps), BEARISH, NEUTRAL

#### Volume Profile
- **poc**: Point of Control (highest volume price level)
- **vah**: Value Area High (70% volume boundary)
- **val**: Value Area Low (70% volume boundary)
- **current_position**: ABOVE_VAH, IN_VALUE_AREA, BELOW_VAL
- **signal**: Market structure signal

#### Funding Rate
- **rate**: Raw funding rate (8-hour rate)
- **rate_percent**: Funding rate as percentage
- **signal**: Market sentiment (-0.01% = extreme bearish, +0.01% = extreme bullish)
- **sentiment**: Interpretation of funding sentiment

#### Consensus
- **consensus**: BULLISH, BEARISH, or NEUTRAL (based on 14 indicators)
- **confidence**: 0.0-1.0 (percentage of indicators in agreement)

---

## Error Handling

### 400 - Insufficient Historical Data

```json
{
  "detail": {
    "error": "Insufficient historical data",
    "message": "Symbol BTC/USDT:USDT only has 150 candles for 15m timeframe. Need at least 200 for EMA200.",
    "suggestion": "Try a higher timeframe (e.g., 1h or 4h) or select a symbol with more historical data.",
    "available_candles": 150,
    "required_candles": 200
  }
}
```

**Causes:**
- Selected timeframe has insufficient historical data
- Symbol is too new or has low trading volume
- 15m timeframe requires 800 candles (8.3 days)

**Solutions:**
- Use a higher timeframe (4h or 1d)
- Wait for more historical data to accumulate
- Select a more liquid symbol

### 422 - Invalid Timeframe Parameter

```json
{
  "detail": [
    {
      "loc": ["query", "timeframe"],
      "msg": "string should match regex '^(15m|1h|4h|1d)$'",
      "type": "value_error.str.regex"
    }
  ]
}
```

**Valid timeframes:** `15m`, `1h`, `4h`, `1d`

**Common mistakes:**
- `5m` - Not supported (use 15m or higher)
- `2h` - Not supported (use 1h or 4h)
- `1H` - Case sensitive (use lowercase `1h`)
- `1hour` - Use shorthand only (`1h`)

### 404 - Symbol Not Found

```json
{
  "detail": "Symbol BTC/USD not found"
}
```

**Solutions:**
- Check symbol format (use `/` for pair separator)
- Verify symbol exists in the exchange
- Call `/api/v1/indicators/symbols` to see available symbols

---

## Usage Guidelines

### Timeframe Selection by Trading Strategy

#### 1. Scalping (Ultra-Short Term)
- **Timeframe**: `15m`
- **Indicator Focus**: RSI, MACD, Volume
- **EMA**: Focus on EMA10 for entry/exit
- **Data Requirement**: Needs 800 candles (8.3 days minimum)
- **Frequency**: Update every 15 minutes

```bash
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=15m"
```

#### 2. Day Trading (Short Term)
- **Timeframe**: `1h` (default)
- **Indicator Focus**: RSI, MACD, ADX, Volume Profile
- **EMA**: Focus on EMA20 for trend confirmation
- **Data Requirement**: 200 candles (8.3 days)
- **Frequency**: Update every hour

```bash
# Default - equivalent to explicit 1h
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current"
```

#### 3. Swing Trading (Medium Term)
- **Timeframe**: `4h`
- **Indicator Focus**: ADX, Fair Value Gaps, Liquidity Sweeps
- **EMA**: Focus on EMA50 for trend strength
- **Data Requirement**: 200 candles (33 days)
- **Frequency**: Update every 4 hours

```bash
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=4h"
```

#### 4. Position Trading (Long Term)
- **Timeframe**: `1d`
- **Indicator Focus**: Volume Profile, ATR, ADX
- **EMA**: Focus on EMA200 for major trend
- **Data Requirement**: 200 candles (200 days)
- **Frequency**: Update daily

```bash
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1d"
```

### Consensus Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 0.90-1.00 | Very Strong Signal | High confidence trade setup |
| 0.70-0.89 | Strong Signal | Good trade setup |
| 0.50-0.69 | Moderate Signal | Verify with price action |
| 0.30-0.49 | Weak Signal | Wait for confirmation |
| 0.00-0.29 | Very Weak Signal | Skip trade |

### Combining Multiple Timeframes

**Recommended Multi-Timeframe Analysis:**

1. **Identify Macro Trend** (1d or 4h)
   ```bash
   # Get daily trend
   curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1d"
   ```

2. **Confirm on Intermediate** (4h)
   ```bash
   # Confirm on 4h
   curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=4h"
   ```

3. **Execute on Micro** (1h or 15m)
   ```bash
   # Find entry on 1h
   curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1h"
   ```

---

## Code Examples

### Python

```python
import requests
import json
from typing import Dict, Any

class IndicatorsAPI:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

    def get_current_indicators(
        self,
        symbol: str,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """Get current indicators for a symbol at specified timeframe."""
        url = f"{self.base_url}/indicators/{symbol}/current"
        params = {"timeframe": timeframe}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_historical_indicators(
        self,
        symbol: str,
        hours: int = 24
    ) -> list:
        """Get historical indicator data."""
        url = f"{self.base_url}/indicators/{symbol}/historical"
        params = {"hours": hours}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

# Usage
api = IndicatorsAPI("http://localhost:8116/api/v1", "YOUR_JWT_TOKEN")

# Get 1h indicators (default)
indicators_1h = api.get_current_indicators("BTC/USDT:USDT")
print(f"Consensus: {indicators_1h['consensus']}")
print(f"Confidence: {indicators_1h['confidence']:.2%}")

# Get 4h indicators for swing trading
indicators_4h = api.get_current_indicators("BTC/USDT:USDT", timeframe="4h")
print(f"ADX Trend Strength: {indicators_4h['adx']['trend_strength']}")

# Get historical data for charting
history = api.get_historical_indicators("BTC/USDT:USDT", hours=24)
print(f"Data points: {len(history)}")
```

### JavaScript/TypeScript

```typescript
import axios, { AxiosInstance } from 'axios'

interface IndicatorsSnapshot {
  symbol: string
  timeframe: '15m' | '1h' | '4h' | '1d'
  timestamp: string
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number
  // ... other fields
}

class IndicatorsAPI {
  private client: AxiosInstance

  constructor(baseUrl: string, jwtToken: string) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      }
    })
  }

  async getCurrentIndicators(
    symbol: string,
    timeframe: '15m' | '1h' | '4h' | '1d' = '1h'
  ): Promise<IndicatorsSnapshot> {
    const response = await this.client.get(
      `/indicators/${symbol}/current`,
      { params: { timeframe } }
    )
    return response.data
  }

  async getHistoricalIndicators(
    symbol: string,
    hours: number = 24
  ): Promise<HistoricalIndicator[]> {
    const response = await this.client.get(
      `/indicators/${symbol}/historical`,
      { params: { hours } }
    )
    return response.data
  }
}

// Usage
const api = new IndicatorsAPI(
  'http://localhost:8116/api/v1',
  'YOUR_JWT_TOKEN'
)

// Get 1h indicators
const indicators = await api.getCurrentIndicators('BTC/USDT:USDT')
console.log(`Consensus: ${indicators.consensus}`)
console.log(`Confidence: ${(indicators.confidence * 100).toFixed(1)}%`)

// Get 4h indicators
const indicators4h = await api.getCurrentIndicators(
  'BTC/USDT:USDT',
  '4h'
)
console.log(`Trend Strength: ${indicators4h.adx.trend_strength}`)
```

### cURL Examples

#### Get current indicators with default 1h timeframe
```bash
curl -X GET "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
```

#### Get indicators for multiple timeframes
```bash
for timeframe in 15m 1h 4h 1d; do
  echo "=== Timeframe: $timeframe ==="
  curl -s "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=$timeframe" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" | jq '.consensus, .confidence'
done
```

#### Parse consensus for automated trading
```bash
INDICATORS=$(curl -s "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1h" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN")

CONSENSUS=$(echo $INDICATORS | jq -r '.consensus')
CONFIDENCE=$(echo $INDICATORS | jq -r '.confidence')

if [ "$CONSENSUS" == "BULLISH" ] && [ "$(echo "$CONFIDENCE > 0.70" | bc)" -eq 1 ]; then
  echo "BUY SIGNAL DETECTED"
elif [ "$CONSENSUS" == "BEARISH" ] && [ "$(echo "$CONFIDENCE > 0.70" | bc)" -eq 1 ]; then
  echo "SELL SIGNAL DETECTED"
else
  echo "NEUTRAL OR WEAK SIGNAL"
fi
```

---

## Backwards Compatibility

### Default Behavior

The timeframe parameter was introduced in Phase 2 of development. All existing clients continue to work without changes:

```bash
# Old code (still works)
GET /api/v1/indicators/BTC/USDT:USDT/current
# Automatically uses timeframe=1h (default)

# New code (explicit)
GET /api/v1/indicators/BTC/USDT:USDT/current?timeframe=1h
# Same result
```

### EMA Multi-Period Enhancement

The EMA response was extended with multi-period support while maintaining backwards compatibility:

**Old Response (still supported):**
```json
{
  "ema": {
    "ema200": 90311.87,
    "current_price": 89500.00,
    "position": "BELOW",
    "trend": "BEARISH"
  }
}
```

**New Response (Phase 2+):**
```json
{
  "ema": {
    "ema10": 89125.56,      // NEW
    "ema20": 89261.69,      // NEW
    "ema50": 89702.05,      // NEW
    "ema200": 90311.87,     // EXISTING
    "current_price": 89500.00,
    "position": "BELOW",
    "trend": "BEARISH",
    "price_above_ema10": false,           // NEW
    "ema10_above_ema20": false,           // NEW
    "ema20_above_ema50": true,            // NEW
    "ema50_above_ema200": true,           // NEW
    "trend_hierarchy_score": 2            // NEW
  }
}
```

### Migration Path

If you're using old API clients:

1. **No action required** - API is fully backwards compatible
2. **Optional**: Update client libraries to handle new EMA fields
3. **Recommended**: Implement timeframe parameter for use-case-specific analysis

---

## Performance Considerations

### Caching

All indicators are **cached for 60 seconds** to balance freshness and performance:

- **First request**: Calculates on-demand (takes 500-1000ms)
- **Subsequent requests (within 60s)**: Returns cached result (takes <50ms)
- **After 60s**: Recalculates from fresh market data

### Recommended Request Rates

| Timeframe | Recommended Update Interval | Max Requests/Hour |
|-----------|----------------------------|------------------|
| 15m | Every 5 minutes | 12 |
| 1h | Every 10 minutes | 6 |
| 4h | Every 30 minutes | 2 |
| 1d | Once daily | <1 |

### Rate Limiting

Respect these limits to avoid server overload:
- **Per minute**: Maximum 60 requests
- **Per hour**: Maximum 1000 requests
- **Burst**: Maximum 10 consecutive requests

---

## Frequently Asked Questions

### Q: Why does my 15m request return insufficient data error?

**A:** The 15m timeframe requires 800 candles (8.3 days of historical data) for EMA200 calculation. Newer symbols may not have enough history. Try `1h` or `4h` instead.

### Q: What's the difference between 4h consensus and 1h consensus?

**A:** They analyze different timeframes. 4h uses 200 4-hour candles (33 days), while 1h uses 200 1-hour candles (8.3 days). Multi-timeframe analysis (checking both) is more reliable.

### Q: Can I combine timeframes for trading signals?

**A:** Yes! Best practice is to check higher timeframe (4h/1d) for trend direction, then use lower timeframe (1h/15m) for entry signals.

### Q: What does trend_hierarchy_score mean?

**A:** It counts how many EMA levels are in perfect bullish order (price > EMA10 > EMA20 > EMA50 > EMA200). Higher = stronger uptrend. Score of 4 = maximum bullish alignment.

### Q: How often are indicators updated?

**A:** Indicators are calculated on-demand when you request them. Results are cached for 60 seconds to improve performance.

---

## Support & Resources

- **API Documentation**: This file
- **Swagger UI**: http://localhost:8116/docs
- **ReDoc**: http://localhost:8116/redoc
- **Implementation**: `/home/cytrex/news-microservices/services/prediction-service/app/api/v1/indicators.py`
- **Type Definitions**: `/home/cytrex/news-microservices/frontend/src/types/indicators.ts`

---

**Last Updated:** December 7, 2025
**API Version:** 1.0
**Status:** Production Ready
