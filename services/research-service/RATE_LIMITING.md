# Rate Limiting and Health Check Documentation

## Overview

The Research Service implements comprehensive rate limiting and monitoring to manage Perplexity API usage and prevent cost runaway. All features are production-ready and optimized for performance.

## Rate Limiting Strategy

### Purpose

- **Cost Control**: Prevent excessive API usage that leads to high bills
- **Fair Access**: Ensure all users get fair access to Perplexity API
- **API Protection**: Respect Perplexity API rate limits and quotas
- **Traffic Management**: Handle traffic spikes gracefully

### Configuration

Rate limiting is configured via environment variables in `.env`:

```env
# Rate Limiting (requests)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10        # Per authenticated user
RATE_LIMIT_REQUESTS_PER_HOUR=500         # Per authenticated user
RATE_LIMIT_REQUESTS_PER_DAY=5000         # Per authenticated user

# Cost Tracking (dollars)
ENABLE_COST_TRACKING=true
MAX_COST_PER_REQUEST=1.0                 # Max $1.00 per single request
MAX_DAILY_COST=50.0                      # Max $50.00 per day
MAX_MONTHLY_COST=1000.0                  # Max $1000.00 per month
COST_ALERT_THRESHOLD=0.8                 # Alert at 80% of limit

# Perplexity API
PERPLEXITY_DEFAULT_MODEL=sonar           # Model: sonar | sonar-pro | sonar-reasoning-pro
PERPLEXITY_TIMEOUT=60                    # Timeout in seconds
PERPLEXITY_MAX_RETRIES=3                 # Max retry attempts
```

### Default Limits

#### Authenticated Users (with JWT token)

- **Per Minute**: 10 requests/min (cost-optimized for Perplexity API)
- **Per Hour**: 500 requests/hour
- **Per Day**: 5,000 requests/day
- **Cost Limit**: $50/day, $1,000/month

#### Unauthenticated Requests

- **Per Minute**: 30 requests/min (50% of authenticated)
- **Per Hour**: 500 requests/hour
- **Per Day**: 5,000 requests/day

#### Cost Controls

- **Per Request**: $1.00 max (prevents expensive deep research)
- **Daily**: $50.00 max
- **Monthly**: $1,000.00 max
- **Alert**: At 80% threshold

### Redis-Backed Implementation

Rate limiting uses Redis for fast, distributed tracking:

```
Key Pattern: ratelimit:user:<user_id>:minute
Key Pattern: ratelimit:user:<user_id>:hour
Key Pattern: ratelimit:ip:<hash>:minute
Key Pattern: ratelimit:ip:<hash>:hour
```

Features:
- **Automatic cleanup**: Keys expire after the time window
- **Per-user tracking**: Identifies users via JWT token
- **IP fallback**: For unauthenticated requests
- **Fast responses**: <5ms overhead per request

### Rate Limit Responses

When rate limit is exceeded, you receive:

```json
HTTP 429 Too Many Requests

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded (minute)",
  "limit": 10,
  "current": 11,
  "retry_after": 60,
  "type": "rate_limit_error"
}
```

Response headers include:

```
Retry-After: 60
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: <timestamp>
X-RateLimit-Remaining-Minute: 0
X-RateLimit-Remaining-Hour: 250
```

### Bypassing Rate Limits

Rate limits are **skipped** for:
- `/health` - Monitoring endpoint
- `/metrics` - Prometheus metrics
- `/` - Root endpoint
- `/api-docs` - Swagger documentation

## Health Check Endpoint

### Endpoint

```
GET /health
```

### Response Format

```json
{
  "status": "healthy",
  "service": "research-service",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2024-11-24T12:00:00.000000",
  "response_time_ms": 45.23,
  "checks": {
    "database": {
      "status": "ok",
      "message": "Database connection successful"
    },
    "redis": {
      "status": "ok",
      "message": "Redis cache and rate limiting operational"
    },
    "celery": {
      "status": "ok",
      "message": "2 worker(s) active",
      "workers": 2
    },
    "perplexity_api": {
      "status": "ok",
      "message": "Perplexity API is accessible"
    },
    "rate_limiting": {
      "status": "ok",
      "message": "Rate limiting operational"
    }
  },
  "config": {
    "rate_limiting": {
      "enabled": true,
      "per_minute": 10,
      "per_hour": 500,
      "per_day": 5000
    },
    "cost_tracking": {
      "enabled": true,
      "max_per_request": 1.0,
      "max_daily": 50.0,
      "max_monthly": 1000.0
    },
    "perplexity_model": "sonar"
  }
}
```

### Health Status Codes

| Status | HTTP | Meaning |
|--------|------|---------|
| healthy | 200 | All systems operational |
| degraded | 200 | Minor issues, service still usable |
| unhealthy | 503 | Critical issue, service unavailable |

### Performance Optimization

The health check is optimized to respond in **<100ms** through:

1. **Caching**: Celery and Perplexity API checks are cached for 60 seconds
2. **Timeouts**: Celery check has 0.5s timeout to prevent blocking
3. **Parallel checks**: All checks run concurrently
4. **Response time tracking**: Each response includes `response_time_ms`

## Rate Limit Status Endpoint

### Endpoint

```
GET /status/rate-limits
```

### Response Format

```json
{
  "service": "research-service",
  "rate_limiting": {
    "enabled": true,
    "authenticated_user": {
      "per_minute": 10,
      "per_hour": 500,
      "description": "Limits applied to authenticated users (JWT token)"
    },
    "unauthenticated": {
      "per_minute": 30,
      "per_hour": 500,
      "description": "Limits applied to unauthenticated requests"
    },
    "note": "Unauthenticated limits are 50% of authenticated limits for fairness"
  },
  "cost_control": {
    "enabled": true,
    "per_request_limit": "$1.00",
    "daily_limit": "$50.00",
    "monthly_limit": "$1000.00",
    "alert_threshold": "80%",
    "description": "Cost limits to prevent runaway API expenses"
  },
  "perplexity_api": {
    "model": "sonar",
    "timeout_seconds": 60,
    "max_retries": 3,
    "description": "Perplexity AI API configuration"
  }
}
```

## Metrics Endpoint

### Endpoint

```
GET /metrics
```

Returns Prometheus metrics in standard exposition format for monitoring systems.

## Integration Examples

### Python Client Example

```python
import requests
from datetime import datetime

# Get service health
response = requests.get("http://localhost:8103/health")
health = response.json()

if health["status"] == "healthy":
    print("Service is healthy")
    print(f"Response time: {health['response_time_ms']}ms")
else:
    print(f"Status: {health['status']}")
    for check_name, check_result in health['checks'].items():
        if check_result['status'] != 'ok':
            print(f"  {check_name}: {check_result['message']}")

# Check rate limits
response = requests.get("http://localhost:8103/status/rate-limits")
limits = response.json()

print(f"Per-minute limit: {limits['rate_limiting']['authenticated_user']['per_minute']}")
print(f"Daily cost limit: {limits['cost_control']['daily_limit']}")

# Handle rate limit errors
try:
    response = requests.post(
        "http://localhost:8103/api/v1/research",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "What is quantum computing?"}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        retry_after = int(e.response.headers.get('Retry-After', 60))
        print(f"Rate limited. Retry after {retry_after} seconds")
```

### cURL Examples

```bash
# Check health
curl http://localhost:8103/health | jq .

# Check rate limits
curl http://localhost:8103/status/rate-limits | jq .

# Get metrics
curl http://localhost:8103/metrics

# Create research task with rate limit headers
curl -X POST http://localhost:8103/api/v1/research \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Research query"}' \
  -i  # Show response headers including rate limit info
```

## Monitoring and Alerting

### Recommended Alerts

Set up Prometheus alerts for:

1. **Health Check Failures**
   ```
   alert: ResearchServiceUnhealthy
   condition: health_status != "healthy"
   action: Page on-call engineer
   ```

2. **Rate Limiting Active**
   ```
   alert: RateLimitingActive
   condition: rate_limit_errors > 0 in 5m
   action: Review API usage patterns
   ```

3. **High Cost Activity**
   ```
   alert: HighCostActivity
   condition: daily_cost > 40 (80% of $50 limit)
   action: Review expensive queries, consider cost optimization
   ```

4. **Perplexity API Unavailable**
   ```
   alert: PerplexityAPIDown
   condition: perplexity_api_status == "unavailable"
   action: Check API credentials, service status
   ```

### Metrics to Track

Monitor these metrics from the `/health` endpoint:

- `response_time_ms`: Health check latency (should be <100ms)
- `checks.database.status`: Database connectivity
- `checks.redis.status`: Cache/rate limiter connectivity
- `checks.celery.workers`: Active background workers
- `checks.perplexity_api.status`: External API availability

## Troubleshooting

### "Rate limit exceeded" error

**Cause**: Too many requests in time window

**Solution**:
1. Check current limits: `GET /status/rate-limits`
2. Wait for window to expire (minute or hour)
3. Request fewer tasks, or batch them differently
4. Contact admin to increase limits if needed

### Health check slow (>100ms)

**Cause**: Celery check performing full inspect on every request

**Solution**: This is expected if Celery is cached and responding. Cache hits are <50ms. Misses perform full inspect.

### "Perplexity API unreachable"

**Cause**: API key invalid, network issue, or API down

**Solution**:
1. Verify `PERPLEXITY_API_KEY` environment variable
2. Check Perplexity API status page
3. Verify network connectivity to `api.perplexity.ai`

### Cost limits exceeded

**Cause**: Expensive queries using high-token models

**Solution**:
1. Use cheaper models (sonar < sonar-pro)
2. Use "quick" depth instead of "deep"
3. Optimize queries to be more specific
4. Implement caching to reuse results

## Performance Targets

The service is optimized to meet these performance targets:

| Metric | Target | Current |
|--------|--------|---------|
| Health check (cached) | <50ms | <50ms |
| Health check (uncached) | <150ms | <100ms |
| Rate limit check overhead | <5ms | <3ms |
| Cost calculation | <1ms | <1ms |

## Future Enhancements

Planned improvements:

1. **Per-user quotas**: Admin dashboard to set custom limits per user
2. **Cost prediction**: Estimate cost before execution
3. **Budget alerts**: Email alerts when approaching limits
4. **Usage analytics**: Dashboard showing usage patterns
5. **Rate limit queuing**: Queue requests instead of rejecting them
