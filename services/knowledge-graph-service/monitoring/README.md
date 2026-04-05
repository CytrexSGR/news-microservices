# FMP-KG Integration Monitoring

**Service:** Knowledge-Graph Service (FMP Integration)
**Component:** Observability & Monitoring
**Created:** 2025-11-16 (Sprint 4)

---

## Overview

This directory contains monitoring and observability components for the FMP Service → Knowledge-Graph Service → Neo4j integration.

**Components:**
- ✅ Prometheus metrics implementation
- ✅ Grafana dashboard configuration
- ✅ Prometheus alert rules
- ✅ Structured logging configuration
- ✅ Health check endpoints

---

## Files

```
monitoring/
├── README.md                        # This file
├── grafana_dashboard_fmp_kg.json   # Grafana dashboard (import ready)
├── prometheus_alerts.yml           # Prometheus AlertManager rules
└── (Python modules in ../app/)
    ├── app/monitoring/
    │   ├── __init__.py              # Package init
    │   └── metrics.py               # Prometheus metrics definitions
    ├── app/core/
    │   └── logging_config.py        # Structured JSON logging
    └── app/api/routes/
        └── health.py                # Health checks + /metrics endpoint
```

---

## Quick Start

### 1. Import Grafana Dashboard

```bash
# Option A: Via Grafana UI
1. Open Grafana: http://localhost:3000
2. Navigate to: Dashboards → Import
3. Upload: monitoring/grafana_dashboard_fmp_kg.json
4. Select Prometheus datasource
5. Click "Import"

# Option B: Via API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-key>" \
  -d @monitoring/grafana_dashboard_fmp_kg.json
```

**Dashboard URL:** `http://localhost:3000/d/fmp-kg-integration`

### 2. Configure Prometheus Alerts

```bash
# Copy alert rules to Prometheus
cp monitoring/prometheus_alerts.yml /etc/prometheus/rules/

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Or restart Prometheus
docker restart prometheus
```

### 3. Verify Metrics Endpoint

```bash
# Check metrics are being exposed
curl http://localhost:8111/health/metrics

# Expected output (sample):
# TYPE fmp_sync_requests_total counter
# fmp_sync_requests_total{status="success",asset_type="all"} 42
# ...
```

### 4. Enable Structured Logging

```python
# In app startup (main.py or __init__.py)
from app.core.logging_config import setup_logging

# Configure logging
setup_logging(
    level="INFO",              # or from env: settings.LOG_LEVEL
    service_name="knowledge-graph-service",
    json_format=True           # False for local development
)
```

**Environment Variables:**
```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json or text
SERVICE_NAME=knowledge-graph-service
```

---

## Metrics Reference

### Core Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `fmp_sync_requests_total` | Counter | `status`, `asset_type` | Total sync requests by status |
| `fmp_sync_duration_seconds` | Histogram | `asset_type` | Sync operation duration |
| `fmp_markets_total` | Gauge | `asset_type` | Total markets in Neo4j |
| `fmp_active_markets` | Gauge | `asset_type` | Active markets count |
| `neo4j_query_errors_total` | Counter | `query_type`, `error_type` | Neo4j query errors |
| `neo4j_query_duration_seconds` | Histogram | `query_type` | Neo4j query duration |
| `circuit_breaker_state` | Gauge | `service` | Circuit breaker state (0/1/2) |

### Usage Examples

**In Market Sync Service:**
```python
from app.monitoring import record_sync_request, record_sync_duration

# Record sync request outcome
record_sync_request(status="success", asset_type="STOCK")

# Track sync duration
with record_sync_duration(asset_type="STOCK"):
    # Perform sync operation
    pass
```

**In Neo4j Service:**
```python
from app.monitoring import record_neo4j_query

# Track query performance
with record_neo4j_query("merge_market"):
    result = await neo4j.execute_query(query, params)
```

**Circuit Breaker State:**
```python
from app.monitoring import update_circuit_breaker_state

# Update state
update_circuit_breaker_state(
    service="fmp_service",
    state="open"  # closed, open, half_open
)
```

---

## Dashboard Panels

### Panel 1: Market Sync Success Rate (7d)
- **Type:** Gauge
- **Query:** `sum(rate(fmp_sync_requests_total{status="success"}[7d])) / sum(rate(fmp_sync_requests_total[7d])) * 100`
- **Thresholds:** Red < 95%, Yellow 95-99%, Green > 99%
- **SLO:** 95%+ success rate

### Panel 2: Average Sync Duration
- **Type:** Time Series
- **Queries:** P50, P95, P99 percentiles
- **SLO:** P95 < 200ms

### Panel 3: Market Counts
- **Type:** Stat
- **Metrics:** Total markets, Active markets
- **Expected:** 40 total, 40 active (for default setup)

### Panel 4: Active vs Inactive Markets by Asset Type
- **Type:** Time Series (Bars)
- **Breakdown:** STOCK, FOREX, COMMODITY, CRYPTO

### Panel 5: Circuit Breaker Status
- **Type:** Gauge
- **Mapping:** 0=Closed (Green), 1=Open (Red), 2=Half-Open (Yellow)
- **Services:** fmp_service, neo4j

### Panel 6: Neo4j Query Performance
- **Type:** Time Series
- **Query:** P95 latency by query_type
- **SLO:** P95 < 5ms (indexed queries)

### Panel 7: Error Rate by Type
- **Type:** Time Series
- **Metrics:** Neo4j errors, FMP sync failures

---

## Alert Rules

### Critical Alerts (Immediate Response)

| Alert | Trigger | Impact | Runbook |
|-------|---------|--------|---------|
| `CircuitBreakerOpen` | state=open for 1min | Service degraded | [troubleshooting.md#circuit-breaker-open](../../docs/operations/fmp-kg-troubleshooting.md) |
| `FMPSyncAvailabilityLow` | < 99.5% for 5min | SLO violation | [troubleshooting.md#sync-availability](../../docs/operations/fmp-kg-troubleshooting.md) |

### Warning Alerts (15-30min Response)

| Alert | Trigger | Impact | Runbook |
|-------|---------|--------|---------|
| `FMPSyncLatencyHigh` | P95 > 200ms for 10min | Performance degraded | [troubleshooting.md#high-latency](../../docs/operations/fmp-kg-troubleshooting.md) |
| `Neo4jQueryLatencyHigh` | P95 > 5ms for 5min | Query optimization needed | [troubleshooting.md#neo4j-slow](../../docs/operations/fmp-kg-troubleshooting.md) |
| `Neo4jQueryErrorRateHigh` | > 1% for 5min | Data integrity risk | [troubleshooting.md#neo4j-errors](../../docs/operations/fmp-kg-troubleshooting.md) |
| `FMPSyncFailureRateHigh` | > 5% for 10min | Data freshness risk | [troubleshooting.md#sync-failures](../../docs/operations/fmp-kg-troubleshooting.md) |
| `MarketDataStale` | No sync in 1h | Data outdated | [troubleshooting.md#stale-data](../../docs/operations/fmp-kg-troubleshooting.md) |

---

## Structured Logging

### Log Format (JSON)

```json
{
  "timestamp": "2025-11-16T10:30:00.123Z",
  "level": "INFO",
  "service": "knowledge-graph-service",
  "logger": "app.services.market_sync_service",
  "message": "Sync operation: sync_markets",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "operation": "sync_markets",
  "status": "success",
  "asset_type": "STOCK",
  "symbols_count": 40,
  "duration_ms": 2345.67
}
```

### Usage Examples

**Basic Logging:**
```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Market sync completed")
```

**With Correlation ID:**
```python
from app.core.logging_config import set_correlation_id, get_logger

# Set correlation ID (typically in middleware)
correlation_id = set_correlation_id()  # Auto-generates UUID

logger = get_logger(__name__)
logger.info("Processing request")  # Includes correlation_id
```

**Sync Operation Logging:**
```python
from app.core.logging_config import log_sync_operation

log_sync_operation(
    logger=logger,
    operation="sync_markets",
    asset_type="STOCK",
    symbols_count=40,
    duration_ms=2345.67,
    status="success"
)
```

**Neo4j Query Logging:**
```python
from app.core.logging_config import log_neo4j_query

log_neo4j_query(
    logger=logger,
    query_type="merge_market",
    duration_ms=3.45
)
```

### Log Analysis (jq)

```bash
# Filter by correlation ID
cat logs.json | jq 'select(.correlation_id == "550e8400-...")'

# Find slow operations (> 1s)
cat logs.json | jq 'select(.duration_ms > 1000)'

# Count errors by type
cat logs.json | jq -r 'select(.level == "ERROR") | .error' | sort | uniq -c
```

---

## Health Checks

### Endpoints

| Endpoint | Purpose | K8s Probe |
|----------|---------|-----------|
| `GET /health/live` | Service alive | Liveness |
| `GET /health/ready` | Dependencies ready | Readiness |
| `GET /health/metrics` | Prometheus metrics | - |
| `GET /health` | Detailed health | - |

### Kubernetes Configuration

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8111
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8111
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Example Responses

**Liveness (200 OK):**
```json
{
  "status": "alive",
  "timestamp": "2025-11-16T10:30:00Z",
  "service": "knowledge-graph-service"
}
```

**Readiness (200 OK / 503 Service Unavailable):**
```json
{
  "status": "ready",
  "timestamp": "2025-11-16T10:30:00Z",
  "service": "knowledge-graph-service",
  "checks": {
    "neo4j": "healthy",
    "fmp_service": "healthy"
  }
}
```

**Health (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-16T10:30:00Z",
  "service": "knowledge-graph-service",
  "version": "1.0.0",
  "checks": {
    "neo4j": {
      "status": "healthy",
      "response_time_ms": 2.34
    },
    "fmp_service": {
      "status": "not_configured",
      "message": "FMP Service health check not yet implemented"
    }
  },
  "response_time_ms": 5.67
}
```

---

## SLI/SLO Reference

**Full Documentation:** [docs/operations/fmp-kg-sli-slo.md](../../docs/operations/fmp-kg-sli-slo.md)

### Quick Reference

| SLI | Target | Measurement | Alert Threshold |
|-----|--------|-------------|-----------------|
| Availability | 99.5% | Rolling 1h | < 99.5% for 5min |
| Latency (P95) | < 200ms | Rolling 5min | > 200ms for 10min |
| Neo4j Latency (P95) | < 5ms | Rolling 5min | > 5ms for 5min |
| Error Rate | < 1% | Rolling 5min | > 1% for 5min |
| Sync Success Rate | > 95% | Rolling 15min | < 95% for 10min |

---

## Troubleshooting

### No Metrics Showing in Grafana

**Check:**
1. Prometheus scraping endpoint: `http://localhost:8111/health/metrics`
2. Prometheus targets: `http://localhost:9090/targets`
3. Verify service is registered in Prometheus `prometheus.yml`:
   ```yaml
   scrape_configs:
     - job_name: 'knowledge-graph-service'
       static_configs:
         - targets: ['knowledge-graph-service:8111']
   ```

### Alerts Not Firing

**Check:**
1. Alert rules loaded: `http://localhost:9090/alerts`
2. Alert evaluation: Check "State" column
3. AlertManager configured: `http://localhost:9093`

### High Cardinality Metrics

**Symptom:** Prometheus performance degraded

**Solution:** Limit label values
- ❌ Bad: `{symbol="AAPL"}` (100+ values)
- ✅ Good: `{asset_type="STOCK"}` (4 values)

**Current Cardinality:**
- `status`: 3 values (success, failed, partial)
- `asset_type`: 5 values (all, STOCK, FOREX, COMMODITY, CRYPTO)
- `service`: 2 values (fmp_service, neo4j)
- Total: < 50 unique time series ✅

---

## Performance Impact

**Metrics Collection:**
- Overhead: < 1ms per request
- Memory: ~2MB (for 10K time series)
- CPU: < 0.1%

**Logging:**
- JSON encoding: ~0.5ms per log entry
- Disk I/O: Async (non-blocking)

**Health Checks:**
- Liveness: < 1ms (no I/O)
- Readiness: < 10ms (includes Neo4j ping)

---

## Next Steps

1. **Deploy Monitoring Stack:** Prometheus + Grafana containers
2. **Import Dashboard:** Upload `grafana_dashboard_fmp_kg.json`
3. **Configure Alerts:** Copy `prometheus_alerts.yml` to Prometheus
4. **Enable Logging:** Set `LOG_FORMAT=json` in production
5. **Test Health Checks:** Verify K8s liveness/readiness probes

---

## References

- **SLI/SLO Documentation:** [docs/operations/fmp-kg-sli-slo.md](../../docs/operations/fmp-kg-sli-slo.md)
- **Troubleshooting Guide:** [docs/operations/fmp-kg-troubleshooting.md](../../docs/operations/fmp-kg-troubleshooting.md)
- **Operations Runbook:** [docs/operations/fmp-kg-runbook.md](../../docs/operations/fmp-kg-runbook.md)
- **Prometheus Docs:** https://prometheus.io/docs/
- **Grafana Docs:** https://grafana.com/docs/

---

**Created:** 2025-11-16 (Sprint 4)
**Maintainer:** Platform Engineering
**Last Updated:** 2025-11-16
