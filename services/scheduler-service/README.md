# Scheduler Service

**Port:** 8008
**Purpose:** Automated feed monitoring and analysis orchestration

## Overview

The Scheduler Service monitors all feeds with `auto_analyze_enabled=True` and orchestrates multi-stage content analysis by coordinating between Feed Service and Content Analysis Service.

## Architecture

### 3-Stage Analysis Model

```
Feed Configuration (Feed Service)
├── enable_categorization: bool           # Stage 1: Article Categorization
├── enable_finance_sentiment: bool        # Stage 2: Finance Sentiment
└── enable_geopolitical_sentiment: bool   # Stage 2: Geopolitical Sentiment
```

### Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Scheduler Service (8008)                     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Feed Monitor (every 60 seconds)                            │   │
│  │  - Query Feed Service for active feeds                      │   │
│  │  - Check for new articles (via Feed Service API)            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                  │                                  │
│                                  ▼                                  │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Analysis Orchestrator                                       │   │
│  │                                                              │   │
│  │  For each new article:                                       │   │
│  │                                                              │   │
│  │  Stage 1: Categorization (if enabled)                       │   │
│  │  POST /api/v1/analysis/topics                              │   │
│  │  → Returns: ["finance", "markets", "economy"]              │   │
│  │                                                              │   │
│  │  Stage 2: Specialized Sentiment (if enabled)                │   │
│  │  if "finance" in categories:                                │   │
│  │      POST /api/v1/analysis/finance-sentiment               │   │
│  │  if "geopolitical" in categories:                           │   │
│  │      POST /api/v1/analysis/geopolitical-sentiment          │   │
│  │                                                              │   │
│  │  Stage 3: Standard Sentiment (always)                       │   │
│  │  POST /api/v1/analysis/sentiment                            │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## User Workflow

### Step 1: Create Feed (Feed Service)
```bash
POST http://localhost:8001/api/v1/feeds
{
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed/",
  "fetch_interval": 60,
  "enable_categorization": false,        # Initially disabled
  "enable_finance_sentiment": false,
  "enable_geopolitical_sentiment": false
}
```

### Step 2: Let Articles Accumulate
User reviews articles manually for a period (e.g., 1 week).

### Step 3: Enable Categorization
```bash
PATCH http://localhost:8001/api/v1/feeds/{feed_id}
{
  "enable_categorization": true
}
```

Scheduler will now:
- Call `POST /api/v1/analysis/topics` for new articles
- Store categories in Analysis Service

### Step 4: Enable Finance + Geopolitical Sentiment
```bash
PATCH http://localhost:8001/api/v1/feeds/{feed_id}
{
  "enable_finance_sentiment": true,
  "enable_geopolitical_sentiment": true
}
```

Scheduler will now:
- Check if article has "finance" category → run finance sentiment
- Check if article has "geopolitical" category → run geopolitical sentiment
- Always run standard sentiment analysis

## Configuration

### Environment Variables

```env
# Service Configuration
SERVICE_NAME=scheduler-service
SERVICE_PORT=8008
LOG_LEVEL=INFO

# Feed Service
FEED_SERVICE_URL=http://feed-service:8001

# Content Analysis Service
ANALYSIS_SERVICE_URL=http://content-analysis-service:8002

# Polling Configuration
FEED_CHECK_INTERVAL=60  # seconds
MAX_CONCURRENT_ANALYSES=10
BATCH_SIZE=50  # articles per batch

# RabbitMQ (for event publishing)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_ROUTING_KEY_PREFIX=scheduler

# PostgreSQL (for scheduler state tracking)
DATABASE_URL=postgresql://user:password@postgres:5432/scheduler_db
```

## Database Schema

### Tables

#### `feed_schedule_state`
Tracks last processing time per feed to avoid duplicate work.

```sql
CREATE TABLE feed_schedule_state (
    id UUID PRIMARY KEY,
    feed_id UUID NOT NULL UNIQUE,  -- References Feed Service
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_article_processed_at TIMESTAMP WITH TIME ZONE,
    total_articles_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `analysis_job_queue`
Queue for pending analysis jobs.

```sql
CREATE TABLE analysis_job_queue (
    id UUID PRIMARY KEY,
    feed_id UUID NOT NULL,
    article_id UUID NOT NULL,
    job_type VARCHAR(50) NOT NULL,  -- 'categorization', 'finance_sentiment', 'geopolitical_sentiment', 'standard_sentiment'
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_analysis_job_status ON analysis_job_queue(status, priority DESC, created_at);
CREATE INDEX idx_analysis_job_article ON analysis_job_queue(article_id);
```

## API Endpoints

### Health Check
```http
GET /health
```

### Scheduler Status
```http
GET /api/v1/scheduler/status
```

Response:
```json
{
  "is_running": true,
  "active_feeds": 42,
  "pending_jobs": 127,
  "processing_jobs": 8,
  "last_check_at": "2025-10-13T16:30:00Z"
}
```

### Force Feed Check
```http
POST /api/v1/scheduler/feeds/{feed_id}/check
```

Triggers immediate check and analysis for a specific feed.

### Job Queue Stats
```http
GET /api/v1/scheduler/jobs/stats
```

Response:
```json
{
  "total_pending": 127,
  "total_processing": 8,
  "total_completed_24h": 1523,
  "total_failed_24h": 12,
  "avg_processing_time_ms": 2340,
  "by_type": {
    "categorization": 45,
    "finance_sentiment": 32,
    "geopolitical_sentiment": 18,
    "standard_sentiment": 32
  }
}
```

## Implementation Plan

### Phase 1: Service Skeleton
- [x] Create service directory structure
- [ ] Setup FastAPI application
- [ ] Database models and migrations
- [ ] Basic health check endpoint

### Phase 2: Feed Monitoring
- [ ] Implement Feed Service client
- [ ] Poll for new articles every 60 seconds
- [ ] Track last processed article per feed

### Phase 3: Analysis Orchestration
- [ ] Implement Content Analysis Service client
- [ ] Build 3-stage analysis pipeline
- [ ] Category-based routing logic

### Phase 4: Job Queue
- [ ] Implement job queue with priorities
- [ ] Retry logic with exponential backoff
- [ ] Concurrent job processing

### Phase 5: Event Publishing
- [ ] Publish scheduler events to RabbitMQ
- [ ] Event types: `scheduler.feed_checked`, `scheduler.analysis_started`, `scheduler.analysis_completed`

## ✅ Monitoring & Observability (STABILIZED - 2025-11-24)

### Prometheus Metrics

**Implementation:** `/app/core/metrics.py`

**Metrics Endpoint:** `GET /metrics`

#### Task Execution Metrics
- `scheduler_task_runs_total{task_name, status}` - Total task executions
- `scheduler_task_duration_seconds{task_name}` - Task duration histogram
- `scheduler_task_failures_total{task_name, error_type}` - Task failures
- `scheduler_task_retries_total{task_name, attempt}` - Retry attempts

#### Job Queue Metrics
- `scheduler_job_queue_size{status}` - Jobs by status (pending, processing, etc.)
- `scheduler_job_processing_duration_seconds{job_type}` - Processing duration
- `scheduler_job_queue_age_seconds{status}` - Time in queue

#### Feed Monitor Metrics
- `scheduler_feeds_checked_total{status}` - Feed check count
- `scheduler_articles_discovered_total{feed_category}` - New articles
- `scheduler_feed_check_duration_seconds` - Check cycle duration

#### Circuit Breaker Metrics
- `scheduler_circuit_breaker_state{service}` - Circuit state (CLOSED/OPEN/HALF_OPEN)
- `scheduler_circuit_breaker_failures_total{service}` - Failure count
- `scheduler_circuit_breaker_trips_total{service}` - State transitions to OPEN

#### HTTP Client Metrics
- `scheduler_http_requests_total{service, method, status_code}` - HTTP requests
- `scheduler_http_request_duration_seconds{service, method}` - Request duration

#### Service Health Metrics
- `scheduler_service_health` - Overall health (healthy/degraded/unhealthy)
- `scheduler_service_uptime_seconds` - Service uptime
- `scheduler_running{component}` - Component running status

### Health Check Endpoints

**Implementation:** `/app/api/health.py`

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `GET /health` | Comprehensive health | Detailed diagnostics |
| `GET /health/live` | Liveness probe | Kubernetes liveness |
| `GET /health/ready` | Readiness probe | Kubernetes readiness |
| `GET /health/startup` | Startup probe | Kubernetes startup |

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T12:00:00Z",
  "uptime_seconds": 3600.5,
  "version": "0.1.0",
  "components": {
    "database": {"status": "healthy", "response_time_ms": 5.2},
    "redis": {"status": "healthy"},
    "rabbitmq": {"status": "healthy"},
    "feed_service": {"status": "healthy", "response_time_ms": 12.5},
    "content_analysis_service": {"status": "healthy"},
    "feed_monitor": {"status": "healthy"},
    "job_processor": {"status": "healthy"},
    "cron_scheduler": {"status": "healthy"}
  },
  "summary": {"healthy": 8, "degraded": 0, "unhealthy": 0}
}
```

### Logs

- Feed check results
- Analysis job creation
- API call failures
- Retry attempts
- Circuit breaker state changes
- Error categorization

## Docker Compose

```yaml
scheduler-service:
  build: ./services/scheduler-service
  container_name: scheduler-service
  ports:
    - "8008:8008"
  environment:
    - SERVICE_NAME=scheduler-service
    - FEED_SERVICE_URL=http://feed-service:8001
    - ANALYSIS_SERVICE_URL=http://content-analysis-service:8002
    - DATABASE_URL=postgresql://scheduler:password@postgres:5432/scheduler_db
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    - postgres
    - rabbitmq
    - feed-service
    - content-analysis-service
  networks:
    - news-network
```

## ✅ Error Handling (STABILIZED - 2025-11-24)

### Retry Strategy

**Implementation:** `/app/core/error_handling.py`

| Error Type | Category | Action |
|------------|----------|--------|
| Feed Service unavailable | TRANSIENT | Exponential backoff (1s, 2s, 4s, 8s, max 60s) |
| Analysis Service unavailable | TRANSIENT | Exponential backoff with max 3 retries |
| Article not found (404) | PERMANENT | Skip, log warning, no retry |
| Analysis timeout (>30s) | TIMEOUT | Retry with same timeout |
| Rate limit (429) | RATE_LIMIT | Retry with 2x backoff |
| Connection refused | TRANSIENT | Exponential backoff |
| Invalid request (400-499) | PERMANENT | No retry |
| Server error (500-599) | TRANSIENT | Retry with backoff |

### Circuit Breaker Pattern

**Implementation:** `/app/core/error_handling.py`

- **States:** CLOSED → OPEN → HALF_OPEN
- **Failure Threshold:** 5 consecutive failures
- **Success Threshold:** 2 consecutive successes to close
- **Timeout:** 60 seconds before attempting recovery
- **Per-Service Tracking:** Separate circuit breakers for each external service

**Usage:**
```python
from app.core.error_handling import with_retry, RetryConfig, CircuitBreaker

circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

@with_retry(
    config=RetryConfig(max_retries=3, base_delay=1.0),
    circuit_breaker=circuit_breaker
)
async def fetch_data():
    # Automatic retry and circuit breaker protection
    pass
```

## ✅ Testing (STABILIZED - 2025-11-24)

**Test Coverage:** ~85% (Target: 80%+) ✅

### Unit Tests

**Files:**
- `tests/test_cron_scheduler.py` (40+ tests)
- `tests/test_job_processor.py` (35+ tests)
- `tests/test_feed_monitor.py` (30+ tests)

**Coverage:**
- Feed monitoring logic ✅
- Analysis orchestration rules ✅
- Category-based routing ✅
- Retry logic with exponential backoff ✅
- Circuit breaker state transitions ✅
- Error categorization ✅
- Job queue management ✅
- Health check endpoints ✅

### Integration Tests

- End-to-end flow: Feed → Categorization → F+G Sentiment → Standard Sentiment ✅
- Error handling and retries ✅
- Concurrent job processing ✅
- Database transactions and rollback ✅
- HTTP client mocking ✅
- APScheduler integration ✅

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run with HTML coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_cron_scheduler.py

# Run in parallel
pytest -n auto

# Run only unit tests
pytest -m unit

# View coverage report
open coverage_html/index.html
```

### Test Configuration

- **Framework:** pytest 8.2.0
- **Async Support:** pytest-asyncio 0.23.6
- **Coverage Target:** 80%+ (achieved: ~85%)
- **Fixtures:** Centralized in `tests/conftest.py`
- **Database:** SQLite in-memory for tests
- **Mocking:** pytest-mock, freezegun, responses

### Load Tests (TODO)

- 100 feeds with 1000 articles/hour
- Max job queue depth: 10,000
- Target throughput: 50 analyses/second

## See Also

- [Feed Service API](../feed-service/README.md)
- [Content Analysis Service API](../content-analysis-service/README.md)
- [Architecture Decision Records](../../docs/adr/)

## Documentation

- [Service Documentation](../../docs/services/scheduler-service.md)
- [API Documentation](../../docs/api/scheduler-service-api.md)
