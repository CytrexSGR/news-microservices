# Content Analysis V2 - Prometheus Monitoring Guide

**Version:** 2.0
**Last Updated:** 2025-10-26
**Author:** Claude (AI Assistant)

---

## Table of Contents

1. [Overview](#overview)
2. [Metrics Reference](#metrics-reference)
3. [Prometheus Setup](#prometheus-setup)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Alerting Rules](#alerting-rules)
6. [Common Monitoring Scenarios](#common-monitoring-scenarios)
7. [Troubleshooting with Metrics](#troubleshooting-with-metrics)
8. [Best Practices](#best-practices)

---

## Overview

Content Analysis V2 exposes comprehensive Prometheus metrics for monitoring pipeline performance, costs, reliability, and resource usage. This guide covers metric interpretation, dashboard setup, and alerting configuration.

### Key Monitoring Goals

1. **Performance:** Processing time, throughput
2. **Reliability:** Success rate, failure patterns
3. **Cost:** LLM API usage, cost per article
4. **Capacity:** Queue depth, worker utilization
5. **Quality:** Category accuracy, priority distribution

### Metrics Endpoint

```
Service: content-analysis-v2
Endpoint: http://localhost:8000/metrics
Format: Prometheus text format
Update Frequency: Real-time (on event)
```

**Enable Metrics:**
```bash
# services/content-analysis-v2/.env
ENABLE_METRICS=true
```

---

## Metrics Reference

### Pipeline Execution Metrics

#### `pipeline_articles_total` (Counter)

**Description:** Total number of articles processed by pipeline

**Labels:**
- `status`: Article processing status
  - `success`: Processing completed successfully
  - `failed`: Processing failed (sent to DLQ)
  - `duplicate`: Skipped due to idempotency check

**Example:**
```
# TYPE pipeline_articles_total counter
pipeline_articles_total{status="success"} 1523
pipeline_articles_total{status="failed"} 12
pipeline_articles_total{status="duplicate"} 47
```

**Queries:**

Total articles processed:
```promql
sum(pipeline_articles_total)
```

Success rate (last 5 minutes):
```promql
100 * (
  rate(pipeline_articles_total{status="success"}[5m])
  / rate(pipeline_articles_total[5m])
)
```

Processing rate (articles/hour):
```promql
rate(pipeline_articles_total{status="success"}[1h]) * 3600
```

Duplicate rate:
```promql
100 * (
  rate(pipeline_articles_total{status="duplicate"}[5m])
  / rate(pipeline_articles_total[5m])
)
```

---

#### `pipeline_processing_duration_seconds` (Histogram)

**Description:** Time spent processing articles (end-to-end)

**Buckets:** [1, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 300]

**Example:**
```
# TYPE pipeline_processing_duration_seconds histogram
pipeline_processing_duration_seconds_bucket{le="1"} 0
pipeline_processing_duration_seconds_bucket{le="5"} 23
pipeline_processing_duration_seconds_bucket{le="10"} 156
pipeline_processing_duration_seconds_bucket{le="15"} 489
pipeline_processing_duration_seconds_bucket{le="20"} 1234
pipeline_processing_duration_seconds_bucket{le="30"} 1501
pipeline_processing_duration_seconds_bucket{le="+Inf"} 1523
pipeline_processing_duration_seconds_sum 26789.45
pipeline_processing_duration_seconds_count 1523
```

**Queries:**

Average processing time:
```promql
rate(pipeline_processing_duration_seconds_sum[5m])
/ rate(pipeline_processing_duration_seconds_count[5m])
```

95th percentile processing time:
```promql
histogram_quantile(0.95, rate(pipeline_processing_duration_seconds_bucket[5m]))
```

99th percentile processing time:
```promql
histogram_quantile(0.99, rate(pipeline_processing_duration_seconds_bucket[5m]))
```

---

#### `pipeline_cost_usd_total` (Counter)

**Description:** Total cost in USD for LLM API calls

**Example:**
```
# TYPE pipeline_cost_usd_total counter
pipeline_cost_usd_total 3.614523
```

**Queries:**

Total cost:
```promql
pipeline_cost_usd_total
```

Cost per hour:
```promql
rate(pipeline_cost_usd_total[1h]) * 3600
```

Daily cost projection:
```promql
rate(pipeline_cost_usd_total[1h]) * 3600 * 24
```

---

#### `pipeline_cost_per_article_usd` (Histogram)

**Description:** Cost per article in USD

**Buckets:** [0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1]

**Example:**
```
# TYPE pipeline_cost_per_article_usd histogram
pipeline_cost_per_article_usd_bucket{le="0.001"} 234
pipeline_cost_per_article_usd_bucket{le="0.002"} 789
pipeline_cost_per_article_usd_bucket{le="0.005"} 1401
pipeline_cost_per_article_usd_bucket{le="0.01"} 1520
pipeline_cost_per_article_usd_bucket{le="+Inf"} 1523
pipeline_cost_per_article_usd_sum 3.614523
pipeline_cost_per_article_usd_count 1523
```

**Queries:**

Average cost per article:
```promql
rate(pipeline_cost_per_article_usd_sum[5m])
/ rate(pipeline_cost_per_article_usd_count[5m])
```

95th percentile cost:
```promql
histogram_quantile(0.95, rate(pipeline_cost_per_article_usd_bucket[5m]))
```

---

### Agent Execution Metrics

#### `agent_execution_total` (Counter)

**Description:** Total number of agent executions

**Labels:**
- `agent_name`: Name of the agent
  - `category_classifier` (Tier 0)
  - `entity_extractor` (Tier 1)
  - `relationship_extractor` (Tier 1)
  - `summarizer` (Tier 1)
  - `geopolitical_analyzer` (Tier 2)
  - `economic_analyzer` (Tier 2)
  - `sentiment_analyzer` (Tier 2)
  - `impact_synthesizer` (Tier 3)
- `status`: Execution status
  - `success`: Completed successfully
  - `failed`: Execution failed
  - `cached`: Result from cache
  - `skipped`: Skipped (e.g., Tier 2 when priority < 70)

**Example:**
```
# TYPE agent_execution_total counter
agent_execution_total{agent_name="category_classifier",status="success"} 1523
agent_execution_total{agent_name="entity_extractor",status="success"} 1523
agent_execution_total{agent_name="geopolitical_analyzer",status="success"} 678
agent_execution_total{agent_name="geopolitical_analyzer",status="skipped"} 845
```

**Queries:**

Tier 2 skip rate:
```promql
100 * (
  sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer",status="skipped"}[5m]))
  / sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer"}[5m]))
)
```

Agent success rate:
```promql
100 * (
  rate(agent_execution_total{status="success"}[5m])
  / rate(agent_execution_total[5m])
) by (agent_name)
```

---

#### `agent_execution_duration_seconds` (Histogram)

**Description:** Time spent executing individual agents

**Labels:**
- `agent_name`: Name of the agent

**Buckets:** [0.5, 1, 2, 5, 10, 15, 30, 60, 90, 120]

**Example:**
```
# TYPE agent_execution_duration_seconds histogram
agent_execution_duration_seconds_bucket{agent_name="category_classifier",le="5"} 1501
agent_execution_duration_seconds_bucket{agent_name="category_classifier",le="10"} 1523
agent_execution_duration_seconds_sum{agent_name="category_classifier"} 4876.23
agent_execution_duration_seconds_count{agent_name="category_classifier"} 1523
```

**Queries:**

Average agent execution time:
```promql
rate(agent_execution_duration_seconds_sum[5m])
/ rate(agent_execution_duration_seconds_count[5m])
by (agent_name)
```

Slowest agents:
```promql
topk(5,
  rate(agent_execution_duration_seconds_sum[5m])
  / rate(agent_execution_duration_seconds_count[5m])
  by (agent_name)
)
```

---

### Queue Metrics

#### `queue_size_current` (Gauge)

**Description:** Current number of messages in queue

**Labels:**
- `queue_name`: Name of the queue
  - `content_analysis_v2_queue`

**Example:**
```
# TYPE queue_size_current gauge
queue_size_current{queue_name="content_analysis_v2_queue"} 47
```

**Queries:**

Current queue depth:
```promql
queue_size_current{queue_name="content_analysis_v2_queue"}
```

Queue depth over time (graph):
```promql
queue_size_current{queue_name="content_analysis_v2_queue"}
```

---

#### `dlq_messages_total` (Counter)

**Description:** Total messages sent to Dead Letter Queue

**Labels:**
- `error_type`: Type of error that caused DLQ routing
  - `invalid_message_format`
  - `malformed_json`
  - `pipeline_failed`
  - `unexpected_error`

**Example:**
```
# TYPE dlq_messages_total counter
dlq_messages_total{error_type="invalid_message_format"} 12
dlq_messages_total{error_type="pipeline_failed"} 8
dlq_messages_total{error_type="malformed_json"} 3
```

**Queries:**

Total DLQ messages:
```promql
sum(dlq_messages_total)
```

DLQ rate (messages/hour):
```promql
rate(dlq_messages_total[1h]) * 3600
```

DLQ breakdown by error type:
```promql
sum(rate(dlq_messages_total[5m])) by (error_type)
```

---

### Worker Metrics

#### `worker_active_count` (Gauge)

**Description:** Number of currently active workers

**Example:**
```
# TYPE worker_active_count gauge
worker_active_count 3
```

**Queries:**

Current worker count:
```promql
worker_active_count
```

---

#### `worker_message_processing_current` (Gauge)

**Description:** Number of messages currently being processed

**Example:**
```
# TYPE worker_message_processing_current gauge
worker_message_processing_current 2
```

**Queries:**

Current messages in processing:
```promql
worker_message_processing_current
```

Worker utilization:
```promql
100 * (
  worker_message_processing_current / worker_active_count
)
```

---

### Category Classification Metrics

#### `category_classification_total` (Counter)

**Description:** Total articles classified by category

**Labels:**
- `category`: Article category
  - `GEOPOLITICS_SECURITY`
  - `ECONOMY_MARKETS`
  - `TECHNOLOGY_SCIENCE`
  - `CLIMATE_ENVIRONMENT_HEALTH`
  - `POLITICS_SOCIETY`
  - `PANORAMA`

**Example:**
```
# TYPE category_classification_total counter
category_classification_total{category="GEOPOLITICS_SECURITY"} 234
category_classification_total{category="ECONOMY_MARKETS"} 456
category_classification_total{category="TECHNOLOGY_SCIENCE"} 189
```

**Queries:**

Category distribution:
```promql
sum(rate(category_classification_total[1h])) by (category)
```

Most common category:
```promql
topk(1, sum(category_classification_total) by (category))
```

---

#### `priority_score_distribution` (Histogram)

**Description:** Distribution of priority scores (0-100)

**Buckets:** [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

**Example:**
```
# TYPE priority_score_distribution histogram
priority_score_distribution_bucket{le="70"} 678
priority_score_distribution_bucket{le="80"} 1201
priority_score_distribution_bucket{le="90"} 1489
priority_score_distribution_bucket{le="100"} 1523
```

**Queries:**

Average priority score:
```promql
rate(priority_score_distribution_sum[5m])
/ rate(priority_score_distribution_count[5m])
```

Percentage of articles with priority >= 70:
```promql
100 * (
  sum(rate(priority_score_distribution_bucket{le="100"}[5m]))
  - sum(rate(priority_score_distribution_bucket{le="70"}[5m]))
) / sum(rate(priority_score_distribution_count[5m]))
```

---

### Error Metrics

#### `pipeline_errors_total` (Counter)

**Description:** Total pipeline errors

**Labels:**
- `error_type`: Type of error
  - `pipeline_execution_failed`
  - `json_decode_error`
  - `unexpected_error`
  - `database_error`
  - `llm_api_error`
- `agent_name`: Agent that encountered error

**Example:**
```
# TYPE pipeline_errors_total counter
pipeline_errors_total{error_type="pipeline_execution_failed",agent_name="pipeline"} 12
pipeline_errors_total{error_type="llm_api_error",agent_name="category_classifier"} 5
```

**Queries:**

Error rate:
```promql
rate(pipeline_errors_total[5m])
```

Errors by type:
```promql
sum(rate(pipeline_errors_total[5m])) by (error_type)
```

---

## Prometheus Setup

### Configuration

**File:** `/etc/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'content-analysis-v2'
    static_configs:
      - targets:
          - 'localhost:8000'  # Metrics endpoint

    # If using multi-replica deployment with exposed ports
    # - targets:
    #     - 'localhost:8114'  # Worker 1
    #     - 'localhost:8115'  # Worker 2
    #     - 'localhost:8116'  # Worker 3

    # Labels for all metrics from this job
    labels:
      service: 'content-analysis-v2'
      environment: 'production'
```

### Verification

```bash
# Check Prometheus can scrape metrics
curl http://localhost:9090/api/v1/targets

# Expected:
# {
#   "status": "success",
#   "data": {
#     "activeTargets": [
#       {
#         "labels": {
#           "job": "content-analysis-v2"
#         },
#         "health": "up",
#         "lastScrape": "2025-10-26T10:15:30Z"
#       }
#     ]
#   }
# }
```

---

## Grafana Dashboards

### Dashboard 1: Pipeline Overview

**Panels:**

1. **Processing Rate** (Graph)
   ```promql
   rate(pipeline_articles_total{status="success"}[5m]) * 60
   ```
   - Unit: articles/min
   - Target: > 10 articles/min (3 workers)

2. **Success Rate** (Gauge)
   ```promql
   100 * (
     rate(pipeline_articles_total{status="success"}[5m])
     / rate(pipeline_articles_total[5m])
   )
   ```
   - Unit: Percent
   - Threshold: Green > 99%, Yellow 95-99%, Red < 95%

3. **Queue Depth** (Graph)
   ```promql
   queue_size_current{queue_name="content_analysis_v2_queue"}
   ```
   - Alert: > 500 messages

4. **Avg Processing Time** (Stat)
   ```promql
   rate(pipeline_processing_duration_seconds_sum[5m])
   / rate(pipeline_processing_duration_seconds_count[5m])
   ```
   - Unit: Seconds
   - Target: < 20s

5. **Worker Count** (Stat)
   ```promql
   worker_active_count
   ```

6. **Worker Utilization** (Gauge)
   ```promql
   100 * (
     worker_message_processing_current / worker_active_count
   )
   ```
   - Unit: Percent
   - Target: 60-80% (healthy load)

---

### Dashboard 2: Cost Analysis

**Panels:**

1. **Total Cost Today** (Stat)
   ```promql
   increase(pipeline_cost_usd_total[24h])
   ```
   - Unit: USD
   - Format: $0.00

2. **Cost per Hour** (Graph)
   ```promql
   rate(pipeline_cost_usd_total[1h]) * 3600
   ```
   - Unit: USD/hour

3. **Avg Cost per Article** (Stat)
   ```promql
   rate(pipeline_cost_per_article_usd_sum[1h])
   / rate(pipeline_cost_per_article_usd_count[1h])
   ```
   - Unit: USD
   - Target: < $0.005

4. **Cost Distribution** (Heatmap)
   ```promql
   rate(pipeline_cost_per_article_usd_bucket[5m])
   ```

5. **Projected Monthly Cost** (Stat)
   ```promql
   (rate(pipeline_cost_usd_total[24h]) * 30)
   ```
   - Unit: USD
   - Budget: Alert if > $1,000

6. **Tier 2 Skip Rate** (Gauge)
   ```promql
   100 * (
     sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer",status="skipped"}[5m]))
     / sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer"}[5m]))
   )
   ```
   - Target: 40-60% (cost optimization)

---

### Dashboard 3: Agent Performance

**Panels:**

1. **Agent Execution Time** (Graph)
   ```promql
   rate(agent_execution_duration_seconds_sum[5m])
   / rate(agent_execution_duration_seconds_count[5m])
   by (agent_name)
   ```
   - Grouped by agent_name
   - Shows which agents are slowest

2. **Agent Success Rate** (Gauge)
   ```promql
   100 * (
     rate(agent_execution_total{status="success"}[5m])
     / rate(agent_execution_total[5m])
   ) by (agent_name)
   ```

3. **Tier 2 Skip Count** (Stat)
   ```promql
   sum(rate(agent_execution_total{status="skipped"}[1h])) * 3600
   ```
   - Unit: Skips/hour

4. **Cache Hit Rate** (Gauge)
   ```promql
   100 * (
     rate(agent_execution_total{status="cached"}[5m])
     / rate(agent_execution_total[5m])
   ) by (agent_name)
   ```
   - Target: > 10%

---

### Dashboard 4: Category & Priority

**Panels:**

1. **Category Distribution** (Pie Chart)
   ```promql
   sum(increase(category_classification_total[1h])) by (category)
   ```

2. **Priority Score Distribution** (Graph)
   ```promql
   rate(priority_score_distribution_bucket[5m])
   ```
   - Heatmap showing distribution over time

3. **High Priority Articles** (Stat)
   ```promql
   sum(increase(priority_score_distribution_bucket{le="100"}[1h]))
   - sum(increase(priority_score_distribution_bucket{le="70"}[1h]))
   ```
   - Count of articles with priority >= 70

4. **Avg Priority Score** (Gauge)
   ```promql
   rate(priority_score_distribution_sum[5m])
   / rate(priority_score_distribution_count[5m])
   ```

---

### Dashboard 5: Errors & Reliability

**Panels:**

1. **DLQ Rate** (Graph)
   ```promql
   rate(dlq_messages_total[5m]) * 3600
   ```
   - Unit: Messages/hour
   - Alert: > 10 messages/hour

2. **DLQ by Error Type** (Stacked Graph)
   ```promql
   sum(rate(dlq_messages_total[5m])) by (error_type)
   ```

3. **Error Rate** (Graph)
   ```promql
   rate(pipeline_errors_total[5m])
   ```

4. **Duplicate Rate** (Stat)
   ```promql
   100 * (
     rate(pipeline_articles_total{status="duplicate"}[5m])
     / rate(pipeline_articles_total[5m])
   )
   ```
   - Target: < 5%

5. **Failed vs Successful** (Pie Chart)
   ```promql
   sum(increase(pipeline_articles_total[1h])) by (status)
   ```

---

## Alerting Rules

### Prometheus Alert Rules

**File:** `/etc/prometheus/rules/content_analysis_v2.yml`

```yaml
groups:
  - name: content_analysis_v2
    interval: 30s
    rules:

      # High failure rate
      - alert: HighFailureRate
        expr: |
          100 * (
            rate(pipeline_articles_total{status="failed"}[5m])
            / rate(pipeline_articles_total[5m])
          ) > 5
        for: 10m
        labels:
          severity: critical
          service: content-analysis-v2
        annotations:
          summary: "High article processing failure rate"
          description: "{{ $value | humanizePercentage }} of articles failing (threshold: 5%)"

      # Queue depth growing
      - alert: QueueDepthHigh
        expr: queue_size_current{queue_name="content_analysis_v2_queue"} > 500
        for: 15m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "Queue depth is high"
          description: "{{ $value }} messages in queue (threshold: 500)"

      # Queue depth critical
      - alert: QueueDepthCritical
        expr: queue_size_current{queue_name="content_analysis_v2_queue"} > 1000
        for: 10m
        labels:
          severity: critical
          service: content-analysis-v2
        annotations:
          summary: "Queue depth is critical"
          description: "{{ $value }} messages in queue (threshold: 1000) - scale up workers immediately"

      # Slow processing
      - alert: SlowProcessing
        expr: |
          rate(pipeline_processing_duration_seconds_sum[5m])
          / rate(pipeline_processing_duration_seconds_count[5m])
          > 30
        for: 15m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "Average processing time is high"
          description: "{{ $value | humanizeDuration }} per article (threshold: 30s)"

      # DLQ growing rapidly
      - alert: DLQGrowth
        expr: rate(dlq_messages_total[1h]) * 3600 > 50
        for: 15m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "DLQ growing rapidly"
          description: "{{ $value }} messages/hour entering DLQ (threshold: 50)"

      # High duplicate rate
      - alert: HighDuplicateRate
        expr: |
          100 * (
            rate(pipeline_articles_total{status="duplicate"}[5m])
            / rate(pipeline_articles_total[5m])
          ) > 10
        for: 20m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "High duplicate message rate"
          description: "{{ $value | humanizePercentage }} of messages are duplicates (threshold: 10%)"

      # No workers active
      - alert: NoActiveWorkers
        expr: worker_active_count == 0
        for: 5m
        labels:
          severity: critical
          service: content-analysis-v2
        annotations:
          summary: "No active workers detected"
          description: "Worker count is {{ $value }} (expected: >= 1)"

      # High cost per article
      - alert: HighCostPerArticle
        expr: |
          rate(pipeline_cost_per_article_usd_sum[1h])
          / rate(pipeline_cost_per_article_usd_count[1h])
          > 0.01
        for: 30m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "Cost per article is high"
          description: "${{ $value }} per article (threshold: $0.01)"

      # Agent execution failures
      - alert: AgentExecutionFailures
        expr: |
          100 * (
            rate(agent_execution_total{status="failed"}[5m])
            / rate(agent_execution_total[5m])
          ) by (agent_name) > 10
        for: 10m
        labels:
          severity: warning
          service: content-analysis-v2
        annotations:
          summary: "Agent {{ $labels.agent_name }} has high failure rate"
          description: "{{ $value | humanizePercentage }} failures (threshold: 10%)"

      # Low Tier 2 skip rate (cost concern)
      - alert: LowTier2SkipRate
        expr: |
          100 * (
            sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer",status="skipped"}[30m]))
            / sum(rate(agent_execution_total{agent_name=~"geopolitical_analyzer|economic_analyzer|sentiment_analyzer"}[30m]))
          ) < 20
        for: 1h
        labels:
          severity: info
          service: content-analysis-v2
        annotations:
          summary: "Tier 2 skip rate is low"
          description: "{{ $value | humanizePercentage }} skip rate (threshold: < 20%) - may increase costs"
```

---

## Common Monitoring Scenarios

### Scenario 1: Detecting Processing Bottleneck

**Symptoms:**
- Queue depth growing
- Processing time increasing
- Worker utilization 100%

**Metrics to Check:**

1. **Queue Depth Trend:**
   ```promql
   queue_size_current{queue_name="content_analysis_v2_queue"}
   ```
   - If steadily increasing: Insufficient worker capacity

2. **Worker Utilization:**
   ```promql
   100 * (worker_message_processing_current / worker_active_count)
   ```
   - If consistently > 90%: Workers maxed out

3. **Processing Time:**
   ```promql
   histogram_quantile(0.95, rate(pipeline_processing_duration_seconds_bucket[5m]))
   ```
   - If increasing: LLM API slowdown or more complex articles

**Actions:**
- Scale up workers (see Worker Scaling Guide)
- Check LLM API status
- Review recent articles for complexity spike

---

### Scenario 2: Cost Spike Investigation

**Symptoms:**
- Daily cost unexpectedly high
- Cost per article increased

**Metrics to Check:**

1. **Cost Trend:**
   ```promql
   rate(pipeline_cost_usd_total[1h]) * 3600
   ```
   - Identify when spike started

2. **Tier 2 Skip Rate:**
   ```promql
   100 * (
     sum(rate(agent_execution_total{status="skipped"}[1h]))
     / sum(rate(agent_execution_total[1h]))
   )
   ```
   - If decreased: More articles running Tier 2 specialists

3. **Priority Score Distribution:**
   ```promql
   rate(priority_score_distribution_bucket[1h])
   ```
   - If shifted toward higher scores: More high-priority articles

4. **Category Distribution:**
   ```promql
   sum(rate(category_classification_total[1h])) by (category)
   ```
   - GEOPOLITICS articles more expensive (always run Tier 2)

**Actions:**
- Review TIER2_PRIORITY_THRESHOLD setting
- Analyze recent news events (breaking news = more high priority)
- Check if category classifier is over-prioritizing

---

### Scenario 3: Quality Issue Detection

**Symptoms:**
- Reports of miscategorized articles
- Missing entity extraction

**Metrics to Check:**

1. **Agent Success Rates:**
   ```promql
   100 * (
     rate(agent_execution_total{status="success"}[1h])
     / rate(agent_execution_total[1h])
   ) by (agent_name)
   ```
   - Identify failing agents

2. **Error Distribution:**
   ```promql
   sum(rate(pipeline_errors_total[1h])) by (error_type, agent_name)
   ```
   - Find error patterns

3. **Category Distribution:**
   ```promql
   sum(increase(category_classification_total[24h])) by (category)
   ```
   - Check for anomalies (e.g., 90% PANORAMA suddenly)

**Actions:**
- Review agent prompt templates
- Check LLM model performance
- Analyze sample of failed articles

---

## Troubleshooting with Metrics

### Problem: Workers Not Processing

**Check:**

1. **Worker Count:**
   ```promql
   worker_active_count
   ```
   - If 0: Workers crashed or not started

2. **Messages in Processing:**
   ```promql
   worker_message_processing_current
   ```
   - If 0 and queue > 0: Workers not consuming

3. **Queue Depth:**
   ```promql
   queue_size_current{queue_name="content_analysis_v2_queue"}
   ```
   - If > 0 and not decreasing: Workers stuck

**Actions:**
```bash
# Check worker logs
docker compose logs content-analysis-v2 --tail 100

# Restart workers
docker compose restart content-analysis-v2
```

---

### Problem: High DLQ Rate

**Check:**

1. **DLQ Breakdown:**
   ```promql
   sum(rate(dlq_messages_total[1h])) by (error_type)
   ```

2. **Error Patterns:**
   ```promql
   sum(rate(pipeline_errors_total[1h])) by (error_type)
   ```

**Common Causes:**

- `invalid_message_format`: Feed service sending malformed events
- `pipeline_failed`: LLM API errors, database issues
- `malformed_json`: Scraping service encoding problems

**Actions:**
```bash
# Inspect DLQ messages
docker exec rabbitmq rabbitmqadmin get queue=content_analysis_v2_queue_dlq count=10

# Fix upstream service
# Republish fixed messages
```

---

## Best Practices

### Dashboard Organization

1. **Overview Dashboard** (for stakeholders)
   - Processing rate, success rate, cost
   - Simple visualizations, no technical jargon

2. **Operational Dashboard** (for on-call engineers)
   - Queue depth, worker health, error rates
   - Alert status, actionable metrics

3. **Performance Dashboard** (for optimization)
   - Agent timing, cost breakdown, cache hit rates
   - Tier 2 skip analysis, processing time distribution

4. **Debugging Dashboard** (for troubleshooting)
   - Error logs integration
   - Per-agent success rates
   - DLQ analysis

### Alert Configuration

**Severity Levels:**

- **Critical:** Immediate action required (paging)
  - No workers active
  - Queue > 1000
  - Failure rate > 10%

- **Warning:** Investigate soon (Slack notification)
  - Queue > 500
  - Slow processing (> 30s avg)
  - DLQ growing

- **Info:** Nice to know (log only)
  - Low Tier 2 skip rate
  - High priority article count

**Alert Tuning:**
- Start conservative (few alerts)
- Add alerts as you learn system behavior
- Adjust thresholds based on production data
- Avoid alert fatigue (no trivial alerts)

### Metric Retention

```yaml
# prometheus.yml
global:
  # Raw metrics: 15 days
  retention: 15d

# Aggregated metrics (via recording rules): 90 days
```

**Recording Rules** (pre-compute expensive queries):

```yaml
# prometheus_rules.yml
groups:
  - name: content_analysis_v2_aggregations
    interval: 1m
    rules:
      - record: job:pipeline_success_rate:rate5m
        expr: |
          100 * (
            rate(pipeline_articles_total{status="success"}[5m])
            / rate(pipeline_articles_total[5m])
          )

      - record: job:pipeline_cost_per_article:rate5m
        expr: |
          rate(pipeline_cost_per_article_usd_sum[5m])
          / rate(pipeline_cost_per_article_usd_count[5m])
```

---

## Support

For issues or questions:

1. **Check Dashboards:** Identify affected metrics
2. **Review Logs:** `docker compose logs content-analysis-v2`
3. **Check Alerts:** Prometheus UI at `http://localhost:9090/alerts`
4. **Documentation:** `/docs/services/content-analysis-v2.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-26
**Maintained By:** Development Team
