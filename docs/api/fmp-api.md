# FMP Service API Documentation

**Base URL**: `http://localhost:8113`
**API Version**: `v1`
**Authentication**: None (internal service)

---

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/quotes/indices` | GET | Get all major indices |
| `/api/v1/quotes/{symbol}` | GET | Get quote by symbol |
| `/api/v1/quotes/sync` | POST | Sync quotes from FMP |
| `/api/v1/history/{symbol}` | GET | Get historical data |
| `/api/v1/history/{symbol}/backfill` | POST | Backfill historical data |
| `/api/v1/earnings/calendar` | GET | Get earnings calendar |
| `/api/v1/earnings/{symbol}/history` | GET | Get earnings history |
| `/api/v1/earnings/sync` | POST | Sync earnings calendar |
| `/api/v1/backfill/indices` | POST | Backfill all major indices |
| `/api/v1/backfill/symbols` | POST | Backfill custom symbols |
| `/api/v1/backfill/macro-indicators` | POST | Backfill macro indicators |
| `/api/v1/backfill/status` | GET | Get backfill status |

---

## Data Models

### IndexQuote

```json
{
  "symbol": "string",
  "name": "string",
  "price": "decimal(20,8)",
  "change": "decimal(20,8)",
  "change_percent": "decimal(10,4)",
  "volume": "integer",
  "timestamp": "datetime"
}
```

### MarketHistory

```json
{
  "symbol": "string",
  "date": "date",
  "open": "decimal(20,8)",
  "high": "decimal(20,8)",
  "low": "decimal(20,8)",
  "close": "decimal(20,8)",
  "adj_close": "decimal(20,8)",
  "volume": "integer"
}
```

### EarningsEvent

```json
{
  "symbol": "string",
  "company_name": "string",
  "fiscal_date": "date",
  "report_date": "datetime",
  "eps_actual": "decimal(10,4)",
  "eps_estimate": "decimal(10,4)",
  "revenue_actual": "integer",
  "revenue_estimate": "integer",
  "time": "string"
}
```

---

## Endpoints

### GET /api/v1/quotes/indices

Get latest quotes for all major indices.

**Request:**
```bash
curl http://localhost:8113/api/v1/quotes/indices
```

**Response:** `200 OK`
```json
[
  {
    "symbol": "^GSPC",
    "name": "S&P 500",
    "price": "6791.69000000",
    "change": "53.25000000",
    "change_percent": "0.7902",
    "volume": 3027308000,
    "timestamp": "2025-10-25T07:39:05.822766"
  },
  {
    "symbol": "^DJI",
    "name": "Dow Jones Industrial Average",
    "price": "47207.12000000",
    "change": "472.51000000",
    "change_percent": "1.0111",
    "volume": 406028586,
    "timestamp": "2025-10-25T07:39:05.825688"
  }
]
```

---

### GET /api/v1/quotes/{symbol}

Get latest quote for a specific symbol.

**Path Parameters:**
- `symbol` (required): Stock/Index symbol

**Request:**
```bash
curl http://localhost:8113/api/v1/quotes/%5EGSPC
```

**Response:** `200 OK`
```json
{
  "symbol": "^GSPC",
  "name": "S&P 500",
  "price": "6791.69000000",
  "change": "53.25000000",
  "change_percent": "0.7902",
  "volume": 3027308000,
  "timestamp": "2025-10-25T07:39:05.822766"
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Quote for INVALID not found"
}
```

---

### POST /api/v1/quotes/sync

Manually trigger quotes synchronization from FMP API.

**Request:**
```bash
curl -X POST http://localhost:8113/api/v1/quotes/sync
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "quotes_synced": 6
}
```

---

### GET /api/v1/history/{symbol}

Get historical EOD data for a symbol.

**Path Parameters:**
- `symbol` (required): Stock/Index symbol

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD), defaults to 30 days ago
- `to_date` (optional): End date (YYYY-MM-DD), defaults to today
- `limit` (optional): Maximum records to return (1-1000), default 100

**Request:**
```bash
curl "http://localhost:8113/api/v1/history/%5EGSPC?from_date=2024-10-01&to_date=2024-10-25&limit=5"
```

**Response:** `200 OK`
```json
[
  {
    "symbol": "^GSPC",
    "date": "2024-10-24",
    "open": "6750.50000000",
    "high": "6801.25000000",
    "low": "6745.00000000",
    "close": "6791.69000000",
    "adj_close": "6791.69000000",
    "volume": 3027308000
  },
  {
    "symbol": "^GSPC",
    "date": "2024-10-23",
    "open": "6720.30000000",
    "high": "6755.75000000",
    "low": "6715.20000000",
    "close": "6738.44000000",
    "adj_close": "6738.44000000",
    "volume": 2950123000
  }
]
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "No historical data found for INVALID"
}
```

---

### POST /api/v1/history/{symbol}/backfill

Manually trigger historical data backfill for a symbol.

**Path Parameters:**
- `symbol` (required): Stock/Index symbol

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD), defaults to 5 years ago
- `to_date` (optional): End date (YYYY-MM-DD), defaults to today

**Request:**
```bash
curl -X POST "http://localhost:8113/api/v1/history/%5EGSPC/backfill?from_date=2020-01-01"
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "symbol": "^GSPC",
  "records_backfilled": 1260
}
```

---

### GET /api/v1/earnings/calendar

Get upcoming earnings events.

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD), defaults to today
- `to_date` (optional): End date (YYYY-MM-DD), defaults to 30 days from now
- `symbol` (optional): Filter by symbol
- `limit` (optional): Maximum records (1-500), default 50

**Request:**
```bash
curl "http://localhost:8113/api/v1/earnings/calendar?symbol=AAPL&limit=5"
```

**Response:** `200 OK`
```json
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "fiscal_date": "2024-12-31",
    "report_date": "2025-01-30T16:30:00",
    "eps_actual": 2.18,
    "eps_estimate": 2.10,
    "revenue_actual": 124300000000,
    "revenue_estimate": 121000000000,
    "time": "amc"
  }
]
```

---

### GET /api/v1/earnings/{symbol}/history

Get earnings history for a specific symbol.

**Path Parameters:**
- `symbol` (required): Stock symbol

**Query Parameters:**
- `limit` (optional): Maximum records (1-100), default 10

**Request:**
```bash
curl "http://localhost:8113/api/v1/earnings/AAPL/history?limit=5"
```

**Response:** `200 OK`
```json
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "fiscal_date": "2024-12-31",
    "report_date": "2025-01-30T16:30:00",
    "eps_actual": 2.18,
    "eps_estimate": 2.10,
    "revenue_actual": 124300000000,
    "revenue_estimate": 121000000000,
    "time": "amc"
  }
]
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "No earnings history found for INVALID"
}
```

---

### POST /api/v1/earnings/sync

Manually trigger earnings calendar synchronization.

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD), defaults to today
- `to_date` (optional): End date (YYYY-MM-DD), defaults to 30 days from now

**Request:**
```bash
curl -X POST "http://localhost:8113/api/v1/earnings/sync"
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "events_synced": 152
}
```

---

### POST /api/v1/backfill/indices

Backfill historical data for all major indices.

**Query Parameters:**
- `years` (optional): Number of years to backfill, default 5

**Request:**
```bash
curl -X POST "http://localhost:8113/api/v1/backfill/indices?years=5"
```

**Response:** `200 OK`
```json
{
  "status": "started",
  "message": "Backfilling 6 indices from 2020-10-25 to 2025-10-25",
  "symbols": [
    "^GSPC",
    "^DJI",
    "^IXIC",
    "^NDX",
    "^RUT",
    "^VIX"
  ],
  "estimated_records": 7560
}
```

**Note:** Runs as background task. Check logs for completion.

---

### POST /api/v1/backfill/symbols

Backfill historical data for custom list of symbols.

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "from_date": "2020-01-01",
  "to_date": "2025-10-25"
}
```

**Request:**
```bash
curl -X POST http://localhost:8113/api/v1/backfill/symbols \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "from_date": "2020-01-01"
  }'
```

**Response:** `200 OK`
```json
{
  "status": "started",
  "message": "Backfilling 3 symbols from 2020-01-01 to 2025-10-25",
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Symbols list cannot be empty"
}
```

---

### POST /api/v1/backfill/macro-indicators

Backfill macroeconomic indicators.

**Request Body (optional):**
```json
{
  "indicators": ["GDP", "CPI", "UNEMPLOYMENT_RATE"],
  "from_date": "2015-01-01",
  "to_date": "2025-10-25"
}
```

**Default Indicators:**
- GDP
- CPI
- UNEMPLOYMENT_RATE
- RETAIL_SALES
- INDUSTRIAL_PRODUCTION

**Request:**
```bash
curl -X POST http://localhost:8113/api/v1/backfill/macro-indicators \
  -H "Content-Type: application/json" \
  -d '{
    "indicators": ["GDP", "CPI"]
  }'
```

**Response:** `200 OK`
```json
{
  "status": "started",
  "message": "Backfilling 2 macro indicators from 2015-10-25 to 2025-10-25",
  "indicators": ["GDP", "CPI"]
}
```

---

### GET /api/v1/backfill/status

Get status of data backfill.

**Request:**
```bash
curl http://localhost:8113/api/v1/backfill/status
```

**Response:** `200 OK`
```json
{
  "historical_records": 7560,
  "macro_records": 1250,
  "date_range": {
    "from": "2020-10-25",
    "to": "2025-10-25"
  }
}
```

---

## Error Handling

All endpoints return errors in a consistent format:

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - FMP API unavailable

---

## Rate Limiting

**Current Limit:** 300 calls per 24 hours (FMP API limitation)

**Headers (Phase 2):**
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1730012400
```

**Error Response:** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded: 300 calls per 86400s"
}
```

---

## Usage Examples

### Python

```python
import httpx

async def get_sp500_quote():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8113/api/v1/quotes/%5EGSPC"
        )
        return response.json()

async def backfill_indices():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8113/api/v1/backfill/indices",
            params={"years": 5}
        )
        return response.json()
```

### JavaScript

```javascript
// Get quote
const quote = await fetch('http://localhost:8113/api/v1/quotes/%5EGSPC')
  .then(res => res.json());

// Backfill indices
const backfill = await fetch('http://localhost:8113/api/v1/backfill/indices?years=5', {
  method: 'POST'
}).then(res => res.json());
```

### cURL

```bash
# Get all indices
curl http://localhost:8113/api/v1/quotes/indices | jq .

# Get historical data
curl "http://localhost:8113/api/v1/history/%5EGSPC?limit=10" | jq .

# Sync earnings
curl -X POST http://localhost:8113/api/v1/earnings/sync
```

---

## Interactive Documentation

The service provides interactive API documentation via Swagger UI:

**URL:** http://localhost:8113/docs

Features:
- Try out API calls directly in browser
- View request/response schemas
- Download OpenAPI specification

---

**Last Updated**: 2025-10-25
**API Version**: 1.0.0
