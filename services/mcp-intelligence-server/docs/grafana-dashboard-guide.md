# Grafana Dashboard Guide - MCP Intelligence Server

## Overview

Comprehensive production monitoring dashboard for the MCP Intelligence Server, covering:
- **Tool Metrics**: Call rates, durations, and distribution
- **Cache Performance**: Hit ratios, latency, and errors
- **HTTP Client Metrics**: Requests, errors, and timeouts to backend services
- **Circuit Breaker Monitoring**: States, failures, and rejections
- **Service Health**: Overall health and Redis connectivity

## Access

**URL:** http://localhost:3002

**Credentials:**
- Username: `admin`
- Password: `admin` (default Grafana installation)

**Dashboard Location:** `Services` folder → `MCP Intelligence Server - Production Monitoring`

---

## Dashboard Sections

### 1. Overview (Top Row)

**Service Health Status**
- Shows if MCP Intelligence Server is running
- Green = HEALTHY, Red = UNHEALTHY

**Redis Connection Status**
- Shows Redis cache connectivity
- Green = CONNECTED, Red = DISCONNECTED

**Open Circuit Breakers**
- Number of circuit breakers currently in OPEN state
- 0 = All healthy (green), ≥1 = Services failing (red)

**Tool Calls (Last Hour)**
- Total number of MCP tool calls in the last hour
- Blue = Low, Green = Normal, Yellow = High load

**Cache Hit Ratio**
- Percentage of requests served from cache
- Red <50%, Yellow 50-70%, Green >70%

### 2. Tool Metrics

**Tool Call Rate (per minute)**
- Real-time rate of tool calls by tool name
- Use to identify:
  - Most frequently used tools
  - Traffic patterns
  - Load spikes

**Tool Duration (95th percentile)**
- 95th percentile response time by tool
- Thresholds:
  - Green: <1s (excellent)
  - Yellow: 1-3s (acceptable)
  - Red: >3s (slow, needs investigation)

**Tool Calls by Tool (Top 10)**
- Table showing most called tools in last hour
- Use for:
  - Usage analysis
  - Cache strategy optimization
  - Performance prioritization

### 3. Cache Metrics

**Cache Performance**
- Stacked area chart showing hits vs misses
- Green area = Cache hits (good)
- Orange area = Cache misses (backend calls)
- Goal: More green than orange

**Cache Latency**
- Shows p50, p95, p99 latency for cache operations
- Should be <50ms for all operations
- Spike indicates Redis performance issue

**Cache Keys Count**
- Number of keys currently in cache
- Increases gradually as cache warms up
- Drops indicate cache invalidation or restart

**Cache Errors**
- Bar chart of cache errors by type
- Should be 0 under normal operation
- Spikes indicate Redis connectivity issues

### 4. HTTP Client Metrics

**HTTP Requests by Service**
- Request rate to each backend service
- Use to identify:
  - Service dependencies
  - Cache effectiveness
  - Load distribution

**HTTP Request Duration (p95)**
- 95th percentile latency to backend services
- Thresholds:
  - Green: <1s
  - Yellow: 1-5s
  - Red: >5s

**HTTP Errors by Service**
- Error rate by service and status code
- Common codes:
  - 404: Resource not found
  - 500: Backend server error
  - 503: Service unavailable (circuit breaker may open)

**HTTP Timeouts**
- Timeout rate by service
- Indicates:
  - Backend service slowness
  - Network issues
  - Need for timeout adjustment

### 5. Circuit Breaker Metrics

**Circuit Breaker States**
- Real-time state of all circuit breakers
- States:
  - 0 = CLOSED (green): Normal operation
  - 1 = HALF_OPEN (yellow): Testing recovery
  - 2 = OPEN (red): Service failing, requests rejected

**Circuit Breaker Failures**
- Failure rate per circuit breaker
- Thresholds:
  - Green: <5 failures/min
  - Yellow: 5-10 failures/min
  - Red: >10 failures/min

**Circuit Breaker Rejections**
- Requests rejected due to open circuits
- Indicates backend service unavailability
- Prevents cascading failures

### 6. Redis Operations

**Redis Operations**
- Operations by type (get, set, delete) and status
- All operations should show "success" status
- Failures indicate connectivity issues

---

## Dashboard Features

### Variables (Top of Dashboard)

**Tool Filter**
- Select specific tools to focus on
- Multi-select enabled
- "All" shows all tools

**Service Filter**
- Filter HTTP metrics by backend service
- Multi-select enabled
- "All" shows all services

### Annotations

**Circuit Opened (Red)**
- Automatic annotation when circuit breaker opens
- Shows which circuit and when
- Click to see context

**Cache Errors (Orange)**
- Automatic annotation when >10 cache errors/min
- Indicates Redis issues
- Click to see error types

### Time Range

**Default:** Last 1 hour
**Options:** 5m, 15m, 1h, 6h, 12h, 24h, 2d, 7d

**Refresh Rate:** 10 seconds (auto-refresh)

---

## Common Scenarios

### Scenario 1: High Load

**Symptoms:**
- Tool call rate increases significantly
- Cache hit ratio may drop
- HTTP request duration increases

**Actions:**
1. Check "Tool Call Rate" panel - which tools are being called?
2. Check "Cache Hit Ratio" - is cache warming up?
3. Check "Circuit Breaker States" - are circuits opening?
4. Check k6 load test results for performance baseline

### Scenario 2: Backend Service Down

**Symptoms:**
- Circuit breaker opens (state = 2)
- HTTP errors increase for specific service
- HTTP timeouts spike

**Actions:**
1. Identify affected service in "Circuit Breaker States"
2. Check "HTTP Errors by Service" for status codes
3. Check backend service logs: `docker logs <service-name>`
4. Wait for circuit breaker recovery (60s default)

### Scenario 3: Cache Issues

**Symptoms:**
- Cache hit ratio drops below 50%
- Cache errors increase
- "Redis Connection Status" shows DISCONNECTED

**Actions:**
1. Check Redis container: `docker ps | grep redis`
2. Check Redis logs: `docker logs news-redis`
3. Verify cache keys: `curl http://localhost:9001/metrics | grep cache`
4. Restart Redis if needed: `docker compose restart redis`

### Scenario 4: Slow Tool Performance

**Symptoms:**
- Tool duration p95 >3s (red threshold)
- HTTP request duration increases
- Users report slow responses

**Actions:**
1. Identify slow tool in "Tool Duration" panel
2. Check if cached in `app/cache.py` - add caching if not
3. Check backend service response time in "HTTP Request Duration"
4. Run stress test to find bottleneck: `docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/stress.js`

### Scenario 5: Memory Leak Detection

**Symptoms:**
- Process memory increases steadily
- Cache keys count grows unbounded
- Eventually service crashes

**Actions:**
1. Check "Cache Keys Count" - should stabilize
2. Check process memory in container: `docker stats mcp-intelligence-server`
3. Check TTL settings in `app/cache.py`
4. Review cache invalidation logic

---

## Alerting (Future Enhancement)

**Recommended Alerts:**

1. **Circuit Breaker Opened**
   - Condition: `circuit_breaker_state == 2`
   - Severity: Warning
   - Action: Check backend service health

2. **High Error Rate**
   - Condition: `rate(http_request_errors_total[5m]) > 10`
   - Severity: Critical
   - Action: Investigate backend services

3. **Low Cache Hit Ratio**
   - Condition: Cache hit ratio <30% for >5min
   - Severity: Warning
   - Action: Review cache strategy

4. **Redis Disconnected**
   - Condition: `redis_connected == 0`
   - Severity: Critical
   - Action: Restart Redis container

---

## Integration with k6 Load Tests

### Before Running Load Tests

1. Open dashboard: http://localhost:3002
2. Set time range to "Last 15 minutes"
3. Enable auto-refresh (10s)
4. Note baseline metrics:
   - Tool call rate: ~0 (no load)
   - Cache hit ratio: N/A (cache empty)
   - Circuit breaker states: All CLOSED

### During Load Tests

**Smoke Test** (1 min, 1-2 VUs):
- Tool call rate: ~5-10 req/min
- Cache warming up (hit ratio increases)
- All circuit breakers should stay CLOSED

**Load Test** (5 min, 10-50 VUs):
- Tool call rate: ~50-100 req/min
- Cache hit ratio should reach >50%
- Circuit breakers should stay CLOSED
- HTTP latency stable

**Stress Test** (10 min, 10-200 VUs):
- Tool call rate: ~100-500+ req/min
- Circuit breakers may open under extreme load
- Monitor for graceful degradation
- Check rejection rates

**Spike Test** (5 min, 10→300→10 VUs):
- Sudden traffic burst to 1000+ req/min
- Circuit breakers should activate
- Recovery after spike should be fast (<2s avg)

### After Load Tests

1. Check "Circuit Breaker Performance Impact" panel
2. Review "Tool Duration" trends
3. Analyze cache effectiveness
4. Export results for documentation

---

## Prometheus Query Examples

Useful queries for custom panels or debugging:

```promql
# Cache hit ratio
sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100

# Top 5 slowest tools
topk(5, histogram_quantile(0.95, rate(mcp_tool_duration_seconds_bucket[5m])))

# Circuit breaker failure ratio
(sum by (name) (rate(circuit_breaker_failures_total[5m]))) / (sum by (name) (rate(circuit_breaker_failures_total[5m]) + rate(circuit_breaker_successes_total[5m]))) * 100

# HTTP error rate by service
sum by (service) (rate(http_request_errors_total[5m])) / sum by (service) (rate(http_requests_total[5m])) * 100

# Redis operations success rate
sum(rate(redis_operations_total{status="success"}[5m])) / sum(rate(redis_operations_total[5m])) * 100
```

---

## Troubleshooting

### Dashboard Not Showing Data

**Problem:** All panels show "No data"

**Solutions:**
1. Check Prometheus is running: `docker ps | grep prometheus`
2. Check MCP server is exposing metrics: `curl http://localhost:9001/metrics`
3. Verify Prometheus scraping: http://localhost:9090/targets
4. Check Grafana datasource: Settings → Data Sources → Prometheus

### Panels Show Errors

**Problem:** "Error executing query" in panels

**Solutions:**
1. Check Prometheus URL in datasource: http://prometheus:9090
2. Verify metric names match (case-sensitive)
3. Test query in Prometheus UI: http://localhost:9090
4. Check Grafana logs: `docker logs grafana`

### Dashboard Not Loading

**Problem:** Dashboard doesn't appear in Grafana

**Solutions:**
1. Check file exists: `/home/cytrex/news-microservices/monitoring/grafana/dashboards/mcp-intelligence-server.json`
2. Verify provisioning config: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
3. Restart Grafana: `docker compose restart grafana`
4. Check Grafana logs for provisioning errors

---

## Maintenance

### Regular Tasks

**Daily:**
- Check for open circuit breakers
- Review cache hit ratio trends
- Monitor error rates

**Weekly:**
- Review tool duration trends
- Analyze cache effectiveness
- Check for memory leaks (process memory, cache keys)

**Monthly:**
- Review dashboard layout and metrics
- Add new panels for new features
- Update alert thresholds based on traffic patterns

### Dashboard Updates

**Location:** `/home/cytrex/news-microservices/monitoring/grafana/dashboards/mcp-intelligence-server.json`

**After Updates:**
1. Edit JSON file
2. Restart Grafana: `docker compose restart grafana`
3. Verify changes in UI
4. Update this documentation

---

## Related Documentation

- [k6 Load Testing Guide](../k6-tests/README.md)
- [Circuit Breaker Dashboard](../../../docs/guides/grafana-circuit-breaker-dashboard.md)
- [Prometheus Metrics Reference](../app/metrics.py)
- [Cache Implementation](../app/cache.py)
- [Circuit Breaker Implementation](../app/resilience/http_circuit_breaker.py)

---

**Last Updated:** 2025-12-04
**Maintainer:** MCP Intelligence Server Team
**Version:** 1.0.0
