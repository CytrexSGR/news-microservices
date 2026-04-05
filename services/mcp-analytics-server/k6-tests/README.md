# k6 Load Testing - MCP Intelligence Server

Comprehensive load testing suite for the MCP Intelligence Server using k6.

## Overview

This test suite validates:
- ✅ **Performance** under various load conditions
- ✅ **Cache effectiveness** (Redis caching)
- ✅ **Circuit breaker behavior** (ResilientHTTPClient)
- ✅ **Resilience** during failures and recovery
- ✅ **Scalability** limits and breaking points

## Performance Baseline

**📊 Complete Performance Analysis:** [docs/performance-baseline.md](../docs/performance-baseline.md)

**Baseline Results (2025-12-04):**
- ✅ **Normal Load (50 VUs):** 1.09ms avg latency, 0.48% error rate
- ⚠️ **Breaking Point:** 200 VUs (1% error rate, 1.73ms avg latency)
- 🔴 **Overload (300 VUs):** 100% error rate during spike, circuit breaker protected
- ✅ **Circuit Breaker:** Prevented backend overload, enabled fast recovery

**Production Recommendations:**
- **Safe Operating Range:** 0-50 VUs (<2ms P95 latency, <0.5% errors)
- **Monitor Closely:** 50-150 VUs (scale if sustained)
- **Scale Trigger:** >100 VUs sustained or P95 >5ms
- **Do Not Exceed:** 200 VUs (breaking point reached)

## Test Scenarios

### 1. Smoke Test (`smoke.js`)
**Purpose:** Verify basic functionality with minimal load

- **Duration:** 1 minute
- **VUs:** 1-2
- **RPS:** ~5-10
- **Tests:** Health checks, tool calls, metrics endpoint

**Run:**
```bash
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/smoke.js
```

### 2. Load Test (`load.js`)
**Purpose:** Test under normal expected load

- **Duration:** 5 minutes
- **VUs:** 10-50
- **RPS:** ~50-100
- **Tests:** Cache effectiveness, sustained performance, circuit breaker behavior

**Run:**
```bash
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/load.js
```

### 3. Stress Test (`stress.js`)
**Purpose:** Find system limits and breaking point

- **Duration:** 10 minutes
- **VUs:** 10-200
- **RPS:** ~100-500+
- **Tests:** Extreme load, error rates, circuit breaker activation

**Run:**
```bash
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/stress.js
```

### 4. Spike Test (`spike.js`)
**Purpose:** Test sudden traffic spikes and recovery

- **Duration:** 5 minutes
- **VUs:** 10 → 300 → 10
- **RPS:** ~50 → ~1000+ → ~50
- **Tests:** Spike handling, circuit breaker fast-fail, recovery time

**Run:**
```bash
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/spike.js
```

## Running Tests

### Prerequisites
- Docker installed
- MCP Intelligence Server running on `localhost:9001`
- Backend services available (intelligence-service, narrative-service, etc.)

### Quick Start

1. **Ensure services are running:**
```bash
docker compose up -d
docker ps | grep mcp-intelligence
```

2. **Navigate to tests directory:**
```bash
cd /home/cytrex/news-microservices/services/mcp-intelligence-server
```

3. **Run tests:**
```bash
# Smoke test (quick validation)
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/smoke.js

# Load test (normal load)
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/load.js

# Stress test (find limits)
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/stress.js

# Spike test (burst handling)
docker run --rm --network host -v $(pwd)/k6-tests:/tests grafana/k6 run /tests/spike.js
```

### Custom Configuration

Override the base URL:
```bash
docker run --rm --network host \
  -e BASE_URL=http://localhost:9001 \
  -v $(pwd)/k6-tests:/tests \
  grafana/k6 run /tests/load.js
```

## Interpreting Results

### Success Criteria

**Smoke Test:**
- ✅ All checks pass
- ✅ p95 < 2s
- ✅ Failure rate < 1%

**Load Test:**
- ✅ p95 < 3s, p99 < 5s
- ✅ Failure rate < 5%
- ✅ Cache hit ratio > 50%
- ✅ RPS > 10

**Stress Test:**
- ✅ p95 < 5s, p99 < 10s
- ✅ Failure rate < 10%
- ✅ Circuit breaker activates under extreme load
- ✅ RPS > 20

**Spike Test:**
- ✅ p95 < 8s during spike
- ✅ Failure rate < 15% during spike
- ✅ Fast recovery after spike (<2s avg)

### Metrics to Monitor

1. **Response Times**
   - avg, p50, p95, p99, max
   - Should remain stable under load

2. **Error Rates**
   - http_req_failed
   - Should stay below thresholds

3. **Cache Performance**
   - cache_hit_ratio
   - Should be >50% for cacheable tools

4. **Circuit Breaker**
   - circuit_breaker_trips
   - Should activate under extreme load
   - Should prevent cascading failures

5. **Throughput**
   - http_reqs rate
   - Should meet minimum RPS targets

## Grafana Dashboard

**Real-time monitoring:** http://localhost:3002

Navigate to: `Services` → `MCP Intelligence Server - Production Monitoring`

**Monitor during tests:**
- Tool call rates and duration
- Cache hit ratios
- Circuit breaker states
- HTTP request performance
- Service health

**Full guide:** [docs/grafana-dashboard-guide.md](../docs/grafana-dashboard-guide.md)

## Prometheus Metrics

During tests, monitor these metrics at `http://localhost:9001/metrics`:

```bash
# Cache metrics
cache_hits_total
cache_misses_total
cache_operation_duration_seconds

# Circuit breaker metrics
circuit_breaker_state
circuit_breaker_failures_total
circuit_breaker_successes_total
circuit_breaker_rejections_total

# HTTP metrics
http_requests_total
http_request_duration_seconds
http_request_errors_total
http_request_timeouts_total

# Tool metrics
mcp_tool_calls_total
mcp_tool_duration_seconds
```

## Analyzing Results

### 1. Check Test Output
Tests output JSON summaries with key metrics.

### 2. Monitor Prometheus
```bash
curl http://localhost:9001/metrics | grep -E "(cache_|circuit_breaker_|http_request)"
```

### 3. Check Service Logs
```bash
docker logs mcp-intelligence-server --tail 100
```

### 4. Look for Patterns
- **Cache warming:** First requests slow, subsequent fast
- **Circuit breaker:** 503 errors when backend fails
- **Resource exhaustion:** Increasing response times
- **Recovery:** Return to baseline after spike

## Troubleshooting

### High Failure Rates
- Check backend service health
- Verify circuit breaker thresholds
- Monitor resource usage (CPU, memory)

### Slow Response Times
- Check cache hit ratio
- Monitor backend service latency
- Check database query performance

### Circuit Breaker Issues
- Verify failure thresholds (default: 5 failures)
- Check timeout settings (default: 60s recovery)
- Monitor backend service availability

## Test Development

### Adding New Tests
1. Copy existing test as template
2. Modify stages and thresholds
3. Add custom metrics if needed
4. Document in this README

### Tool Coverage
Current tests cover all 12 MCP tools:
- Intelligence: 4 tools
- Narrative: 4 tools
- Entity: 2 tools
- OSINT: 2 tools

### Best Practices
- Start with smoke test
- Run load test for baseline
- Use stress test to find limits
- Use spike test for resilience

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run k6 Smoke Test
  run: |
    docker compose up -d
    docker run --rm --network host \
      -v $(pwd)/k6-tests:/tests \
      grafana/k6 run /tests/smoke.js
```

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Thresholds](https://k6.io/docs/using-k6/thresholds/)
- [k6 Metrics](https://k6.io/docs/using-k6/metrics/)
- [Circuit Breaker Pattern](../../docs/decisions/ADR-035-circuit-breaker-pattern.md)

---

**Last Updated:** 2025-12-04
**Maintainer:** MCP Intelligence Server Team
