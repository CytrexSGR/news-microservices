# Scheduler Service - Metrics Guide

This guide covers all Prometheus metrics exposed by the Scheduler Service and how to use them for monitoring and alerting.

---

## Metrics Endpoint

**URL:** `GET /metrics`

**Format:** Prometheus text format

**Example:**
```bash
curl http://localhost:8108/metrics
```

---

## Metric Categories

### 1. Task Execution Metrics

Track scheduled task executions (feed monitor, job processor, etc.)

#### `scheduler_task_runs_total`
- **Type:** Counter
- **Labels:** `task_name`, `status`
- **Description:** Total number of scheduled task executions
- **Status Values:** `success`, `failure`, `timeout`

**Usage:**
```promql
# Success rate for feed monitor
rate(scheduler_task_runs_total{task_name="feed_monitor",status="success"}[5m])

# Failure rate
rate(scheduler_task_runs_total{status="failure"}[5m])
```

#### `scheduler_task_duration_seconds`
- **Type:** Histogram
- **Labels:** `task_name`
- **Buckets:** 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0

**Usage:**
```promql
# Average task duration
rate(scheduler_task_duration_seconds_sum[5m]) / rate(scheduler_task_duration_seconds_count[5m])

# 95th percentile
histogram_quantile(0.95, rate(scheduler_task_duration_seconds_bucket[5m]))
```

#### `scheduler_task_failures_total`
- **Type:** Counter
- **Labels:** `task_name`, `error_type`
- **Description:** Total task failures by error type

**Usage:**
```promql
# Most common errors
topk(5, sum by (error_type) (rate(scheduler_task_failures_total[1h])))
```

#### `scheduler_task_retries_total`
- **Type:** Counter
- **Labels:** `task_name`, `attempt`
- **Description:** Total retry attempts

---

### 2. Job Queue Metrics

Track analysis job queue status and processing

#### `scheduler_job_queue_size`
- **Type:** Gauge
- **Labels:** `status`
- **Status Values:** `pending`, `processing`, `completed`, `failed`

**Usage:**
```promql
# Pending jobs
scheduler_job_queue_size{status="pending"}

# Processing jobs
scheduler_job_queue_size{status="processing"}
```

**Alerting:**
```yaml
- alert: HighJobQueueSize
  expr: scheduler_job_queue_size{status="pending"} > 1000
  for: 10m
  annotations:
    summary: "High job queue size ({{ $value }} pending jobs)"
```

#### `scheduler_job_processing_duration_seconds`
- **Type:** Histogram
- **Labels:** `job_type`
- **Job Types:** `categorization`, `finance_sentiment`, `geopolitical_sentiment`, `standard_sentiment`, `osint`, `summary`, `entities`, `topics`

**Usage:**
```promql
# Average processing time by job type
rate(scheduler_job_processing_duration_seconds_sum[5m]) / rate(scheduler_job_processing_duration_seconds_count[5m])
```

#### `scheduler_job_queue_age_seconds`
- **Type:** Histogram
- **Labels:** `status`
- **Description:** Time jobs spend in queue

---

### 3. Feed Monitor Metrics

Track feed checking and article discovery

#### `scheduler_feeds_checked_total`
- **Type:** Counter
- **Labels:** `status`
- **Status Values:** `success`, `error`

**Usage:**
```promql
# Feed check success rate
rate(scheduler_feeds_checked_total{status="success"}[5m]) / rate(scheduler_feeds_checked_total[5m])
```

#### `scheduler_articles_discovered_total`
- **Type:** Counter
- **Labels:** `feed_category`
- **Categories:** `finance`, `geopolitics`, `general`, etc.

**Usage:**
```promql
# Articles discovered per minute by category
rate(scheduler_articles_discovered_total[1m]) * 60
```

#### `scheduler_feed_check_duration_seconds`
- **Type:** Histogram
- **Description:** Duration of feed check cycles

---

### 4. Circuit Breaker Metrics

Monitor circuit breaker states and failures

#### `scheduler_circuit_breaker_state`
- **Type:** Enum
- **Labels:** `service`
- **States:** `CLOSED`, `OPEN`, `HALF_OPEN`

**Usage:**
```promql
# Check if any circuit breaker is OPEN
scheduler_circuit_breaker_state{state="OPEN"} == 1
```

**Alerting:**
```yaml
- alert: CircuitBreakerOpen
  expr: scheduler_circuit_breaker_state{state="OPEN"} == 1
  for: 5m
  annotations:
    summary: "Circuit breaker OPEN for {{ $labels.service }}"
```

#### `scheduler_circuit_breaker_failures_total`
- **Type:** Counter
- **Labels:** `service`

#### `scheduler_circuit_breaker_trips_total`
- **Type:** Counter
- **Labels:** `service`
- **Description:** Count of state transitions to OPEN

---

### 5. HTTP Client Metrics

Track outgoing HTTP requests to external services

#### `scheduler_http_requests_total`
- **Type:** Counter
- **Labels:** `service`, `method`, `status_code`
- **Services:** `feed_service`, `content_analysis_service`

**Usage:**
```promql
# Error rate for Feed Service
rate(scheduler_http_requests_total{service="feed_service",status_code=~"5.."}[5m])

# Success rate
rate(scheduler_http_requests_total{status_code=~"2.."}[5m]) / rate(scheduler_http_requests_total[5m])
```

#### `scheduler_http_request_duration_seconds`
- **Type:** Histogram
- **Labels:** `service`, `method`

**Usage:**
```promql
# 99th percentile response time
histogram_quantile(0.99, rate(scheduler_http_request_duration_seconds_bucket[5m]))
```

---

### 6. Service Health Metrics

Monitor overall service health and uptime

#### `scheduler_service_health`
- **Type:** Enum
- **States:** `healthy`, `degraded`, `unhealthy`

**Alerting:**
```yaml
- alert: ServiceUnhealthy
  expr: scheduler_service_health{state="unhealthy"} == 1
  for: 2m
  annotations:
    summary: "Scheduler service is unhealthy"
```

#### `scheduler_service_uptime_seconds`
- **Type:** Gauge
- **Description:** Service uptime in seconds

**Usage:**
```promql
# Uptime in hours
scheduler_service_uptime_seconds / 3600
```

#### `scheduler_running`
- **Type:** Gauge
- **Labels:** `component`
- **Components:** `feed_monitor`, `job_processor`, `cron_scheduler`
- **Values:** 1 (running), 0 (stopped)

**Alerting:**
```yaml
- alert: SchedulerComponentDown
  expr: scheduler_running == 0
  for: 1m
  annotations:
    summary: "Scheduler component {{ $labels.component }} is not running"
```

---

## Example Grafana Queries

### Dashboard Panel: Job Queue Size Over Time

```promql
scheduler_job_queue_size{status="pending"}
```

### Dashboard Panel: Task Success Rate

```promql
sum(rate(scheduler_task_runs_total{status="success"}[5m]))
/
sum(rate(scheduler_task_runs_total[5m]))
```

### Dashboard Panel: Average Processing Time

```promql
sum by (job_type) (
  rate(scheduler_job_processing_duration_seconds_sum[5m])
)
/
sum by (job_type) (
  rate(scheduler_job_processing_duration_seconds_count[5m])
)
```

### Dashboard Panel: Circuit Breaker Status

```promql
scheduler_circuit_breaker_state
```

### Dashboard Panel: HTTP Error Rate

```promql
sum by (service) (
  rate(scheduler_http_requests_total{status_code=~"5.."}[5m])
)
```

---

## Alerting Rules

### Recommended Prometheus Alerts

```yaml
groups:
  - name: scheduler_service
    interval: 30s
    rules:
      - alert: HighJobQueueSize
        expr: scheduler_job_queue_size{status="pending"} > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High job queue size"
          description: "{{ $value }} pending jobs in queue"

      - alert: CircuitBreakerOpen
        expr: scheduler_circuit_breaker_state{state="OPEN"} == 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker OPEN for {{ $labels.service }}"

      - alert: LowTaskSuccessRate
        expr: |
          sum(rate(scheduler_task_runs_total{status="success"}[5m]))
          /
          sum(rate(scheduler_task_runs_total[5m]))
          < 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Task success rate below 90%"

      - alert: SchedulerComponentDown
        expr: scheduler_running == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.component }} is not running"

      - alert: ServiceUnhealthy
        expr: scheduler_service_health{state="unhealthy"} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Scheduler service is unhealthy"

      - alert: HighHTTPErrorRate
        expr: |
          sum(rate(scheduler_http_requests_total{status_code=~"5.."}[5m]))
          /
          sum(rate(scheduler_http_requests_total[5m]))
          > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High HTTP error rate (>5%)"
```

---

## Metric Recording Best Practices

### Using the Metrics API

```python
from app.core.metrics import (
    record_task_execution,
    record_task_failure,
    update_job_queue_size,
    record_http_request
)

# Record task execution
start_time = time.time()
try:
    # Task logic
    status = "success"
except Exception as e:
    status = "failure"
    record_task_failure("task_name", type(e).__name__)
finally:
    duration = time.time() - start_time
    record_task_execution("task_name", status, duration)

# Record HTTP request
record_http_request("feed_service", "GET", 200, 0.15)

# Update queue size
update_job_queue_size("pending", 42)
```

### Using Decorators

```python
from app.core.metrics import track_task_execution

@track_task_execution("feed_monitor")
async def monitor_feeds():
    # Automatically tracks duration, success/failure, errors
    pass
```

---

## Troubleshooting

### Metrics Not Appearing

1. Check metrics endpoint:
   ```bash
   curl http://localhost:8108/metrics
   ```

2. Verify Prometheus is scraping:
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'scheduler-service'
       static_configs:
         - targets: ['scheduler-service:8108']
   ```

3. Check service logs:
   ```bash
   docker logs scheduler-service
   ```

### High Cardinality Issues

- Avoid using unbounded label values (e.g., article IDs, timestamps)
- Use labels for low-cardinality dimensions only
- Aggregate high-cardinality data in logs, not metrics

---

## See Also

- [Health Check Guide](HEALTH_CHECK_GUIDE.md)
- [Error Handling Guide](ERROR_HANDLING_GUIDE.md)
- [Stabilization Report](../STABILIZATION_REPORT.md)
