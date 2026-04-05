# Rate Limiting Guide

**Status:** ✅ Implemented (2025-11-24)
**Coverage:** 7 services (auth, feed, analytics, research, osint, notification, search)
**Backend:** Redis
**Implementation:** `/services/common/rate_limiting.py`

---

## Overview

All public-facing services implement Redis-backed rate limiting with:
- **Per-user tracking** via JWT user_id
- **Global limits** for unauthenticated requests
- **Multiple time windows** (minute + hour)
- **Automatic cleanup** with TTL
- **Proper error responses** (429 + Retry-After headers)

---

## Rate Limits

### Authenticated Users (JWT token)
- **60 requests/minute** (per user)
- **1000 requests/hour** (per user)

### Unauthenticated Requests
- **30 requests/minute** (global)
- **500 requests/hour** (global)

### Exempt Endpoints
These endpoints are **NOT** rate-limited:
- `/health` - Health checks
- `/metrics` - Prometheus metrics
- `/` - Root endpoint

---

## Implementation Details

### Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  Rate Limit Middleware  │  ← Checks Redis counters
└──────┬──────────────────┘
       │
       ├─ JWT present? ─→ Per-user limits (60/min, 1000/hr)
       │
       └─ No JWT? ─────→ Global limits (30/min, 500/hr)
       │
       ▼
┌─────────────┐
│    Redis    │  ← Stores counters with TTL
└─────────────┘
```

### Redis Key Structure

```
# Per-user limits
ratelimit:user:user:{user_id}:minute → Counter (TTL: 60s)
ratelimit:user:user:{user_id}:hour   → Counter (TTL: 3600s)

# Global limits (unauthenticated)
ratelimit:global:ip:{ip_hash}:minute → Counter (TTL: 60s)
ratelimit:global:ip:{ip_hash}:hour   → Counter (TTL: 3600s)
```

### JWT Extraction

Rate limiter extracts `user_id` from JWT **without signature verification**:
- Signature verification is handled by auth middleware
- Rate limiter only needs user_id for key generation
- Falls back to IP address if no valid JWT

**Security:** This is safe because:
1. Invalid JWTs still get rate-limited (via IP)
2. Auth middleware rejects invalid JWTs before business logic
3. Rate limiting is DoS protection, not authorization

---

## Service Integration

### Integration Pattern

All services follow this pattern in `app/main.py`:

```python
# 1. Import
import sys
sys.path.insert(0, '/home/cytrex/news-microservices/services')
from common.rate_limiting import setup_rate_limiting

# 2. Configure (after CORS, before routers)
app = FastAPI(...)
app.add_middleware(CORSMiddleware, ...)

setup_rate_limiting(app, settings.get_redis_url())

app.include_router(...)
```

### Integrated Services

| Service | Port | Integration | Config Source |
|---------|------|-------------|---------------|
| auth-service | 8100 | ✅ | `settings.get_redis_url()` |
| feed-service | 8101 | ✅ | `settings.REDIS_URL` |
| analytics-service | 8107 | ✅ | `os.getenv("REDIS_URL")` |
| research-service | 8103 | ✅ | `settings.REDIS_URL` |
| osint-service | 8104 | ✅ | `settings.REDIS_URL` or fallback |
| notification-service | 8105 | ✅ | `settings.REDIS_URL` or fallback |
| search-service | 8106 | ✅ | `settings.REDIS_URL` |

---

## Response Formats

### Success Response (200)

Headers include remaining limits:

```http
HTTP/1.1 200 OK
X-RateLimit-Remaining-Minute: 57
X-RateLimit-Remaining-Hour: 995
Content-Type: application/json

{
  "data": "..."
}
```

### Rate Limit Exceeded (429)

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1732459200
Content-Type: application/json

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded (minute)",
  "limit": 60,
  "current": 61,
  "retry_after": 42,
  "type": "rate_limit_error"
}
```

### Header Definitions

| Header | Description |
|--------|-------------|
| `Retry-After` | Seconds until limit resets |
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |
| `X-RateLimit-Remaining-Minute` | Requests remaining (minute window) |
| `X-RateLimit-Remaining-Hour` | Requests remaining (hour window) |

---

## Configuration

### Environment Variables

Required in `.env` or service config:

```bash
# Redis connection (used for rate limiting)
REDIS_URL=redis://:redis_secret_2024@redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secret_2024
REDIS_DB=0
```

### Adjusting Limits

Limits are defined in `/services/common/rate_limiting.py`:

```python
class RateLimitConfig:
    # Per-user limits (authenticated)
    USER_RATE_PER_MINUTE = 60
    USER_RATE_PER_HOUR = 1000

    # Global limits (unauthenticated)
    GLOBAL_RATE_PER_MINUTE = 30
    GLOBAL_RATE_PER_HOUR = 500
```

**To change limits:**
1. Edit values in `RateLimitConfig`
2. Restart affected services
3. No database changes needed (Redis counters reset automatically)

---

## Testing

### Manual Testing

```bash
# Test unauthenticated limit (should hit 429 after 30 requests)
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8100/api/v1/auth/status
done

# Test authenticated limit (requires valid token)
TOKEN="your_jwt_token"
for i in {1..65}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8101/api/v1/feeds
done
```

### Automated Tests

```bash
# Run rate limiting tests
cd /home/cytrex/news-microservices
pytest tests/test_rate_limiting.py -v

# Tests verify:
# - Health endpoints are exempt
# - Unauthenticated limits work
# - Authenticated limits work
# - Headers are present
# - Redis connectivity
# - Configuration is correct
```

---

## Monitoring

### Redis Keys Inspection

```bash
# Connect to Redis
docker exec -it news-microservices-redis-1 redis-cli -a redis_secret_2024

# List all rate limit keys
KEYS ratelimit:*

# Check specific user's limits
GET ratelimit:user:user:123:minute
GET ratelimit:user:user:123:hour
TTL ratelimit:user:user:123:minute

# Check global limits
KEYS ratelimit:global:*
```

### Prometheus Metrics

(TODO: Add Prometheus metrics for rate limiting)

Proposed metrics:
- `rate_limit_requests_total{service, status}` - Total requests
- `rate_limit_exceeded_total{service}` - 429 responses
- `rate_limit_redis_errors_total{service}` - Redis connection errors

---

## Troubleshooting

### Problem: All requests return 429

**Symptom:**
```bash
curl http://localhost:8100/api/v1/auth/status
{"error":"rate_limit_exceeded",...}
```

**Causes:**
1. Redis not running
2. Redis connection refused
3. Incorrect Redis URL

**Solution:**
```bash
# Check Redis status
docker ps | grep redis

# Test Redis connection
docker exec news-microservices-redis-1 redis-cli -a redis_secret_2024 ping
# Expected: PONG

# Check service logs
docker logs news-microservices-auth-service-1 | grep -i redis
```

### Problem: Rate limiting not working

**Symptom:**
```bash
# Can make unlimited requests
for i in {1..100}; do curl -s http://localhost:8100/api/v1/auth/status; done
# All succeed
```

**Causes:**
1. Rate limiting not initialized
2. Middleware not registered
3. Wrong endpoint (exempt from rate limiting)

**Solution:**
```bash
# Check service logs for startup message
docker logs news-microservices-auth-service-1 | grep "Rate limiting"
# Expected: "Rate limiting enabled: 60/min, 1000/hour (authenticated)"

# Verify Redis keys are created
docker exec -it news-microservices-redis-1 redis-cli -a redis_secret_2024
> KEYS ratelimit:*
# Should show keys after making requests

# Test non-exempt endpoint
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}'
```

### Problem: Headers not present

**Symptom:**
```bash
curl -I http://localhost:8101/api/v1/feeds
# Missing: X-RateLimit-Remaining-Minute, X-RateLimit-Remaining-Hour
```

**Causes:**
1. Middleware execution order incorrect
2. Response modified after middleware

**Solution:**
```bash
# Check middleware order in app/main.py
# Rate limiting should be AFTER CORS, BEFORE routers

# Verify with verbose curl
curl -v http://localhost:8101/api/v1/feeds 2>&1 | grep -i ratelimit
```

### Problem: JWT user_id not extracted

**Symptom:**
- All authenticated requests counted as global/IP-based
- User limits not working

**Causes:**
1. JWT format incorrect
2. Missing `user_id` or `sub` claim
3. JWT not in `Authorization: Bearer` header

**Solution:**
```bash
# Decode JWT (without verification)
echo "your.jwt.token" | cut -d. -f2 | base64 -d 2>/dev/null | jq .
# Check for "user_id" or "sub" field

# Test with valid token from login
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8101/api/v1/feeds
```

---

## Security Considerations

### DDoS Protection

Rate limiting provides **basic DDoS protection**, but:
- ✅ Stops simple flooding attacks
- ✅ Prevents credential stuffing (30 guesses/min)
- ⚠️ Does NOT stop distributed attacks (many IPs)
- ⚠️ Does NOT stop application-layer attacks

**For production:**
- Add Cloudflare or AWS WAF for distributed DDoS
- Implement IP reputation checks
- Add CAPTCHA for sensitive endpoints
- Monitor for anomalous traffic patterns

### Privacy

IP addresses are **hashed** before storage:
```python
ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
```

This ensures:
- ✅ Cannot reverse IP from Redis keys
- ✅ GDPR compliant (pseudonymized data)
- ✅ Still unique per client

### Token Security

JWT extraction does **NOT verify signatures**:
- ⚠️ Allows invalid JWTs to attempt rate-limited requests
- ✅ Auth middleware still rejects invalid JWTs
- ✅ Rate limiting is DoS prevention, not authentication

**Why this is safe:**
1. Invalid JWTs still consume rate limit budget (IP-based)
2. Auth middleware verifies signatures before business logic
3. Attacker cannot bypass rate limits with fake JWTs

---

## Future Enhancements

### Planned (Priority)
1. **Prometheus metrics** - Track 429 responses, Redis errors
2. **Dynamic limits** - Adjust based on load/subscription tier
3. **Burst allowance** - Allow short bursts above limit
4. **Rate limit exemptions** - Whitelist IPs (internal services)

### Under Consideration
1. **Token bucket algorithm** - More flexible than fixed window
2. **Per-endpoint limits** - Different limits for expensive operations
3. **Sliding window** - Smoother rate limiting
4. **Redis Cluster support** - Scale beyond single Redis instance

---

## References

- **Implementation:** `/services/common/rate_limiting.py`
- **Tests:** `/tests/test_rate_limiting.py`
- **Dependencies:** `slowapi==0.1.9`, `redis[hiredis]==5.0.1`
- **Related Docs:**
  - [Redis Configuration](./redis-guide.md)
  - [Authentication Guide](./authentication-guide.md)
  - [API Design Principles](../api/design-principles.md)

---

**Last Updated:** 2025-11-24
**Author:** Security Backend Developer Agent
**Reviewers:** Backend Team
