# Content Analysis V2 - Worker Scaling Deployment Guide

**Version:** 2.0
**Last Updated:** 2025-10-26
**Author:** Claude (AI Assistant)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Understanding Worker Scaling](#understanding-worker-scaling)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Capacity Planning](#capacity-planning)
8. [Scaling Operations](#scaling-operations)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

This guide covers deploying and scaling Content Analysis V2 pipeline workers in production. The service uses Docker Compose with replica deployment to horizontally scale message processing.

### Key Features

- **Horizontal Scaling:** Add/remove workers dynamically
- **Load Distribution:** RabbitMQ distributes messages across workers
- **Auto-Recovery:** Failed workers automatically restart
- **Zero-Downtime Scaling:** Add workers without disrupting processing
- **Resource Isolation:** Each worker runs in separate container

### Use Cases

- **Low Traffic (1,000-5,000 articles/day):** 1-2 workers
- **Medium Traffic (5,000-15,000 articles/day):** 3-5 workers
- **High Traffic (15,000-50,000 articles/day):** 5-10 workers
- **Peak Load Handling:** Temporarily scale up during breaking news

---

## Architecture

### Deployment Topology

```
┌────────────────────────────────────────────────────────────┐
│                     Docker Host                            │
│                                                            │
│  ┌──────────────┐                                         │
│  │  RabbitMQ    │                                         │
│  │  Queue:      │                                         │
│  │  content_    │                                         │
│  │  analysis_   │                                         │
│  │  v2_queue    │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │ Distributes messages (round-robin)              │
│         │                                                  │
│    ┌────┴─────┬──────────┬──────────┐                     │
│    │          │          │          │                     │
│    ▼          ▼          ▼          ▼                     │
│ ┌─────┐   ┌─────┐   ┌─────┐    ┌─────┐                  │
│ │  W1 │   │  W2 │   │  W3 │... │  WN │                  │
│ │ PID │   │ PID │   │ PID │    │ PID │                  │
│ │ 1234│   │ 1235│   │ 1236│    │ ... │                  │
│ └──┬──┘   └──┬──┘   └──┬──┘    └──┬──┘                  │
│    │         │         │           │                      │
│    └─────────┴─────────┴───────────┘                      │
│                  │                                         │
│                  ▼                                         │
│         ┌────────────────┐                                │
│         │   PostgreSQL   │                                │
│         │   (Shared DB)  │                                │
│         └────────────────┘                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Component Communication

```
Feed Service
    │
    │ Publishes article.created event
    ▼
RabbitMQ Exchange (news.events)
    │
    │ Routes to queue
    ▼
Content Analysis V2 Queue (content_analysis_v2_queue)
    │
    │ Round-robin distribution (QoS prefetch_count=1)
    │
    ├─→ Worker 1 (news-microservices-content-analysis-v2-1)
    ├─→ Worker 2 (news-microservices-content-analysis-v2-2)
    ├─→ Worker 3 (news-microservices-content-analysis-v2-3)
    └─→ Worker N
         │
         │ Processes article
         ▼
    PostgreSQL (Shared)
         │
         │ Stores results
         ▼
    Pipeline Execution Record
```

---

## Prerequisites

### System Requirements

**Per Worker:**
- **CPU:** 1-2 cores
- **RAM:** 2-4GB (3GB recommended)
- **Disk:** 500MB (minimal, logs rotate)

**Total System:**
- **3 Workers:** 6-12GB RAM, 4-6 cores
- **5 Workers:** 10-20GB RAM, 6-10 cores
- **10 Workers:** 20-40GB RAM, 12-20 cores

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+
- RabbitMQ 3.11+
- Redis 7.0+

### Network Requirements

- Workers → PostgreSQL: Port 5432
- Workers → RabbitMQ: Port 5672
- Workers → Redis: Port 6379
- Workers → Google Gemini API: Port 443 (HTTPS)

---

## Understanding Worker Scaling

### How Docker Compose Replicas Work

**Single Worker (replicas: 1):**
```yaml
deploy:
  replicas: 1
```

Docker creates:
- `news-microservices-content-analysis-v2-1`

**Multiple Workers (replicas: 3):**
```yaml
deploy:
  replicas: 3
```

Docker creates:
- `news-microservices-content-analysis-v2-1`
- `news-microservices-content-analysis-v2-2`
- `news-microservices-content-analysis-v2-3`

### RabbitMQ Load Distribution

**QoS Configuration:**
```python
await channel.set_qos(prefetch_count=1)
```

**Behavior:**
- Each worker receives **1 message at a time**
- Worker must ACK before receiving next message
- RabbitMQ uses **round-robin** distribution
- Fast workers process more (slow workers don't get overwhelmed)

**Example with 3 workers:**
```
Queue: [M1, M2, M3, M4, M5, M6, M7, M8, M9]

Distribution:
W1: M1 → M4 → M7
W2: M2 → M5 → M8
W3: M3 → M6 → M9
```

**Self-Balancing:**
```
W1: M1 (17s) → M4
W2: M2 (20s) → M5
W3: M3 (15s) → M6 → M7 (W3 finishes first, gets M7)
```

### Scaling Math

**Processing Capacity:**
```
Throughput = (Workers × 3600 seconds) / Avg Processing Time

Example (3 workers, 18s avg):
Throughput = (3 × 3600) / 18
          = 10,800 / 18
          = 600 articles/hour
          = 14,400 articles/day
```

**Capacity Table:**

| Workers | Articles/Hour | Articles/Day | Cost/Day (at $0.0024/article) |
|---------|--------------|--------------|-------------------------------|
| 1 | 200 | 4,800 | $11.52 |
| 2 | 400 | 9,600 | $23.04 |
| 3 | 600 | 14,400 | $34.56 |
| 5 | 1,000 | 24,000 | $57.60 |
| 10 | 2,000 | 48,000 | $115.20 |

*Assumes 18s average processing time*

---

## Configuration

### Docker Compose Configuration

**File:** `/home/cytrex/news-microservices/docker-compose.yml`

```yaml
services:
  content-analysis-v2:
    build:
      context: .
      dockerfile: ./services/content-analysis-service/Dockerfile.dev

    # IMPORTANT: No container_name for multi-replica deployment
    # Containers auto-named: news-microservices-content-analysis-v2-{1,2,3,...}

    restart: unless-stopped

    # Run pipeline worker (not FastAPI server)
    command: python -m app.workers.pipeline_worker

    # Environment variables
    env_file:
      - ./services/content-analysis-v2/.env
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      REDIS_HOST: redis
      REDIS_PORT: 6379
      RABBITMQ_HOST: rabbitmq
      RABBITMQ_PORT: 5672

    # No ports exposed - workers are consumers only (no HTTP API)
    # If you need metrics endpoint, expose on different ports per replica

    # Volume mounts for hot-reload (development)
    volumes:
      - ./services/content-analysis-v2/app:/app/app
      - ./services/content-analysis-v2/config:/app/config
      - ./database:/app/database

    # Network configuration
    networks:
      - news_network

    # Dependencies
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

    # ===== SCALING CONFIGURATION =====
    deploy:
      replicas: 3  # <-- Change this to scale workers

      # Restart policy for failed workers
      restart_policy:
        condition: on-failure  # Auto-restart on crash
        delay: 5s             # Wait 5s before restart
        max_attempts: 3       # Give up after 3 failures
        window: 120s          # Reset counter after 2 minutes
```

### Environment Configuration

**File:** `/home/cytrex/news-microservices/services/content-analysis-v2/.env`

```bash
# Service Configuration
SERVICE_NAME=content-analysis-v2
VERSION=2.0

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=news_mcp

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=news_user
RABBITMQ_PASSWORD=news_password
RABBITMQ_EXCHANGE=news.events
RABBITMQ_QUEUE=content_analysis_v2_queue
RABBITMQ_ROUTING_KEY=article.created

# Google Gemini API
GEMINI_API_KEY=your_api_key_here

# Pipeline Configuration
MAX_CONCURRENT_AGENTS=10
PIPELINE_TIMEOUT=300
ENABLE_CACHE=true
TIER2_PRIORITY_THRESHOLD=70

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8000  # Note: Will conflict if exposing ports with replicas
```

**⚠️ Important:** If you need to expose metrics endpoint with replicas, use different ports:

```yaml
# In docker-compose.yml
content-analysis-v2:
  ports:
    - "8114-8123:8000"  # Maps ports 8114-8123 to container port 8000
  deploy:
    replicas: 10
```

Worker 1: localhost:8114
Worker 2: localhost:8115
...

---

## Deployment

### Initial Deployment (3 Workers)

**Step 1: Configure Replicas**

Edit `docker-compose.yml`:

```yaml
deploy:
  replicas: 3
```

**Step 2: Start Services**

```bash
cd /home/cytrex/news-microservices

# Start all infrastructure + workers
docker compose up -d content-analysis-v2
```

**Step 3: Verify Deployment**

```bash
# Check all 3 workers are running
docker compose ps content-analysis-v2

# Expected output:
NAME                                            STATUS
news-microservices-content-analysis-v2-1        running
news-microservices-content-analysis-v2-2        running
news-microservices-content-analysis-v2-3        running
```

**Step 4: Check Logs**

```bash
# All workers
docker compose logs content-analysis-v2 --tail 50

# Specific worker
docker logs news-microservices-content-analysis-v2-1 --tail 50
```

Expected log output (per worker):
```
✓ Connected to RabbitMQ: rabbitmq:5672
✓ Connected to queue: content_analysis_v2_queue
✓ Dead Letter Queue configured: content_analysis_v2_queue_dlq
✓ Pipeline orchestrator initialized
✓ Worker started, waiting for messages...
```

**Step 5: Verify RabbitMQ Consumers**

```bash
# Check RabbitMQ Management UI
# http://localhost:15672

# Or via CLI
docker exec rabbitmq rabbitmqctl list_consumers

# Expected: 3 consumers on content_analysis_v2_queue
```

---

## Capacity Planning

### Estimating Required Workers

**Formula:**

```
Required Workers = (Expected Messages/Hour × Avg Processing Time) / 3600

Example:
Expected: 1,000 articles/hour
Avg Time: 18 seconds/article

Required Workers = (1,000 × 18) / 3600
                 = 18,000 / 3600
                 = 5 workers
```

**Add 20% buffer for peak load:**
```
Production Workers = Required × 1.2
                   = 5 × 1.2
                   = 6 workers (round up)
```

### Scaling Decision Matrix

| Daily Articles | Peak/Hour | Avg Time | Workers | RAM Needed |
|---------------|-----------|----------|---------|------------|
| 1,000 | 100 | 18s | 1 | 3GB |
| 5,000 | 500 | 18s | 3 | 9GB |
| 10,000 | 1,000 | 18s | 5 | 15GB |
| 20,000 | 2,000 | 18s | 10 | 30GB |
| 50,000 | 5,000 | 18s | 25 | 75GB |

### Performance Benchmarks

**Test Environment:**
- Workers: 3
- Articles: 10
- Avg Processing Time: 17.56s
- Success Rate: 100%

**Projected Performance:**

```
Capacity Calculation:
- Workers: 3
- Seconds/hour: 3,600
- Avg processing time: 17.56s

Hourly Throughput = (3 × 3,600) / 17.56
                  = 10,800 / 17.56
                  = 615 articles/hour

Daily Capacity = 615 × 24
               = 14,760 articles/day

Monthly Capacity = 14,760 × 30
                 = 442,800 articles/month
```

---

## Scaling Operations

### Scaling Up (Add Workers)

**Scenario:** Need to process 25,000 articles/day (currently at 15,000)

**Step 1: Calculate Required Workers**

```
Current: 3 workers = 14,760 articles/day
Target: 25,000 articles/day

Required = (25,000 / 14,760) × 3
         = 1.69 × 3
         = 5.08 ≈ 5 workers
```

**Step 2: Update Configuration**

```yaml
# docker-compose.yml
deploy:
  replicas: 5  # Changed from 3
```

**Step 3: Apply Changes (Zero-Downtime)**

```bash
# Method 1: Rolling restart (preferred)
docker compose up -d --scale content-analysis-v2=5

# Method 2: Explicit restart
docker compose stop content-analysis-v2
docker compose up -d content-analysis-v2
```

**Step 4: Verify Scale-Up**

```bash
# Should show 5 workers
docker compose ps content-analysis-v2

# Check all are consuming
docker exec rabbitmq rabbitmqctl list_consumers | grep content_analysis
# Expected: 5 consumers
```

**Step 5: Monitor Performance**

```bash
# Watch queue depth (should decrease faster)
watch -n 2 'docker exec rabbitmq rabbitmqctl list_queues name messages consumers'

# Monitor processing rate
curl localhost:8000/metrics | grep pipeline_processing_duration_seconds_count
```

---

### Scaling Down (Remove Workers)

**Scenario:** Traffic decreased, want to reduce costs

**Step 1: Check Current Load**

```bash
# Check queue depth
docker exec rabbitmq rabbitmqctl list_queues | grep content_analysis_v2_queue

# If messages < 100, safe to scale down
```

**Step 2: Update Configuration**

```yaml
deploy:
  replicas: 2  # Reduced from 5
```

**Step 3: Graceful Scale-Down**

```bash
# Let workers finish current messages (up to 30s)
docker compose up -d --scale content-analysis-v2=2

# Docker will:
# 1. Stop new message consumption on 3 workers
# 2. Wait for in-progress messages to complete
# 3. Shut down extra workers gracefully
```

**Step 4: Verify Scale-Down**

```bash
# Should show 2 workers
docker compose ps content-analysis-v2

# Check consumers
docker exec rabbitmq rabbitmqctl list_consumers | grep content_analysis
# Expected: 2 consumers
```

---

### Emergency Scaling (Breaking News)

**Scenario:** Sudden traffic spike (5,000 articles in queue)

**Quick Scale-Up:**

```bash
# Scale to 10 workers immediately
docker compose up -d --scale content-analysis-v2=10

# Monitor queue drain rate
watch -n 5 'docker exec rabbitmq rabbitmqctl list_queues name messages consumers'
```

**Expected Drain Rate:**

```
10 workers × 3,600 seconds/hour / 18s avg processing
= 36,000 / 18
= 2,000 articles/hour

5,000 article backlog / 2,000 per hour
= 2.5 hours to clear backlog
```

**Scale Back Down After Spike:**

```bash
# When queue < 100 messages
docker compose up -d --scale content-analysis-v2=3
```

---

## Monitoring

### Key Metrics to Track

**1. Queue Depth**

```bash
# Real-time queue monitoring
watch -n 2 'docker exec rabbitmq rabbitmqctl list_queues name messages consumers message_stats'
```

**Interpretation:**
- `messages < 100`: Healthy, workers keeping up
- `messages 100-500`: Monitor closely, consider scaling up
- `messages > 500`: Scale up immediately

**2. Worker Health**

```bash
# Check all workers are running
docker compose ps content-analysis-v2

# Check for restart loops
docker stats --no-stream | grep content-analysis-v2
```

**3. Processing Rate**

```bash
# Prometheus metrics
curl localhost:8000/metrics | grep pipeline_processing_duration_seconds_count

# Calculate rate
# (current_count - previous_count) / time_elapsed = articles/second
```

**4. Resource Usage**

```bash
# Memory usage per worker
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}" | grep content-analysis-v2

# Expected per worker:
# Memory: 2-4GB
# CPU: 20-50% (spikes to 80% during processing)
```

### Prometheus Queries

**Processing Rate (Last 5 Minutes):**
```promql
rate(pipeline_articles_total{status="success"}[5m]) * 60
```

**Average Processing Time:**
```promql
rate(pipeline_processing_duration_seconds_sum[5m])
/
rate(pipeline_processing_duration_seconds_count[5m])
```

**Queue Depth:**
```promql
queue_size_current{queue_name="content_analysis_v2_queue"}
```

**Worker Utilization:**
```promql
worker_message_processing_current / worker_active_count
```

### Grafana Dashboard

**Create Dashboard with Panels:**

1. **Queue Depth** (Graph)
   - Query: `queue_size_current{queue_name="content_analysis_v2_queue"}`
   - Alert: > 1000 messages

2. **Processing Rate** (Stat)
   - Query: `rate(pipeline_articles_total[1m]) * 60`
   - Unit: articles/min

3. **Worker Count** (Stat)
   - Query: `worker_active_count`

4. **Success Rate** (Gauge)
   - Query: `100 * rate(pipeline_articles_total{status="success"}[5m]) / rate(pipeline_articles_total[5m])`
   - Target: > 99%

5. **Avg Processing Time** (Graph)
   - Query: `rate(pipeline_processing_duration_seconds_sum[5m]) / rate(pipeline_processing_duration_seconds_count[5m])`
   - Target: < 20s

---

## Troubleshooting

### Workers Not Starting

**Symptoms:**
```bash
docker compose ps content-analysis-v2
# Shows: Restarting, Exit 1
```

**Debug:**

```bash
# Check logs for error
docker compose logs content-analysis-v2 --tail 100

# Common errors:
```

**Error 1: Database Connection Failed**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Fix:**
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection from worker
docker exec news-microservices-content-analysis-v2-1 \
  pg_isready -h postgres -p 5432
```

**Error 2: RabbitMQ Connection Failed**
```
ConnectionError: [Errno 111] Connection refused
```

**Fix:**
```bash
# Check RabbitMQ is running
docker compose ps rabbitmq

# Check from worker
docker exec news-microservices-content-analysis-v2-1 \
  nc -zv rabbitmq 5672
```

**Error 3: Missing API Key**
```
google.api_core.exceptions.Unauthenticated: API key not valid
```

**Fix:**
```bash
# Check .env file
cat services/content-analysis-v2/.env | grep GEMINI_API_KEY

# Update if missing
echo "GEMINI_API_KEY=your_key_here" >> services/content-analysis-v2/.env

# Restart workers
docker compose restart content-analysis-v2
```

---

### Workers Consuming But Not Processing

**Symptoms:**
- Queue depth constant
- Logs show "message received" but no "pipeline completed"
- Workers show high CPU but no database writes

**Debug:**

```bash
# Check worker logs for pipeline errors
docker logs news-microservices-content-analysis-v2-1 --tail 100 | grep -i error

# Check database connectivity
docker exec news-microservices-content-analysis-v2-1 \
  psql -h postgres -U news_user -d news_mcp -c "SELECT 1"
```

**Common Causes:**

1. **LLM API Timeout**
   - Symptom: Logs show "Request timeout"
   - Fix: Increase PIPELINE_TIMEOUT in .env

2. **Database Deadlock**
   - Symptom: Logs show "Deadlock detected"
   - Fix: Check for long-running transactions, increase connection pool

3. **Memory Exhaustion**
   - Symptom: Worker OOM killed
   - Fix: Increase Docker memory limit or reduce MAX_CONCURRENT_AGENTS

---

### High DLQ Rate

**Symptoms:**
```bash
# Check DLQ size
docker exec rabbitmq rabbitmqctl list_queues | grep dlq

# Shows: content_analysis_v2_queue_dlq  523
```

**Analyze DLQ Messages:**

```bash
# Get sample messages from DLQ
docker exec rabbitmq rabbitmqadmin get queue=content_analysis_v2_queue_dlq count=10

# Common error types:
```

**Error 1: Invalid Message Format**
```json
{
  "error": "missing article_id"
}
```

**Fix:** Fix upstream publisher (feed-service)

**Error 2: Pipeline Execution Failed**
```json
{
  "error": "LLM API error: rate limit exceeded"
}
```

**Fix:**
- Add retry logic for rate limits
- Increase API quota
- Reduce worker count to stay within rate limits

**Republish Fixed Messages:**

```bash
# After fixing root cause, republish from DLQ
docker exec rabbitmq rabbitmqadmin get queue=content_analysis_v2_queue_dlq count=100 > dlq_messages.json

# Manual republish (or script it)
python scripts/republish_dlq.py dlq_messages.json
```

---

### Uneven Load Distribution

**Symptoms:**
- Worker 1: 1000 messages processed
- Worker 2: 100 messages processed
- Worker 3: 50 messages processed

**Possible Causes:**

1. **Different Processing Times**
   - Some articles much longer/complex
   - Normal behavior (self-balancing)

2. **Worker Restarted**
   - Worker 3 recently restarted, catching up
   - Check restart count: `docker compose ps`

3. **QoS Not Configured**
   - Check worker code for `channel.set_qos(prefetch_count=1)`
   - Without QoS, RabbitMQ pre-distributes messages

**Verify QoS:**

```bash
# Check RabbitMQ consumer prefetch count
docker exec rabbitmq rabbitmqctl list_consumers | grep content_analysis

# Should show: prefetch_count=1
```

---

## Best Practices

### Development Environment

**Use 1-2 Workers:**
```yaml
deploy:
  replicas: 1  # Development
```

**Reasons:**
- Easier debugging (single log stream)
- Lower resource usage
- Faster startup time

### Staging Environment

**Use Production-Like Configuration:**
```yaml
deploy:
  replicas: 3  # Same as production
```

**Test Scenarios:**
- Worker crash recovery
- Scaling up/down
- DLQ handling
- Peak load simulation

### Production Environment

**Start Conservative:**
```yaml
deploy:
  replicas: 3  # Initial production deployment
```

**Monitor for 1 Week:**
- Track queue depth patterns
- Identify peak hours
- Measure actual processing times
- Calculate cost per article

**Scale Based on Data:**
- If queue depth consistently > 500: Scale up
- If queue depth always < 50: Scale down
- If processing time > 25s: Optimize pipeline or scale up

### Capacity Planning

**Always Plan for:**

1. **20% Peak Buffer**
   - If avg is 10,000 articles/day, plan for 12,000

2. **Breaking News Spikes**
   - Major events can 5x-10x normal traffic
   - Keep scale-up procedure documented and tested

3. **Gradual Growth**
   - Traffic typically grows 10-20% per month
   - Review capacity quarterly

### Cost Optimization

**Tier 2 Skip Rate:**
```
Current: 40-60% of articles skip Tier 2
Savings: ~35% cost reduction

Monitor: If skip rate < 30%, tune TIER2_PRIORITY_THRESHOLD
```

**Worker Right-Sizing:**
```
Over-provisioned: 3 workers, queue always empty → Waste
Under-provisioned: 3 workers, queue growing → Lost revenue

Target: Queue depth 50-200 messages during peak hours
```

**Auto-Scaling (Future):**
```bash
# Pseudo-code for auto-scaling script
if queue_depth > 500:
    scale_up(current_workers + 2)
elif queue_depth < 50 and current_workers > 3:
    scale_down(current_workers - 1)
```

---

## Appendix

### Quick Reference

**Start Workers:**
```bash
docker compose up -d content-analysis-v2
```

**Scale Workers:**
```bash
docker compose up -d --scale content-analysis-v2=5
```

**Check Status:**
```bash
docker compose ps content-analysis-v2
```

**View Logs:**
```bash
docker compose logs content-analysis-v2 -f
```

**Restart Workers:**
```bash
docker compose restart content-analysis-v2
```

**Stop Workers:**
```bash
docker compose stop content-analysis-v2
```

**Check Queue:**
```bash
docker exec rabbitmq rabbitmqctl list_queues name messages consumers
```

### Resource Limits

**Set in docker-compose.yml:**

```yaml
content-analysis-v2:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2.0'
        memory: 4GB
      reservations:
        cpus: '1.0'
        memory: 2GB
```

**Calculate Total Resources:**
```
3 workers × 4GB limit = 12GB total
3 workers × 2 CPU limit = 6 CPUs total
```

---

## Support

For issues or questions:

1. **Check Logs:** `docker compose logs content-analysis-v2 --tail 200`
2. **Review Documentation:** `/docs/services/content-analysis-v2.md`
3. **Check Metrics:** `curl localhost:8000/metrics`
4. **RabbitMQ UI:** `http://localhost:15672`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-26
**Maintained By:** Development Team
