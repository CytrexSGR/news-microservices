# Grafana Circuit Breaker Dashboard Guide

**Task:** Task 406 - Circuit Breaker Pattern Implementation (Phase 5)
**Dashboard:** `/monitoring/grafana/dashboards/circuit-breaker-monitoring.json`
**Last Updated:** 2025-11-03

---

## Overview

This dashboard provides comprehensive monitoring for all circuit breakers across the news-microservices system. It visualizes circuit breaker states, failure rates, rejection patterns, and recovery behavior in real-time.

**Key Features:**
- Real-time circuit breaker state tracking
- Failure and success rate visualization
- Rejection rate monitoring
- State transition history
- Per-service circuit breaker isolation
- Automatic annotations for state changes

---

## Quick Start

### 1. Import Dashboard

```bash
# Method 1: Grafana UI
# 1. Open Grafana: http://localhost:3000
# 2. Navigate to: Dashboards → Import
# 3. Upload: /monitoring/grafana/dashboards/circuit-breaker-monitoring.json
# 4. Select datasource: Prometheus
# 5. Click "Import"

# Method 2: API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @/monitoring/grafana/dashboards/circuit-breaker-monitoring.json
```

### 2. Access Dashboard

**URL:** http://localhost:3000/d/circuit-breaker-monitoring

**Default View:**
- Time range: Last 1 hour
- Refresh interval: 10 seconds
- Auto-refresh: Enabled

---

## Dashboard Panels

### 1. Circuit Breaker States Overview

**Type:** Time Series
**Location:** Top, full width
**Description:** Shows current state of all circuit breakers over time

**States:**
- **0 (CLOSED)** - Green: Normal operation, all requests pass through
- **1 (OPEN)** - Red: Fail-fast mode, rejecting all requests
- **2 (HALF_OPEN)** - Yellow: Testing recovery with limited requests

**Query:**
```promql
circuit_breaker_state
```

**Interpretation:**
- **Flat green line (0):** Healthy, no issues
- **Spike to red (1):** Circuit opened due to failures
- **Brief yellow (2):** Testing recovery
- **Return to green (0):** Successfully recovered

**Alert Conditions:**
- Any circuit stays OPEN > 5 minutes → Investigate root cause
- Frequent transitions (>10/hour) → Service instability

### 2. Open Circuit Breakers (Current)

**Type:** Stat Panel
**Location:** Top row, left
**Description:** Number of circuit breakers currently in OPEN state

**Query:**
```promql
sum(circuit_breaker_state == 1)
```

**Thresholds:**
- **Green (0):** All circuits closed, system healthy
- **Red (≥1):** One or more circuits open, services degraded

**Action Required:**
- **0:** No action
- **1+:** Check affected services, investigate failures

### 3. Half-Open Circuit Breakers

**Type:** Stat Panel
**Location:** Top row, second from left
**Description:** Circuit breakers currently testing recovery

**Query:**
```promql
sum(circuit_breaker_state == 2)
```

**Thresholds:**
- **Green (0):** No recovery testing
- **Yellow (≥1):** Recovery in progress

**Interpretation:**
- Brief yellow → Normal recovery
- Stuck yellow → Recovery failing repeatedly

### 4. Total Rejections (Last Hour)

**Type:** Stat Panel
**Location:** Top row, third from left
**Description:** Requests rejected due to open circuits

**Query:**
```promql
sum(increase(circuit_breaker_rejections_total[1h]))
```

**Thresholds:**
- **Green (0-99):** Minimal rejections
- **Yellow (100-499):** Moderate impact
- **Red (≥500):** High rejection rate, significant service degradation

**Cost Impact:**
- High rejection rate = Many 503 errors to clients
- May need to scale up or fix underlying service

### 5. State Transitions (Last Hour)

**Type:** Stat Panel
**Location:** Top row, right
**Description:** Number of circuit breaker state changes

**Query:**
```promql
sum(increase(circuit_breaker_state_transitions_total[1h]))
```

**Thresholds:**
- **Green (0-9):** Stable system
- **Yellow (10-49):** Some instability
- **Red (≥50):** High instability, flapping circuits

**Interpretation:**
- **0 transitions:** Perfect stability
- **2-4 transitions:** Single outage with recovery
- **>20 transitions:** Circuit flapping, investigate threshold configuration

### 6. Failure Rate by Circuit Breaker

**Type:** Time Series
**Location:** Middle section, left
**Description:** Failures per minute for each circuit breaker

**Query:**
```promql
rate(circuit_breaker_failures_total[1m]) * 60
```

**Unit:** Requests per minute (reqpm)

**Thresholds:**
- **Green (0-4):** Acceptable failure rate
- **Yellow (5-9):** Elevated failures
- **Red (≥10):** High failure rate

**Analysis:**
- **LLM circuit breakers:** 5+ failures/min → OpenAI/Gemini issues
- **RabbitMQ circuit breakers:** 10+ failures/min → Broker connection issues
- **Database circuit breakers:** 5+ failures/min → PostgreSQL timeout/outage
- **HTTP circuit breakers:** 3+ failures/min → External API issues

### 7. Success Rate by Circuit Breaker

**Type:** Time Series
**Location:** Middle section, right
**Description:** Successful requests per minute

**Query:**
```promql
rate(circuit_breaker_successes_total[1m]) * 60
```

**Unit:** Requests per minute (reqpm)

**Interpretation:**
- High success rate → Healthy circuit
- Sudden drop to zero → Circuit opened
- Gradual increase from zero → Recovery in progress

### 8. Failure Ratio by Circuit Breaker

**Type:** Gauge
**Location:** Lower middle, left
**Description:** Percentage of failed requests (failures / total)

**Query:**
```promql
(sum by (name) (rate(circuit_breaker_failures_total[5m]))) /
(sum by (name) (rate(circuit_breaker_failures_total[5m]) +
rate(circuit_breaker_successes_total[5m]))) * 100
```

**Unit:** Percentage (%)
**Range:** 0-100%

**Thresholds:**
- **Green (0-5%):** Acceptable error rate
- **Yellow (5-20%):** Elevated errors
- **Red (>20%):** Critical error rate

**Target:** <5% failure ratio for all circuits

### 9. Rejection Rate by Circuit Breaker

**Type:** Time Series (Bars)
**Location:** Lower middle, right
**Description:** Requests rejected per minute due to open circuit

**Query:**
```promql
rate(circuit_breaker_rejections_total[1m]) * 60
```

**Unit:** Requests per minute (reqpm)

**Thresholds:**
- **Green (0-9):** Minimal rejections
- **Yellow (10-49):** Moderate impact
- **Red (≥50):** High rejection rate

**Business Impact:**
- Rejections = 503 errors to clients
- High rejection rate = Degraded user experience
- Track rejection patterns to identify problem services

### 10. State Transitions by Circuit Breaker

**Type:** Table
**Location:** Bottom section
**Description:** Circuit breaker state changes in last hour

**Query:**
```promql
sum by (name, from_state, to_state) (increase(circuit_breaker_state_transitions_total[1h]))
```

**Columns:**
- `name`: Circuit breaker name (e.g., "llm-openai")
- `from_state`: Previous state (CLOSED, OPEN, HALF_OPEN)
- `to_state`: New state
- `Value`: Number of transitions

**Sorting:** By value (descending)

**Common Patterns:**
- **CLOSED → OPEN:** Failure threshold exceeded
- **OPEN → HALF_OPEN:** Timeout elapsed, testing recovery
- **HALF_OPEN → CLOSED:** Recovery successful
- **HALF_OPEN → OPEN:** Recovery failed

### 11-14. Service-Specific Circuit Breakers

**Panels:**
- **Panel 11:** LLM Circuit Breakers (OpenAI, Gemini)
- **Panel 12:** RabbitMQ Circuit Breakers
- **Panel 13:** Database Circuit Breakers
- **Panel 14:** HTTP Circuit Breakers (Perplexity, Webhooks)

**Type:** Time Series
**Location:** Bottom section, 2×2 grid

**Filtering:**
```promql
# Panel 11: LLM
circuit_breaker_state{name=~"llm-.*"}

# Panel 12: RabbitMQ
circuit_breaker_state{name=~"rabbitmq-.*"}

# Panel 13: Database
circuit_breaker_state{name=~"database-.*"}

# Panel 14: HTTP
circuit_breaker_state{name=~"http-.*"}
```

**Use Case:** Isolate specific dependency types for focused monitoring

### 15. Circuit Breaker Performance Impact

**Type:** Stat Panel
**Location:** Bottom, full width
**Description:** Comparison of protected vs rejected requests

**Queries:**
```promql
# Protected Requests
sum(rate(circuit_breaker_successes_total[5m]))

# Rejected Requests
sum(rate(circuit_breaker_rejections_total[5m]))
```

**Unit:** Requests per second (reqps)

**Interpretation:**
- High protected requests → Circuit breaker working normally
- High rejected requests → Services degraded, circuits open

### 16. Recent Circuit Breaker Events

**Type:** Logs Panel
**Location:** Bottom
**Description:** Log messages for circuit breaker state transitions

**Queries:**
```promql
{service="content-analysis-v2"} |~ "Circuit breaker.*transitioned"
{service="feed-service"} |~ "Circuit breaker.*transitioned"
{service="research-service"} |~ "Circuit breaker.*transitioned"
```

**Log Format:**
```
[timestamp] INFO Circuit breaker 'llm-openai' transitioned to OPEN (5 failures)
[timestamp] INFO Circuit breaker 'llm-openai' transitioned to HALF_OPEN (timeout elapsed)
[timestamp] INFO Circuit breaker 'llm-openai' transitioned to CLOSED (recovered)
```

**Use Case:** Debug state transition reasons, correlate with incidents

---

## Annotations

**Automatic Annotations:** Circuit breaker state changes are automatically annotated on all time series panels.

### Circuit Opened (Red)

**Trigger:** Circuit transitions to OPEN state
**Query:**
```promql
changes(circuit_breaker_state{state="1"}[1m])
```

**Icon:** Red vertical line
**Tooltip:** Circuit breaker name + "OPEN"

### Circuit Closed (Green)

**Trigger:** Circuit transitions to CLOSED state
**Query:**
```promql
changes(circuit_breaker_state{state="0"}[1m])
```

**Icon:** Green vertical line
**Tooltip:** Circuit breaker name + "CLOSED"

---

## Variables & Filters

### Service Variable

**Name:** `$service`
**Type:** Query
**Datasource:** Prometheus
**Query:**
```promql
label_values(circuit_breaker_state, name)
```

**Options:**
- Multi-select: Yes
- Include all: Yes
- Refresh: On dashboard load

**Usage:** Filter all panels to show only selected circuit breakers

**Example:**
- Select "llm-openai" → Show only OpenAI circuit breaker
- Select "All" → Show all circuit breakers

---

## Alerting Rules

### Recommended Alerts

#### 1. Circuit Breaker Stuck Open

```yaml
alert: CircuitBreakerStuckOpen
expr: |
  circuit_breaker_state == 1
  and
  time() - circuit_breaker_last_failure_time > 300
for: 5m
labels:
  severity: warning
annotations:
  summary: "Circuit breaker {{ $labels.name }} stuck OPEN for 5+ minutes"
  description: "Circuit breaker has been OPEN for {{ $value }}s"
```

**Action:** Investigate underlying service, consider manual reset

#### 2. High Rejection Rate

```yaml
alert: HighCircuitBreakerRejectionRate
expr: |
  rate(circuit_breaker_rejections_total[5m]) * 60 > 50
for: 10m
labels:
  severity: critical
annotations:
  summary: "High rejection rate for {{ $labels.name }}"
  description: "{{ $value }} rejections/min"
```

**Action:** Scale up service or fix underlying issue

#### 3. Circuit Breaker Flapping

```yaml
alert: CircuitBreakerFlapping
expr: |
  increase(circuit_breaker_state_transitions_total[1h]) > 10
for: 15m
labels:
  severity: warning
annotations:
  summary: "Circuit breaker {{ $labels.name }} flapping"
  description: "{{ $value }} state transitions in last hour"
```

**Action:** Adjust circuit breaker thresholds or fix intermittent failures

#### 4. High Failure Rate

```yaml
alert: HighCircuitBreakerFailureRate
expr: |
  rate(circuit_breaker_failures_total[5m]) * 60 > 10
for: 10m
labels:
  severity: warning
annotations:
  summary: "High failure rate for {{ $labels.name }}"
  description: "{{ $value }} failures/min"
```

**Action:** Investigate service health, check logs

---

## Troubleshooting

### Dashboard Not Showing Data

**Problem:** All panels empty, no metrics

**Solutions:**

1. **Check Prometheus datasource:**
   ```bash
   curl http://localhost:9090/api/v1/query?query=circuit_breaker_state
   ```
   Expected: JSON with circuit breaker states

2. **Verify metrics endpoint:**
   ```bash
   curl http://localhost:8114/metrics | grep circuit_breaker
   ```
   Expected: Prometheus metrics

3. **Check Grafana datasource config:**
   - Grafana → Configuration → Data Sources → Prometheus
   - URL should be: http://prometheus:9090
   - Test & save

### No Circuit Breaker Metrics

**Problem:** `circuit_breaker_*` metrics not available

**Solutions:**

1. **Enable circuit breaker metrics:**
   ```python
   # In circuit breaker config
   CircuitBreakerConfig(
       enable_metrics=True,  # Must be True
   )
   ```

2. **Restart service:**
   ```bash
   docker compose restart content-analysis-v2
   ```

3. **Check service logs:**
   ```bash
   docker logs news-microservices-content-analysis-v2 | grep "Circuit breaker"
   ```

### Panels Show "No Data"

**Problem:** Some panels empty, others working

**Solutions:**

1. **Check metric names:**
   ```bash
   # List all circuit breaker metrics
   curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep circuit_breaker
   ```

2. **Verify circuit breaker names:**
   ```bash
   curl -s http://localhost:9090/api/v1/query?query=circuit_breaker_state | jq '.data.result[].metric.name'
   ```
   Expected: ["llm-openai", "llm-gemini", "rabbitmq-feed-events", ...]

3. **Check time range:** Ensure time range covers recent circuit breaker activity

### Incorrect State Values

**Problem:** States showing wrong colors or values

**Solutions:**

1. **Verify state encoding:**
   - CLOSED = 0 (green)
   - OPEN = 1 (red)
   - HALF_OPEN = 2 (yellow)

2. **Check metrics export:**
   ```python
   # In metrics.py
   circuit_breaker_state_gauge.labels(name="llm-openai").set(
       0 if state == CircuitBreakerState.CLOSED else
       1 if state == CircuitBreakerState.OPEN else
       2  # HALF_OPEN
   )
   ```

---

## Best Practices

### 1. Regular Monitoring

**Daily:**
- Check for open circuits (Panel 2)
- Review rejection rate (Panel 4)
- Verify no flapping (Panel 5)

**Weekly:**
- Analyze failure trends (Panel 6)
- Review state transitions (Panel 10)
- Adjust thresholds if needed

**Monthly:**
- Review circuit breaker effectiveness
- Optimize threshold configuration
- Plan capacity based on rejection patterns

### 2. Incident Response

**When Circuit Opens:**

1. **Check Panel 1:** Identify which circuit opened
2. **Check Panel 6:** Review failure rate before opening
3. **Check Panel 16:** Read log messages for context
4. **Investigate:** Check underlying service health
5. **Monitor Panel 3:** Watch for automatic recovery

**Example:**
```
1. Panel 1: "llm-openai" turned red (OPEN)
2. Panel 6: 15 failures/min before opening
3. Panel 16: "Circuit breaker 'llm-openai' transitioned to OPEN (5 failures)"
4. Action: Check OpenAI API status
5. Panel 3: Watch for HALF_OPEN state after 60s
```

### 3. Threshold Tuning

**If circuits open too frequently:**
- Increase `failure_threshold` (e.g., 5 → 10)
- Increase `timeout_seconds` (e.g., 60 → 120)

**If circuits don't open when they should:**
- Decrease `failure_threshold` (e.g., 5 → 3)
- Decrease `timeout_seconds` (e.g., 60 → 30)

**Monitor Panel 5 (State Transitions) after tuning:**
- Expect 0-5 transitions/hour in healthy system
- 10+ transitions/hour = Still needs tuning

### 4. Performance Baselines

**Healthy System Baselines:**
- Open circuits: 0
- Rejection rate: 0-10 req/min
- Failure ratio: <5%
- State transitions: 0-5/hour
- Success rate: >95%

**Alert Thresholds:**
- Open circuits ≥1 → Warning
- Rejection rate >50 req/min → Critical
- Failure ratio >20% → Critical
- State transitions >10/hour → Warning
- Success rate <80% → Critical

---

## Dashboard Customization

### Add Custom Panel

**Example: Circuit Breaker Cost Savings**

```json
{
  "id": 99,
  "title": "Cost Savings (LLM Rejections)",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(increase(circuit_breaker_rejections_total{name=~\"llm-.*\"}[1h])) * 0.50",
      "legendFormat": "Saved $$",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "currencyUSD"
    }
  },
  "gridPos": {"h": 4, "w": 6, "x": 0, "y": 60}
}
```

**Calculation:** Rejected LLM requests × $0.50/request

### Add Custom Variable

**Example: Time Range Variable**

```json
{
  "name": "timerange",
  "type": "interval",
  "options": ["1m", "5m", "15m", "1h"],
  "current": {
    "text": "5m",
    "value": "5m"
  }
}
```

**Usage:** `rate(circuit_breaker_failures_total[$timerange])`

### Export Dashboard

```bash
# Export as JSON
curl http://admin:admin@localhost:3000/api/dashboards/uid/circuit-breaker-monitoring \
  | jq '.dashboard' \
  > circuit-breaker-dashboard-backup.json

# Import to another Grafana instance
curl -X POST http://admin:admin@grafana-prod:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @circuit-breaker-dashboard-backup.json
```

---

## Related Documentation

1. **Circuit Breaker Implementation:**
   - [ADR-035: Circuit Breaker Pattern](../decisions/ADR-035-circuit-breaker-pattern.md)

2. **Integration Guides:**
   - [Database Circuit Breaker Guide](../../shared/news-mcp-common/docs/DATABASE_CIRCUIT_BREAKER_GUIDE.md)

---

## Support

**Dashboard Issues:**
- File: `/monitoring/grafana/dashboards/circuit-breaker-monitoring.json`
- Import errors: Check Grafana version (requires ≥9.0)
- Query errors: Verify Prometheus datasource

**Circuit Breaker Issues:**
- Library: `/shared/news-mcp-common/news_mcp_common/resilience/`
- Metrics: Check `enable_metrics=True` in config
- Logs: Check service logs for state transitions

**Questions:**
- ADR-035: Architecture decisions and rationale
- Task 406 Docs: Implementation details and testing
- Team: Contact infrastructure team

---

**Last Updated:** 2025-11-03
**Dashboard Version:** 1.0.0
**Grafana Version:** ≥9.0
**Prometheus Version:** ≥2.40

---

## See Also

- **[ADR-035: Circuit Breaker Pattern](../decisions/ADR-035-circuit-breaker-pattern.md)** - Architecture and implementation details
- **[CLAUDE.backend.md - Circuit Breaker](../../CLAUDE.backend.md#-resilience-patterns)** - Quick reference
- **[Database Integration Guide](../../shared/news-mcp-common/docs/DATABASE_CIRCUIT_BREAKER_GUIDE.md)** - PostgreSQL integration

---
