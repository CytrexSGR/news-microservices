# Entity Canonicalization Service

**Version:** 2.0.0 (Hybrid Async/HTTP)
**Port:** 8112 (HTTP), 9112 (Metrics)
**Language:** Python 3.11
**Framework:** FastAPI

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Async Integration (RabbitMQ)](#async-integration-rabbitmq)
5. [Configuration](#configuration)
6. [Database Schema](#database-schema)
7. [Performance](#performance)
8. [Monitoring](#monitoring)
9. [Development](#development)
10. [Enhanced Entity Resolution (Epic 1.4)](#enhanced-entity-resolution-epic-14)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Entity Canonicalization Service maps entity mentions (e.g., "München", "Munich", "Muenchen") to canonical forms with Wikidata IDs. This service ensures consistent entity representation across the news platform.

### Key Features

✅ **High Cache Hit Rate:** 89-90% (6,488+ canonical entities, 8,325+ aliases)
✅ **Fast Response:** < 10ms for cached entities
✅ **Wikidata Integration:** Automatic lookup for cache misses
✅ **Batch Processing:** Optimized for 10-20 entities per batch
✅ **Hybrid Architecture:** Async (RabbitMQ) + HTTP fallback
✅ **Prometheus Metrics:** Comprehensive monitoring

### Use Cases

1. **n8n Workflow Orchestration:** Entity-to-Knowledge-Graph workflow (primary)
2. **ML Model Integration:** Content analysis pipeline
3. **Knowledge Graph Construction:** Entity relationship mapping
4. **Research & OSINT:** Entity disambiguation for intelligence gathering

---

## Architecture

### Hybrid Async/HTTP Architecture (v2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                     n8n Workflow                            │
│                                                             │
│  ┌──────────────┐      ┌─────────────────────────────┐    │
│  │ Fetch        │      │  Canonicalization Strategy  │    │
│  │ Unprocessed  │─────▶│  - Priority: High? → HTTP   │    │
│  │ Entities     │      │  - Default → RabbitMQ       │    │
│  └──────────────┘      └─────────────────────────────┘    │
│                          │                    │            │
│                          ▼                    ▼            │
│                   ┌──────────┐       ┌────────────────┐   │
│                   │   HTTP   │       │   RabbitMQ     │   │
│                   │ Request  │       │   Publish      │   │
│                   └──────────┘       └────────────────┘   │
│                          │                    │            │
└──────────────────────────┼────────────────────┼────────────┘
                           │                    │
                           ▼                    ▼
                ┌──────────────────────────────────────┐
                │  Entity Canonicalization Service     │
                │                                      │
                │  ┌────────────┐  ┌───────────────┐ │
                │  │    HTTP    │  │   RabbitMQ    │ │
                │  │  Endpoint  │  │   Consumer    │ │
                │  └────────────┘  └───────────────┘ │
                │         │               │          │
                │         └───────┬───────┘          │
                │                 ▼                  │
                │      ┌────────────────────┐       │
                │      │ Canonicalization   │       │
                │      │ Logic (Shared)     │       │
                │      └────────────────────┘       │
                │                 │                  │
                │                 ▼                  │
                │      ┌────────────────────┐       │
                │      │ PostgreSQL + Cache │       │
                │      └────────────────────┘       │
                └──────────────────────────────────┘
```

### Components

1. **HTTP Endpoint:** FastAPI REST API (Port 8112)
2. **RabbitMQ Consumer:** Async message queue consumer
3. **Wikidata Client:** External API integration with retry logic
4. **PostgreSQL Database:** Canonical entities + aliases (news_mcp.public)
5. **Prometheus Exporter:** Metrics endpoint (Port 9112)

---

## API Endpoints

### Health Check

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-10-29T10:00:00Z"
}
```

### Single Entity Canonicalization

**POST** `/api/v1/canonicalization/canonicalize`

**Request:**
```json
{
  "entity_name": "München",
  "entity_type": "LOCATION",
  "language": "de"
}
```

**Response:**
```json
{
  "canonical_name": "Munich",
  "wikidata_id": "Q1726",
  "entity_type": "LOCATION",
  "confidence": 1.0,
  "source": "exact",
  "processing_time_ms": 2.1
}
```

### Batch Entity Canonicalization

**POST** `/api/v1/canonicalization/canonicalize/batch`

**Request:**
```json
{
  "entities": [
    {
      "entity_name": "Berlin",
      "entity_type": "LOCATION",
      "language": "de"
    },
    {
      "entity_name": "München",
      "entity_type": "LOCATION",
      "language": "de"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "canonical_name": "Berlin",
      "wikidata_id": "Q64",
      "entity_type": "LOCATION",
      "confidence": 1.0,
      "source": "exact"
    },
    {
      "canonical_name": "Munich",
      "wikidata_id": "Q1726",
      "entity_type": "LOCATION",
      "confidence": 1.0,
      "source": "exact"
    }
  ],
  "cache_hit_rate": 1.0,
  "processing_time_ms": 19.3
}
```

### Metrics Endpoint

**GET** `/metrics` (Port 9112)

**Response:** Prometheus-formatted metrics

---

## Async Integration (RabbitMQ)

### Message Queue Architecture

**Exchange:** `news.events` (topic, durable)
**Request Queue:** `canonicalization.requests` (durable, DLQ enabled)
**Response Pattern:** `canonicalization.batch.response.<correlation_id>`
**Dead Letter Queue:** `canonicalization.requests.dlq`

### Request Message Format

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "660e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-29T10:00:00Z",
  "requester": "n8n-workflow-5o3ZjyhLELti9its",
  "priority": "normal",
  "timeout_ms": 120000,
  "payload": {
    "article_id": "770e8400-e29b-41d4-a716-446655440000",
    "agent_result_id": "550e8400-e29b-41d4-a716-446655440000",
    "entities": [
      {
        "entity_name": "Berlin",
        "entity_type": "LOCATION",
        "language": "de"
      }
    ]
  }
}
```

### Response Message Format

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-29T10:00:01.234Z",
  "status": "success",
  "payload": {
    "results": [
      {
        "canonical_name": "Berlin",
        "wikidata_id": "Q64",
        "entity_type": "LOCATION",
        "confidence": 1.0,
        "source": "exact"
      }
    ],
    "cache_hit_rate": 1.0,
    "processing_time_ms": 12.5
  }
}
```

### Error Message Format

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-29T10:00:01.234Z",
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid entity type",
    "details": {
      "entity_name": "Unknown",
      "entity_type": "INVALID"
    }
  }
}
```

### Consumer Configuration

**File:** `app/rabbitmq_consumer.py`

```python
from aio_pika import connect_robust, Message, DeliveryMode

class CanonicalizationConsumer:
    PREFETCH_COUNT = 5  # Concurrent message processing
    QUEUE_MAX_LENGTH = 10000
    MESSAGE_TTL = 300000  # 5 minutes

    async def connect(self):
        self.connection = await connect_robust(
            settings.RABBITMQ_URL,
            timeout=30
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.PREFETCH_COUNT)
        # ... (see rabbitmq_consumer.py for full implementation)
```

### When to Use Async vs HTTP

| Scenario | Use | Rationale |
|----------|-----|-----------|
| **n8n Workflow (Default)** | Async | Queue visibility, retry logic, DLQ |
| **High-Priority User Request** | HTTP | Immediate response, no queue delay |
| **RabbitMQ Downtime** | HTTP | Fallback ensures zero downtime |
| **Debugging/Testing** | HTTP | Direct curl access, easier debugging |
| **ML Model Integration** | Async | Better for batch processing pipelines |

---

## Configuration

### Environment Variables

**File:** `.env` (or `docker-compose.yml`)

```bash
# Database
DATABASE_URL=postgresql://news_user:news_password@postgres:5432/news_mcp

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_REQUEST_QUEUE=canonicalization.requests
RABBITMQ_RESPONSE_ROUTING_KEY=canonicalization.batch.response

# Consumer Settings
PREFETCH_COUNT=5
QUEUE_MAX_LENGTH=10000
MESSAGE_TTL=300000  # 5 minutes

# Wikidata API
WIKIDATA_API_URL=https://www.wikidata.org/w/api.php
WIKIDATA_TIMEOUT=30  # seconds
WIKIDATA_RETRY_COUNT=3
WIKIDATA_RETRY_DELAY=2  # seconds

# Service
LOG_LEVEL=INFO
PORT=8112
METRICS_PORT=9112
```

### Service Settings

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    RABBITMQ_EXCHANGE: str = "news.events"
    RABBITMQ_REQUEST_QUEUE: str = "canonicalization.requests"
    RABBITMQ_RESPONSE_ROUTING_KEY: str = "canonicalization.batch.response"

    # Consumer
    PREFETCH_COUNT: int = 5
    QUEUE_MAX_LENGTH: int = 10000
    MESSAGE_TTL: int = 300000

    # Wikidata
    WIKIDATA_API_URL: str = "https://www.wikidata.org/w/api.php"
    WIKIDATA_TIMEOUT: int = 30
    WIKIDATA_RETRY_COUNT: int = 3
    WIKIDATA_RETRY_DELAY: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## Database Schema

### Tables

#### `canonical_entities`

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PRIMARY KEY | Unique entity ID |
| `name` | VARCHAR(255) NOT NULL | Canonical entity name (e.g., "Berlin") |
| `wikidata_id` | VARCHAR(20) UNIQUE | Wikidata identifier (e.g., "Q64") |
| `type` | VARCHAR(50) | Entity type (PERSON, LOCATION, ORGANIZATION, etc.) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes:**
- `idx_canonical_entities_wikidata_id` on `wikidata_id`
- `idx_canonical_entities_name` on `name`

#### `entity_aliases`

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PRIMARY KEY | Unique alias ID |
| `canonical_id` | INTEGER NOT NULL | Foreign key to `canonical_entities.id` |
| `alias` | VARCHAR(255) NOT NULL | Entity alias (e.g., "München" → Munich) |
| `created_at` | TIMESTAMP | Creation timestamp |

**Indexes:**
- `idx_entity_aliases_alias` on `alias`
- `idx_entity_aliases_canonical_id` on `canonical_id`

**Foreign Keys:**
- `canonical_id` → `canonical_entities.id` (ON DELETE CASCADE)

### Sample Data

```sql
-- Canonical entity: Munich
INSERT INTO canonical_entities (name, wikidata_id, type)
VALUES ('Munich', 'Q1726', 'LOCATION');

-- Aliases for Munich
INSERT INTO entity_aliases (canonical_id, alias)
VALUES
  (8041, 'München'),
  (8041, 'Muenchen'),
  (8041, 'Munich');
```

### Database Stats (as of 2025-10-29)

- **Canonical Entities:** 6,488
- **Entity Aliases:** 8,325
- **Cache Hit Rate:** 89-90%
- **Database Size:** ~15 MB

---

## Performance

### Latency Benchmarks (Checkpoint 5 Testing)

| Scenario | Latency | Cache Status |
|----------|---------|--------------|
| Single entity (cached) | 9-11ms | 100% hit |
| Batch (10 entities, all cached) | 19ms | 100% hit |
| Batch (10 entities, 1 miss) | 2.7-3.9s | 90% hit |
| Batch (10 entities, 5 misses) | 12-16s | 50% hit |

### Performance Characteristics

**Cache Hits (89-90% of requests):**
- Latency: < 10ms per entity
- Throughput: ~1000 entities/second
- Bottleneck: PostgreSQL query (< 1ms)

**Cache Misses (10-11% of requests):**
- Latency: 2-20 seconds per entity
- Throughput: ~5 entities/minute
- Bottleneck: Wikidata API external call

**Key Insight:** Wikidata API is the PRIMARY bottleneck, not HTTP overhead

### Async vs HTTP Overhead

- **HTTP:** ~934ms (batch of 10 with 1 cache miss)
- **Async:** ~955ms (batch of 10 with 1 cache miss)
- **Overhead:** +20ms for RabbitMQ round-trip

**Conclusion:** Async is NOT faster, but MORE RELIABLE (retry logic, DLQ, timeout handling)

### Batch Size Optimization

| Batch Size | Avg Latency | Cache Hit Rate | Recommendation |
|------------|-------------|----------------|----------------|
| 5 entities | 432ms | 89% | Too small |
| **10 entities** | **864ms** | **89%** | **✅ Optimal** |
| 15 entities | 93.4s | 89% | Performance cliff |
| 20 entities | 127s | 89% | Too slow |

**Recommendation:** Batch size 10 for production (confirmed by testing)

---

## Monitoring

### Prometheus Metrics

**Endpoint:** `http://localhost:9112/metrics`

#### Custom Metrics

```python
# Request metrics
canonicalization_requests_total = Counter(
    "canonicalization_requests_total",
    "Total canonicalization requests",
    ["method", "status"]
)

canonicalization_async_requests_total = Counter(
    "canonicalization_async_requests_total",
    "Total async requests via RabbitMQ",
    ["status"]
)

# Processing duration
canonicalization_processing_duration_seconds = Histogram(
    "canonicalization_processing_duration_seconds",
    "Processing duration in seconds",
    ["method", "cache_status"]
)

# Cache metrics
canonicalization_cache_hits_total = Counter(
    "canonicalization_cache_hits_total",
    "Total cache hits"
)

canonicalization_cache_misses_total = Counter(
    "canonicalization_cache_misses_total",
    "Total cache misses"
)

# Queue metrics
canonicalization_queue_depth = Gauge(
    "canonicalization_queue_depth",
    "Current queue depth"
)

canonicalization_dlq_depth = Gauge(
    "canonicalization_dlq_depth",
    "Current DLQ depth (critical if > 10)"
)

# Error metrics
canonicalization_errors_total = Counter(
    "canonicalization_errors_total",
    "Total errors",
    ["error_type"]
)

canonicalization_retry_total = Counter(
    "canonicalization_retry_total",
    "Total retry attempts",
    ["reason"]
)

# Wikidata API metrics
canonicalization_wikidata_requests_total = Counter(
    "canonicalization_wikidata_requests_total",
    "Total Wikidata API requests",
    ["status"]
)

canonicalization_wikidata_latency_seconds = Histogram(
    "canonicalization_wikidata_latency_seconds",
    "Wikidata API latency"
)
```

### Grafana Dashboard

**Import:** See [CANONICALIZATION_MONITORING.md](../../userdocs/n8n/CANONICALIZATION_MONITORING.md)

**Key Panels:**
1. **Queue Depth** (alert if > 100)
2. **DLQ Depth** (critical if > 10)
3. **Processing Duration** (p95, p99)
4. **Cache Hit Rate** (target: 89-90%)
5. **Error Rate** (target: < 1%)
6. **HTTP Fallback Rate** (target: < 1%)

### Alerting Rules

**Prometheus Alert Rules:**

```yaml
- alert: CanonicalizationDLQHigh
  expr: canonicalization_dlq_depth > 10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "DLQ depth > 10, investigate failed requests"

- alert: CanonicalizationQueueBacklog
  expr: canonicalization_queue_depth > 100
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Queue backlog > 100, consider scaling"

- alert: CanonicalizationErrorRate
  expr: rate(canonicalization_errors_total[15m]) / rate(canonicalization_requests_total[15m]) > 0.05
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Error rate > 5%"
```

---

## Development

### Local Setup

```bash
# 1. Navigate to service directory
cd /home/cytrex/news-microservices/services/entity-canonicalization-service

# 2. Install dependencies (if running locally, not in Docker)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start service via Docker Compose (recommended)
cd ../..
docker compose up -d entity-canonicalization

# 4. Verify service is running
curl http://localhost:8112/health
```

### Testing

```bash
# Test single entity
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "Berlin", "entity_type": "LOCATION", "language": "de"}'

# Expected response:
# {"canonical_name":"Berlin","wikidata_id":"Q64","entity_type":"LOCATION","confidence":1.0,"source":"exact","processing_time_ms":2.1}

# Test batch
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize/batch \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"entity_name": "Berlin", "entity_type": "LOCATION", "language": "de"},
      {"entity_name": "München", "entity_type": "LOCATION", "language": "de"}
    ]
  }'
```

### Code Structure

```
services/entity-canonicalization-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings
│   ├── rabbitmq_consumer.py    # Async consumer
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── canonicalization.py  # HTTP endpoints
│   ├── models/
│   │   └── database.py         # SQLAlchemy models
│   ├── clients/
│   │   └── wikidata_client.py  # Wikidata API integration
│   └── utils/
│       └── metrics.py          # Prometheus metrics
├── requirements.txt
├── Dockerfile
└── README.md (this file)
```

### Running Tests

```bash
# Unit tests
pytest tests/test_canonicalization.py -v

# Integration tests (requires Docker)
pytest tests/test_integration.py -v

# Performance tests
pytest tests/test_performance.py -v

# Cache performance test
bash /tmp/test_cache_performance.sh
```

### Adding New Entities

```sql
-- Add canonical entity
INSERT INTO canonical_entities (name, wikidata_id, type)
VALUES ('Paris', 'Q90', 'LOCATION')
RETURNING id;

-- Add aliases
INSERT INTO entity_aliases (canonical_id, alias)
VALUES
  (12345, 'Paris'),
  (12345, 'París'),
  (12345, 'Parigi');
```

---

## Enhanced Entity Resolution (Epic 1.4)

### Type-Aware Matching

The service now supports different matching strategies based on alias type:

| Alias Type | Strategy | Case Sensitive | Example |
|------------|----------|----------------|---------|
| `ticker` | Exact match | Yes | AAPL, MSFT |
| `abbreviation` | Exact match | No | USA, EU |
| `nickname` | Lenient fuzzy (70%) | No | "The Donald" |
| `name` | Standard fuzzy (95%) | No | "Apple Inc." |

### Fragmentation Metrics

New endpoints for analyzing entity fragmentation:

```bash
# Get fragmentation report
curl http://localhost:8112/api/v1/fragmentation/report?entity_type=ORGANIZATION

# Find potential duplicates
curl http://localhost:8112/api/v1/fragmentation/duplicates?entity_type=PERSON&threshold=0.90

# Get singleton entities (high risk)
curl http://localhost:8112/api/v1/fragmentation/singletons?entity_type=LOCATION
```

### Performance Targets

- Exact match: < 10ms
- Fuzzy match (1000 candidates): < 50ms
- Type-aware match: < 50ms

### Usage Tracking

Aliases now track usage count for ranking:

```sql
SELECT alias, usage_count FROM entity_aliases
ORDER BY usage_count DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue 1: Service Not Starting

**Symptoms:**
```
ERROR: Failed to connect to database
ERROR: Failed to connect to RabbitMQ
```

**Solution:**
```bash
# Check PostgreSQL
docker ps | grep postgres

# Check RabbitMQ
docker ps | grep rabbitmq

# Verify connection from service
docker exec news-entity-canonicalization-1 ping postgres
docker exec news-entity-canonicalization-1 ping rabbitmq
```

### Issue 2: Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 85%
- Processing latency increased

**Diagnosis:**
```sql
-- Check entity count
SELECT COUNT(*) FROM canonical_entities;

-- Check alias count
SELECT COUNT(*) FROM entity_aliases;

-- Find entities without aliases
SELECT ce.name, ce.wikidata_id
FROM canonical_entities ce
LEFT JOIN entity_aliases ea ON ce.id = ea.canonical_id
WHERE ea.id IS NULL;
```

**Solution:**
- Add missing entities via Wikidata lookup
- Add common aliases (München, Muenchen, etc.)

### Issue 3: Wikidata API Timeout

**Symptoms:**
- Processing latency > 30s
- Errors: "Wikidata API timeout"

**Solution:**
```python
# Increase timeout in config.py
WIKIDATA_TIMEOUT: int = 60  # from 30
WIKIDATA_RETRY_COUNT: int = 5  # from 3
```

### Issue 4: DLQ Messages Accumulating

**Symptoms:**
- DLQ depth > 0
- Alert: "CanonicalizationDLQHigh"

**Diagnosis:**
```bash
# Get DLQ messages
docker exec news-rabbitmq rabbitmqadmin get queue=canonicalization.requests.dlq count=10

# Check service logs
docker logs news-entity-canonicalization-1 | grep ERROR
```

**Common Causes:**
1. Invalid message format → Fix n8n workflow
2. Wikidata API error → Check API status
3. Database connection error → Check PostgreSQL health

---

## Related Documentation

- **Deployment Guide:** [CANONICALIZATION_DEPLOYMENT_GUIDE.md](../../userdocs/n8n/CANONICALIZATION_DEPLOYMENT_GUIDE.md)
- **Architecture Decision:** [ADR-031](../../docs/decisions/ADR-031-hybrid-async-http-canonicalization.md)
- **Async Architecture:** [CANONICALIZATION_ASYNC_ARCHITECTURE.md](../../userdocs/n8n/CANONICALIZATION_ASYNC_ARCHITECTURE.md)
- **Testing Report:** [CANONICALIZATION_TEST_REPORT.md](../../userdocs/n8n/CANONICALIZATION_TEST_REPORT.md)
- **Batch Analysis:** [CANONICALIZATION_BATCH_SIZE_ANALYSIS.md](../../userdocs/n8n/CANONICALIZATION_BATCH_SIZE_ANALYSIS.md)
- **n8n Patterns:** [CLAUDE.n8n.md](../../CLAUDE.n8n.md) - Critical Learning #37
- **Monitoring Spec:** [CANONICALIZATION_MONITORING.md](../../userdocs/n8n/CANONICALIZATION_MONITORING.md)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-29 | 2.0.0 | Hybrid Async/HTTP architecture implemented | System Architect |
| 2025-10-29 | 1.1.0 | München bug fixed (Q1726), batch optimization | System Architect |
| 2025-10-25 | 1.0.0 | Initial release (HTTP only) | Development Team |

---

**Questions or Issues?**

Contact: Entity Canonicalization Team
Documentation: `/home/cytrex/userdocs/n8n/`
Service: `entity-canonicalization-service` (Port 8112)
