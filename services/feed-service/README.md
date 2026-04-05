# Feed Service

## Overview

The Feed Service is a comprehensive RSS/Atom feed management and fetching microservice that handles automated feed updates, content parsing, and event-driven communication with other services in the News Microservices platform.

**Key Capabilities:**
- Automated RSS/Atom feed fetching with intelligent scheduling
- **Production-ready resilience patterns (Task 406):**
  - Circuit breaker pattern with Prometheus metrics
  - Retry logic with exponential backoff
  - Dead Letter Queue (DLQ) for failed messages
  - Standardized error handling across all endpoints
- Content deduplication using SHA-256 hashing
- Health monitoring and quality scoring
- Event-driven architecture with RabbitMQ
- Celery-based background task processing
- Full content scraping integration (with scraping-service)
- RESTful API with JWT authentication

**Technology Stack:**
- **Framework:** FastAPI 0.115.0
- **Task Queue:** Celery 5.3.6 with Redis backend
- **Feed Parsing:** feedparser 6.0.11
- **Message Broker:** RabbitMQ (aio-pika 9.4.0)
- **Database:** PostgreSQL with asyncpg and SQLAlchemy 2.0
- **Authentication:** JWT (python-jose 3.3.0)
- **HTTP Client:** httpx 0.27.0

## Quick Start

See full documentation in the sections below for complete setup instructions, API reference, and integration patterns.

**Port:** 8001
**Base URL:** http://localhost:8001
**API Docs:** http://localhost:8001/docs

## Architecture

The Feed Service implements a sophisticated feed processing pipeline with the following components:

1. **FeedScheduler** - Checks every 60 seconds for feeds due for fetching, applies exponential backoff for failing feeds
2. **FeedFetcher** - Fetches RSS/Atom feeds with circuit breaker pattern, parses entries, deduplicates content
3. **EventPublisher** - Publishes events to RabbitMQ for other services to consume
4. **FeedQualityScorer** - Calculates quality metrics based on freshness, consistency, content, and reliability

### Feed Processing Flow
```
User creates feed → Database → Event published → Initial fetch triggered
    ↓
Scheduler checks every 60s → Feeds due for fetch → FeedFetcher
    ↓
Circuit breaker check → HTTP fetch (with ETag/Last-Modified) → Parse with feedparser
    ↓
Process entries → Hash content (SHA-256) → Check for duplicates → Create FeedItem
    ↓
If scraping enabled → Publish "feed.item.created" → Scraping service → PATCH endpoint
    ↓
Update health metrics → Publish events (fetch_completed, article.created, etc.)
```

## API Endpoints (25 Total)

### Feed Management
1. **GET /api/v1/feeds** - List all feeds with pagination and filtering
   - Query params: skip, limit, is_active, status, category, health_score_min/max
   - Authentication: Optional

2. **POST /api/v1/feeds** - Create new feed
   - Request body: name, url, fetch_interval, scrape_full_content, enable_* flags
   - Authentication: Required (JWT)
   - Triggers background fetch immediately
   - Publishes: feed.created event

3. **GET /api/v1/feeds/{id}** - Get feed details
   - Returns full feed information with categories
   - Authentication: Required (JWT)

4. **PUT /api/v1/feeds/{id}** - Update feed (URL cannot be changed)
   - Partial updates supported
   - Publishes: feed.updated event
   - Authentication: Required (JWT)

5. **DELETE /api/v1/feeds/{id}** - Delete feed (cascades to all related data)
   - Publishes: feed.deleted event
   - Authentication: Required (JWT)

6. **POST /api/v1/feeds/{id}/fetch** - Manually trigger feed fetch
   - Runs asynchronously in background
   - Authentication: Required (JWT)

### Feed Entries
7. **GET /api/v1/feeds/{id}/items** - Get items for a feed
   - Query params: skip, limit, since (datetime)
   - Authentication: Optional

8. **PATCH /api/v1/feeds/{id}/items/{item_id}** - Update feed item
   - Used by scraping-service to store scraped content
   - Authentication: None (service-to-service with X-Service-Key)

### V3 Analysis Integration

Feed item responses include **both V2 (legacy) and V3 (active) analysis data** from the unified `public.article_analysis` table.

**Response Structure:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Article Title",
  "link": "https://example.com/article",
  "published_at": "2025-11-19T10:00:00Z",

  "pipeline_execution": {
    // V2 Analysis (legacy format)
    // null if no V2 analysis exists
  },

  "v3_analysis": {
    // V3 Analysis (active format)
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "pipeline_version": "3.0",
    "success": true,

    "tier0": {
      // Triage decision (PascalCase for frontend compatibility)
      "PriorityScore": 8,
      "category": "FINANCE",
      "keep": true,
      "tokens_used": 722,
      "cost_usd": 0.0001326,
      "model": "gpt-4.1-nano"
    },

    "tier1": {
      // Foundation extraction
      "entities": [...],      // Full entity array
      "relations": [...],     // Full relation array
      "topics": [...],        // Full topic array
      "scores": {
        // Nested scores object (frontend requirement)
        "impact_score": 8.0,
        "credibility_score": 7.0,
        "urgency_score": 7.0
      },
      "tokens_used": 2188,
      "cost_usd": 0.00045465,
      "model": "gpt-4.1-nano"
    },

    "tier2": {
      // Specialist findings (nested by specialist type)
      "ENTITY_EXTRACTOR": {
        "entity_enrichment": {
          "entities": [...]
        },
        "tokens_used": 1234,
        "cost_usd": 0.00021,
        "model": "gpt-4.1-nano"
      },
      "TOPIC_CLASSIFIER": {
        "topic_classification": {
          "topics": [...]
        }
      },
      "FINANCIAL_ANALYST": null,  // null if not executed
      "GEOPOLITICAL_ANALYST": null,
      "SENTIMENT_ANALYZER": null
    },

    "metrics": {
      "tier0_cost_usd": 0.0001326,
      "tier1_cost_usd": 0.00045465,
      "tier2_cost_usd": 0.00034965,
      "total_cost_usd": 0.00093375,
      "total_time_ms": 18500
    }
  }
}
```

**Data Flow:**
1. **content-analysis-v3** executes analysis pipeline
2. **content-analysis-v3** publishes `analysis.v3.completed` event to RabbitMQ
3. **feed-service analysis_consumer** receives event
4. **feed-service analysis_consumer** stores results in `public.article_analysis` (unified table)
5. **feed-service API** reads from unified table and returns both V2 and V3 data

**Frontend Integration:**
- V2 data: Displayed in `ArticleV2AnalysisCard.tsx`
- V3 data: Displayed in `ArticleDetailPageV3.tsx` (tier0, tier1, tier2 specialists)
- Frontend access: `GET /api/v1/feeds/{id}/items` or `GET /api/v1/feeds/{id}/items/{item_id}`

**Performance:**
- Direct database read (no proxy service calls)
- Sequential requests: 4-5ms (30-40x faster than legacy proxy)
- Concurrent requests: 93ms average (2x faster)
- Database query execution: 0.145ms

**See Also:**
- `services/feed-service/app/services/analysis_loader.py` - Data loading and transformation
- `services/feed-service/app/workers/analysis_consumer.py` - Event consumer and storage
- `services/content-analysis-v3/README.md` - V3 pipeline documentation

### Monitoring
9. **GET /api/v1/feeds/{id}/health** - Get health metrics
   - Returns: health_score, success_rate, uptime (24h/7d/30d), avg_response_time
   - Authentication: None

10. **GET /api/v1/feeds/{id}/quality** - Get quality score and analysis
    - Calculates: freshness_score, consistency_score, content_score, reliability_score
    - Returns recommendations for improvement
    - Authentication: None

### Bulk Operations
11. **POST /api/v1/bulk-fetch** - Trigger fetch for multiple feeds
    - Can fetch specific feeds or all active feeds
    - Force option to bypass recent fetch check
    - Authentication: Optional

### Intelligent Scheduling (New - Solves Thundering Herd Problem)
12. **GET /api/v1/scheduling/timeline** - Get feed schedule timeline for visualization
    - Query params: hours (default: 24)
    - Returns: 5-minute time slots with scheduled feeds
    - Purpose: Visualize feed distribution over time
    - Authentication: None

13. **GET /api/v1/scheduling/distribution** - Get schedule distribution statistics
    - Returns: total_active_feeds, max_concurrent_feeds, distribution_score (0-100), recommendation
    - Purpose: Monitor scheduling efficiency and load balance quality
    - Authentication: None

14. **POST /api/v1/scheduling/optimize** - Calculate and optionally apply schedule optimization
    - Query params: apply (default: false) - set true to apply changes immediately
    - Returns: before/after comparison, improvement percentage, preview of changes
    - Purpose: Redistribute feeds to minimize concurrent load
    - Algorithm: Stagger feeds with same interval evenly across time slots
    - Authentication: Required (JWT)

15. **GET /api/v1/scheduling/conflicts** - Detect scheduling conflicts (clustering)
    - Query params: threshold_minutes (default: 5)
    - Returns: clusters of feeds scheduled too close together
    - Purpose: Identify and fix timing conflicts
    - Authentication: None

16. **GET /api/v1/scheduling/stats** - Get comprehensive scheduling statistics
    - Returns: interval distribution, health status, max cluster size
    - Purpose: Overall scheduling health monitoring
    - Authentication: None

17. **PUT /api/v1/scheduling/feeds/{feed_id}/schedule** - Manually reschedule a specific feed
    - Query params: offset_minutes - minutes to offset from base time
    - Returns: updated schedule information
    - Purpose: Fine-tune individual feed timing
    - Authentication: Required (JWT)

### Duplicate Detection (Epic 1.2)

20. **GET /api/v1/duplicates** - List pending near-duplicates for review
    - Query params: status (pending, reviewed, auto_resolved, all), page, page_size
    - Returns: Paginated list of duplicate candidates
    - Authentication: Required (JWT)

21. **GET /api/v1/duplicates/{id}** - Get single candidate with article details
    - Returns: Detailed candidate info including both articles' titles, links, descriptions
    - Includes: hamming_distance, simhash values, review status
    - Authentication: Required (JWT)

22. **PUT /api/v1/duplicates/{id}** - Submit review decision
    - Request body: `{ "decision": "keep_both|merge|reject_new", "notes": "optional" }`
    - Decisions:
      - `keep_both`: False positive, both articles kept
      - `merge`: Mark for future merge (not yet implemented)
      - `reject_new`: Mark new article as withheld (true duplicate)
    - Authentication: Required (JWT, admin role)

23. **GET /api/v1/duplicates/stats** - Get duplicate detection statistics
    - Returns: pending_count, reviewed_count, auto_resolved_count, total_count
    - Authentication: Required (JWT)

### Service Health
24. **GET /health** - Service health check
    - Returns service status, version, scheduler status
    - Authentication: None

25. **GET /** - Root endpoint
    - Returns service info and documentation links
    - Authentication: None

## Database Models (6 Total)

### 1. Feed
Main feed configuration and metadata.

**Key Fields:**
- `id` (UUID): Primary key
- `url` (str, unique): RSS/Atom feed URL
- `name` (str): Feed display name
- `description` (str, optional): Feed description
- `fetch_interval` (int, default=60): Minutes between fetches
- `is_active` (bool, default=True): Whether feed is active
- `status` (str): ACTIVE, PAUSED, ERROR, INACTIVE
- `last_fetched_at` (datetime): Last successful fetch
- `health_score` (int, 0-100): Current health score
- `consecutive_failures` (int): Number of consecutive fetch failures
- `scrape_full_content` (bool): Enable full content scraping
- `enable_categorization` (bool): Enable auto-categorization
- `enable_finance_sentiment` (bool): Enable finance sentiment analysis
- `enable_geopolitical_sentiment` (bool): Enable geopolitical analysis
- `enable_osint_analysis` (bool): Enable OSINT event analysis

**Intelligent Scheduling Fields (New - Migration 002):**
- `next_fetch_at` (datetime, nullable): Explicit next fetch timestamp (prevents thundering herd)
- `schedule_offset_minutes` (int, default=0): Minutes offset from base time for staggering
- `scheduling_priority` (int, default=5): Priority for scheduling conflicts (1-10, higher = more important)

**Relationships:**
- items: List[FeedItem]
- fetch_logs: List[FetchLog]
- health: FeedHealth (one-to-one)
- categories: List[FeedCategory]

### 2. FeedItem
Feed entries (append-only, immutable after creation).

**Key Fields:**
- `id` (UUID): Primary key
- `feed_id` (UUID): Foreign key to Feed
- `title` (str): Article title
- `link` (str): Article URL
- `description` (str, optional): Article summary
- `content` (str, optional): Full content (RSS or scraped)
- `author` (str, optional): Article author
- `guid` (str, optional): Unique identifier from feed
- `published_at` (datetime): Publication date
- `content_hash` (str, unique): SHA-256 hash for deduplication
- `scraped_at` (datetime, optional): When content was scraped
- `scrape_status` (str): success, paywall, error, timeout
- `scrape_word_count` (int): Word count of scraped content

**Note:** FeedItem is append-only. Items are never updated except for scraping fields via PATCH endpoint.

### 3. FetchLog
History of feed fetch attempts.

**Key Fields:**
- `feed_id` (UUID): Foreign key
- `status` (str): running, success, error
- `items_found` (int): Total items in feed
- `items_new` (int): New items added
- `duration` (float): Fetch duration in seconds
- `error` (str, optional): Error message if failed
- `response_time_ms` (int): HTTP response time
- `response_status_code` (int): HTTP status code
- `started_at`, `completed_at` (datetime)

### 4. FeedHealth
Feed reliability and performance metrics (one-to-one with Feed).

**Key Fields:**
- `health_score` (int, 0-100): Overall health
- `consecutive_failures` (int): Failure counter
- `is_healthy` (bool): Health status
- `avg_response_time_ms` (float): Average response time
- `success_rate` (float, 0-1): Success rate
- `uptime_24h`, `uptime_7d`, `uptime_30d` (float, 0-1): Uptime percentages
- `last_success_at`, `last_failure_at` (datetime)

### 5. FeedCategory
Feed categorization for organization.

**Key Fields:**
- `name` (str): Category name
- `description` (str, optional)
- `parent_id` (UUID, optional): For hierarchical categories
- Unique constraint on (feed_id, name)

### 6. FeedSchedule
Cron-based scheduling for custom intervals.

**Key Fields:**
- `cron_expression` (str): e.g., "0 */6 * * *"
- `is_active` (bool)
- `timezone` (str, default="UTC")
- `last_run_at`, `next_run_at` (datetime)

## RabbitMQ Events (8 Types)

**Exchange:** `news.events` (Topic, durable)
**Routing Keys:** Event types with underscores (e.g., `feed_created`)

### Published Events

1. **feed.created** - New feed was created
   ```json
   {
     "event_type": "feed.created",
     "service": "feed-service",
     "timestamp": "2025-10-15T10:30:00Z",
     "payload": {
       "feed_id": "uuid",
       "url": "https://example.com/feed.xml",
       "name": "Example Feed"
     }
   }
   ```

2. **feed.updated** - Feed was updated
   ```json
   {
     "payload": {
       "feed_id": "uuid",
       "updated_fields": ["name", "fetch_interval"]
     }
   }
   ```

3. **feed.deleted** - Feed was deleted
   ```json
   {
     "payload": {
       "feed_id": "uuid",
       "url": "https://example.com/feed.xml"
     }
   }
   ```

4. **feed.fetch_completed** - Fetch completed successfully
   ```json
   {
     "payload": {
       "feed_id": "uuid",
       "items_found": 10,
       "items_new": 3,
       "item_ids": ["uuid1", "uuid2", "uuid3"]
     }
   }
   ```
   **Consumers:** Content Analysis, Search, Analytics services

5. **feed.fetch_failed** - Fetch failed
   ```json
   {
     "payload": {
       "feed_id": "uuid",
       "error": "Connection timeout",
       "consecutive_failures": 3
     }
   }
   ```
   **Consumers:** Notification service (alerts admins)

6. **article.created** - New article/item created (per item)
   ```json
   {
     "payload": {
       "item_id": "uuid",
       "feed_id": "uuid"
     }
   }
   ```
   **Consumers:** Content Analysis, OSINT services

7. **feed.item.created** - New item for scraping (if scraping enabled)
   ```json
   {
     "payload": {
       "feed_id": "uuid",
       "item_id": "uuid",
       "url": "https://example.com/article",
       "scrape_method": "auto"
     }
   }
   ```
   **Consumers:** Scraping service

8. **feed.items_cleaned** - Old items cleaned up
   ```json
   {
     "payload": {
       "items_deleted": 1250,
       "cutoff_date": "2025-07-17T02:00:00Z",
       "retention_days": 90
     }
   }
   ```

## Celery Tasks (4 Total)

### 1. feed.fetch_single
Fetch a single feed by ID.

- **Queue:** feed_fetches
- **Priority:** 5 (high)
- **Max Retries:** 3
- **Retry Delay:** 60 seconds
- **Usage:** Background tasks for manual fetch triggers

### 2. feed.fetch_all_active
Fetch all active feeds due for fetching.

- **Queue:** feed_bulk
- **Priority:** 3
- **Schedule:** Every hour at minute 0 (Celery Beat)
- **Behavior:** Processes feeds in batches of 10 concurrently
- **Returns:** Summary of all fetch results

### 3. feed.cleanup_old_items
Delete feed items older than retention period.

- **Queue:** maintenance
- **Priority:** 1
- **Schedule:** Daily at 2:00 AM
- **Default Retention:** 90 days
- **Behavior:** Prevents database bloat, publishes cleanup event

### 4. feed.health_check
Health check task for Celery monitoring.

- **Queue:** health
- **Priority:** 0
- **Schedule:** Every 5 minutes (300 seconds)
- **Purpose:** Verify Celery worker is alive

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql+asyncpg://news_user:password@localhost:5433/news_mcp
RABBITMQ_URL=amqp://guest:guest@localhost:5673/
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/2
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
AUTH_SERVICE_URL=http://localhost:8100
```

### Optional Configuration
```bash
# Service
SERVICE_PORT=8001
SERVICE_NAME=feed-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=false

# Feed Processing
DEFAULT_FETCH_INTERVAL_MINUTES=60
MAX_ITEMS_PER_FETCH=50
MAX_FETCH_RETRIES=3
FETCH_TIMEOUT_SECONDS=30
USER_AGENT=NewsMicroservices-FeedService/1.0

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_INTERVAL_SECONDS=60

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2
CIRCUIT_BREAKER_TIMEOUT_SECONDS=120

# Health
CONSECUTIVE_FAILURES_FOR_ERROR=5
HEALTH_SCORE_THRESHOLD=70

# Celery
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_ALWAYS_EAGER=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Development Setup

### Using Docker Compose (Recommended)
```bash
# Start feed service with all dependencies
~/.local/bin/docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d feed-service

# View logs
docker logs news-feed-service -f

# Check health
curl http://localhost:8001/health

# Access API docs
open http://localhost:8001/docs
```

### Manual Setup
```bash
# Install dependencies
cd services/feed-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Terminal 1: FastAPI server (hot-reload enabled)
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0

# Terminal 2: Celery worker
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Celery beat scheduler
celery -A app.celery_app beat --loglevel=info

# Terminal 4 (optional): Celery Flower monitoring
celery -A app.celery_app flower --port=5555
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html -v

# Run specific test file
pytest tests/test_feed_fetcher.py -v

# Run integration tests (requires infrastructure)
pytest tests/integration/ -v
```

## Architecture Patterns

### Intelligent Scheduling (Solves Thundering Herd Problem)
**Problem Solved:** Previously, 21+ feeds were fetching simultaneously at the same time, causing resource spikes and potential system overload ("thundering herd" problem).

**Solution:** Explicit scheduling with staggering algorithm instead of dynamic calculation.

**How It Works:**
1. **Explicit Timestamps:** Each feed has `next_fetch_at` timestamp instead of calculating `last_fetched_at + interval`
2. **Staggering Algorithm:** Feeds with same interval are evenly distributed across time slots
   - Example: 33 feeds with 15-min interval → stagger by 15/33 = ~27 seconds each
3. **Offset Tracking:** `schedule_offset_minutes` stores the stagger offset for each feed
4. **Distribution Score:** 0-100 metric based on variance in feed distribution across time slots
5. **Auto-Optimization:** Admin can preview and apply optimization with one click

**Results:**
- **Before:** Max 21 feeds fetching simultaneously
- **After:** Max 4 feeds concurrent (78% reduction)
- **Distribution Score:** 100.0 (Excellent)
- **Load Balance:** Even distribution across all time slots

**Frontend Integration:**
- Timeline visualization (5-minute buckets over 24 hours)
- Distribution quality metrics with color-coded status
- One-click optimization with before/after preview
- Conflict detection and resolution recommendations

**Migration:** Migration 002 adds three new fields to `feeds` table. Backward compatible - falls back to old logic if `next_fetch_at` is NULL.

### Circuit Breaker Pattern
- **Per-feed circuit breakers** prevent cascading failures
- Opens after 5 consecutive failures
- Timeout: 120 seconds before half-open state
- Closes after 2 successful requests in half-open state

### Exponential Backoff
- Feeds in ERROR status get increased fetch intervals
- Multiplier: 2^consecutive_failures (max 64x normal interval)
- Prevents hammering failing feeds

### Content Deduplication
- SHA-256 hash of title + link + summary
- Unique constraint on content_hash column
- Prevents duplicate articles across multiple fetches

### Event-Driven Integration
- RabbitMQ topic exchange for flexible routing
- Services subscribe to relevant event patterns with wildcards
- Loose coupling between microservices

## Integration with Other Services

| Service | Port | Integration Type | Purpose |
|---------|------|------------------|---------|
| Auth Service | 8100 | JWT Validation | Validates authentication tokens |
| Content Analysis | 8102 | Event Consumer | Analyzes new articles (categorization, sentiment) |
| Scraping Service | 8110 | Event Consumer + API | Fetches full article content, calls PATCH endpoint |
| Research Service | 8103 | API Consumer | Queries feed items for research context |
| OSINT Service | 8104 | Event Consumer | Extracts intelligence from articles |
| Search Service | 8106 | Event Consumer | Indexes articles for full-text search |
| Notification Service | 8105 | Event Consumer | Alerts administrators on feed failures |
| Analytics Service | 8107 | Event Consumer | Tracks metrics and activity |

## Troubleshooting

### Feed Not Fetching Automatically
1. Check scheduler status: `GET /health` → verify `scheduler.is_running: true`
2. Verify feed is active: `GET /feeds/{id}` → check `is_active: true`, `status: "ACTIVE"`
3. Check fetch interval: Feed may not be due yet
4. Review logs: `docker logs news-feed-service --tail 100`

### Circuit Breaker Open
- Wait for 120-second timeout
- Verify feed URL is accessible: `curl -I {feed_url}`
- Check health: `GET /feeds/{id}/health`
- Manually trigger after fixing: `POST /feeds/{id}/fetch`

### Celery Tasks Not Executing
1. Verify worker is running: `docker ps | grep celery-worker`
2. Check Redis connection: `redis-cli -h localhost -p 6380 ping`
3. View Celery logs: `docker logs news-feed-celery-worker`
4. Check Flower UI: http://localhost:5555

### RabbitMQ Events Not Publishing
1. Check RabbitMQ connection in service logs
2. Verify exchange exists: Management UI → Exchanges → `news.events`
3. Enable tracing for debugging: Management UI → Admin → Tracing
4. Check consumer queue bindings and routing keys

## Performance Optimization

- **Concurrent Fetching:** Max 10 simultaneous fetches with 2-second jitter
- **Conditional HTTP Requests:** Uses ETag and Last-Modified headers
- **Connection Pooling:** 5 connections, 10 overflow (configurable)
- **Content Hashing:** Prevents duplicate processing with SHA-256
- **Circuit Breakers:** Automatically skip failing feeds
- **Async Operations:** Fully async with asyncpg and aio-pika

## Monitoring & Observability

### Health Checks
- Service health: `GET /health`
- Feed health: `GET /feeds/{id}/health`
- Quality metrics: `GET /feeds/{id}/quality`

### Celery Monitoring
- Flower UI: http://localhost:5555
- Task history, status, and performance metrics

### RabbitMQ Monitoring
- Management UI: http://localhost:15673
- Exchange/queue statistics, message tracing

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing

## API Documentation

- **Swagger UI:** http://localhost:8001/docs (interactive)
- **ReDoc:** http://localhost:8001/redoc (clean documentation)
- **OpenAPI Spec:** http://localhost:8001/openapi.json

## Dependencies (46 Total)

**Core Framework:**
- fastapi==0.115.0, uvicorn[standard]==0.30.0, pydantic==2.8.0

**Database:**
- sqlalchemy==2.0.35, alembic==1.13.0, asyncpg==0.29.0, psycopg2-binary==2.9.9

**Task Queue:**
- celery[redis]==5.3.6, flower==2.0.1, redis==5.0.1

**Message Broker:**
- aio-pika==9.4.0

**Feed Processing:**
- feedparser==6.0.11, beautifulsoup4==4.12.3, lxml==5.1.0, httpx==0.27.0

**Authentication:**
- python-jose[cryptography]==3.3.0

**Testing:**
- pytest==7.4.4, pytest-asyncio==0.23.3, pytest-cov==4.1.0, pytest-mock==3.12.0

**Development:**
- black==23.12.1, flake8==7.0.0, mypy==1.8.0, pre-commit==3.6.0

---

## Epic 2.2: Time-Decay Ranking

The feed-service supports **relevance-based sorting** using a time-decay algorithm. Articles lose relevance as they age, with category-specific decay rates to handle different content types appropriately.

### Overview

- **Purpose:** Sort articles by relevance rather than just recency
- **Algorithm:** Exponential decay based on article age
- **Categories:** Different decay rates for different content types (breaking news decays faster than analysis)
- **Batch Updates:** Celery task runs every 30 minutes to recalculate scores

### API Usage

Sort articles by relevance score using the `sort_by` parameter:

```bash
# Get articles sorted by relevance (highest first)
curl "http://localhost:8101/api/v1/feeds/items?sort_by=relevance_score&order=desc"

# With pagination
curl "http://localhost:8101/api/v1/feeds/items?sort_by=relevance_score&limit=20&skip=0"

# Filter by date range and sort by relevance
curl "http://localhost:8101/api/v1/feeds/items?sort_by=relevance_score&date_from=2026-01-01"
```

**Valid sort_by values:**
- `created_at` (default) - When the article was added to the system
- `published_at` - When the article was originally published
- `relevance_score` - Time-decay relevance score (highest = most relevant)

### Category-Specific Decay Rates

Different content types decay at different rates based on their nature:

| Category | Half-Life | Decay Rate | Use Case |
|----------|-----------|------------|----------|
| `breaking_news` | ~12 hours | 0.058 | Time-sensitive news that loses relevance quickly |
| `market_update` | ~18 hours | 0.039 | Financial market updates |
| `earnings` | ~24 hours | 0.029 | Earnings reports and financial announcements |
| `analysis` | ~7 days | 0.004 | In-depth analysis that stays relevant longer |
| `research` | ~10 days | 0.003 | Evergreen research content |
| `default` | ~2 days | 0.014 | Standard news content |

**Half-life meaning:** After the half-life period, an article's relevance score will be approximately 50% of its original value.

### How Scores Are Calculated

```python
from app.services.relevance_calculator import RelevanceCalculator, CATEGORY_DECAY_RATES

calculator = RelevanceCalculator()

# Calculate score for a single article
score = calculator.calculate_score(
    published_at=article.published_at,
    category="breaking_news",      # Category determines decay rate
    article_quality=0.8,            # Optional quality multiplier (0-1)
)
# Returns: 0.0 to 1.0 (higher = more relevant)

# Batch calculation for multiple articles
scores = calculator.calculate_batch([
    {"id": "article-1", "published_at": datetime.now() - timedelta(hours=1), "category": "breaking_news"},
    {"id": "article-2", "published_at": datetime.now() - timedelta(days=3), "category": "analysis"},
])
# Returns: {"article-1": 0.94, "article-2": 0.65}
```

### Database Schema

The `feed_items` table includes these columns for time-decay ranking:

```sql
-- Relevance score (0.0 to 1.0, higher = more relevant)
relevance_score FLOAT NULL

-- When the score was last calculated
relevance_calculated_at TIMESTAMP WITH TIME ZONE NULL
```

### Celery Beat Schedule

Relevance scores are automatically updated via Celery Beat:

```python
# From app/celery_app.py
"update-relevance-scores": {
    "task": "feed.update_relevance_scores",
    "schedule": 1800.0,  # Every 30 minutes
    "kwargs": {"days": 7, "batch_size": 1000},
    "options": {"expires": 900},
}
```

**Task Details:**
- **Schedule:** Every 30 minutes
- **Scope:** Articles from the last 7 days
- **Batch Size:** 1000 articles per batch
- **Queue:** `maintenance` (low priority)
- **Performance Target:** 22k+ articles in < 30 seconds

### Manual Score Recalculation

You can trigger a manual recalculation via Celery:

```python
from app.tasks.relevance_batch import update_relevance_scores_task

# Recalculate scores for last 7 days
result = update_relevance_scores_task.delay(days=7, batch_size=1000)

# Check result
print(result.get())
# {"processed": 22000, "updated": 21500, "errors": 0, "reference_time": "2026-01-22T12:00:00Z"}
```

### Related Files

- `app/services/relevance_calculator.py` - Core scoring algorithm with CATEGORY_DECAY_RATES
- `app/tasks/relevance_batch.py` - Celery batch update task
- `app/celery_app.py` - Beat schedule configuration
- `app/api/items.py` - API endpoint with `sort_by=relevance_score`
- `app/models/feed.py` - FeedItem model with `relevance_score` column
- `tests/test_relevance_calculator.py` - Unit tests for calculator
- `tests/test_relevance_batch.py` - Unit tests for batch task
- `tests/integration/test_time_decay_integration.py` - Full integration test

### Architecture Decision

See [ADR for Time-Decay Ranking](../../docs/decisions/) for architectural decisions related to this feature.

---

**Service Version:** 1.2.0
**Default Port:** 8001
**Last Updated:** 2026-01-22 (Added Time-Decay Ranking - Epic 2.2)
**Status:** Production Ready

## Epic 0.4: SimHash & NewsML-G2 Integration

The feed-service now includes advanced article fingerprinting and version tracking capabilities:

### SimHash Fingerprinting
- Calculated on article ingestion from `title + content`
- Stored in `simhash_fingerprint` column (BIGINT)
- Enables near-duplicate detection using Hamming distance

```python
from news_intelligence_common import SimHasher

# Check if two articles are duplicates
hasher = SimHasher()
if hasher.is_duplicate(article1.simhash_fingerprint, article2.simhash_fingerprint):
    print("Duplicate detected!")

# Calculate Hamming distance
distance = SimHasher.hamming_distance(fp1, fp2)
# distance < 3: exact duplicate
# distance 3-7: near-duplicate
# distance > 7: different content
```

### NewsML-G2 Version Tracking
- `version`: Increments on each update (starts at 1)
- `version_created_at`: Timestamp of version creation
- `pub_status`: `usable`, `withheld`, or `canceled`

### Article Update API

```bash
# Update article (increments version, recalculates SimHash)
curl -X PUT "http://localhost:8101/api/v1/items/{id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "change_type": "update"}'

# Correction (records reason in version history)
curl -X PUT "http://localhost:8101/api/v1/items/{id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Corrected Title", "change_type": "correction", "change_reason": "Fixed factual error"}'

# Withdrawal (sets pub_status to canceled)
curl -X PUT "http://localhost:8101/api/v1/items/{id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"change_type": "withdrawal", "change_reason": "Content no longer accurate"}'

# Get version history
curl "http://localhost:8101/api/v1/items/{id}/versions" \
  -H "Authorization: Bearer $TOKEN"
```

### article.created Event (Updated for Epic 0.4)

```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2026-01-04T10:30:00Z",
  "payload": {
    "item_id": "uuid",
    "feed_id": "uuid",
    "source_id": "uuid",
    "title": "Breaking News: Major Event",
    "link": "https://example.com/article",
    "content": "Full article content...",
    "has_content": true,
    "scrape_full_content": false,
    "scrape_method": "auto",
    "simhash_fingerprint": 1234567890123456789,
    "version": 1,
    "pub_status": "usable",
    "analysis_config": {
      "enable_summary": true,
      "enable_entity_extraction": true,
      "enable_topic_classification": true,
      "enable_categorization": false,
      "enable_finance_sentiment": false,
      "enable_geopolitical_sentiment": false,
      "enable_osint_analysis": false
    }
  }
}
```

### article.updated Event (New for Epic 0.4)

Published when an article is updated via the update API:

```json
{
  "event_type": "article.updated",
  "service": "feed-service",
  "timestamp": "2026-01-04T11:00:00Z",
  "payload": {
    "item_id": "uuid",
    "version": 2,
    "pub_status": "usable",
    "change_type": "update",
    "simhash_fingerprint": 9876543210987654321
  }
}
```

### Related Files
- `app/services/feed_fetcher.py` - SimHash calculation on ingestion
- `app/services/article_update_service.py` - Version tracking service (NEW)
- `app/api/items.py` - Update API endpoints
- `app/schemas/feed.py` - ArticleUpdateRequest, ArticleVersionResponse schemas
- `tests/test_simhash_integration.py` - SimHash tests
- `tests/test_article_update_service.py` - Update service tests
- `tests/test_epic_0_4_integration.py` - Integration tests

---

## Documentation

- [Service Documentation](../../docs/services/feed-service.md)
- [API Documentation](../../docs/api/feed-service-api.md)
