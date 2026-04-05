# SITREP Service

**Version:** 1.0.0
**Port:** 8123 (HTTP), /metrics (Prometheus)
**Language:** Python 3.11
**Framework:** FastAPI

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Event Flow (RabbitMQ)](#event-flow-rabbitmq)
5. [Configuration](#configuration)
6. [Database Schema](#database-schema)
7. [Dependencies](#dependencies)
8. [Development](#development)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The SITREP (Situation Report) Service generates AI-powered intelligence briefings from aggregated news clusters. It consumes cluster events, ranks stories by relevance, and uses OpenAI GPT-4 to produce structured reports.

### Key Features

- **LLM-Powered Generation:** Uses OpenAI GPT-4o-mini for fast, cost-effective summarization
- **Event-Driven Architecture:** Consumes cluster events from RabbitMQ
- **Story Aggregation:** Ranks and prioritizes stories using time-decay relevance scoring
- **Scheduled Generation:** Automatic daily SITREP generation at configurable hour
- **Manual Generation:** On-demand SITREP generation via REST API
- **Structured Output:** Key developments, risk assessments, sentiment analysis
- **Token Tracking:** Monitors prompt/completion tokens for cost management

### Use Cases

1. **Daily Briefings:** Automated morning intelligence reports
2. **Breaking News Alerts:** Real-time reports for burst-detected clusters
3. **Weekly Summaries:** Aggregated analysis across longer time windows
4. **Decision Support:** Risk-assessed developments for stakeholders
5. **Trend Analysis:** Emerging signals detection and monitoring

---

## Architecture

### Component Overview

```
                                     ┌─────────────────────────────────────┐
                                     │         SITREP Service              │
                                     │          (Port 8123)                │
                                     └─────────────────┬───────────────────┘
                                                       │
                    ┌──────────────────────────────────┼──────────────────────────────────┐
                    │                                  │                                   │
                    ▼                                  ▼                                   ▼
        ┌───────────────────────┐      ┌───────────────────────────┐      ┌────────────────────────┐
        │   Cluster Consumer    │      │     REST API (FastAPI)    │      │  Scheduled Generator   │
        │   (RabbitMQ Events)   │      │    /api/v1/sitreps/*      │      │  (AsyncIO Scheduler)   │
        └───────────┬───────────┘      └───────────────┬───────────┘      └────────────┬───────────┘
                    │                                  │                               │
                    │                                  │                               │
                    ▼                                  │                               │
        ┌───────────────────────┐                      │                               │
        │   Story Aggregator    │◄─────────────────────┴───────────────────────────────┘
        │   (In-Memory Cache)   │
        │   + Relevance Scorer  │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SITREP Generator    │
        │   (OpenAI GPT-4)      │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SITREP Repository   │
        │   (PostgreSQL)        │
        └───────────────────────┘
```

### Components

1. **FastAPI Application** (`app/main.py`)
   - REST API endpoints (Port 8123)
   - Prometheus metrics endpoint
   - Health/readiness checks
   - Lifespan management (startup/shutdown)

2. **Cluster Consumer** (`app/workers/cluster_consumer.py`)
   - Consumes cluster events from RabbitMQ
   - Routes events to StoryAggregator
   - Handles reconnection and error recovery

3. **Story Aggregator** (`app/services/story_aggregator.py`)
   - Maintains in-memory story cache
   - Applies time-decay relevance scoring
   - Ranks stories by composite score
   - Provides top stories for SITREP generation

4. **Relevance Scorer** (`app/services/relevance_scorer.py`)
   - Time-decay algorithm for story freshness
   - Configurable decay rate and weighting
   - Breaking news boost factor

5. **SITREP Generator** (`app/services/sitrep_generator.py`)
   - Builds prompts from story data
   - Calls OpenAI GPT-4 API
   - Parses structured JSON responses
   - Handles retry logic and rate limits

6. **Scheduled Generator** (`app/workers/scheduled_generator.py`)
   - AsyncIO-based scheduler (no Celery dependency)
   - Configurable generation hour (default 6 AM UTC)
   - Automatic retry with exponential backoff

7. **SITREP Repository** (`app/repositories/sitrep_repository.py`)
   - PostgreSQL CRUD operations
   - Pagination and filtering support
   - Model-to-schema conversion

---

## API Endpoints

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "service": "sitrep-service"
}
```

### Readiness Check

**GET** `/ready`

```json
{
  "status": "ready"
}
```

### List SITREPs

**GET** `/api/v1/sitreps`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | `20` | Page size (1-100) |
| `offset` | int | `0` | Pagination offset |
| `report_type` | string | `null` | Filter: `daily`, `weekly`, `breaking` |

**Response:**
```json
{
  "sitreps": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "report_date": "2026-01-05",
      "report_type": "daily",
      "title": "Daily SITREP - 2026-01-05",
      "executive_summary": "Markets showed mixed signals...",
      "articles_analyzed": 150,
      "confidence_score": 0.85,
      "human_reviewed": false,
      "generation_model": "gpt-4o-mini",
      "generation_time_ms": 2500
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Get SITREP by ID

**GET** `/api/v1/sitreps/{sitrep_id}`

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "report_date": "2026-01-05",
  "report_type": "daily",
  "title": "Daily SITREP - 2026-01-05",
  "executive_summary": "Markets showed mixed signals...",
  "content_markdown": "# Daily Intelligence Briefing\n\n## Executive Summary\n...",
  "key_developments": [
    {
      "title": "Central Bank Policy Shift",
      "summary": "Federal Reserve signals rate adjustment...",
      "significance": "Major impact on market expectations",
      "risk_assessment": {
        "level": "high",
        "category": "economic",
        "description": "Potential market volatility"
      },
      "related_entities": ["Federal Reserve", "NYSE"]
    }
  ],
  "top_stories": [
    {
      "cluster_id": "660e8400-e29b-41d4-a716-446655440000",
      "title": "Fed Rate Decision Analysis",
      "article_count": 25,
      "tension_score": 8.5,
      "is_breaking": true,
      "category": "finance"
    }
  ],
  "key_entities": [
    {"name": "Federal Reserve", "type": "organization", "mention_count": 45}
  ],
  "sentiment_summary": {
    "overall": "mixed",
    "positive_percent": 35.0,
    "negative_percent": 30.0,
    "neutral_percent": 35.0
  },
  "emerging_signals": [
    {
      "signal_type": "trend",
      "description": "Increasing volatility in tech sector",
      "confidence": 0.75,
      "related_entities": ["NASDAQ", "Tech Index"]
    }
  ],
  "generation_model": "gpt-4-turbo-preview",
  "generation_time_ms": 2500,
  "prompt_tokens": 3500,
  "completion_tokens": 1200,
  "articles_analyzed": 150,
  "confidence_score": 0.85,
  "human_reviewed": false,
  "created_at": "2026-01-05T06:00:00Z"
}
```

### Get Latest SITREP

**GET** `/api/v1/sitreps/latest`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report_type` | string | `daily` | Type: `daily`, `weekly`, `breaking` |

Returns the most recently created SITREP of the specified type.

### Generate SITREP

**POST** `/api/v1/sitreps/generate`

**Request:**
```json
{
  "report_type": "daily",
  "report_date": "2026-01-05",
  "top_stories_count": 10,
  "min_cluster_size": 3
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated daily SITREP from 10 stories",
  "sitrep_id": "550e8400-e29b-41d4-a716-446655440000",
  "sitrep": { /* Full SitrepResponse */ }
}
```

### Mark SITREP as Reviewed

**PATCH** `/api/v1/sitreps/{sitrep_id}/review`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviewed` | bool | `true` | Review status |

### Delete SITREP

**DELETE** `/api/v1/sitreps/{sitrep_id}`

Returns `204 No Content` on success.

### Prometheus Metrics

**GET** `/metrics`

Returns Prometheus-formatted metrics.

---

## Event Flow (RabbitMQ)

### Consumed Events

The service subscribes to cluster events from the `news.events` exchange:

**Queue:** `sitrep_cluster_events`
**Exchange:** `news.events` (topic)
**Routing Keys:**
- `cluster.created`
- `cluster.updated`
- `cluster.burst_detected`

#### Event: `cluster.created`

New cluster created from seed article.

```json
{
  "event_type": "cluster.created",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "payload": {
    "cluster_id": "UUID",
    "title": "Article Title",
    "article_count": 1
  }
}
```

#### Event: `cluster.updated`

Article added to existing cluster.

```json
{
  "event_type": "cluster.updated",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "payload": {
    "cluster_id": "UUID",
    "article_count": 5,
    "tension_score": 7.5,
    "is_breaking": false,
    "primary_entities": [{"name": "Entity", "type": "ORG"}]
  }
}
```

#### Event: `cluster.burst_detected`

Breaking news threshold reached.

```json
{
  "event_type": "cluster.burst_detected",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "payload": {
    "cluster_id": "UUID",
    "title": "Breaking Story",
    "article_count": 10,
    "growth_rate": 2.0,
    "tension_score": 9.0,
    "severity": "high"
  }
}
```

### Event Flow Diagram

```
┌─────────────────────┐                              ┌─────────────────────┐
│ Clustering Service  │                              │   SITREP Service    │
│                     │     cluster.created          │                     │
│   cluster.created   │─────────────────────────────▶│  Cluster Consumer   │
│   cluster.updated   │─────────────────────────────▶│         │           │
│   cluster.burst     │─────────────────────────────▶│         ▼           │
│                     │                              │  Story Aggregator   │
└─────────────────────┘                              │  (ranks, caches)    │
                                                     │         │           │
                                                     │         ▼           │
                                   Scheduled ────────▶  SITREP Generator  │
                                   (6 AM UTC)        │  (OpenAI GPT-4)     │
                                                     │         │           │
                                                     │         ▼           │
                                                     │  PostgreSQL         │
                                                     │  (sitrep_reports)   │
                                                     └─────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Service
SERVICE_NAME=sitrep-service
SERVICE_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/news_intelligence

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_CLUSTER_QUEUE=sitrep_cluster_events

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.3

# SITREP Generation
SITREP_TOP_STORIES_COUNT=10        # Stories to include in report
SITREP_MIN_CLUSTER_SIZE=3          # Minimum articles per cluster
SITREP_GENERATION_HOUR=6           # Hour (0-23 UTC) for daily generation

# Relevance Scoring
DEFAULT_DECAY_RATE=0.05            # Time-decay rate for story freshness

# JWT Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

### Tuning Recommendations

| Parameter | Low Value | High Value | Effect |
|-----------|-----------|------------|--------|
| `SITREP_TOP_STORIES_COUNT` | 5 | 20 | Fewer = shorter reports, more = comprehensive |
| `SITREP_MIN_CLUSTER_SIZE` | 1 | 5 | Lower = more stories included, higher = quality filter |
| `DEFAULT_DECAY_RATE` | 0.01 | 0.1 | Lower = older stories stay relevant, higher = recent bias |
| `OPENAI_TEMPERATURE` | 0.0 | 0.7 | Lower = consistent output, higher = creative variation |

---

## Database Schema

### Table: `sitrep_reports`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique report identifier |
| `report_date` | DATE | Date of the report |
| `report_type` | VARCHAR(50) | `daily`, `weekly`, `breaking` |
| `title` | VARCHAR(200) | Report title |
| `executive_summary` | TEXT | High-level summary |
| `content_markdown` | TEXT | Full content in Markdown |
| `content_html` | TEXT | Optional HTML version |
| `top_stories` | JSONB | Array of story data |
| `key_entities` | JSONB | Array of entities |
| `sentiment_summary` | JSONB | Sentiment analysis |
| `emerging_signals` | JSONB | Detected patterns |
| `key_developments` | JSONB | Key developments with risk assessment |
| `generation_model` | VARCHAR(100) | LLM model used |
| `generation_time_ms` | INTEGER | Generation time in ms |
| `prompt_tokens` | INTEGER | Tokens in prompt |
| `completion_tokens` | INTEGER | Tokens in completion |
| `articles_analyzed` | INTEGER | Total articles analyzed |
| `confidence_score` | FLOAT | Confidence (0-1) |
| `human_reviewed` | BOOLEAN | Review status flag |
| `created_at` | TIMESTAMP (TZ) | Creation timestamp |

**Indexes:**
- Primary key on `id`
- Index on `report_type` for filtered queries
- Index on `report_date` for date-range queries
- Index on `created_at` for latest queries

---

## Dependencies

### Python Packages

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.25
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
aio-pika>=9.3.0
openai>=1.8.0
httpx>=0.26.0
prometheus-client>=0.19.0
python-json-logger>=2.0.7
python-jose[cryptography]>=3.3.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Shared Libraries

**news-intelligence-common**
- `create_event()` - EventEnvelope creation
- Standardized event format

**news-mcp-common**
- Common patterns and utilities

### Infrastructure Dependencies

| Service | Purpose |
|---------|---------|
| PostgreSQL | SITREP storage |
| RabbitMQ | Event consumption |
| OpenAI API | LLM generation |
| Prometheus | Metrics collection |

---

## Development

### Local Setup

```bash
# 1. Navigate to service directory
cd /home/cytrex/news-microservices/services/sitrep-service

# 2. Create virtual environment (optional for local development)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start via Docker Compose (recommended)
cd /home/cytrex/news-microservices
docker compose up -d sitrep-service

# 4. Verify service is running
curl http://localhost:8123/health
# Expected: {"status":"healthy","service":"sitrep-service"}
```

### Code Structure

```
services/sitrep-service/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Settings and configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── sitreps.py          # REST API endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py              # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── sitrep.py               # SQLAlchemy models
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── sitrep_repository.py    # Database CRUD operations
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── sitrep.py               # Pydantic API schemas
│   │   ├── story.py                # Story schemas
│   │   └── events.py               # Event payload schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sitrep_generator.py     # LLM generation logic
│   │   ├── story_aggregator.py     # Story ranking/caching
│   │   └── relevance_scorer.py     # Time-decay scoring
│   └── workers/
│       ├── __init__.py
│       ├── cluster_consumer.py     # RabbitMQ event consumer
│       └── scheduled_generator.py  # AsyncIO scheduler
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── test_cluster_consumer.py
│   ├── test_relevance_scorer.py
│   ├── test_scheduled_generator.py
│   ├── test_sitrep_generator.py
│   ├── test_sitrep_repository.py
│   ├── test_sitreps_api.py
│   ├── test_story_aggregator.py
│   └── integration/
│       ├── __init__.py
│       ├── test_api_integration.py
│       └── test_event_to_sitrep_flow.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### API Documentation

- **Swagger UI:** http://localhost:8123/docs
- **ReDoc:** http://localhost:8123/redoc
- **OpenAPI JSON:** http://localhost:8123/openapi.json

---

## Testing

### Run Unit Tests

```bash
# From service directory
cd /home/cytrex/news-microservices/services/sitrep-service

# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_sitrep_generator.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run only unit tests (exclude integration)
pytest tests/ -v --ignore=tests/integration
```

### Test API Endpoints

```bash
# Get auth token (use system credentials)
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r '.access_token')

# Health check
curl http://localhost:8123/health

# List SITREPs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/v1/sitreps?limit=5"

# Get latest daily SITREP
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/v1/sitreps/latest?report_type=daily"

# Generate SITREP manually
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "http://localhost:8123/api/v1/sitreps/generate" \
  -d '{"report_type":"daily","top_stories_count":10}'
```

### Test Coverage Summary

| Module | Coverage |
|--------|----------|
| `services/sitrep_generator.py` | ~90% |
| `services/story_aggregator.py` | ~95% |
| `services/relevance_scorer.py` | ~95% |
| `repositories/sitrep_repository.py` | ~85% |
| `workers/scheduled_generator.py` | ~85% |
| `api/v1/sitreps.py` | ~80% |

---

## Troubleshooting

### Issue 1: Service Not Starting

**Symptoms:**
```
ERROR: Failed to connect to PostgreSQL
ERROR: Failed to connect to RabbitMQ
```

**Solution:**
```bash
# Check PostgreSQL
docker ps | grep postgres
docker logs news-postgres-1

# Check RabbitMQ
docker ps | grep rabbitmq
docker logs news-rabbitmq-1

# Verify network connectivity
docker exec news-sitrep-service-1 ping postgres
docker exec news-sitrep-service-1 ping rabbitmq
```

### Issue 2: No SITREPs Being Generated

**Symptoms:**
- Scheduled generation not triggering
- Manual generation returns "No stories available"

**Diagnosis:**
```bash
# Check if cluster events are being received
docker logs news-sitrep-service-1 | grep "Processed event"

# Check story count in aggregator
curl http://localhost:8123/health  # Check logs for story count

# Check RabbitMQ queue
curl -u guest:guest http://localhost:15672/api/queues/%2F/sitrep_cluster_events
```

**Common Causes:**
1. Clustering service not running or not emitting events
2. Queue not bound to exchange correctly
3. `min_cluster_size` too high (no clusters meet threshold)

### Issue 3: OpenAI API Errors

**Symptoms:**
```
ERROR: OpenAI API error: Rate limit exceeded
ERROR: API timeout after 3 retries
```

**Solution:**
```bash
# Check API key configuration
docker exec news-sitrep-service-1 env | grep OPENAI

# Verify API key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits and usage
# Visit: https://platform.openai.com/usage
```

### Issue 4: High Generation Time

**Symptoms:**
- `generation_time_ms` > 30000
- Timeouts during generation

**Diagnosis:**
```bash
# Check LLM metrics
curl http://localhost:8123/metrics | grep sitrep

# Review prompt length
docker logs news-sitrep-service-1 | grep "Prompt length"
```

**Solution:**
- Reduce `SITREP_TOP_STORIES_COUNT`
- Reduce `OPENAI_MAX_TOKENS`
- Consider switching to faster model (gpt-4o-mini)

### Issue 5: Memory Usage Growing

**Symptoms:**
- Service memory increasing over time
- Story aggregator cache unbounded

**Diagnosis:**
```bash
# Check memory usage
docker stats news-sitrep-service-1

# Check story count (should be bounded)
docker logs news-sitrep-service-1 | grep "story_count"
```

**Solution:**
- Story aggregator automatically evicts old stories
- If issue persists, restart service
- Check for memory leaks in event processing

---

## Related Documentation

- **Architecture Overview:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
- **Backend Development Guide:** [CLAUDE.backend.md](../../CLAUDE.backend.md)
- **Clustering Service:** [services/clustering-service/README.md](../clustering-service/README.md)
- **Circuit Breaker Pattern:** [ADR-035](../../docs/decisions/ADR-035-circuit-breaker-pattern.md)
- **news-intelligence-common:** [libs/news-intelligence-common/](../../libs/news-intelligence-common/)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-05 | 1.0.0 | Initial release - Epic 1.5 SITREP Foundation | Development Team |

---

**Questions or Issues?**

- Documentation: `/home/cytrex/news-microservices/docs/`
- Service: `sitrep-service` (Port 8123)
- Swagger UI: http://localhost:8123/docs
