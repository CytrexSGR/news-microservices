# Resilience Module

Circuit breaker pattern implementation for protecting against cascading failures in external API calls.

## Features

- **Async/await support** - Full asyncio compatibility
- **Context manager pattern** - Clean integration with async code
- **Prometheus metrics** - Full observability
- **Thread-safe** - Uses asyncio.Lock
- **Configurable** - Thresholds, timeouts, recovery settings
- **Registry pattern** - Manage multiple circuit breakers

## Quick Start

### Basic Usage (Context Manager - Recommended)

```python
from news_mcp_common.resilience import CircuitBreaker

# Create circuit breaker
circuit_breaker = CircuitBreaker(
    name="openai-api",
    config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=120,
    )
)

# Use as context manager
async def call_openai():
    async with circuit_breaker():
        response = await client.chat.completions.create(...)
        return response
```

### Manual Control

```python
async def call_external_api():
    if not circuit_breaker.can_execute():
        raise CircuitBreakerOpenError("Circuit is open")

    try:
        result = await risky_operation()
        circuit_breaker.record_success()
        return result
    except Exception as e:
        circuit_breaker.record_failure(e)
        raise
```

### Registry Pattern (Multi-Resource)

```python
from news_mcp_common.resilience import CircuitBreakerRegistry

# Create registry
registry = CircuitBreakerRegistry()

# Get or create circuit breakers
openai_cb = await registry.get_or_create("openai-api")
gemini_cb = await registry.get_or_create("gemini-api")

# Use them
async with openai_cb():
    result = await call_openai()
```

## Configuration

```python
from news_mcp_common.resilience import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes in half-open
    timeout_seconds=120,      # Wait 120s before trying half-open
    enable_metrics=True,      # Enable Prometheus metrics
)
```

## States

- **CLOSED** - Normal operation, requests pass through
- **OPEN** - Service failing, requests blocked
- **HALF_OPEN** - Testing recovery (allows limited requests)

## State Transitions

```
CLOSED -> OPEN         (after failure_threshold failures)
OPEN -> HALF_OPEN      (after timeout_seconds)
HALF_OPEN -> CLOSED    (after success_threshold successes)
HALF_OPEN -> OPEN      (on any failure)
```

## Prometheus Metrics

```python
# Metrics exposed:
circuit_breaker_state{name}                          # Current state (0/1/2)
circuit_breaker_failures_total{name, error_type}     # Total failures
circuit_breaker_successes_total{name}                # Total successes
circuit_breaker_rejections_total{name}               # Blocked requests
circuit_breaker_state_changes_total{name, from, to}  # State transitions
circuit_breaker_recovery_time_seconds{name}          # Recovery duration
```

## Statistics

```python
# Get current stats
stats = circuit_breaker.get_stats()
# {
#     "name": "openai-api",
#     "state": "closed",
#     "failure_count": 0,
#     "total_failures": 123,
#     "total_successes": 45678,
#     "total_rejections": 5,
#     ...
# }

# Registry stats
all_stats = registry.get_all_stats()
```

## Example: LLM Provider with Failover

```python
from news_mcp_common.resilience import CircuitBreakerRegistry

registry = CircuitBreakerRegistry()

async def generate_with_failover(prompt: str):
    # Try OpenAI first
    openai_cb = await registry.get_or_create("openai")
    if openai_cb.can_execute():
        try:
            async with openai_cb():
                return await call_openai(prompt)
        except Exception:
            pass  # Fall through to failover

    # Failover to Gemini
    gemini_cb = await registry.get_or_create("gemini")
    async with gemini_cb():
        return await call_gemini(prompt)
```

## Testing

```python
# Manual reset (for testing/admin)
circuit_breaker.reset()

# Check state
assert circuit_breaker.state == CircuitBreakerState.CLOSED
```

## Integration with Existing Code

### feed-service Migration

```python
# Before (feed-service implementation)
circuit_breaker = self.get_circuit_breaker(feed_id)
if not circuit_breaker.can_execute():
    return False, 0

# After (shared library)
from news_mcp_common.resilience import CircuitBreaker

circuit_breaker = CircuitBreaker(name=f"feed-{feed_id}")
async with circuit_breaker():
    response = await fetch_feed(feed_url)
```

## Performance

- **Overhead:** < 1ms per operation
- **Thread-safe:** Uses asyncio.Lock
- **Memory:** ~200 bytes per circuit breaker

## Best Practices

1. **Use context manager** - Cleanest pattern, automatic error handling
2. **Per-resource breakers** - One circuit breaker per external service
3. **Tune thresholds** - Start conservative (5 failures), adjust based on metrics
4. **Monitor state changes** - Alert on OPEN state
5. **Implement failover** - Use registry pattern for graceful degradation

## See Also

- Based on: `services/feed-service/app/services/feed_fetcher.py:26-78`
- Metrics: `news_mcp_common.observability`
- Events: `news_mcp_common.events`
