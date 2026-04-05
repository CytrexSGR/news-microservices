# Scraping Service Documentation

## Overview

The Scraping Service is an autonomous content extraction service that fetches full article content from RSS feed items using intelligent multi-strategy scraping.

**Key Responsibilities:**
- Extract full article content from URLs published by Feed Service
- Support multiple scraping strategies (newspaper4k, Playwright) with automatic fallback
- Track scraping failures and automatically disable problematic feeds
- Enrich articles with Wikipedia data for entity relationships
- Publish events for downstream processing (Content Analysis, OSINT)

**Architecture Pattern:** Event-driven microservice with RabbitMQ consumer and REST API

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 14+ (shared with Feed Service)
- Redis 7+ (failure tracking)
- RabbitMQ 3.12+ (event consumption/publication)

### Installation

```bash
# Start service
cd /home/cytrex/news-microservices
docker compose up -d scraping-service

# Check health
curl http://localhost:8009/health

# Expected response:
# {"status":"healthy","service":"scraping-service","version":"1.0.0"}
```

### Docker Compose Configuration

```yaml
scraping-service:
  build:
    context: .
    dockerfile: ./services/scraping-service/Dockerfile.dev
  container_name: news-scraping-service
  restart: unless-stopped
  pids_limit: 512
  ports:
    - "8009:8009"
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: 5432
    REDIS_HOST: redis
    REDIS_PORT: 6379
    RABBITMQ_HOST: rabbitmq
    RABBITMQ_PORT: 5672
  volumes:
    - ./services/scraping-service/app:/app/app  # Hot-reload enabled
  depends_on:
    - postgres
    - redis
    - rabbitmq
  networks:
    - news_network
```

## Architecture

### System Components

```mermaid
graph TB
    subgraph "External Sources"
        RSS[RSS Feeds]
        Web[Web Content]
        Wiki[Wikipedia API]
    end

    subgraph "scraping-service:8009"
        API[FastAPI Application]
        Worker[RabbitMQ Worker]
        Scraper[Content Scraper<br/>newspaper4k + Playwright]
        WikiClient[Wikipedia Client<br/>MediaWiki API]
        FailTracker[Failure Tracker<br/>Redis]
        EventPub[Event Publisher<br/>RabbitMQ]
    end

    subgraph "Infrastructure"
        RMQ[RabbitMQ<br/>news.events exchange]
        Redis[(Redis DB 1<br/>Failure Counters)]
        Feed[Feed Service<br/>API :8101]
    end

    subgraph "Downstream Services"
        Content[Content Analysis<br/>:8102]
        OSINT[OSINT Service<br/>:8104]
    end

    RSS -->|feed items| Feed
    Feed -->|article.created| RMQ
    RMQ -->|scraping job| Worker
    Worker -->|scrape| Scraper
    Scraper -->|fetch| Web
    Scraper -->|update| Feed
    Worker -->|track| FailTracker
    FailTracker -->|counters| Redis
    Worker -->|publish| EventPub
    EventPub -->|item_scraped| RMQ
    RMQ -->|trigger| Content
    RMQ -->|trigger| OSINT
    API -->|enrich| WikiClient
    WikiClient -->|query| Wiki

    style API fill:#4CAF50
    style Worker fill:#2196F3
    style Scraper fill:#FF9800
    style WikiClient fill:#9C27B0
```

### Data Flow

#### 1. Scraping Job Flow (Event-Driven)

```mermaid
sequenceDiagram
    participant Feed as Feed Service
    participant RMQ as RabbitMQ
    participant Worker as Scraping Worker
    participant Scraper as Content Scraper
    participant Website as Target Website
    participant Tracker as Failure Tracker
    participant Redis as Redis
    participant EventPub as Event Publisher

    Feed->>RMQ: Publish article.created event<br/>{feed_id, item_id, url}
    RMQ->>Worker: Deliver message (queue: scraping_jobs)
    Worker->>Scraper: scrape(url, method="newspaper4k")
    Scraper->>Website: Download HTML
    Website-->>Scraper: HTML content
    Scraper->>Scraper: Extract article text<br/>+ metadata (NLP)
    Scraper-->>Worker: ScrapeResult<br/>(content, word_count, status)

    alt Scraping Success
        Worker->>Feed: PATCH /feeds/{id}/items/{id}<br/>Update content + metadata
        Worker->>Tracker: record_success(feed_id)
        Tracker->>Redis: DELETE scrape_failures:{feed_id}
        Worker->>EventPub: Publish item_scraped event
        EventPub->>RMQ: Route to content-analysis
    else Scraping Failed
        Worker->>Feed: PATCH /feeds/{id}/items/{id}<br/>Update status only
        Worker->>Tracker: record_failure(feed_id)
        Tracker->>Redis: INCR scrape_failures:{feed_id}
        Tracker->>Tracker: Check threshold (default: 5)
        alt Threshold Exceeded
            Tracker->>Feed: PATCH /feeds/{id}<br/>Set scrape_full_content=false
        end
        Worker->>EventPub: Publish scraping.failed event
    end
```

#### 2. Wikipedia Enrichment Flow (API-Driven)

```mermaid
sequenceDiagram
    participant Client as Knowledge Graph
    participant API as Wikipedia API
    participant WikiClient as Wikipedia Client
    participant MediaWiki as MediaWiki API

    Client->>API: POST /api/v1/wikipedia/search<br/>{query: "Elon Musk"}
    API->>WikiClient: search(query, language, limit)
    WikiClient->>MediaWiki: GET /w/api.php?action=query&list=search
    MediaWiki-->>WikiClient: Search results with page_ids
    WikiClient-->>API: List[WikipediaSearchResult]
    API-->>Client: {results: [{title, page_id, snippet}]}

    Client->>API: POST /api/v1/wikipedia/article<br/>{title: "Elon Musk"}
    API->>WikiClient: get_article(title, include_infobox=true)
    WikiClient->>MediaWiki: GET /w/api.php?action=query&prop=...
    MediaWiki-->>WikiClient: Article data
    WikiClient->>MediaWiki: GET /w/api.php?action=parse (for infobox)
    MediaWiki-->>WikiClient: HTML with infobox table
    WikiClient->>WikiClient: Parse infobox key-value pairs
    WikiClient-->>API: WikipediaArticle (extract, infobox, categories, links)
    API-->>Client: Full article data with structured metadata

    Client->>API: POST /api/v1/wikipedia/relationships<br/>{title: "Tesla, Inc."}
    API->>WikiClient: extract_relationships(title)
    WikiClient->>WikiClient: Analyze infobox + text<br/>Map fields to relationship types
    WikiClient-->>API: List of relationship candidates<br/>with confidence scores
    API-->>Client: {relationships: [{entity1, entity2, type, confidence}]}
```

### Integration Points

#### Upstream Dependencies
1. **Feed Service (8101)** - REST API client
   - `PATCH /api/v1/feeds/{feed_id}/items/{item_id}` - Update scraped content
   - `PATCH /api/v1/feeds/{feed_id}` - Disable scraping on failure threshold
   - `GET /api/v1/feeds/{feed_id}/threshold` - Get feed-specific failure threshold
   - Authentication: `X-Service-Key` header (service-to-service API key)

2. **RabbitMQ (news.events exchange)** - Event consumption
   - Queue: `scraping_jobs` (durable)
   - Routing Keys: `article.created`, `feed_item_created`, `feed.item.created`
   - Prefetch: 3 concurrent jobs (configurable via `SCRAPING_WORKER_CONCURRENCY`)

3. **Redis (DB 1)** - Failure tracking
   - Keys: `scrape_failures:{feed_id}` (24-hour TTL)
   - Keys: `feed_threshold:{feed_id}` (1-hour cache for thresholds)

4. **External APIs**
   - Wikipedia MediaWiki API (de.wikipedia.org, en.wikipedia.org)
   - No authentication required (public API)

#### Downstream Services
1. **Content Analysis Service** - Consumes `item_scraped` events
2. **OSINT Service** - Consumes `item_scraped` events for intelligence monitoring

## API Endpoints

### Health & Status

#### GET /health
**Description:** Service health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "scraping-service",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

#### GET /
**Description:** Service information and capabilities

**Response:**
```json
{
  "service": "scraping-service",
  "version": "1.0.0",
  "description": "Autonomous content scraping service",
  "methods": ["httpx", "playwright", "auto"]
}
```

---

### Monitoring & Metrics

#### GET /api/v1/monitoring/metrics
**Description:** Get comprehensive service metrics

**Response:**
```json
{
  "concurrency": {
    "active_jobs": 2,
    "max_concurrent": 3,
    "available_slots": 1,
    "total_jobs_processed": 150,
    "active_job_details": [
      {
        "url": "https://example.com/article1",
        "start_time": "2024-11-24T10:00:00Z",
        "duration_seconds": 5.2
      }
    ]
  },
  "retry": {
    "total_retries": 12,
    "successful_retries": 10,
    "failed_retries": 2
  },
  "browser": {
    "initialized": true,
    "playwright_initialized": true
  }
}
```

**Status Codes:**
- `200 OK` - Metrics retrieved successfully

**Use Case:** Monitor service health and performance

---

#### GET /api/v1/monitoring/rate-limits/{key}
**Description:** Get rate limit statistics for a specific key

**Path Parameters:**
- `key` - Rate limit key (e.g., `domain:example.com`, `global`, `feed:uuid`)

**Response:**
```json
{
  "key": "domain:example.com",
  "current_count": 5,
  "limit": 10,
  "window_seconds": 60,
  "reset_at": "2024-11-24T10:01:00Z"
}
```

**Status Codes:**
- `200 OK` - Rate limit stats retrieved
- `404 Not Found` - Key does not exist

**Use Case:** Monitor rate limiting per domain/feed

---

#### GET /api/v1/monitoring/active-jobs
**Description:** Get detailed information about currently active scraping jobs

**Response:**
```json
{
  "count": 2,
  "max_concurrent": 3,
  "available_slots": 1,
  "jobs": [
    {
      "url": "https://example.com/article1",
      "start_time": "2024-11-24T10:00:00Z",
      "duration_seconds": 5.2
    },
    {
      "url": "https://example.com/article2",
      "start_time": "2024-11-24T10:00:03Z",
      "duration_seconds": 2.8
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Active jobs retrieved

**Use Case:** Real-time monitoring of scraping operations

---

#### POST /api/v1/monitoring/reset-stats
**Description:** Reset collected statistics (for debugging/testing)

**Response:**
```json
{
  "status": "success",
  "message": "Statistics reset"
}
```

**Resets:**
- Concurrency statistics
- Retry statistics

**Status Codes:**
- `200 OK` - Statistics reset successfully

**Use Case:** Clear metrics during testing or after maintenance

---

#### GET /api/v1/monitoring/failures/{feed_id}
**Description:** Get failure count and status for a specific feed

**Path Parameters:**
- `feed_id` - Feed UUID

**Response:**
```json
{
  "feed_id": "123e4567-e89b-12d3-a456-426614174000",
  "failure_count": 3,
  "threshold": 5,
  "is_disabled": false
}
```

**Status Codes:**
- `200 OK` - Failure stats retrieved
- `500 Internal Server Error` - Redis connection failed

**Use Case:** Track feed health and auto-disable status

---

### Wikipedia API (Entity Enrichment)

#### POST /api/v1/wikipedia/search
**Description:** Search Wikipedia articles by query

**Request Body:**
```json
{
  "query": "Elon Musk",
  "language": "de",  // "de" or "en"
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Elon Musk",
      "page_id": 123456,
      "snippet": "Elon Reeve Musk ist ein..."
    }
  ],
  "query": "Elon Musk",
  "count": 1
}
```

**Status Codes:**
- `200 OK` - Search successful
- `500 Internal Server Error` - Wikipedia API failure

**Use Case:** Find correct Wikipedia article title before data extraction

---

#### POST /api/v1/wikipedia/article
**Description:** Extract full Wikipedia article with structured data

**Request Body:**
```json
{
  "title": "Tesla, Inc.",
  "language": "en",
  "include_infobox": true,
  "include_categories": true,
  "include_links": true
}
```

**Response:**
```json
{
  "title": "Tesla, Inc.",
  "extract": "Tesla, Inc. is an American automotive and clean energy company...",
  "url": "https://en.wikipedia.org/wiki/Tesla,_Inc.",
  "infobox": {
    "Industry": "Automotive",
    "Founded": "July 1, 2003",
    "Founder": "Elon Musk, Martin Eberhard, JB Straubel, Marc Tarpenning, Ian Wright",
    "Headquarters": "Austin, Texas, U.S.",
    "CEO": "Elon Musk"
  },
  "categories": [
    "Electric vehicle manufacturers",
    "Companies listed on NASDAQ",
    "American electric vehicle manufacturers"
  ],
  "links": [
    "Elon Musk",
    "SpaceX",
    "Model 3",
    "Model S",
    "Gigafactory"
  ],
  "language": "en",
  "page_id": 2242799,
  "last_modified": "2024-11-23T10:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Article extracted successfully
- `404 Not Found` - Article does not exist
- `500 Internal Server Error` - Extraction failed

**Use Case:** Enrich Knowledge Graph entities with Wikipedia data

---

#### POST /api/v1/wikipedia/relationships
**Description:** Extract relationship candidates from Wikipedia article

**Request Body:**
```json
{
  "title": "Tesla, Inc.",
  "language": "en",
  "entity_type": "ORGANIZATION"  // Optional hint
}
```

**Response:**
```json
{
  "entity": "Tesla, Inc.",
  "relationships": [
    {
      "entity1": "Tesla, Inc.",
      "entity2": "Elon Musk",
      "relationship_type": "CEO_of",
      "confidence": 0.95,
      "evidence": "Wikipedia infobox: CEO=Elon Musk",
      "source": "wikipedia_infobox"
    },
    {
      "entity1": "Tesla, Inc.",
      "entity2": "Austin, Texas",
      "relationship_type": "located_in",
      "confidence": 0.90,
      "evidence": "Wikipedia infobox: Headquarters=Austin, Texas, U.S.",
      "source": "wikipedia_infobox"
    }
  ],
  "count": 2
}
```

**Relationship Types Extracted:**
- **Organizations:** `founded_by`, `CEO_of`, `located_in`, `operates_in`, `owns`, `owned_by`
- **People:** `born_in`, `works_as`, `works_for`, `associated_with`, `member_of`

**Status Codes:**
- `200 OK` - Relationships extracted (may be empty list)
- `500 Internal Server Error` - Extraction failed

**Use Case:** Bootstrap Knowledge Graph relationships from Wikipedia

---

**Full API Reference:** [OpenAPI Specification](../openapi-specs/scraping-service.yaml)

## Configuration

### Environment Variables

#### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `FEED_SERVICE_API_KEY` | Service-to-service authentication key for Feed Service API | `secret-key-123` |
| `RABBITMQ_USER` | RabbitMQ username | `admin` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `secure-password` |

#### Connection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SERVICE_NAME` | `scraping-service` | Service identifier |
| `SERVICE_PORT` | `8109` | HTTP server port |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |
| `FEED_SERVICE_URL` | `http://feed-service:8001` | Feed Service base URL |
| `RABBITMQ_URL` | (optional) | Full RabbitMQ connection URL (overrides individual params) |
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ port |
| `RABBITMQ_VHOST` | `news_mcp` | RabbitMQ virtual host |
| `RABBITMQ_EXCHANGE` | `news.events` | Exchange name (topic) |
| `RABBITMQ_QUEUE` | `scraping_jobs` | Queue name (durable) |
| `RABBITMQ_ROUTING_KEY` | `feed.item.created` | Primary routing key |
| `REDIS_URL` | (optional) | Full Redis connection URL (overrides individual params) |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `1` | Redis database number (0-15) |
| `REDIS_PASSWORD` | (optional) | Redis password |

#### Scraping Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SCRAPING_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `SCRAPING_MAX_RETRIES` | `3` | Maximum retry attempts per URL |
| `SCRAPING_FAILURE_THRESHOLD` | `5` | Default failures before auto-disable (feeds can override) |
| `SCRAPING_WORKER_CONCURRENCY` | `3` | Concurrent scraping jobs (RabbitMQ prefetch) |

#### Newspaper4k Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NEWSPAPER4K_TIMEOUT` | `15` | Download timeout (seconds) |
| `NEWSPAPER4K_MIN_WORD_COUNT` | `50` | Minimum characters for successful scrape |

#### Playwright Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser in headless mode |
| `PLAYWRIGHT_TIMEOUT` | `30000` | Page load timeout (milliseconds) |

### Configuration Example

```bash
# .env file for scraping-service
SERVICE_NAME=scraping-service
SERVICE_PORT=8109
LOG_LEVEL=INFO

# Feed Service Integration
FEED_SERVICE_URL=http://feed-service:8001
FEED_SERVICE_API_KEY=your-secret-key-here

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=secure-password
RABBITMQ_VHOST=news_mcp
RABBITMQ_EXCHANGE=news.events
RABBITMQ_QUEUE=scraping_jobs

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

# Scraping
SCRAPING_TIMEOUT=30
SCRAPING_WORKER_CONCURRENCY=3
SCRAPING_FAILURE_THRESHOLD=5

# Newspaper4k
NEWSPAPER4K_MIN_WORD_COUNT=50

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
```

## Event Integration

### Events Consumed

#### `article.created` (Primary)
**Exchange:** `news.events` (topic)
**Queue:** `scraping_jobs` (durable)
**Routing Keys:** `article.created`, `feed_item_created`, `feed.item.created` (backwards compatibility)

**Payload:**
```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2024-11-24T10:00:00Z",
  "payload": {
    "feed_id": "123e4567-e89b-12d3-a456-426614174000",
    "item_id": "789e4567-e89b-12d3-a456-426614174001",
    "url": "https://example.com/article",
    "scrape_method": "newspaper4k"  // or "playwright", "auto"
  }
}
```

**Processing:**
1. Scrape content from URL using specified method
2. Update Feed Service with extracted content + metadata
3. Track success/failure in Redis
4. Publish result event (`item_scraped` or `scraping.failed`)

---

### Events Published

#### `item_scraped` (Success)
**Exchange:** `news.events` (topic)
**Routing Key:** `item_scraped`
**Consumers:** Content Analysis Service, OSINT Service

**Payload:**
```json
{
  "event_type": "item_scraped",
  "service": "scraping-service",
  "timestamp": "2024-11-24T10:00:30Z",
  "correlation_id": "789e4567-e89b-12d3-a456-426614174001",
  "payload": {
    "feed_id": "123e4567-e89b-12d3-a456-426614174000",
    "item_id": "789e4567-e89b-12d3-a456-426614174001",
    "url": "https://example.com/article",
    "word_count": 1250,
    "scrape_method": "newspaper4k",
    "status": "success"
  }
}
```

**Triggers:** Downstream content analysis and OSINT monitoring

---

#### `scraping.failed` (Failure)
**Exchange:** `news.events` (topic)
**Routing Key:** `scraping.failed`
**Consumers:** Monitoring/alerting systems

**Payload:**
```json
{
  "event_type": "scraping.failed",
  "service": "scraping-service",
  "timestamp": "2024-11-24T10:00:30Z",
  "correlation_id": "789e4567-e89b-12d3-a456-426614174001",
  "payload": {
    "feed_id": "123e4567-e89b-12d3-a456-426614174000",
    "item_id": "789e4567-e89b-12d3-a456-426614174001",
    "url": "https://example.com/article",
    "error_message": "Access blocked (403)",
    "scrape_status": "blocked"  // or "timeout", "error", "paywall"
  }
}
```

**Scrape Status Values:**
- `success` - Content extracted successfully
- `paywall` - Paywall detected (content may be partial)
- `timeout` - Request/page load timeout
- `blocked` - Access blocked (403 Forbidden)
- `error` - General error (see error_message)

---

**Event Architecture:** [Event-Driven Architecture](../../docs/architecture/EVENT_DRIVEN_ARCHITECTURE.md)

## Code Structure

### Directory Tree

```
scraping-service/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application + lifespan
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Pydantic settings (env vars)
│   │
│   ├── api/
│   │   └── wikipedia.py             # Wikipedia enrichment endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scraper.py               # Content scraper (newspaper4k + Playwright)
│   │   ├── wikipedia_client.py      # MediaWiki API client
│   │   ├── failure_tracker.py       # Redis-based failure tracking
│   │   └── event_publisher.py       # RabbitMQ event publishing
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   └── scraping_worker.py       # RabbitMQ consumer (scraping jobs)
│   │
│   └── models/                      # (Empty - uses Feed Service models)
│
├── Dockerfile.dev                   # Development build (hot-reload)
├── healthcheck.sh                   # Health check script
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # Quick reference
```

### Component Responsibilities

#### `app/main.py`
- FastAPI application initialization
- CORS middleware configuration
- Lifespan management:
  - Startup: Initialize scraper, failure tracker, worker
  - Shutdown: Gracefully close all connections
- Health check endpoints

#### `app/core/config.py`
- Pydantic Settings for environment variables
- URL parsing for RabbitMQ/Redis connection strings
- Configuration validation

#### `app/api/wikipedia.py`
- REST endpoints for Wikipedia data extraction
- Request/response models (Pydantic)
- Error handling and logging

#### `app/services/scraper.py`
- **ContentScraper class:**
  - Multi-strategy scraping (newspaper4k, Playwright)
  - HTTP client management (httpx)
  - Playwright browser lifecycle management
  - Paywall detection
  - Content extraction and cleaning

#### `app/services/wikipedia_client.py`
- **WikipediaClient class:**
  - MediaWiki API integration (Query API + REST API)
  - Article search and extraction
  - Infobox parsing (structured data)
  - Category and link extraction
  - Relationship extraction from infobox + text patterns

#### `app/services/failure_tracker.py`
- **FailureTracker class:**
  - Redis-based failure counting (24-hour TTL)
  - Feed-specific threshold retrieval (with 1-hour cache)
  - Automatic feed disabling via Feed Service API
  - Success tracking (reset counters)

#### `app/services/event_publisher.py`
- **EventPublisher class:**
  - RabbitMQ connection management (robust connection)
  - Event publishing with custom JSON encoder (UUID, datetime, Decimal)
  - Batch event publishing
  - Singleton pattern for global instance

#### `app/workers/scraping_worker.py`
- **ScrapingWorker class:**
  - RabbitMQ consumer (queue: scraping_jobs)
  - Message parsing and job extraction
  - Scraping orchestration
  - Feed Service API updates
  - Event publishing (success/failure)
  - Prefetch control for concurrency

## Scraping Methods

### 1. newspaper4k (Default, Recommended)

**Best For:** News articles, blogs, standard content sites

**Features:**
- Intelligent article extraction using NLP
- Automatic cookie banner/ad removal
- Author detection
- Publish date parsing
- Top image extraction
- Fast performance (no browser overhead)

**Configuration:**
```python
NEWSPAPER4K_TIMEOUT=15
NEWSPAPER4K_MIN_WORD_COUNT=50
```

**Example Output:**
```python
ScrapeResult(
    content="Full article text...",
    word_count=1250,
    status="success",
    method_used="newspaper4k",
    extracted_title="Article Title",
    extracted_authors=["John Doe", "Jane Smith"],
    extracted_publish_date=datetime(2024, 11, 24),
    extracted_metadata={
        "top_image": "https://example.com/image.jpg",
        "images": ["https://example.com/img1.jpg", ...],
        "movies": []
    }
)
```

---

### 2. Playwright (JavaScript-Heavy Sites)

**Best For:** Single-page applications (SPAs), JavaScript-rendered content

**Features:**
- Full Chromium browser automation
- Waits for JavaScript to render content
- Network idle detection
- Screenshot capability (future)
- Slower but handles complex sites

**Configuration:**
```python
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000  # milliseconds
```

**Browser Management:**
- Lazy initialization (only when needed)
- Page-level lifecycle (create/close per request)
- Headless mode for production
- Automatic cleanup on service shutdown

---

### 3. Auto Strategy (Future)

**Planned Feature:** Intelligent strategy selection
1. Try newspaper4k first (fast)
2. If content too short or failed, retry with Playwright
3. Track per-domain success rates in Redis
4. Auto-select best strategy for each domain

---

### Scraping Flow

```python
async def scrape(url: str, method: str = "newspaper4k") -> ScrapeResult:
    """
    Scrape content from URL.

    Returns:
        ScrapeResult with status:
        - success: Content extracted (word_count > 0)
        - paywall: Paywall detected (partial content)
        - timeout: Request/page load timeout
        - blocked: Access blocked (403)
        - error: General failure
    """
```

**Content Extraction:**
1. Download HTML (newspaper4k) or render page (Playwright)
2. Remove noise elements (scripts, styles, nav, footer, header)
3. Extract main content using CSS selectors:
   - `<article>`, `[role="main"]`, `.article-content`, `.post-content`
   - Fallback: Extract all `<p>` tags
4. Clean text (strip whitespace, remove [references])
5. Count words, validate minimum length
6. Detect paywall indicators

**Paywall Detection:**
- Keywords: "subscribe", "subscription", "paywall", "premium content"
- Threshold: Content < 200 words + keyword present

## Failure Tracking

### Redis-Based Failure Counting

**Purpose:** Track scraping failures per feed and auto-disable problematic feeds

**Redis Keys:**
- `scrape_failures:{feed_id}` - Failure counter (expires after 24 hours)
- `feed_threshold:{feed_id}` - Cached feed-specific threshold (expires after 1 hour)

### Failure Workflow

```mermaid
stateDiagram-v2
    [*] --> Scraping
    Scraping --> Success: Content extracted
    Scraping --> Failed: Error/timeout/blocked

    Success --> ResetCounter: record_success()
    ResetCounter --> [*]: Redis: DELETE scrape_failures:{feed_id}

    Failed --> IncrementCounter: record_failure()
    IncrementCounter --> CheckThreshold: Redis: INCR scrape_failures:{feed_id}

    CheckThreshold --> BelowThreshold: count < threshold
    CheckThreshold --> AboveThreshold: count >= threshold

    BelowThreshold --> [*]: Continue scraping

    AboveThreshold --> DisableFeed: PATCH /feeds/{id}<br/>scrape_full_content=false
    DisableFeed --> [*]: Stop scraping this feed
```

### Feed-Specific Thresholds

**Default:** 5 failures (configurable via `SCRAPING_FAILURE_THRESHOLD`)

**Feed Override:** Feeds can specify custom thresholds
- Stored in Feed Service database: `feeds.scrape_failure_threshold`
- Fetched via API: `GET /api/v1/feeds/{feed_id}/threshold`
- Cached in Redis for 1 hour to reduce API calls

**Auto-Disable Behavior:**
```json
{
  "scrape_full_content": false,
  "scrape_disabled_reason": "auto_threshold",
  "scrape_failure_count": 5,
  "scrape_last_failure_at": "2024-11-24T10:00:00Z"
}
```

**Re-Enable:** Manual intervention required
1. Fix underlying issue (update feed URL, adjust scraping method)
2. Reset failure counter: `DELETE scrape_failures:{feed_id}` in Redis
3. Update feed: `PATCH /api/v1/feeds/{feed_id}` → `scrape_full_content=true`

## Wikipedia Enrichment

### Use Cases

1. **Entity Resolution:** Find canonical entity names via search
2. **Knowledge Graph Enrichment:** Extract structured data (infobox)
3. **Relationship Discovery:** Bootstrap entity relationships
4. **Category Classification:** Auto-tag entities by Wikipedia categories

### MediaWiki API Integration

**Endpoints Used:**
- `action=query&list=search` - Search articles
- `action=query&prop=extracts|info|categories|links` - Get article data
- `action=parse&page=...` - Get HTML for infobox parsing

**Rate Limiting:** No authentication required, but respect User-Agent header

**Supported Languages:**
- German (de.wikipedia.org)
- English (en.wikipedia.org)

### Infobox Extraction

**Infobox Types:**
- Organizations: Industry, Founded, Founder, CEO, Headquarters
- People: Born, Occupation, Employer, Known for
- Places: Location, Type, Population

**Parsing Algorithm:**
1. Fetch HTML via `action=parse`
2. Find `<table class="infobox">` in BeautifulSoup
3. Extract `<th>` (key) and `<td>` (value) pairs
4. Clean values (remove [reference] markers)
5. Return as dictionary

### Relationship Extraction

**Confidence Scoring:**
- Infobox field: 0.80 - 0.95 (high confidence)
- Text pattern match: 0.70 (lower confidence, requires NER)

**Relationship Mappings:**
```python
{
    "Founded": ("founded", 0.95),
    "Founder": ("founded_by", 0.95),
    "CEO": ("CEO_of", 0.95),
    "Headquarters": ("located_in", 0.90),
    "Industry": ("operates_in", 0.80),
    "Parent": ("owned_by", 0.90),
    "Born": ("born_in", 0.90),
    "Occupation": ("works_as", 0.80),
}
```

**Future Enhancement:** Replace text pattern matching with NER (spaCy/BERT) for higher accuracy

## Deployment

### Docker Build

```bash
# Development build (hot-reload)
docker build -f Dockerfile.dev -t scraping-service:dev .

# Production build (future - Dockerfile missing)
# TODO: Create optimized production Dockerfile
```

### Health Check

**Script:** `healthcheck.sh`
```bash
#!/bin/sh
# Step 1: Validate imports
python3 -c "from app.main import app" 2>/dev/null || exit 1

# Step 2: Check HTTP endpoint
curl -f http://localhost:8000/health || exit 1
```

**Note:** Port mismatch in healthcheck (8000 vs 8009) - See Issues Report

### Resource Requirements

**Development:**
- CPU: 0.5 cores (idle), 2 cores (active scraping)
- Memory: 512 MB (newspaper4k), 1 GB (Playwright)
- Disk: 500 MB (base image + Playwright browser)

**Production Recommendations:**
- CPU: 2 cores minimum (Playwright browser)
- Memory: 2 GB minimum (browser + concurrent jobs)
- Disk: 1 GB (browser cache)
- PID Limit: 512 (current) or 1024 (recommended for Playwright)

### Scaling

**Horizontal Scaling:**
- Multiple instances can consume from same RabbitMQ queue
- Redis failure counters are shared across instances
- No state stored in service (stateless)

**Concurrency Control:**
- `SCRAPING_WORKER_CONCURRENCY=3` (RabbitMQ prefetch)
- Increase for higher throughput (watch memory usage)
- Recommended: 3-5 per instance

**Performance Tuning:**
- newspaper4k: 5-10 seconds per article
- Playwright: 15-30 seconds per article
- Throughput: ~10-20 articles/minute per instance (newspaper4k)

## Troubleshooting

### Common Issues

#### 1. Worker Not Consuming Messages

**Symptoms:**
- Messages stay in queue
- Logs show "Scraping worker started" but no "Processing scraping job" messages

**Diagnosis:**
```bash
# Check RabbitMQ queue status
docker exec -it news-rabbitmq rabbitmqctl list_queues name messages consumers

# Expected output:
# scraping_jobs  5  1  (1 consumer active)
```

**Solutions:**
- Verify queue binding: Check `routing_keys` in worker initialization
- Check RabbitMQ credentials: Ensure `RABBITMQ_USER` and `RABBITMQ_PASSWORD` are correct
- Inspect RabbitMQ logs: `docker logs news-rabbitmq`

---

#### 2. Playwright Browser Fails to Start

**Symptoms:**
- Logs show: "Error launching browser: ..."
- Scraping method falls back to error state

**Diagnosis:**
```bash
# Check if Playwright browsers are installed
docker exec -it news-scraping-service playwright install --dry-run
```

**Solutions:**
```bash
# Install browsers (if missing)
docker exec -it news-scraping-service playwright install chromium

# OR rebuild image (Dockerfile.dev already includes dependencies)
docker compose build scraping-service
```

**Root Cause:** Playwright requires system libraries (see Dockerfile.dev lines 8-33)

---

#### 3. High Memory Usage (Playwright)

**Symptoms:**
- Memory usage > 2 GB per instance
- OOM (Out of Memory) kills

**Diagnosis:**
```bash
# Check memory usage
docker stats news-scraping-service
```

**Solutions:**
- Reduce concurrency: `SCRAPING_WORKER_CONCURRENCY=1` or `2`
- Close browser between batches: Implement periodic browser restart
- Use newspaper4k for most feeds, Playwright only for SPAs

**Memory Breakdown:**
- Base service: 150 MB
- newspaper4k: +50 MB per job
- Playwright browser: +300 MB (base) + 100 MB per page

---

#### 4. Feed Service API Authentication Fails

**Symptoms:**
- Logs show: "Failed to update feed item ... 401 Unauthorized"
- Scraped content not saved to database

**Diagnosis:**
```bash
# Test Feed Service API key
curl -H "X-Service-Key: your-key-here" \
     -H "X-Service-Name: scraping-service" \
     http://localhost:8101/api/v1/feeds

# Expected: 200 OK (list of feeds)
```

**Solutions:**
- Verify `FEED_SERVICE_API_KEY` matches Feed Service configuration
- Check Feed Service logs: `docker logs news-feed-service`
- Ensure Feed Service is running: `docker ps | grep feed-service`

---

#### 5. Redis Connection Failed

**Symptoms:**
- Logs show: "Error connecting to Redis ..."
- Failure tracking not working

**Diagnosis:**
```bash
# Test Redis connection
docker exec -it news-scraping-service redis-cli -h redis ping

# Expected: PONG
```

**Solutions:**
- Check Redis is running: `docker ps | grep redis`
- Verify `REDIS_HOST` and `REDIS_PORT` in environment
- Check Redis logs: `docker logs news-redis`

---

#### 6. Paywall Content Extracted

**Symptoms:**
- Low word count (<200 words) for known full articles
- Content ends with "Subscribe to read more"

**Current Behavior:**
- Paywall detection sets `status=paywall` but still saves content
- No retry with different method

**Solutions:**
- Mark article as paywall in Feed Service (already done)
- Future: Implement anti-paywall strategies (cookies, user agent rotation)
- Manual: Disable `scrape_full_content` for paywalled feeds

---

#### 7. Scraping Timeout

**Symptoms:**
- Logs show: "Request timeout" or "Page load timeout"
- Status: `timeout`

**Solutions:**
- Increase timeouts:
  - `SCRAPING_TIMEOUT=60` (newspaper4k)
  - `PLAYWRIGHT_TIMEOUT=60000` (Playwright)
- Check network connectivity: `docker exec -it news-scraping-service curl -I <target-url>`
- Retry with different method: Change `scrape_method` to `playwright` if using `newspaper4k`

---

### Debug Mode

**Enable verbose logging:**
```bash
# docker-compose.yml or .env
LOG_LEVEL=DEBUG
```

**Restart service:**
```bash
docker compose restart scraping-service
```

**View logs:**
```bash
# Follow live logs
docker logs -f news-scraping-service

# Search logs
docker logs news-scraping-service | grep "Processing scraping job"
```

---

### Testing Scraping Manually

**Method 1: Trigger via RabbitMQ Management UI**
1. Open http://localhost:15672
2. Login: `admin` / `[password]`
3. Go to "Queues" → `scraping_jobs`
4. Publish message:
```json
{
  "event_type": "article.created",
  "payload": {
    "feed_id": "123e4567-e89b-12d3-a456-426614174000",
    "item_id": "789e4567-e89b-12d3-a456-426614174001",
    "url": "https://example.com/test-article",
    "scrape_method": "newspaper4k"
  }
}
```

**Method 2: Python Script**
```python
import aio_pika
import asyncio
import json

async def test_scraping():
    connection = await aio_pika.connect_robust(
        "amqp://admin:password@localhost:5672/news_mcp"
    )
    channel = await connection.channel()
    exchange = await channel.get_exchange("news.events")

    message = {
        "event_type": "article.created",
        "payload": {
            "feed_id": "test-feed-id",
            "item_id": "test-item-id",
            "url": "https://example.com/article",
            "scrape_method": "newspaper4k"
        }
    }

    await exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key="article.created"
    )
    print("Test message published!")
    await connection.close()

asyncio.run(test_scraping())
```

---

### Performance Monitoring

**Key Metrics:**
- Scraping success rate: `successful_scrapes / total_scrapes`
- Average word count: Indicator of content quality
- Failure rate per feed: Identify problematic sources
- Processing time: Time from message receipt to event publication

**Future:** Integrate with Prometheus/Grafana for dashboards

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.115.0 | REST API + async support |
| ASGI Server | Uvicorn | 0.30.0 | Production server with hot-reload |
| HTTP Client | httpx | 0.27.0 | Async HTTP requests |
| HTML Parsing | BeautifulSoup4 | 4.12.3 | HTML parsing |
| HTML Parser | lxml | 5.1.0 | Fast XML/HTML parsing |
| Article Extraction | newspaper4k | 0.9.3 | Intelligent article extraction with NLP |
| Browser Automation | Playwright | 1.41.0 | JavaScript-heavy site scraping |
| Message Queue | aio-pika | 9.4.0 | Async RabbitMQ client |
| Cache/Storage | redis | 5.0.1 | Async Redis client for failure tracking |
| Configuration | pydantic-settings | 2.4.0 | Environment variable management |
| Logging | structlog | 24.4.0 | Structured logging |
| Date Parsing | python-dateutil | 2.8.2 | Date parsing utilities |

**Development Tools:**
- pytest 7.4.4 - Testing framework
- pytest-asyncio 0.23.3 - Async test support
- black 23.12.1 - Code formatting
- flake8 7.0.0 - Linting
- mypy 1.8.0 - Type checking

## Related Documentation

- [API Documentation](../openapi-specs/scraping-service.yaml) - OpenAPI 3.1 specification
- [Code Quality Report](../issues/scraping-service-issues.md) - Security, performance, technical debt
- [Feed Service Documentation](../../docs/services/feed-service.md) - Upstream dependency
- [Content Analysis Service](../../docs/services/content-analysis-v3.md) - Downstream consumer
- [Event-Driven Architecture](../../docs/architecture/EVENT_DRIVEN_ARCHITECTURE.md) - Event patterns
- [RabbitMQ Configuration](../../docs/guides/rabbitmq-guide.md) - Message queue setup

---

**Service Version:** 1.0.0
**Default Port:** 8009
**Last Updated:** 2024-11-24
**Status:** Production Ready

**Known Issues:** See [Code Quality Report](../issues/scraping-service-issues.md)
