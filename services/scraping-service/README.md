# Scraping Service

Autonomous content extraction service with intelligent multi-strategy scraping, auto-profiling, and database-backed source profiles.

## Features

### Core Capabilities
- **Multi-Strategy Scraping:** newspaper4k → trafilatura → Playwright → Playwright Stealth (cascading fallback)
- **Auto-Profiling:** Automatically tests and selects the best scraping method for new domains
- **Source Registry:** Database-backed domain profiles with persistence across restarts
- **Intelligent Method Selection:** Uses historical success data to choose optimal scraping strategy

### Resilience & Performance
- **Exponential Backoff Retry:** Jittered retries with configurable delays
- **Rate Limiting:** Per-domain, per-feed, global limits (Redis-backed, fail-open)
- **Concurrency Control:** Semaphore-based job limiting with queue management
- **HTTP Caching:** In-memory cache for repeated requests
- **Priority Queue:** Job prioritization based on feed importance

### Anti-Detection & Stealth
- **User-Agent Rotation:** Dynamic UA pool via fake-useragent
- **Playwright Stealth:** Anti-bot detection patches for headless browsers
- **Proxy Rotation:** Optional proxy pool with health monitoring

### Integration
- **Event-Driven:** Consumes RabbitMQ events from Feed Service
- **PostgreSQL Persistence:** Source profiles stored in database
- **Prometheus Metrics:** Scraping statistics and performance monitoring
- **JWT Authentication:** Protected API endpoints

## Quick Start

```bash
# Start service
docker compose up -d scraping-service

# Check health
curl http://localhost:8009/health

# Direct scrape (auto-profiles new domains)
curl -X POST http://localhost:8009/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'

# View source profiles
curl http://localhost:8009/api/v1/source-profiles

# View metrics
curl http://localhost:8009/api/v1/monitoring/metrics

# Run tests
docker compose exec scraping-service python -m pytest tests/ -v
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Scraping Service                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   RabbitMQ   │───▶│   Scraping   │───▶│    Content Scraper       │  │
│  │    Worker    │    │    Worker    │    │  (newspaper4k/Playwright) │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│         │                   │                        │                  │
│         ▼                   ▼                        ▼                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │ Priority     │    │ Rate Limiter │    │   Auto-Profiler          │  │
│  │ Queue Worker │    │   (Redis)    │    │   (Method Testing)       │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│                             │                        │                  │
│                             ▼                        ▼                  │
│                      ┌──────────────┐    ┌──────────────────────────┐  │
│                      │   Source     │◀──▶│     PostgreSQL           │  │
│                      │   Registry   │    │  (source_profiles table) │  │
│                      └──────────────┘    └──────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Flow

```
Feed Service → article.created event → Scraping Worker
    ↓
Rate Limit Check (per-domain, per-feed, global)
    ↓
Source Registry Lookup (get domain profile)
    ↓
[New Domain?] → Auto-Profiler (test methods, save best)
    ↓
Intelligent Method Selection (based on profile)
    ↓
Scrape with Retry Logic (jittered exponential backoff)
    ↓
Update Source Profile (success/failure metrics)
    ↓
Update Feed Service (PATCH article content)
    ↓
Publish Events:
    - item_scraped (success) → Content Analysis
    - scraping.failed (failure) → DLQ / Monitoring
```

## Scraping Methods (Priority Order)

| Method | Use Case | Speed | JS Support |
|--------|----------|-------|------------|
| **newspaper4k** | News articles, blogs | Fast | No |
| **trafilatura** | Fallback extractor | Fast | No |
| **playwright** | JS-heavy sites | Slow | Yes |
| **playwright_stealth** | Anti-bot protected sites | Slow | Yes |

### Auto-Profiling

When encountering a new domain, the Auto-Profiler:

1. Tests `newspaper4k` first (fastest)
2. If word count < 50, tries `trafilatura`
3. If still insufficient, tries `playwright`
4. Finally tries `playwright_stealth` if needed
5. Saves the best method to database for future use

```bash
# Logs during auto-profiling:
🔍 Auto-profiling new domain: example.com
Starting auto-profiling for domain: example.com
Method newspaper4k works well, skipping remaining tests
Auto-profiling complete for example.com: method=newspaper4k, paywall=none
✅ Auto-profile complete: domain=example.com, method=newspaper4k
```

## API Endpoints

### Scraping

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scrape` | Direct scrape request |
| `POST` | `/api/v1/scrape/batch` | Batch scrape multiple URLs |

### Source Profiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/source-profiles` | List all domain profiles |
| `GET` | `/api/v1/source-profiles/{domain}` | Get specific domain profile |
| `PUT` | `/api/v1/source-profiles/{domain}` | Update domain profile |
| `DELETE` | `/api/v1/source-profiles/{domain}` | Delete domain profile |

### Queue Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/queue/stats` | Priority queue statistics |
| `GET` | `/api/v1/queue/jobs` | List queued jobs |
| `POST` | `/api/v1/queue/enqueue` | Add job to queue |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/api/v1/monitoring/metrics` | Detailed metrics |
| `GET` | `/api/v1/monitoring/active-jobs` | Currently running jobs |
| `GET` | `/api/v1/monitoring/rate-limits/{key}` | Rate limit status |
| `GET` | `/api/v1/monitoring/failures/{feed_id}` | Failure count |

### Cache Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cache/stats` | Cache statistics |
| `DELETE` | `/api/v1/cache/clear` | Clear cache |
| `DELETE` | `/api/v1/cache/{url}` | Remove specific entry |

### Dead Letter Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dlq` | List failed jobs |
| `POST` | `/api/v1/dlq/{id}/retry` | Retry failed job |
| `DELETE` | `/api/v1/dlq/{id}` | Remove from DLQ |

### Wikipedia API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wikipedia/search` | Search Wikipedia |
| `GET` | `/api/v1/wikipedia/summary/{title}` | Get article summary |
| `GET` | `/api/v1/wikipedia/content/{title}` | Get full content |

## Configuration

### Environment Variables

```bash
# =============================================================================
# Service Configuration
# =============================================================================
SERVICE_NAME=scraping-service
SERVICE_PORT=8009
LOG_LEVEL=INFO

# =============================================================================
# Database (PostgreSQL) - for Source Profile Persistence
# =============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=news_mcp
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# =============================================================================
# RabbitMQ
# =============================================================================
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_QUEUE=scraping_jobs
RABBITMQ_EXCHANGE=news.events

# =============================================================================
# Redis (Rate Limiting & Failure Tracking)
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=2
REDIS_PASSWORD=

# =============================================================================
# Scraping Configuration
# =============================================================================
SCRAPING_TIMEOUT=30                    # Request timeout (seconds)
SCRAPING_MAX_RETRIES=3                 # Max retry attempts
SCRAPING_FAILURE_THRESHOLD=10          # Failures before feed disabled
SCRAPING_WORKER_CONCURRENCY=3          # RabbitMQ prefetch count
SCRAPING_MAX_CONCURRENT_JOBS=5         # Max parallel jobs

# =============================================================================
# Rate Limiting
# =============================================================================
SCRAPING_RATE_LIMIT_PER_DOMAIN=10      # Requests per domain per window
SCRAPING_RATE_LIMIT_PER_FEED=20        # Requests per feed per window
SCRAPING_RATE_LIMIT_GLOBAL=50          # Total requests per window
SCRAPING_RATE_LIMIT_WINDOW=60          # Window duration (seconds)

# Wikipedia API (polite: ~1 req/sec)
WIKIPEDIA_RATE_LIMIT=10
WIKIPEDIA_RATE_LIMIT_WINDOW=10

# =============================================================================
# Feature Flags - Phase 1 (Enterprise Upgrade)
# =============================================================================
ENABLE_UA_ROTATION=true                # Dynamic User-Agent pool
ENABLE_JITTERED_BACKOFF=true           # Jittered exponential backoff
ENABLE_TRAFILATURA_FALLBACK=true       # Fallback to trafilatura

# =============================================================================
# Feature Flags - Phase 2 (Intelligence)
# =============================================================================
ENABLE_SOURCE_REGISTRY=true            # Track per-source profiles
ENABLE_AUTO_METHOD_SELECTION=true      # Intelligent method selection
ENABLE_AUTO_PROFILING=true             # Auto-profile new domains

# =============================================================================
# Feature Flags - Phase 6 (Scale)
# =============================================================================
ENABLE_PROXY_ROTATION=false            # Proxy rotation (requires config)
ENABLE_HTTP_CACHE=true                 # In-memory response cache
ENABLE_PRIORITY_QUEUE=true             # Priority-based job queue

# =============================================================================
# HTTP Cache Configuration
# =============================================================================
HTTP_CACHE_MAX_ENTRIES=5000
HTTP_CACHE_MAX_SIZE_MB=500
HTTP_CACHE_DEFAULT_TTL_SECONDS=3600    # 1 hour
HTTP_CACHE_NEWS_TTL_SECONDS=1800       # 30 minutes for news

# =============================================================================
# Priority Queue Configuration
# =============================================================================
PRIORITY_QUEUE_MAX_SIZE=10000
PRIORITY_QUEUE_MAX_RETRIES=3

# =============================================================================
# Playwright Configuration
# =============================================================================
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000               # Milliseconds

# =============================================================================
# newspaper4k / trafilatura Configuration
# =============================================================================
NEWSPAPER4K_TIMEOUT=15
NEWSPAPER4K_MIN_WORD_COUNT=50
TRAFILATURA_TIMEOUT=30
TRAFILATURA_MIN_WORD_COUNT=50

# =============================================================================
# Authentication
# =============================================================================
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
```

## Database Schema

### source_profiles Table

```sql
CREATE TABLE source_profiles (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,

    -- Scraping Configuration
    scrape_method VARCHAR(50),           -- newspaper4k, trafilatura, playwright, playwright_stealth
    fallback_methods JSON,               -- ["trafilatura", "playwright"]
    scrape_status VARCHAR(50),           -- active, blocked, rate_limited

    -- Paywall Detection
    paywall_type VARCHAR(50),            -- none, soft, hard, metered
    paywall_bypass_method VARCHAR(100),

    -- Performance Metrics
    success_rate FLOAT,
    avg_response_time_ms INTEGER,
    total_attempts INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,

    -- Rate Limiting
    rate_limit_per_minute INTEGER,
    last_rate_limited_at TIMESTAMP,

    -- Content Quality
    avg_word_count INTEGER,
    avg_extraction_quality FLOAT,

    -- Anti-Detection Requirements
    requires_ua_rotation BOOLEAN DEFAULT false,
    requires_stealth BOOLEAN DEFAULT false,
    requires_proxy BOOLEAN DEFAULT false,
    custom_headers JSON,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_successful_scrape TIMESTAMP,
    last_failed_scrape TIMESTAMP,

    -- Notes
    notes VARCHAR(1000)
);

CREATE UNIQUE INDEX ix_source_profiles_domain ON source_profiles(domain);
```

## Implementation Phases

### Phase 1: Enterprise Upgrade
- [x] User-Agent rotation (fake-useragent)
- [x] Jittered exponential backoff
- [x] Trafilatura fallback extractor

### Phase 2: Intelligence
- [x] Source Registry with database persistence
- [x] Intelligent method selection
- [x] Auto-profiling for new domains

### Phase 3: Anti-Detection
- [x] Playwright stealth mode
- [x] Prometheus metrics collector

### Phase 4: Hardening
- [x] Exponential backoff retry logic
- [x] Playwright memory leak fix
- [x] Redis-based rate limiting
- [x] Concurrency control

### Phase 5: Quality
- [x] JSON-LD structured data extraction
- [x] Dead Letter Queue handler
- [x] Quality scoring

### Phase 6: Scale
- [x] Proxy rotation support
- [x] HTTP response caching
- [x] Priority queue system

### Phase 7: Auto-Profiling
- [x] Automatic domain profiling
- [x] Method testing cascade
- [x] Database persistence

## Monitoring

### Health Check

```bash
curl http://localhost:8009/health
```

```json
{
  "status": "healthy",
  "service": "scraping-service",
  "version": "3.0.0",
  "components": {
    "browser": "initialized",
    "redis": "connected",
    "database": "connected",
    "rate_limiter": {
      "status": "connected",
      "fail_open": false
    },
    "concurrency": {
      "max_concurrent": 5,
      "active_jobs": 2,
      "available_slots": 3,
      "total_processed": 1543,
      "success_rate": "94.23%"
    },
    "retry": {
      "total_retries": 127,
      "successful_retries": 98,
      "failed_retries": 29,
      "success_rate": "77.17%"
    }
  }
}
```

### Prometheus Metrics

Available at `/api/v1/metrics/prometheus`:

```
# Scraping metrics
scraping_requests_total{method="newspaper4k",status="success"} 1543
scraping_requests_total{method="playwright",status="success"} 234
scraping_duration_seconds{method="newspaper4k"} 0.45
scraping_word_count{domain="example.com"} 850

# Cache metrics
http_cache_hits_total 892
http_cache_misses_total 651
http_cache_size_bytes 125000000

# Queue metrics
priority_queue_size 12
priority_queue_processed_total 3421
```

## Troubleshooting

### Common Issues

#### Auto-Profiling Not Working
```bash
# Check if feature is enabled
docker exec news-scraping-service env | grep ENABLE_AUTO_PROFILING

# Check logs for profiling activity
docker logs news-scraping-service 2>&1 | grep "Auto-profil"
```

#### Database Connection Failed
```bash
# Verify credentials
docker exec news-scraping-service env | grep POSTGRES

# Test connection manually
docker exec news-scraping-service python3 -c "
from app.core.config import settings
print('DATABASE_URL:', settings.DATABASE_URL[:50] + '...')
"
```

#### Profiles Not Persisting
```bash
# Check database for profiles
docker exec postgres psql -U news_user -d news_mcp -c \
  "SELECT domain, scrape_method, total_successes FROM source_profiles;"

# Check service logs for save errors
docker logs news-scraping-service 2>&1 | grep -E "Failed to save|ERROR.*profile"
```

#### High Memory Usage
```bash
# Check browser contexts
docker stats news-scraping-service

# Verify Playwright cleanup
docker logs news-scraping-service 2>&1 | grep -E "browser|context|close"
```

#### Rate Limiting Issues
```bash
# Check current limits
curl http://localhost:8009/api/v1/monitoring/rate-limits/global

# Check Redis connection
curl http://localhost:8009/health | jq '.components.redis'
```

### Performance Tuning

| Scenario | Setting | Recommendation |
|----------|---------|----------------|
| Low load | `SCRAPING_MAX_CONCURRENT_JOBS` | 3 |
| Medium load | `SCRAPING_MAX_CONCURRENT_JOBS` | 5 (default) |
| High load | `SCRAPING_MAX_CONCURRENT_JOBS` | 10 |
| Conservative scraping | `SCRAPING_RATE_LIMIT_PER_DOMAIN` | 5/min |
| Aggressive scraping | `SCRAPING_RATE_LIMIT_PER_DOMAIN` | 20/min |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL (asyncpg) |
| Cache | Redis |
| Message Queue | RabbitMQ (aio-pika) |
| HTTP Client | httpx |
| Browser | Playwright (Chromium) |
| Article Extraction | newspaper4k, trafilatura |
| Anti-Detection | playwright-stealth, fake-useragent |
| Metrics | prometheus_client |

## File Structure

```
services/scraping-service/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── cache.py           # Cache management
│   │   ├── dlq.py             # Dead letter queue
│   │   ├── metrics.py         # Prometheus metrics
│   │   ├── monitoring.py      # Health & monitoring
│   │   ├── proxy.py           # Proxy management
│   │   ├── queue.py           # Priority queue
│   │   ├── scrape.py          # Direct scrape API
│   │   ├── source_profiles.py # Source profile CRUD
│   │   └── wikipedia.py       # Wikipedia API
│   ├── core/                   # Core utilities
│   │   ├── concurrency.py     # Semaphore limiter
│   │   ├── config.py          # Configuration
│   │   ├── rate_limiter.py    # Redis rate limiting
│   │   ├── retry.py           # Retry logic
│   │   └── user_agents.py     # UA rotation
│   ├── db/                     # Database
│   │   ├── __init__.py
│   │   └── session.py         # Async SQLAlchemy
│   ├── models/                 # Data models
│   │   ├── scrape.py          # Scrape request/response
│   │   └── source_profile.py  # SQLAlchemy ORM model
│   ├── services/               # Business logic
│   │   ├── auto_profiler.py   # Domain auto-profiling
│   │   ├── scraper.py         # Main scraper orchestrator
│   │   ├── source_registry.py # Profile management
│   │   └── extraction/        # Content extractors
│   │       ├── newspaper_extractor.py
│   │       ├── playwright_extractor.py
│   │       └── trafilatura_extractor.py
│   ├── workers/                # Background workers
│   │   ├── scraping_worker.py # RabbitMQ consumer
│   │   └── queue_worker.py    # Priority queue processor
│   └── main.py                 # Application entry
├── tests/                      # Unit & integration tests
├── .env                        # Environment config
├── Dockerfile.dev              # Development container
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Related Documentation

- [Architecture Overview](../../ARCHITECTURE.md)
- [Backend Development Guide](../../CLAUDE.backend.md)
- [Service Documentation](../../docs/services/scraping-service.md)
- [API Documentation](../../docs/api/scraping-service-api.md)

---

**Version:** 3.0.0 (Phase 7 - Auto-Profiling + DB Persistence)
**Port:** 8009
**Status:** Production Ready
**Last Updated:** 2025-12-27
