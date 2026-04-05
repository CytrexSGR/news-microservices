# FMP-KG Integration SLI/SLO Definitions

**Service:** Knowledge-Graph Service (FMP Integration)
**Owner:** Platform Engineering
**Last Updated:** 2025-11-16
**Review Cycle:** Quarterly

---

## 1. Overview

This document defines Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the FMP Service → Knowledge-Graph Service → Neo4j integration.

**Purpose:** Establish measurable targets for availability, latency, and error rates to ensure production reliability.

---

## 2. Service Level Indicators (SLIs)

### 2.1 Availability

**Definition:** Percentage of successful requests over total requests

**Measurement:**
```promql
sum(rate(fmp_sync_requests_total{status="success"}[1h])) /
sum(rate(fmp_sync_requests_total[1h]))
```

**Data Source:** Prometheus `fmp_sync_requests_total` counter

**Measurement Window:** Rolling 1-hour

### 2.2 Latency

**Definition:** Time from request initiation to response completion

**Measurements:**
- **P50 (Median):** 50th percentile response time
- **P95:** 95th percentile response time
- **P99:** 99th percentile response time

**PromQL:**
```promql
histogram_quantile(0.95, rate(fmp_sync_duration_seconds_bucket[5m]))
```

**Data Source:** Prometheus `fmp_sync_duration_seconds` histogram

**Measurement Window:** Rolling 5-minute

### 2.3 Error Rate

**Definition:** Percentage of requests resulting in errors

**Categories:**
1. **Query Errors:** Neo4j query failures
2. **Sync Failures:** Complete sync operation failures
3. **Partial Failures:** Sync completed with some asset failures

**Measurements:**
```promql
# Neo4j query error rate
sum(rate(neo4j_query_errors_total[5m])) /
sum(rate(neo4j_query_duration_seconds_count[5m]))

# Sync failure rate
sum(rate(fmp_sync_requests_total{status="failed"}[15m])) /
sum(rate(fmp_sync_requests_total[15m]))
```

**Data Source:** Prometheus counters

**Measurement Window:** Rolling 5-15 minutes

### 2.4 Data Freshness

**Definition:** Time since last successful sync

**Measurement:**
```promql
time() - max(fmp_sync_requests_total)
```

**Data Source:** Prometheus timestamp comparison

**Measurement Window:** Real-time

---

## 3. Service Level Objectives (SLOs)

### 3.1 Availability SLO

**Target:** 99.5% availability

**Calculation:**
- **Monthly:** At least 99.5% of requests succeed
- **Allowed Downtime:** 4 hours 22 minutes per month
- **Weekly:** 50.4 minutes per week

**Measurement Window:** Rolling 30 days

**Alert Threshold:** < 99.5% for 5 minutes

**Impact of Missing SLO:**
- **99.0%:** 7h 18m downtime/month (DEGRADED)
- **98.0%:** 14h 36m downtime/month (CRITICAL)

**Justification:** 99.5% balances reliability with operational cost. 99.9% would require ~10x infrastructure investment.

### 3.2 Latency SLO

**Targets:**
- **P95 < 200ms** for sync endpoints
- **P99 < 500ms** for sync endpoints
- **P95 < 5ms** for Neo4j queries

**Measurement Window:** Rolling 5 minutes

**Alert Thresholds:**
- P95 > 200ms for 10 minutes (WARNING)
- P95 > 500ms for 5 minutes (CRITICAL)
- Neo4j P95 > 5ms for 5 minutes (WARNING)

**Justification:**
- **200ms P95:** Acceptable for batch sync operations
- **5ms Neo4j:** Ensures index effectiveness (<5ms = indexed query)

**Impact of Missing SLO:**
- **P95 @ 500ms:** 2.5x slower than target (user-noticeable delay)
- **P95 @ 1000ms:** 5x slower (unacceptable for interactive use)

### 3.3 Error Rate SLO

**Targets:**
- **< 1% error rate** for market queries
- **< 5% failure rate** for sync operations

**Measurement Window:** Rolling 15 minutes

**Alert Thresholds:**
- Query errors > 1% for 5 minutes (WARNING)
- Sync failures > 5% for 10 minutes (WARNING)

**Justification:**
- **1% query errors:** Allows for transient Neo4j connection issues
- **5% sync failures:** Accounts for occasional FMP API unavailability

**Impact of Missing SLO:**
- **5% query errors:** Data quality concerns, investigate immediately
- **10% sync failures:** Significant data staleness risk

### 3.4 Sync Success Rate SLO

**Target:** > 95% of sync operations complete successfully

**Calculation:**
```promql
sum(rate(fmp_sync_requests_total{status="success"}[15m])) /
sum(rate(fmp_sync_requests_total[15m]))
```

**Measurement Window:** Rolling 15 minutes

**Alert Threshold:** < 95% for 10 minutes

**Justification:** 95% success rate ensures majority of markets stay fresh while allowing for:
- FMP Service rate limits (temporary)
- Individual asset failures (partial syncs)
- Network transients

---

## 4. Error Budget

### 4.1 Definition

**Error Budget:** Amount of acceptable failure within SLO period

**Formula:**
```
Error Budget = (1 - SLO) × Total Requests
```

**Example (99.5% availability SLO):**
- Total monthly requests: 100,000
- Error budget: 500 failed requests/month (0.5%)

### 4.2 Error Budget Policy

**Status Levels:**

| Budget Remaining | Status | Actions |
|-----------------|--------|---------|
| > 50% | HEALTHY | Normal operations, deploy freely |
| 25-50% | CAUTION | Review deployment frequency, investigate trends |
| 10-25% | WARNING | Freeze non-critical deployments, focus on stability |
| < 10% | CRITICAL | Emergency freeze, incident response mode |

**Budget Reset:** Monthly (1st of each month)

### 4.3 Error Budget Consumption

**Tracking:**
```promql
# Availability error budget
1 - (
  sum(rate(fmp_sync_requests_total{status="success"}[30d])) /
  sum(rate(fmp_sync_requests_total[30d]))
) / (1 - 0.995)
```

**Dashboard:** Grafana "Error Budget" panel

---

## 5. Alerts Mapping

### 5.1 Availability Alerts

| Alert | Severity | Threshold | Response Time |
|-------|----------|-----------|---------------|
| `FMPSyncAvailabilityLow` | WARNING | < 99.5% for 5min | 15 minutes |
| `CircuitBreakerOpen` | CRITICAL | state=open for 1min | Immediate |
| `MarketDataStale` | WARNING | No sync in 1h | 30 minutes |

### 5.2 Latency Alerts

| Alert | Severity | Threshold | Response Time |
|-------|----------|-----------|---------------|
| `FMPSyncLatencyHigh` | WARNING | P95 > 200ms for 10min | 30 minutes |
| `Neo4jQueryLatencyHigh` | WARNING | P95 > 5ms for 5min | 15 minutes |

### 5.3 Error Rate Alerts

| Alert | Severity | Threshold | Response Time |
|-------|----------|-----------|---------------|
| `Neo4jQueryErrorRateHigh` | WARNING | > 1% for 5min | 15 minutes |
| `FMPSyncFailureRateHigh` | WARNING | > 5% for 10min | 30 minutes |
| `FMPPartialSyncFrequent` | WARNING | > 10% partial for 15min | 1 hour |

---

## 6. SLO Review Process

### 6.1 Quarterly Review

**Schedule:** First week of each quarter (Q1, Q2, Q3, Q4)

**Participants:**
- Platform Engineering (SLO owner)
- SRE Team
- Product Management

**Agenda:**
1. Review SLO achievement (actual vs target)
2. Analyze error budget consumption trends
3. Identify recurring incidents affecting SLOs
4. Adjust SLO targets if necessary
5. Update alert thresholds based on patterns

### 6.2 SLO Adjustment Criteria

**Criteria for Tightening SLOs (more strict):**
- Consistently exceeding targets by > 20% for 2+ quarters
- User expectations increased
- Competitive pressure

**Criteria for Relaxing SLOs (less strict):**
- Consistently missing targets despite best efforts
- Infrastructure cost exceeds business value
- Unrealistic targets based on dependencies (e.g., FMP API limits)

**Process:**
1. Propose SLO change with justification
2. Review impact on error budget policy
3. Update monitoring dashboards
4. Communicate to stakeholders
5. Document in this file

---

## 7. Dependencies and Risks

### 7.1 External Dependencies

| Dependency | SLO Impact | Mitigation |
|-----------|------------|------------|
| FMP Service | High (availability, latency) | Circuit breaker, retry logic, rate limiting |
| Neo4j Database | Critical (all SLOs) | Connection pooling, query optimization, replica reads |
| RabbitMQ (Phase 3) | Medium (event delivery) | Durable queues, consumer acknowledgments |

### 7.2 Risk Scenarios

**Scenario 1: FMP Service Degradation**
- **Impact:** Availability SLO at risk, sync failures increase
- **Mitigation:** Circuit breaker triggers, fallback to cached data
- **Recovery Time:** 30 minutes (circuit breaker recovery timeout)

**Scenario 2: Neo4j Slow Queries**
- **Impact:** Latency SLO violation, user experience degraded
- **Mitigation:** Query timeout (10s), index optimization
- **Recovery Time:** Immediate (query-specific fix)

**Scenario 3: Network Partition**
- **Impact:** All SLOs affected, service unavailable
- **Mitigation:** Multi-AZ deployment (future), health checks
- **Recovery Time:** Depends on infrastructure recovery

---

## 8. References

- **Monitoring Dashboard:** Grafana `fmp-kg-integration`
- **Alert Rules:** `monitoring/prometheus_alerts.yml`
- **Troubleshooting:** `docs/operations/fmp-kg-troubleshooting.md`
- **Runbook:** `docs/operations/fmp-kg-runbook.md`

---

## 9. Appendix: SLO Calculation Examples

### Example 1: Monthly Availability

```python
# Given
total_requests = 100_000
successful_requests = 99_600

# Calculate availability
availability = successful_requests / total_requests
# = 0.996 = 99.6%

# Check against SLO (99.5%)
meets_slo = availability >= 0.995
# = True (exceeds SLO by 0.1%)

# Calculate downtime
downtime_minutes = (1 - availability) * 30 * 24 * 60
# = 0.004 * 43200 = 172.8 minutes
# = 2 hours 52 minutes (within 4h 22m budget)
```

### Example 2: Error Budget

```python
# Given SLO: 99.5% availability
# Total requests/month: 100,000

# Error budget
error_budget = (1 - 0.995) * 100_000
# = 0.005 * 100_000 = 500 requests

# Actual failures: 400

# Budget remaining
budget_remaining = (error_budget - 400) / error_budget
# = 100 / 500 = 0.2 = 20%
# Status: WARNING (< 25%)
```

---

**Document Version:** 1.0
**Approved By:** Platform Engineering Lead
**Next Review:** 2026-02-16
