# Indicators API - Quick Reference Cheatsheet

**Base URL:** `http://localhost:8116/api/v1`
**Auth:** Bearer JWT Token
**Response Format:** JSON

---

## Endpoints

### Current Indicators
```
GET /indicators/{symbol}/current?timeframe={15m|1h|4h|1d}
Default: timeframe=1h
Response: IndicatorsSnapshot
```

### Historical Indicators
```
GET /indicators/{symbol}/historical?hours={1-168}
Default: hours=24
Response: HistoricalIndicator[]
```

### List Symbols
```
GET /indicators/symbols
Response: string[]
```

---

## Quick Examples

### cURL

```bash
# 1h indicators (default)
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current" \
  -H "Authorization: Bearer $TOKEN"

# 15m scalping
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=15m" \
  -H "Authorization: Bearer $TOKEN"

# 4h swing trading
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=4h" \
  -H "Authorization: Bearer $TOKEN"

# 1d position trading
curl "http://localhost:8116/api/v1/indicators/BTC%2FUSDT:USDT/current?timeframe=1d" \
  -H "Authorization: Bearer $TOKEN"
```

### Python

```python
import requests

API = "http://localhost:8116/api/v1"
TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Get current indicators
resp = requests.get(
  f"{API}/indicators/BTC%2FUSDT:USDT/current?timeframe=1h",
  headers=headers
)
data = resp.json()

print(f"Consensus: {data['consensus']}")
print(f"Confidence: {data['confidence']:.1%}")
```

### JavaScript

```javascript
const API = "http://localhost:8116/api/v1"
const TOKEN = "your-jwt-token"

const resp = await fetch(
  `${API}/indicators/BTC%2FUSDT:USDT/current?timeframe=1h`,
  {
    headers: { "Authorization": `Bearer ${TOKEN}` }
  }
)
const data = await resp.json()

console.log(`Consensus: ${data.consensus}`)
console.log(`Confidence: ${(data.confidence * 100).toFixed(1)}%`)
```

---

## Timeframes

| Timeframe | Use Case | Min Data | Update Freq |
|-----------|----------|----------|------------|
| `15m` | Scalping | 800 candles | Every 5 min |
| `1h` | Day trading | 200 candles | Every 10 min |
| `4h` | Swing trading | 200 candles | Every 30 min |
| `1d` | Position trading | 200 candles | Daily |

---

## Indicators (14 Total)

### Core (9)
- RSI - Momentum (0-100)
- MACD - Trend crossover
- EMA - Multi-period (10, 20, 50, 200)
- Volume - High/Normal/Low
- Bollinger Bands - Volatility
- ATR - Volatility % + Stop-loss
- ADX - Trend strength (WEAK/MODERATE/STRONG)
- Stochastic RSI - Momentum oscillator
- OBV - Volume trend

### Advanced (5)
- Fair Value Gaps - Price imbalances
- Liquidity Sweeps - Stop-hunts
- Volume Profile - POC/VAH/VAL
- Funding Rate - Perpetual sentiment
- Open Interest - Leverage trend

---

## Consensus Scores

```
0.90-1.00  ▓▓▓▓▓ Very Strong
0.70-0.89  ▓▓▓▓  Strong
0.50-0.69  ▓▓▓   Moderate
0.30-0.49  ▓▓    Weak
0.00-0.29  ▓     Very Weak
```

---

## Trend Hierarchy (EMA)

Score 0-4 based on:
1. Price > EMA10?
2. EMA10 > EMA20?
3. EMA20 > EMA50?
4. EMA50 > EMA200?

**4** = Perfect bullish alignment
**0** = Bearish/Misaligned

---

## Error Codes

| Code | Error | Fix |
|------|-------|-----|
| 200 | OK | Success |
| 400 | Insufficient data | Try higher timeframe |
| 404 | Symbol not found | Check symbol format |
| 422 | Invalid timeframe | Use 15m/1h/4h/1d |
| 500 | Server error | Retry or check service |

---

## Response Structure

```json
{
  "symbol": "BTC/USDT:USDT",
  "timeframe": "1h",
  "timestamp": "2025-12-07T16:00:00Z",
  "rsi": { "value": 65, "signal": "NEUTRAL", ... },
  "macd": { "macd": 1250, "signal": 1200, "histogram": 50, ... },
  "ema": {
    "ema10": 89125,
    "ema20": 89261,
    "ema50": 89702,
    "ema200": 90311,
    "trend_hierarchy_score": 2,
    ...
  },
  "adx": { "adx": 28, "trend_strength": "STRONG", ... },
  "funding_rate": { "rate": 0.00008, "signal": "BULLISH", ... },
  "consensus": "BULLISH",
  "confidence": 0.71
}
```

---

## Multi-Timeframe Strategy

1. **Check 1d** for major trend
   ```bash
   curl "...?timeframe=1d" | jq '.consensus'
   ```

2. **Confirm on 4h** for trend strength
   ```bash
   curl "...?timeframe=4h" | jq '.adx.trend_strength'
   ```

3. **Execute on 1h** for entry point
   ```bash
   curl "...?timeframe=1h" | jq '.rsi.value'
   ```

---

## Common Filters

### Get only bullish signals
```bash
curl "...?timeframe=1h" | jq 'select(.consensus=="BULLISH" and .confidence>0.70)'
```

### Get EMA hierarchy
```bash
curl "...?timeframe=1h" | jq '.ema | {score: .trend_hierarchy_score, trend: .trend}'
```

### Get volatility info
```bash
curl "...?timeframe=1h" | jq '.atr | {volatility: .volatility, stop_loss: .stop_loss_suggestion}'
```

### Get volume profile
```bash
curl "...?timeframe=1h" | jq '.volume_profile | {poc, vah, val, position: .current_position}'
```

---

## Caching

- **TTL:** 60 seconds per timeframe
- **Cache Key:** `{symbol}:{timeframe}`
- **First Request:** ~500-1000ms
- **Cached Request:** <50ms

---

## Rate Limits

- **Per Minute:** 60 requests max
- **Per Hour:** 1000 requests max
- **Burst:** 10 consecutive max

---

## Documentation Links

- Full Docs: [indicators-api.md](indicators-api.md)
- Implementation: [indicators-implementation-guide.md](indicators-implementation-guide.md)
- Source: `services/prediction-service/app/api/v1/indicators.py`
- Types: `frontend/src/types/indicators.ts`
- Swagger: http://localhost:8116/docs

---

## Common Issues

**Q: Got 400 "Insufficient data" on 15m?**
A: 15m needs 800 candles (8.3 days). Try 1h or 4h.

**Q: Got 422 with timeframe="5m"?**
A: Invalid timeframe. Use 15m, 1h, 4h, or 1d only.

**Q: Different consensus on same symbol, different timeframes?**
A: Normal! Different timeframes = different analysis windows. Use multi-TF confirmation.

**Q: How often should I poll?**
A: Match refresh to timeframe (15m→5min, 1h→10min, 4h→30min, 1d→daily).

---

**Last Updated:** December 7, 2025
**Version:** 1.0
