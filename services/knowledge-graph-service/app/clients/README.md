# FMP Service HTTP Client

**Version:** 1.0.0
**Status:** Production Ready
**Last Updated:** 2025-11-16

---

## Overview

Robust HTTP client for communicating with the FMP Service (Financial Market Provider) with built-in resilience patterns.

**Key Features:**
- ✅ **Circuit Breaker Pattern** - Prevents cascading failures
- ✅ **Retry Logic** - Exponential backoff for transient errors
- ✅ **Rate Limiting Awareness** - Respects FMP 300 calls/day quota
- ✅ **Comprehensive Error Handling** - Typed exceptions for different error scenarios
- ✅ **Request/Response Logging** - Structured JSON logging
- ✅ **Async/Await** - Full async support with httpx
- ✅ **Type Safety** - Pydantic models for validation

---

## Quick Start

```python
from app.clients import FMPServiceClient, FMPClientConfig

# Initialize client
config = FMPClientConfig(fmp_base_url="http://fmp-service:8113")

async with FMPServiceClient(config) as client:
    # Fetch asset metadata
    assets = await client.fetch_asset_metadata(["AAPL", "GOOGL"])

    # Fetch current quote
    quote = await client.fetch_market_quote("AAPL")

    # Fetch historical data
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=7)
    history = await client.fetch_market_history("AAPL", start, end)
```

---

## Architecture

### Components

```
app/clients/
├── fmp_client.py           # Main client implementation
├── circuit_breaker.py      # Circuit breaker pattern
├── exceptions.py           # Custom exceptions
└── README.md               # This file
```

### Resilience Patterns

#### 1. Circuit Breaker

Protects against cascading failures by detecting when the FMP Service is failing.

**States:**
- **CLOSED**: Normal operation (requests pass through)
- **OPEN**: Service failing (requests blocked)
- **HALF_OPEN**: Testing if service recovered

**Configuration:**
```python
config = FMPClientConfig(
    fmp_circuit_breaker_threshold=5,    # Failures before opening
    fmp_circuit_breaker_timeout=30      # Recovery timeout (seconds)
)
```

**State Transitions:**
```
CLOSED --[5 failures]--> OPEN --[30s timeout]--> HALF_OPEN --[1 success]--> CLOSED
                                                      |
                                                   [failure]
                                                      |
                                                      v
                                                    OPEN
```

#### 2. Retry Logic

Automatically retries transient failures with exponential backoff.

**Retry Strategy:**
- **Max Attempts**: 3
- **Backoff**: Exponential (2s, 4s, 8s)
- **Retried Errors**: Network errors, timeouts, connection failures
- **NOT Retried**: 4xx errors (client errors)

**Example:**
```python
# Attempt 1: Immediate
# Attempt 2: After 2 seconds
# Attempt 3: After 4 seconds (total 6s)
```

#### 3. Error Handling

**Exception Hierarchy:**
```
FMPServiceError (base)
├── FMPServiceUnavailableError (503, circuit open)
├── FMPRateLimitError (429, quota exceeded)
├── FMPNotFoundError (404, resource not found)
└── CircuitBreakerOpenError (circuit open)
```

---

## API Reference

### Configuration

```python
class FMPClientConfig(BaseModel):
    fmp_base_url: str = "http://fmp-service:8113"
    fmp_timeout: int = 30                    # Request timeout (seconds)
    fmp_max_retries: int = 3                 # Max retry attempts
    fmp_circuit_breaker_threshold: int = 5   # Failures before opening
    fmp_circuit_breaker_timeout: int = 30    # Recovery timeout (seconds)
```

### Methods

#### `fetch_asset_metadata()`

Fetch asset metadata from FMP Service.

```python
async def fetch_asset_metadata(
    symbols: Optional[List[str]] = None,
    asset_types: Optional[List[str]] = None,
    bypass_cache: bool = False
) -> List[AssetMetadata]
```

**Parameters:**
- `symbols`: List of symbols (e.g., `["AAPL", "GOOGL"]`)
- `asset_types`: Filter by types (e.g., `["STOCK", "CRYPTO"]`)
- `bypass_cache`: Force fresh data from FMP API

**Returns:** List of `AssetMetadata` objects

**Example:**
```python
# Fetch specific symbols
assets = await client.fetch_asset_metadata(["AAPL", "GOOGL"])

# Fetch all stocks
stocks = await client.fetch_asset_metadata(asset_types=["STOCK"])
```

---

#### `fetch_market_quote()`

Fetch current market quote for symbol.

```python
async def fetch_market_quote(symbol: str) -> MarketQuote
```

**Parameters:**
- `symbol`: Asset symbol (e.g., `"AAPL"`)

**Returns:** `MarketQuote` object

**Example:**
```python
quote = await client.fetch_market_quote("AAPL")
print(f"Price: ${quote.price}, Change: {quote.change_percent}%")
```

---

#### `fetch_market_history()`

Fetch historical market data for symbol.

```python
async def fetch_market_history(
    symbol: str,
    from_date: date,
    to_date: date
) -> List[MarketHistory]
```

**Parameters:**
- `symbol`: Asset symbol
- `from_date`: Start date (inclusive)
- `to_date`: End date (inclusive)

**Returns:** List of `MarketHistory` objects

**Example:**
```python
from datetime import date, timedelta

end = date.today()
start = end - timedelta(days=7)
history = await client.fetch_market_history("AAPL", start, end)
```

---

#### `health_check()`

Check if FMP Service is healthy.

```python
async def health_check() -> bool
```

**Returns:** `True` if service is responding

**Example:**
```python
is_healthy = await client.health_check()
if not is_healthy:
    logger.warning("FMP Service is down")
```

---

### Response Models

#### AssetMetadata

```python
class AssetMetadata(BaseModel):
    symbol: str
    name: str
    asset_type: str  # STOCK, FOREX, COMMODITY, CRYPTO
    sector: Optional[str]
    industry: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]

    # Type-specific fields
    base_currency: Optional[str]   # For FOREX/CRYPTO
    quote_currency: Optional[str]  # For FOREX/CRYPTO
    blockchain: Optional[str]      # For CRYPTO
```

#### MarketQuote

```python
class MarketQuote(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int]
    timestamp: datetime
```

#### MarketHistory

```python
class MarketHistory(BaseModel):
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int]
```

---

## Error Handling

### Exception Types

```python
from app.clients import (
    FMPServiceError,
    FMPServiceUnavailableError,
    FMPRateLimitError,
    FMPNotFoundError,
    CircuitBreakerOpenError
)
```

### Example: Comprehensive Error Handling

```python
async with FMPServiceClient(config) as client:
    try:
        quote = await client.fetch_market_quote("AAPL")

    except CircuitBreakerOpenError as e:
        # Circuit is open, service unavailable
        logger.warning(f"Circuit breaker open: {e}")
        logger.info(f"Will retry after {e.recovery_timeout}s")
        # Use fallback data or cache

    except FMPRateLimitError as e:
        # API quota exceeded
        logger.error(f"Rate limit exceeded: {e}")
        # Wait for quota reset (24 hours)

    except FMPNotFoundError as e:
        # Resource not found
        logger.warning(f"Symbol not found: {e.resource}")
        # Invalid symbol, check input

    except FMPServiceUnavailableError as e:
        # Service temporarily down
        logger.error(f"Service unavailable: {e}")
        # Use cached data or retry later

    except FMPServiceError as e:
        # Generic service error
        logger.error(f"FMP Service error: {e}")
```

---

## Circuit Breaker Monitoring

### Get Statistics

```python
stats = client.get_circuit_breaker_stats()

print(f"Service: {stats['service_name']}")
print(f"State: {stats['state']}")  # CLOSED, OPEN, HALF_OPEN
print(f"Failures: {stats['failure_count']}/{stats['failure_threshold']}")
print(f"Is Open: {stats['is_open']}")
```

### Manual Reset

```python
# Reset circuit breaker to CLOSED state
# Use with caution - typically for testing or manual intervention
client.reset_circuit_breaker()
```

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest services/knowledge-graph-service/tests/test_fmp_client.py -v

# Run with coverage
pytest services/knowledge-graph-service/tests/test_fmp_client.py --cov=app.clients
```

### Test Categories

- **Circuit Breaker Tests**: State transitions, recovery
- **Retry Logic Tests**: Exponential backoff, failure handling
- **Error Handling Tests**: Exception types, HTTP status codes
- **API Method Tests**: Response parsing, validation
- **Context Manager Tests**: Resource cleanup

### Mocking FMP Service

```python
from unittest.mock import MagicMock, patch

# Mock successful response
mock_response = MagicMock()
mock_response.status_code = 200
mock_response.json.return_value = {"symbol": "AAPL", "price": 150.0}

with patch.object(client.client, 'get', return_value=mock_response):
    quote = await client.fetch_market_quote("AAPL")
```

---

## Configuration via Environment

Add to `services/knowledge-graph-service/.env`:

```bash
# FMP Service Configuration
FMP_SERVICE_URL=http://fmp-service:8113
FMP_TIMEOUT=30
FMP_MAX_RETRIES=3
FMP_CIRCUIT_BREAKER_THRESHOLD=5
FMP_CIRCUIT_BREAKER_TIMEOUT=30
```

Load in `config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FMP_SERVICE_URL: str = "http://fmp-service:8113"
    FMP_TIMEOUT: int = 30
    FMP_MAX_RETRIES: int = 3
    FMP_CIRCUIT_BREAKER_THRESHOLD: int = 5
    FMP_CIRCUIT_BREAKER_TIMEOUT: int = 30
```

---

## Examples

See `examples/fmp_client_usage.py` for comprehensive usage examples:

```bash
python services/knowledge-graph-service/examples/fmp_client_usage.py
```

---

## Performance Considerations

### Connection Pooling

The client uses connection pooling to reduce latency:

```python
httpx.Limits(
    max_keepalive_connections=10,
    max_connections=20
)
```

### Timeout Configuration

```python
httpx.Timeout(
    timeout=30.0,    # Total request timeout
    connect=5.0      # Connection timeout
)
```

### Rate Limiting

FMP Service has a quota of **300 API calls per day**. The client does NOT enforce rate limiting - this must be handled by the caller or via a separate rate limiter service.

**Recommendation:** Implement caching to minimize FMP API calls.

---

## Troubleshooting

### Circuit Breaker Stuck Open

**Symptom:** All requests fail with `CircuitBreakerOpenError`

**Solution:**
1. Check FMP Service health: `await client.health_check()`
2. Wait for recovery timeout (default 30s)
3. Manual reset if needed: `client.reset_circuit_breaker()`

### Rate Limit Exceeded

**Symptom:** `FMPRateLimitError` (429)

**Solution:**
1. Check daily quota usage
2. Implement caching to reduce API calls
3. Wait for quota reset (24 hours)

### Slow Response Times

**Symptom:** Requests taking > 5 seconds

**Solution:**
1. Check FMP Service health
2. Reduce timeout: `FMP_TIMEOUT=10`
3. Monitor network latency
4. Verify connection pooling is working

---

## References

- **Architecture Guide**: `/docs/architecture/fmp-kg-integration-implementation-guide.md`
- **API Spec**: `/docs/api/kg-markets-api-spec.yaml`
- **ADR-035**: Circuit Breaker Pattern
- **FMP Service**: Port 8113

---

## Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 1.0.0   | 2025-11-16 | Initial implementation with circuit breaker  |

---

**Maintained by:** Knowledge-Graph Service Team
**Support:** See `/docs/architecture/fmp-kg-integration-implementation-guide.md`
