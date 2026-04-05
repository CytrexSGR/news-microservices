# Scheduler Service Documentation

## Overview

The Scheduler Service orchestrates automated feed monitoring and multi-stage content analysis across the News Microservices platform. It acts as the central coordinator between Feed Service and Content Analysis Service, ensuring articles are analyzed systematically according to configured rules.

**Key Responsibilities:**
- Monitor active feeds for new articles (every 60 seconds)
- Queue analysis jobs based on feed configuration
- Process analysis jobs through Content Analysis Service
- Manage entity extraction and Knowledge Graph integration
- Provide flexible cron-style task scheduling
- Track processing state and prevent duplicate work

**Port:** 8008
**Status:** Production
**Version:** 0.1.0

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 14+
- Redis 7+
- RabbitMQ 3.12+
- Feed Service (port 8000)
- Content Analysis Service (port 8000)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd news-microservices/services/scheduler-service

# Start service
docker compose up -d scheduler-service

# Check health
curl http://localhost:8008/health
```

### Docker Compose Configuration

```yaml
scheduler-service:
  build:
    context: .
    dockerfile: services/scheduler-service/Dockerfile.dev
  container_name: scheduler-service
  ports:
    - "8008:8008"
  environment:
    - SERVICE_NAME=scheduler-service
    - SERVICE_PORT=8008
    - DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp
    - REDIS_URL=redis://:redis_secret_2024@redis:6379/0
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    - FEED_SERVICE_URL=http://feed-service:8000
    - CONTENT_ANALYSIS_URL=http://content-analysis-service:8000
    - FEED_CHECK_INTERVAL=60
    - JOB_PROCESS_INTERVAL=30
  depends_on:
    - postgres
    - redis
    - rabbitmq
    - feed-service
    - content-analysis-service
  volumes:
    - ./services/scheduler-service/app:/app/app
  networks:
    - news-network
```

---

## Architecture

### System Components

```mermaid
graph TB
    subgraph "Scheduler Service (8008)"
        FM[Feed Monitor<br/>Every 60s]
        JP[Job Processor<br/>Every 30s]
        CS[Cron Scheduler<br/>Flexible Tasks]
        EKG[Entity KG Processor<br/>Every 30s]
        PAA[Proposal Auto-Approver<br/>Every 5min]
        ED[Entity Deduplicator<br/>Daily 3:00 AM]

        FM -->|Creates Jobs| JQ[(Job Queue<br/>PostgreSQL)]
        JP -->|Processes Jobs| JQ
        CS -->|Triggers| EKG
        CS -->|Triggers| PAA
        CS -->|Triggers| ED
    end

    subgraph "External Services"
        FS[Feed Service<br/>8000]
        CAS[Content Analysis<br/>8000]
        ECS[Entity Canonicalization<br/>8112]
        KGS[Knowledge Graph<br/>8111]
        OPS[Ontology Proposals<br/>8109]
    end

    subgraph "Infrastructure"
        PG[(PostgreSQL)]
        RD[(Redis)]
        RMQ[RabbitMQ]
    end

    FM -->|Fetch Feeds| FS
    FM -->|Fetch Articles| FS
    JP -->|Analyze Article| CAS
    EKG -->|Canonicalize| ECS
    EKG -->|Publish Events| RMQ
    RMQ -->|Relationships| KGS
    PAA -->|Approve & Implement| OPS

    FM -.->|State| PG
    JP -.->|Jobs| PG
    EKG -.->|Entities| PG

    style FM fill:#e1f5ff
    style JP fill:#fff4e6
    style CS fill:#f3e5f5
    style EKG fill:#e8f5e9
    style PAA fill:#ffe6e6
    style ED fill:#fff0e6
```

### Data Flow

```mermaid
sequenceDiagram
    participant FM as Feed Monitor
    participant FS as Feed Service
    participant JQ as Job Queue
    participant JP as Job Processor
    participant CAS as Content Analysis
    participant EKG as Entity KG Processor
    participant EC as Entity Canonicalization
    participant RMQ as RabbitMQ
    participant KG as Knowledge Graph

    rect rgb(200, 230, 255)
        Note over FM,FS: Feed Monitoring (Every 60s)
        FM->>FS: GET /api/v1/feeds?is_active=true
        FS-->>FM: List of active feeds

        loop For each feed
            FM->>FS: GET /api/v1/feeds/{feed_id}/items?since={last_check}
            FS-->>FM: New articles

            FM->>JQ: Create analysis jobs<br/>(categorization, sentiment, etc.)
        end
    end

    rect rgb(255, 250, 230)
        Note over JP,CAS: Job Processing (Every 30s)
        JP->>JQ: Fetch pending jobs (priority order)

        loop For each job
            JP->>CAS: POST /api/v1/internal/analyze/{type}<br/>{article_id}
            CAS-->>JP: Analysis result
            JP->>JQ: Mark job completed
        end
    end

    rect rgb(230, 255, 230)
        Note over EKG,KG: Entity Processing (Every 30s)
        EKG->>JQ: Fetch unprocessed entities

        EKG->>EC: POST /api/v1/canonicalization/batch/async
        EC-->>EKG: job_id

        loop Poll until complete
            EKG->>EC: GET /api/v1/jobs/{job_id}/status
            EC-->>EKG: status
        end

        EKG->>EC: GET /api/v1/jobs/{job_id}/result
        EC-->>EKG: Canonicalized entities

        EKG->>RMQ: Publish relationships.extracted
        RMQ->>KG: Consume event
        EKG->>JQ: Mark entities processed
    end
```

### Integration Points

**Outbound Dependencies:**
- **Feed Service (8000)**: Fetch feeds and articles
  - `GET /api/v1/feeds` - List active feeds
  - `GET /api/v1/feeds/{feed_id}/items` - Fetch articles

- **Content Analysis Service (8000)**: Execute analysis
  - `POST /api/v1/internal/analyze/categorization`
  - `POST /api/v1/internal/analyze/finance-sentiment`
  - `POST /api/v1/internal/analyze/geopolitical-sentiment`
  - `POST /api/v1/internal/analyze/standard-sentiment`
  - `POST /api/v1/internal/analyze/osint`
  - `POST /api/v1/internal/analyze/summary`
  - `POST /api/v1/internal/analyze/entities`
  - `POST /api/v1/internal/analyze/topics`

- **Entity Canonicalization Service (8112)**: Wikidata enrichment
  - `POST /api/v1/canonicalization/batch/async`
  - `GET /api/v1/jobs/{job_id}/status`
  - `GET /api/v1/jobs/{job_id}/result`

**Inbound Dependencies:**
- Internal services requiring scheduler status
- Monitoring systems (Prometheus, Grafana)

**Event Publishing (RabbitMQ):**
- `analysis.relationships.extracted` - Entity relationships for Knowledge Graph

### Database Tables

#### `feed_schedule_state`
Tracks last processing time per feed to prevent duplicate work.

```sql
CREATE TABLE feed_schedule_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feed_id UUID NOT NULL UNIQUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_article_processed_at TIMESTAMP WITH TIME ZONE,
    total_articles_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feed_schedule_state_feed_id ON feed_schedule_state(feed_id);
```

#### `analysis_job_queue`
Priority queue for pending analysis jobs with retry logic.

```sql
CREATE TABLE analysis_job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feed_id UUID NOT NULL,
    article_id UUID NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
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
CREATE INDEX idx_analysis_job_feed ON analysis_job_queue(feed_id);
```

**Job Types:**
- `categorization` - Article topic classification
- `finance_sentiment` - Financial market sentiment
- `geopolitical_sentiment` - Geopolitical event sentiment
- `standard_sentiment` - General sentiment analysis
- `osint_analysis` - OSINT event extraction (scraped content only)
- `summary` - Text summarization
- `entities` - Named entity recognition
- `topics` - Topic classification

**Job Statuses:**
- `pending` - Waiting for processing
- `processing` - Currently being analyzed
- `completed` - Successfully finished
- `failed` - Failed after max retries

---

## API Endpoints

### Health & Status

#### `GET /health`
Comprehensive health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T10:00:00Z",
  "uptime_seconds": 3600.5,
  "version": "0.1.0",
  "components": {
    "database": {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "last_check": "2025-11-24T10:00:00Z",
      "details": {
        "response_time_ms": 12.5,
        "pool_size": 10
      }
    },
    "feed_monitor": {
      "name": "feed_monitor",
      "status": "healthy",
      "message": "Feed Monitor is running",
      "last_check": "2025-11-24T10:00:00Z",
      "details": {
        "is_running": true,
        "check_interval_seconds": 60
      }
    }
  },
  "summary": {
    "healthy": 8,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

#### `GET /health/live`
Kubernetes liveness probe - checks if service is alive.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2025-11-24T10:00:00Z"
}
```

#### `GET /health/ready`
Kubernetes readiness probe - checks if service is ready to accept requests.

**Response (200 OK):**
```json
{
  "status": "ready",
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "timestamp": "2025-11-24T10:00:00Z",
  "components": {
    "database": "healthy",
    "feed_monitor": "unhealthy",
    "job_processor": "healthy"
  }
}
```

#### `GET /health/startup`
Kubernetes startup probe - checks if service has finished starting.

**Response (200 OK):**
```json
{
  "status": "started",
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "starting",
  "timestamp": "2025-11-24T10:00:00Z",
  "components": {
    "feed_monitor": true,
    "job_processor": false,
    "cron_scheduler": true
  }
}
```

#### `GET /metrics`
Prometheus metrics endpoint.

**Response (text/plain):**
```
# HELP scheduler_service_health Service health status (1=healthy, 0.5=degraded, 0=unhealthy)
# TYPE scheduler_service_health gauge
scheduler_service_health 1.0

# HELP scheduler_uptime_seconds Service uptime in seconds
# TYPE scheduler_uptime_seconds gauge
scheduler_uptime_seconds 3600.5

# ... (additional Prometheus metrics)
```

#### `GET /`
Service information.

**Response:**
```json
{
  "service": "scheduler-service",
  "version": "0.1.0",
  "docs_url": "/docs"
}
```

### Scheduler Operations

#### `GET /api/v1/scheduler/status`
Get scheduler operational status and metrics.

**Response:**
```json
{
  "feed_monitor": {
    "is_running": true,
    "check_interval_seconds": 60
  },
  "job_processor": {
    "is_running": true,
    "process_interval_seconds": 30,
    "max_concurrent_jobs": 5
  },
  "cron_scheduler": {
    "is_running": true,
    "total_jobs": 1,
    "running_jobs": 1
  },
  "queue": {
    "pending_jobs": 127,
    "processing_jobs": 8
  }
}
```

#### `GET /api/v1/scheduler/jobs/stats`
Get job queue statistics.

**Response:**
```json
{
  "total_pending": 127,
  "total_processing": 8,
  "total_completed": 1523,
  "total_failed": 12,
  "by_type": {
    "categorization": 45,
    "finance_sentiment": 32,
    "geopolitical_sentiment": 18,
    "standard_sentiment": 32
  }
}
```

### Job Management

#### `GET /api/v1/scheduler/jobs`
List analysis jobs with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, PROCESSING, COMPLETED, FAILED)
- `limit` (default: 50): Maximum jobs to return
- `offset` (default: 0): Number of jobs to skip

**Response:**
```json
{
  "total": 1245,
  "limit": 50,
  "offset": 0,
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "article_id": "660e8400-e29b-41d4-a716-446655440000",
      "job_type": "categorization",
      "status": "completed",
      "priority": 10,
      "retry_count": 0,
      "created_at": "2025-10-13T16:30:00Z",
      "started_at": "2025-10-13T16:30:05Z",
      "completed_at": "2025-10-13T16:30:10Z",
      "error_message": null
    }
  ]
}
```

#### `POST /api/v1/scheduler/jobs/{job_id}/retry`
Retry a failed job. **Requires service authentication.**

**Response:**
```json
{
  "status": "success",
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 reset for retry",
  "job": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  }
}
```

#### `POST /api/v1/scheduler/jobs/{job_id}/cancel`
Cancel a pending or processing job. **Requires service authentication.**

**Response:**
```json
{
  "status": "success",
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 cancelled",
  "job": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed"
  }
}
```

#### `POST /api/v1/scheduler/feeds/{feed_id}/check`
Force immediate feed check. **Requires service authentication.**

**Response:**
```json
{
  "status": "triggered",
  "feed_id": "770e8400-e29b-41d4-a716-446655440000",
  "message": "Feed check scheduled"
}
```

### Cron Scheduler

#### `GET /api/v1/scheduler/cron/jobs`
List all cron scheduled jobs.

**Response:**
```json
{
  "total": 1,
  "jobs": [
    {
      "id": "process_entities_for_kg",
      "name": "Process Entities for Knowledge Graph",
      "next_run_time": "2025-10-13T16:31:00Z",
      "trigger": "interval[0:00:30]",
      "pending": false
    }
  ]
}
```

### Internal API

#### `POST /api/v1/scheduler/internal/health/service`
Internal health check for service-to-service communication. **Requires service API key.**

**Headers:**
- `X-Service-Key`: Service API key
- `X-Service-Name`: Calling service name

**Response:**
```json
{
  "status": "healthy",
  "authenticated_service": "feed-service",
  "internal_api": "operational"
}
```

**Full API Reference:** See OpenAPI spec at `/docs` (Swagger UI)

---

## Configuration

### Environment Variables

#### Service Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | scheduler-service | Service identifier |
| `SERVICE_PORT` | No | 8008 | HTTP server port |
| `ENVIRONMENT` | No | development | Environment (development/staging/production) |
| `DEBUG` | No | true | Enable debug mode |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |

#### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | No | 10 | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | No | 20 | Max overflow connections |

#### Redis Cache

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | - | Redis connection string |
| `CACHE_ENABLED` | No | true | Enable caching |

#### RabbitMQ

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RABBITMQ_URL` | Yes | - | RabbitMQ connection string |
| `RABBITMQ_EXCHANGE` | No | news.events | Event exchange name |
| `RABBITMQ_ROUTING_KEY_PREFIX` | No | scheduler | Routing key prefix |

#### Service URLs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FEED_SERVICE_URL` | Yes | http://feed-service:8000 | Feed Service endpoint |
| `CONTENT_ANALYSIS_URL` | Yes | http://content-analysis-service:8000 | Content Analysis endpoint |
| `ANALYSIS_SERVICE_URL` | Yes | http://content-analysis-service:8000 | Alias for CONTENT_ANALYSIS_URL |
| `AUTH_SERVICE_URL` | No | http://auth-service:8000 | Auth Service endpoint |

#### Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | No | - | JWT signing secret (for user endpoints) |
| `JWT_ALGORITHM` | No | HS256 | JWT algorithm |
| `SCHEDULER_SERVICE_API_KEY` | Yes | - | This service's API key |
| `FEED_SERVICE_API_KEY` | Yes | - | Feed Service API key |
| `CONTENT_ANALYSIS_API_KEY` | Yes | - | Content Analysis API key |
| `ANALYSIS_SERVICE_API_KEY` | Yes | - | Alias for CONTENT_ANALYSIS_API_KEY |
| `AUTH_SERVICE_API_KEY` | No | - | Auth Service API key |

#### Scheduling Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FEED_CHECK_INTERVAL` | No | 60 | Feed monitoring interval (seconds) |
| `JOB_PROCESS_INTERVAL` | No | 30 | Job processing interval (seconds) |
| `MAX_CONCURRENT_JOBS` | No | 5 | Max jobs per processing cycle |
| `MAX_CONCURRENT_ANALYSES` | No | 10 | Max concurrent analyses (legacy) |
| `BATCH_SIZE` | No | 50 | Articles per batch |
| `JOB_RETRY_DELAY` | No | 10 | Delay before retry (seconds) |
| `MAX_RETRIES` | No | 3 | Maximum retry attempts |

#### Circuit Breaker

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CIRCUIT_BREAKER_THRESHOLD` | No | 5 | Failures before opening circuit |
| `CIRCUIT_BREAKER_TIMEOUT` | No | 60 | Circuit open duration (seconds) |
| `CIRCUIT_BREAKER_SUCCESS_THRESHOLD` | No | 2 | Successes to close circuit |

#### Rate Limiting

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | No | true | Enable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | No | 60 | Max requests per minute |
| `RATE_LIMIT_REQUESTS_PER_HOUR` | No | 1000 | Max requests per hour |

#### Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_TRACING` | No | true | Enable distributed tracing |
| `JAEGER_ENDPOINT` | No | http://localhost:14268/api/traces | Jaeger collector endpoint |

### Example Configuration

```bash
# .env file
SERVICE_NAME=scheduler-service
SERVICE_PORT=8008
ENVIRONMENT=production
LOG_LEVEL=INFO

DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp
REDIS_URL=redis://:redis_secret_2024@redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

FEED_SERVICE_URL=http://feed-service:8000
CONTENT_ANALYSIS_URL=http://content-analysis-service:8000

SCHEDULER_SERVICE_API_KEY=aB1QlN0tt20vQGxnMflUrMznqDlglHEwSwK1qTw_8tU
FEED_SERVICE_API_KEY=ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg
CONTENT_ANALYSIS_API_KEY=4UBM501kPRQy3vX7JssFVRZjfUBA9Z6_4yAAjBkhy-U

FEED_CHECK_INTERVAL=60
JOB_PROCESS_INTERVAL=30
MAX_CONCURRENT_JOBS=5
```

---

## Core Components

### 1. Feed Monitor (`app/services/feed_monitor.py`)

**Purpose:** Polls Feed Service for new articles and creates analysis jobs.

**Key Features:**
- Runs every `FEED_CHECK_INTERVAL` seconds (default: 60)
- Maintains per-feed state to avoid duplicate processing
- Creates jobs based on feed category configuration
- Prevents overlapping executions (max_instances=1)

**Job Creation Rules:**
- **General feeds** (category=None or "general"): Create categorization job first
- **Finance feeds**: Create finance sentiment job
- **Geopolitics feeds**: Create geopolitical sentiment job
- **All feeds**: Create standard sentiment job

**Priority Levels:**
- Categorization: 10 (highest)
- Finance/Geopolitical sentiment: 8
- Standard sentiment: 5

**State Management:**
```python
# Tracks last check time per feed
FeedScheduleState(
    feed_id=UUID,
    last_checked_at=datetime,
    last_article_processed_at=datetime,
    total_articles_processed=int
)
```

### 2. Job Processor (`app/services/job_processor.py`)

**Purpose:** Processes queued analysis jobs via Content Analysis Service.

**Key Features:**
- Runs every `JOB_PROCESS_INTERVAL` seconds (default: 30)
- Processes jobs in priority order (highest first)
- Concurrent processing up to `MAX_CONCURRENT_JOBS` (default: 5)
- Retry logic with exponential backoff

**Supported Job Types:**
- `categorization` → `/api/v1/internal/analyze/categorization`
- `finance_sentiment` → `/api/v1/internal/analyze/finance-sentiment`
- `geopolitical_sentiment` → `/api/v1/internal/analyze/geopolitical-sentiment`
- `standard_sentiment` → `/api/v1/internal/analyze/standard-sentiment`
- `osint_analysis` → `/api/v1/internal/analyze/osint`
- `summary` → `/api/v1/internal/analyze/summary`
- `entities` → `/api/v1/internal/analyze/entities`
- `topics` → `/api/v1/internal/analyze/topics`

**Retry Strategy:**
- Max retries: 3 (configurable)
- Failed jobs reset to PENDING if retry_count < max_retries
- Permanently failed jobs marked as FAILED after max retries
- Error messages stored in `error_message` field

### 3. Cron Scheduler (`app/services/cron_scheduler.py`)

**Purpose:** Flexible task scheduler supporting cron, interval, and one-time triggers.

**Key Features:**
- APScheduler-based async scheduler
- Cron expressions (e.g., "0 */6 * * *" = every 6 hours)
- Interval triggers (seconds/minutes/hours/days)
- One-time date triggers
- Job management (add/remove/pause/resume)

**API:**
```python
# Cron job (daily at midnight)
cron_scheduler.add_cron_job(
    job_id="daily_cleanup",
    func=cleanup_function,
    cron_expression="0 0 * * *"
)

# Interval job (every 30 seconds)
cron_scheduler.add_interval_job(
    job_id="health_check",
    func=check_health,
    seconds=30
)

# One-time job
cron_scheduler.add_date_job(
    job_id="maintenance",
    func=run_maintenance,
    run_date=datetime(2025, 10, 15, 2, 0, 0)
)
```

### 4. Entity KG Processor (`app/services/entity_kg_processor.py`)

**Purpose:** Processes extracted entities and sends them to Knowledge Graph via Entity Canonicalization.

**Key Features:**
- Runs every 30 seconds
- Batch processing (15 entities per run)
- Sub-batching (3 entities per canonicalization job)
- Wikidata enrichment via Entity Canonicalization Service
- RabbitMQ event publishing
- Transactional database updates

**Processing Flow:**
1. Fetch unprocessed entities from `content_analysis_v2.agent_results`
2. Split into sub-batches of 3 entities
3. Send to Entity Canonicalization async API
4. Poll for job completion (max 60 seconds)
5. Build relationship triplets with Wikidata IDs
6. Publish to RabbitMQ (`analysis.relationships.extracted`)
7. Mark entities as processed

**Entity Type Preservation:**
```python
# CRITICAL: Uses original entity types from PostgreSQL
# Entity-Canonicalization may not return all types
original_entity_type_map = {
    e.get('text'): e.get('type', 'MISC')
    for e in original_entities
}
```

**Relationship Triplet Format:**
```json
{
  "subject": {
    "text": "Apple Inc.",
    "type": "ORG",
    "wikidata_id": "Q312"
  },
  "relationship": {
    "type": "MENTIONED_IN",
    "confidence": 0.95,
    "evidence": "Mentioned in article 550e8400-e29b-41d4-a716-446655440000"
  },
  "object": {
    "text": "Article 550e8400-e29b-41d4-a716-446655440000",
    "type": "ARTICLE",
    "wikidata_id": null
  }
}
```

### 5. Proposal Auto-Approver (`app/services/proposal_auto_approver.py`)

**Purpose:** Automatically approves and implements high-confidence ontology proposals from the OSS Service.

**Key Features:**
- Runs every 5 minutes via APScheduler
- Fetches pending proposals from Ontology Proposals Service (8109)
- Applies rule-based auto-approval logic
- Implements approved proposals automatically
- Tracks approval/rejection statistics

**Integration:**
```
OSS Service (8110)
    ↓ Generates proposals
Ontology Proposals Service (8109)
    ↓ Stores proposals
Proposal Auto-Approver (Scheduler)
    ↓ Auto-approves & implements
Knowledge Graph (Neo4j)
```

**Auto-Approval Rules:**

| Change Type | Min Confidence | Min Occurrences | Title Patterns |
|-------------|----------------|-----------------|----------------|
| FLAG_INCONSISTENCY | 95% | 1 | ISO violations, UNKNOWN entities, Article UUID garbage, missing properties, Duplicate entities |
| NEW_ENTITY_TYPE | 98% | 100 | Any pattern |

**Implementation Actions:**
- **ISO Violations:** Logs for manual cleanup (no auto-fix)
- **UNKNOWN Entities:** Flags in Knowledge Graph for review
- **Article UUID Garbage:** Marks for deletion
- **Duplicate Entities:** Logs for merge consideration
- **NEW_ENTITY_TYPE:** Adds to ontology schema

**Configuration:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROPOSAL_CHECK_INTERVAL` | 300 | Check interval (seconds) |
| `PROPOSALS_API_URL` | http://ontology-proposals-service:8109 | Proposals API endpoint |
| `AUTO_APPROVE_ENABLED` | true | Enable auto-approval |
| `MIN_CONFIDENCE_FLAG` | 0.95 | Minimum confidence for FLAG_INCONSISTENCY |
| `MIN_CONFIDENCE_NEW` | 0.98 | Minimum confidence for NEW_ENTITY_TYPE |
| `MIN_OCCURRENCES_NEW` | 100 | Minimum occurrences for NEW_ENTITY_TYPE |

**Logging:**
```python
# Approval log format
logger.info(f"Auto-approved proposal {proposal_id}: {title}")
logger.info(f"Implemented: {change_type} - {description}")

# Rejection log format
logger.debug(f"Skipped proposal {proposal_id}: confidence {confidence} < {threshold}")
```

**API Reference:**
- See: [ADR-047: Ontology Auto-Approval Rules](../decisions/ADR-047-ontology-auto-approval-rules.md)
- See: [OSS Service Documentation](./oss-service.md)

### 6. Entity Deduplicator (`app/services/entity_deduplicator.py`)

**Purpose:** Identifies and merges duplicate entities in the Knowledge Graph.

**Key Features:**
- Runs daily at 3:00 AM via APScheduler
- Uses similarity scoring (name, type, Wikidata ID)
- Generates merge proposals for review
- Supports automatic merging for high-confidence matches

**Deduplication Strategy:**
1. Group entities by normalized name
2. Compare Wikidata IDs (exact match = merge)
3. Calculate Levenshtein distance for similar names
4. Generate merge proposals above threshold

**Configuration:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DEDUP_CRON_HOUR` | 3 | Hour to run (UTC) |
| `DEDUP_CRON_MINUTE` | 0 | Minute to run |
| `DEDUP_MIN_SIMILARITY` | 0.85 | Minimum similarity for proposal |
| `DEDUP_AUTO_MERGE_THRESHOLD` | 0.98 | Auto-merge threshold |

---

## Event Integration

### Events Published

#### `analysis.relationships.extracted`
Published to RabbitMQ when entities are processed for Knowledge Graph.

**Exchange:** `news.events`
**Routing Key:** `analysis.relationships.extracted`

**Payload:**
```json
{
  "event_type": "relationships.extracted",
  "timestamp": "2025-10-13T16:30:00Z",
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_url": null,
    "triplets": [
      {
        "subject": {
          "text": "Apple Inc.",
          "type": "ORG",
          "wikidata_id": "Q312"
        },
        "relationship": {
          "type": "WORKS_FOR",
          "confidence": 0.85,
          "evidence": "Extracted from article..."
        },
        "object": {
          "text": "Tim Cook",
          "type": "PER",
          "wikidata_id": "Q312"
        }
      }
    ],
    "extraction_timestamp": "2025-10-13T16:30:00Z",
    "total_relationships": 15
  },
  "agent_result_id": "660e8400-e29b-41d4-a716-446655440000"
}
```

**Consumers:**
- Knowledge Graph Service (8111)

### Events Consumed

None. Scheduler operates on pull-based polling.

---

## Deployment

### Docker

```bash
# Build image
docker build -f Dockerfile.dev -t scheduler-service:latest .

# Run container
docker run -d \
  -p 8008:8008 \
  -e DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp \
  -e REDIS_URL=redis://:redis_secret_2024@redis:6379/0 \
  -e RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/ \
  -e FEED_SERVICE_URL=http://feed-service:8000 \
  -e CONTENT_ANALYSIS_URL=http://content-analysis-service:8000 \
  scheduler-service:latest
```

### Health Checks

**HTTP Health Check:**
```bash
curl -f http://localhost:8008/health
```

**Docker Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD /usr/local/bin/healthcheck.sh
```

**Health Check Script (`healthcheck.sh`):**
```bash
#!/bin/sh
# Step 1: Validate critical imports
python3 -c "from app.main import app" 2>/dev/null || exit 1

# Step 2: Check HTTP endpoint
curl -f http://localhost:8000/health || exit 1

exit 0
```

**Note:** Port mismatch in health check script (checks 8000 instead of 8008) - see issues report.

### Scaling Considerations

**Horizontal Scaling:**
- ❌ **NOT RECOMMENDED** - Service uses APScheduler with single-instance jobs
- Multiple instances would create duplicate jobs
- Database state tracking prevents duplicate article processing, but job queue would have race conditions

**Vertical Scaling:**
- ✅ Increase `MAX_CONCURRENT_JOBS` (default: 5)
- ✅ Increase `DATABASE_POOL_SIZE` (default: 10)
- ✅ Monitor CPU/memory usage under load

**Recommended Approach:**
- Single instance with adequate resources
- Use `MAX_CONCURRENT_JOBS` to control throughput
- Monitor queue depth via `/api/v1/scheduler/jobs/stats`

---

## Troubleshooting

### Common Issues

#### Service won't start

**Symptom:** Service crashes on startup

**Causes & Solutions:**
1. **Database unreachable**
   ```bash
   # Check database connectivity
   docker exec -it news-postgres psql -U news_user -d news_mcp -c "SELECT 1"

   # Verify DATABASE_URL format
   postgresql://news_user:your_db_password@postgres:5432/news_mcp
   ```

2. **Missing API keys**
   ```bash
   # Check .env file
   grep "_API_KEY" services/scheduler-service/.env

   # Required keys:
   # - SCHEDULER_SERVICE_API_KEY
   # - FEED_SERVICE_API_KEY
   # - CONTENT_ANALYSIS_API_KEY
   ```

3. **Import errors (database models)**
   ```python
   # Common error: ModuleNotFoundError: No module named 'database'
   # Fix: Ensure database/ directory is in sys.path
   # See app/services/feed_monitor.py:15-18
   ```

#### Jobs not processing

**Symptom:** Pending jobs accumulate, but processing_jobs = 0

**Diagnostics:**
```bash
# Check job processor status
curl http://localhost:8008/api/v1/scheduler/status

# Check logs
docker logs scheduler-service --tail 100

# Check Content Analysis Service health
curl http://content-analysis-service:8000/health
```

**Common Causes:**
1. **Content Analysis Service down** - Job processor retries will fail
2. **Invalid API key** - 401 errors in logs
3. **Database connection leak** - Check connection pool exhaustion

#### High memory usage

**Symptom:** Service memory usage grows over time

**Investigation:**
```bash
# Check container memory
docker stats scheduler-service

# Check APScheduler thread count
# Expected: ~3-5 threads (feed_monitor, job_processor, cron_scheduler, entity_kg_processor)
```

**Solutions:**
- Reduce `MAX_CONCURRENT_JOBS` (default: 5)
- Reduce `DATABASE_POOL_SIZE` (default: 10)
- Check for connection leaks in logs
- Monitor Entity KG Processor (processes large batches)

#### Feed monitor not detecting new articles

**Symptom:** `feed_monitor` runs but creates no jobs

**Diagnostics:**
```bash
# Check feed monitor logs
docker logs scheduler-service | grep "Feed monitor"

# Check Feed Service connectivity
curl http://feed-service:8000/api/v1/feeds?is_active=true \
  -H "X-Service-Key: $FEED_SERVICE_API_KEY"

# Check feed_schedule_state table
docker exec -it news-postgres psql -U news_user -d news_mcp -c \
  "SELECT feed_id, last_checked_at, total_articles_processed FROM feed_schedule_state"
```

**Common Causes:**
1. **No active feeds** - Check `is_active=true` in Feed Service
2. **Articles already processed** - Check `last_checked_at` timestamp
3. **API key mismatch** - 401 errors in logs

#### Entity processing stuck

**Symptom:** Entities not appearing in Knowledge Graph

**Diagnostics:**
```bash
# Check unprocessed entities
docker exec -it news-postgres psql -U news_user -d news_mcp -c \
  "SELECT COUNT(*) FROM content_analysis_v2.agent_results
   WHERE agent_name = 'ENTITY_EXTRACTOR' AND processed_by_kg = false"

# Check Entity Canonicalization Service
curl http://news-entity-canonicalization:8112/health

# Check RabbitMQ queue
docker exec -it rabbitmq rabbitmqctl list_queues
```

**Common Causes:**
1. **Entity Canonicalization timeout** - Jobs take > 5 minutes
2. **Wikidata API slow** - Increases canonicalization latency
3. **RabbitMQ connection failed** - Check logs for connection errors

### Debug Strategies

#### Enable Debug Logging

```bash
# .env file
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Monitor APScheduler Jobs

```bash
# Check cron scheduler status
curl http://localhost:8008/api/v1/scheduler/cron/jobs
```

#### Trace Database Queries

```python
# app/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=True  # Enable SQL logging
)
```

#### Monitor Job Queue Growth

```bash
# Watch job queue stats in real-time
watch -n 5 'curl -s http://localhost:8008/api/v1/scheduler/jobs/stats | jq'
```

### Log Locations

**Docker Logs:**
```bash
docker logs scheduler-service
docker logs scheduler-service --follow
docker logs scheduler-service --tail 100
```

**Log Format:**
```
2025-10-13 16:30:00 - app.services.feed_monitor - INFO - Starting feed check cycle
2025-10-13 16:30:01 - app.services.feed_monitor - INFO - Found 42 active feeds to check
2025-10-13 16:30:05 - app.services.job_processor - INFO - Processing 8 jobs
```

**Important Log Messages:**
- `Feed monitor started (interval: 60s)` - Feed monitoring active
- `Job processor started (interval: 30s)` - Job processing active
- `Entity KG processor job registered` - Entity processing active
- `Scheduled X analysis jobs` - Jobs created successfully
- `Job X completed successfully` - Job finished
- `Job X failed: <error>` - Job error (check retry_count)

---

## Development

### Setup

```bash
# Create virtual environment
cd services/scheduler-service
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running Locally

```bash
# Start dependencies
docker compose up -d postgres redis rabbitmq feed-service content-analysis-service

# Run service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8008
```

### Testing

```bash
# Run tests (when implemented)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

**Note:** No tests currently implemented - see issues report.

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.115.0 |
| ASGI Server | Uvicorn | 0.30.0 |
| Database | PostgreSQL | 14+ |
| ORM | SQLAlchemy | 2.0.35 |
| Migration Tool | Alembic | 1.13.0 |
| Async PostgreSQL | asyncpg | 0.29.0 |
| Sync PostgreSQL | psycopg2-binary | 2.9.9 |
| Cache | Redis | 7+ |
| Redis Client | redis | 5.0.1 |
| Message Queue | RabbitMQ | 3.12+ |
| RabbitMQ Client | aio-pika | 9.4.0 |
| Scheduler | APScheduler | 3.10.4 |
| HTTP Client | httpx | 0.27.0 |
| JWT | python-jose | 3.3.0 |
| Logging | structlog | 24.4.0 |
| Validation | pydantic | 2.8.0 |
| Settings | pydantic-settings | 2.4.0 |
| Date/Time | python-dateutil | 2.8.2 |
| Timezone | pytz | 2023.4 |

**Development Dependencies:**
- pytest 7.4.4
- pytest-asyncio 0.23.3
- pytest-cov 4.1.0
- black 23.12.1
- flake8 7.0.0
- mypy 1.8.0
- isort 5.12.0

---

## MCP Integration

The Scheduler Service is accessible via the **MCP Orchestration Server** (Port 9008), providing programmatic access to scheduler status, job management, and cron operations through the Model Context Protocol.

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `orch:scheduler_status` | Get scheduler operational status | None |
| `orch:scheduler_health` | Get detailed health status | None |
| `orch:jobs_list` | List analysis jobs | `status` (str), `limit` (int), `offset` (int) |
| `orch:jobs_stats` | Get job queue statistics | None |
| `orch:jobs_cancel` | Cancel a pending/processing job | `job_id` (str) |
| `orch:jobs_retry` | Retry a failed job | `job_id` (str) |
| `orch:cron_list` | List cron scheduled jobs | None |
| `orch:feed_schedule_check` | Force immediate feed check | `feed_id` (str) |

### MCP Server Configuration

**Server:** MCP Orchestration Server
**Port:** 9008
**Base URL:** `http://{SERVER_IP}:9008`
**Tool Prefix:** `orch:`

### Example Usage

#### Get Scheduler Status
```json
{
  "tool": "orch:scheduler_status",
  "parameters": {}
}
```

**Response:**
```json
{
  "feed_monitor": {
    "is_running": true,
    "check_interval_seconds": 60
  },
  "job_processor": {
    "is_running": true,
    "process_interval_seconds": 30,
    "max_concurrent_jobs": 5
  },
  "cron_scheduler": {
    "is_running": true,
    "total_jobs": 1,
    "running_jobs": 1
  },
  "queue": {
    "pending_jobs": 127,
    "processing_jobs": 8
  }
}
```

#### Get Job Statistics
```json
{
  "tool": "orch:jobs_stats",
  "parameters": {}
}
```

**Response:**
```json
{
  "total_pending": 127,
  "total_processing": 8,
  "total_completed": 1523,
  "total_failed": 12,
  "by_type": {
    "categorization": 45,
    "finance_sentiment": 32,
    "geopolitical_sentiment": 18,
    "standard_sentiment": 32
  }
}
```

#### Retry Failed Job
```json
{
  "tool": "orch:jobs_retry",
  "parameters": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 reset for retry",
  "job": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  }
}
```

### Integration with Claude Desktop

For Claude Desktop integration, use the unified MCP gateway:

```json
{
  "mcpServers": {
    "news-microservices": {
      "command": "node",
      "args": ["C:\\mcp-unified-gateway.js"],
      "env": {
        "MCP_SERVER_IP": "localhost"
      }
    }
  }
}
```

All scheduler tools are then accessible with the `orch:` prefix.

---

## Related Documentation

- [OpenAPI Specification](../openapi-specs/scheduler-service.yaml)
- [Code Quality Report](../issues/scheduler-service-issues.md)
- [Feed Service Documentation](../../services/feed-service/README.md)
- [Content Analysis Service Documentation](../../services/content-analysis-v3/README.md)
- [Entity Canonicalization Service](../../services/entity-canonicalization-service/README.md)
- [Knowledge Graph Service](../../services/knowledge-graph-service/README.md)
- [OSS Service Documentation](./oss-service.md)
- [Ontology Proposals Service](./ontology-proposals-service.md)
- [ADR-047: Ontology Auto-Approval Rules](../decisions/ADR-047-ontology-auto-approval-rules.md)
- [Database Models](../../database/models/scheduler.py)
- [Architecture Overview](../ARCHITECTURE.md)

---

**Service Version:** 0.1.0
**Default Port:** 8008
**Last Updated:** 2025-12-27
**Status:** Production

**Maintainers:** Platform Team
**Support:** #scheduler-service on Slack
