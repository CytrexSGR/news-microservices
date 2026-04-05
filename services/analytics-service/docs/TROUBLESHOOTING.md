# Analytics Service - Troubleshooting Guide

## Table of Contents

1. [Performance Issues](#performance-issues)
2. [Circuit Breaker Problems](#circuit-breaker-problems)
3. [WebSocket Issues](#websocket-issues)
4. [Database Performance](#database-performance)
5. [Monitoring and Diagnostics](#monitoring-and-diagnostics)
6. [Common Error Messages](#common-error-messages)

---

## Performance Issues

### Symptom: High Response Times

**Target Performance:**
- P95 latency: < 200ms
- P99 latency: < 500ms
- Throughput: > 16 req/s

**Diagnosis:**

```bash
# Check current performance metrics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/query-performance
```

**Common Causes:**

1. **Slow database queries**
   - Check query statistics
   - Look for missing indexes
   - Verify connection pool settings

2. **Circuit breaker open**
   - External services unavailable
   - Check circuit breaker status

3. **High load**
   - Too many concurrent requests
   - Check connection pool exhaustion

**Solutions:**

1. **Optimize database queries:**

```bash
# Get query recommendations
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/query-performance | \
  jq '.index_recommendations'
```

2. **Increase connection pool:**

Edit `docker-compose.yml`:

```yaml
services:
  analytics-service:
    environment:
      - SQLALCHEMY_POOL_SIZE=20
      - SQLALCHEMY_MAX_OVERFLOW=40
```

3. **Enable query caching:**

Check Redis is running:

```bash
docker compose ps redis
```

---

## Circuit Breaker Problems

### Symptom: "Circuit breaker is open" Errors

Circuit breakers protect against cascading failures by temporarily blocking requests to failing services.

**Check Circuit Breaker Status:**

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/circuit-breakers
```

**Example Output:**

```json
{
  "circuit_breakers": {
    "feed-service_circuit": {
      "state": "open",
      "failure_count": 5,
      "last_failure_time": "2025-11-24T10:30:00Z",
      "opened_at": "2025-11-24T10:30:05Z"
    }
  },
  "open_circuits": 1
}
```

**Understanding States:**

- **CLOSED**: Normal operation, requests allowed
- **OPEN**: Service failed threshold, requests blocked for 60 seconds
- **HALF_OPEN**: Testing recovery, limited requests allowed

**Root Cause Analysis:**

1. **Check target service health:**

```bash
# Check feed-service
curl http://localhost:8001/health

# Check logs
docker compose logs feed-service --tail=100
```

2. **Check network connectivity:**

```bash
# From analytics container
docker compose exec analytics-service curl http://feed-service:8001/health
```

**Solutions:**

1. **Wait for automatic recovery** (60 seconds)
   - Circuit breaker will automatically transition to HALF_OPEN
   - If service is healthy, will return to CLOSED

2. **Fix underlying service issue**
   - Restart failed service: `docker compose restart feed-service`
   - Check service logs for errors

3. **Adjust circuit breaker settings** (if too sensitive)

Edit `/home/cytrex/news-microservices/services/analytics-service/app/core/resilience.py`:

```python
CircuitBreakerConfig(
    failure_threshold=10,  # Increase from 5
    timeout_seconds=120    # Increase from 60
)
```

---

## WebSocket Issues

### Issue 1: Connection Fails Immediately

**Error:** WebSocket connection closes with code 1008

**Cause:** Authentication failure

**Solution:**

1. **Verify token validity:**

```bash
# Test token with REST API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/health
```

2. **Get fresh token:**

```bash
# Login to get new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "andreas@test.com", "password": "Aug2012#"}'
```

3. **Check token expiration:**

```bash
# Decode JWT (requires jq and base64)
echo "<token>" | cut -d. -f2 | base64 -d | jq .
```

### Issue 2: No Messages Received

**Symptom:** Connected but no metrics updates

**Diagnosis:**

```javascript
// In browser console
ws.send(JSON.stringify({action: "ping"}));
// Should receive: {"type": "pong", "timestamp": "..."}
```

**Causes:**

1. Not subscribed to channel
2. No data available
3. Connection idle

**Solution:**

```javascript
// Subscribe to metrics
ws.send(JSON.stringify({
  action: "subscribe",
  channel: "metrics"
}));

// Request metrics manually
ws.send(JSON.stringify({
  action: "get_metrics"
}));
```

### Issue 3: Frequent Disconnections

**Symptom:** Connection drops every few minutes

**Diagnosis:**

```bash
# Check WebSocket statistics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/ws/stats
```

**Common Causes:**

1. **Client timeout too short**
   - Heartbeat interval is 30s
   - Client timeout should be > 60s

2. **Network proxy/firewall**
   - Some proxies close idle WebSocket connections
   - Solution: Send periodic pings from client

3. **Server overload**
   - Too many connections
   - Check connection count in stats

**Solutions:**

1. **Implement client-side ping:**

```javascript
// Send ping every 20 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({action: "ping"}));
  }
}, 20000);
```

2. **Implement reconnection logic:**

```javascript
let reconnectAttempts = 0;

ws.onclose = () => {
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 60000);
  setTimeout(() => {
    reconnectAttempts++;
    connect(); // Reconnect
  }, delay);
};
```

### Issue 4: High Memory Usage

**Symptom:** Analytics service memory grows over time

**Diagnosis:**

```bash
# Check memory usage
docker stats analytics-service --no-stream

# Check connection count
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/ws/stats | jq '.total_connections'
```

**Causes:**

1. Dead connections not cleaned up
2. Message queue buildup
3. Memory leak in client handling

**Solution:**

```bash
# Restart service to clear memory
docker compose restart analytics-service

# Check for memory leaks in logs
docker compose logs analytics-service | grep -i "memory\|leak"
```

---

## Database Performance

### Issue: Slow Query Performance

**Target:** Query response times < 100ms average

**Diagnosis:**

```bash
# Get query performance statistics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/query-performance
```

**Example Output:**

```json
{
  "total_queries": 5000,
  "unique_patterns": 12,
  "slow_query_threshold_ms": 100,
  "top_queries": [
    {
      "query": "SELECT * FROM analytics_metrics WHERE service = '?' AND timestamp >= '?'",
      "executions": 1000,
      "avg_time_ms": 150.5,
      "slow_query_count": 300
    }
  ],
  "index_recommendations": [
    {
      "table": "analytics_metrics",
      "column": "service",
      "sql": "CREATE INDEX idx_analytics_metrics_service ON analytics_metrics(service);",
      "impact": "high"
    }
  ]
}
```

**Solutions:**

1. **Apply recommended indexes:**

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d news_analytics

# Apply recommended index
CREATE INDEX idx_analytics_metrics_service
ON analytics_metrics(service);

CREATE INDEX idx_analytics_metrics_timestamp
ON analytics_metrics(timestamp DESC);

# Composite index for common queries
CREATE INDEX idx_analytics_metrics_service_timestamp
ON analytics_metrics(service, timestamp DESC);
```

2. **Analyze query plans:**

```sql
-- Check if indexes are used
EXPLAIN ANALYZE
SELECT * FROM analytics_metrics
WHERE service = 'auth-service'
  AND timestamp >= NOW() - INTERVAL '1 hour';
```

3. **Optimize aggregations:**

```sql
-- Add materialized view for frequent aggregations
CREATE MATERIALIZED VIEW hourly_metrics AS
SELECT
  service,
  DATE_TRUNC('hour', timestamp) as hour,
  AVG(value) as avg_value,
  SUM(value) as total_value,
  COUNT(*) as count
FROM analytics_metrics
GROUP BY service, DATE_TRUNC('hour', timestamp);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_metrics;
```

### Issue: Connection Pool Exhausted

**Error:** "QueuePool limit of size X overflow Y reached"

**Diagnosis:**

```bash
# Check connection pool status
docker compose logs analytics-service | grep -i "pool\|connection"
```

**Solution:**

1. **Increase pool size:**

Edit `docker-compose.yml`:

```yaml
services:
  analytics-service:
    environment:
      - SQLALCHEMY_POOL_SIZE=20
      - SQLALCHEMY_MAX_OVERFLOW=40
      - SQLALCHEMY_POOL_TIMEOUT=30
      - SQLALCHEMY_POOL_RECYCLE=3600
```

2. **Fix connection leaks:**

Ensure all database sessions are properly closed:

```python
# Always use context manager
with get_db() as db:
    # Do work
    pass  # Session automatically closed
```

---

## Monitoring and Diagnostics

### System Health Check

```bash
# Quick health check
curl http://localhost:8007/health

# Detailed health with authentication
curl -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/health
```

**Response:**

```json
{
  "status": "healthy",
  "issues": [],
  "metrics": {
    "circuit_breakers": {
      "total": 7,
      "open": 0,
      "closed": 7
    },
    "database": {
      "total_queries": 10000,
      "unique_patterns": 15,
      "slow_queries": 2
    },
    "websocket": {
      "total_connections": 25
    }
  }
}
```

### Performance Benchmarks

**Expected Performance:**

| Metric | Target | Threshold |
|--------|--------|-----------|
| API P95 Latency | < 200ms | Alert if > 500ms |
| API P99 Latency | < 500ms | Alert if > 1000ms |
| Throughput | > 16 req/s | Alert if < 10 req/s |
| Error Rate | < 1% | Alert if > 5% |
| DB Query Avg | < 50ms | Alert if > 100ms |
| WS Connections | 100+ supported | Alert if > 1000 |
| Circuit Breaker Opens | < 1/hour | Alert if > 5/hour |

### Performance Testing

Run performance tests:

```bash
cd /home/cytrex/news-microservices/services/analytics-service

# Run all performance tests
pytest tests/test_performance.py -v -s

# Run specific test
pytest tests/test_performance.py::test_api_load_overview_endpoint -v -s
```

### Monitoring Endpoints

1. **Circuit Breakers:**
   ```bash
   GET /api/v1/monitoring/circuit-breakers
   ```

2. **Query Performance:**
   ```bash
   GET /api/v1/monitoring/query-performance
   ```

3. **WebSocket Stats:**
   ```bash
   GET /api/v1/monitoring/websocket
   ```

4. **System Health:**
   ```bash
   GET /api/v1/monitoring/health
   ```

---

## Common Error Messages

### "Circuit breaker open for {service}"

**Meaning:** Service has failed repeatedly, requests blocked temporarily

**Solution:** Check service health, wait for automatic recovery (60s)

### "Slow query detected: duration {X}ms"

**Meaning:** Database query took longer than threshold (100ms)

**Solution:** Check query performance monitoring, apply recommended indexes

### "websocket_auth_failed"

**Meaning:** JWT token invalid or expired

**Solution:** Obtain fresh token from Auth Service

### "QueuePool limit reached"

**Meaning:** Database connection pool exhausted

**Solution:** Increase pool size or fix connection leaks

### "Service health check failed: HTTP {status}"

**Meaning:** External service returned error status

**Solution:** Check external service logs and health

---

## Getting Help

### Logs

```bash
# View recent logs
docker compose logs analytics-service --tail=100 --follow

# Search for errors
docker compose logs analytics-service | grep -i error

# Search for specific issue
docker compose logs analytics-service | grep -i "circuit\|slow\|websocket"
```

### Debug Mode

Enable debug logging:

```yaml
# docker-compose.yml
services:
  analytics-service:
    environment:
      - LOG_LEVEL=DEBUG
```

Restart service:

```bash
docker compose restart analytics-service
```

### Support Checklist

When reporting issues, provide:

1. **System health:** Output of `/api/v1/monitoring/health`
2. **Recent logs:** Last 100 lines of service logs
3. **Performance stats:** Query and circuit breaker metrics
4. **Steps to reproduce:** What you were doing when issue occurred
5. **Error messages:** Full error text or screenshots

---

## Maintenance

### Reset Query Statistics

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  http://localhost:8007/api/v1/monitoring/query-performance/reset
```

### Clean Old Metrics

Metrics older than 90 days are automatically cleaned up. To manually trigger cleanup:

```bash
docker compose exec analytics-service python -c "
from app.services.metrics_service import MetricsService
from app.core.database import SessionLocal

db = SessionLocal()
service = MetricsService(db)
deleted = await service.cleanup_old_metrics()
print(f'Deleted {deleted} old metrics')
"
```

### Restart Service

```bash
# Graceful restart
docker compose restart analytics-service

# Full rebuild (after code changes)
docker compose up -d --build analytics-service
```

---

## Performance Optimization Checklist

- [ ] Database indexes applied for frequent queries
- [ ] Connection pool sized appropriately
- [ ] Redis caching enabled
- [ ] Circuit breakers configured for all external services
- [ ] WebSocket reconnection logic implemented
- [ ] Query monitoring enabled
- [ ] Performance tests passing
- [ ] Alert thresholds configured
- [ ] Log aggregation set up
- [ ] Backup and restore tested

---

**Last Updated:** 2025-11-24
**Version:** 1.0.0
