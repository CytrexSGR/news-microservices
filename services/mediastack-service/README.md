# MediaStack Service

> Thin API layer for MediaStack news aggregation with n8n workflow orchestration.

## Overview

The MediaStack service provides a lightweight wrapper around the [MediaStack API](https://mediastack.com/documentation) for news URL discovery. It is designed to work with n8n workflows for automated news aggregation pipelines.

**Key Features:**
- Live and historical news fetching
- Redis-based monthly rate limiting (10,000 calls/month free tier)
- RabbitMQ event publishing for workflow integration
- Automatic usage tracking and reporting

## Quick Start

```bash
# Start the service (with dependencies)
docker compose up -d mediastack-service

# Check health
curl http://localhost:8121/health

# Check API usage
curl http://localhost:8121/api/v1/news/usage
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDIASTACK_API_KEY` | Required | Your MediaStack API key |
| `MEDIASTACK_MONTHLY_LIMIT` | 10000 | Monthly call limit |
| `REDIS_URL` | redis://redis:6379/0 | Redis connection for rate limiting |
| `RABBITMQ_URL` | amqp://rabbitmq:5672/ | RabbitMQ for event publishing |
| `SERVICE_PORT` | 8121 | Service port |

Create `.env` file:
```env
MEDIASTACK_API_KEY=your_api_key_here
REDIS_URL=redis://:redis_secret_2024@redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

## API Endpoints

### Live News
```http
GET /api/v1/news/live?keywords=bitcoin&categories=business&limit=25
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `keywords` | string | Search keywords |
| `sources` | string | Comma-separated source IDs |
| `categories` | string | business, entertainment, general, health, science, sports, technology |
| `countries` | string | ISO 2-letter codes (us, de, gb, etc.) |
| `languages` | string | Language codes (en, de, etc.) |
| `limit` | int | 1-100 (default: 25) |
| `offset` | int | Pagination offset |

**Response:**
```json
{
  "pagination": { "limit": 25, "offset": 0, "count": 25, "total": 1000 },
  "data": [
    {
      "author": "John Doe",
      "title": "Breaking News",
      "description": "Short snippet...",
      "url": "https://example.com/article",
      "source": "cnn",
      "image": "https://...",
      "category": "general",
      "language": "en",
      "country": "us",
      "published_at": "2025-12-26T12:00:00+00:00"
    }
  ],
  "usage": {
    "current_calls": 500,
    "monthly_limit": 10000,
    "remaining": 9500,
    "percentage": 5.0,
    "status": "ok"
  }
}
```

### Historical News (Paid Plans Only)
```http
GET /api/v1/news/historical?keywords=bitcoin&date_from=2025-12-01&date_to=2025-12-20
```

Additional parameters: `date_from`, `date_to` (YYYY-MM-DD format)

### Sources
```http
GET /api/v1/news/sources?countries=us,de&categories=business
```

### Usage Stats
```http
GET /api/v1/news/usage
```

**Response:**
```json
{
  "current_calls": 500,
  "monthly_limit": 10000,
  "remaining": 9500,
  "percentage": 5.0,
  "month": "2025-12",
  "days_remaining": 5,
  "calls_per_day_remaining": 1900,
  "status": "ok"  // ok | warning (>70%) | critical (>90%)
}
```

## Rate Limiting

The service implements Redis-based monthly rate limiting:
- **Free Plan:** 10,000 calls/month
- **Counter Reset:** Automatic at month end (TTL-based)
- **Pre-flight Check:** Always call `/usage` before fetching

**Rate Limit Response (HTTP 429):**
```json
{
  "detail": {
    "error": "Monthly rate limit exceeded",
    "usage": { "remaining": 0, "status": "critical" }
  }
}
```

## RabbitMQ Events

The service publishes events to the `news` exchange (topic type):

| Event | Routing Key | When |
|-------|-------------|------|
| Articles Fetched | `news.articles.fetched` | After successful API call |
| URLs Discovered | `news.urls.discovered` | When extracting URLs for scraping |

**Event Payload Example:**
```json
{
  "event_type": "news.articles.fetched",
  "timestamp": "2025-12-26T12:00:00",
  "source": "mediastack_live",
  "article_count": 25,
  "query_params": { "keywords": "bitcoin" },
  "articles": [...]
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MediaStack Service                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  FastAPI     │  │  Redis       │  │  RabbitMQ    │       │
│  │  Endpoints   │  │  Rate Limit  │  │  Publisher   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────────────────────────────────────────┐      │
│  │           MediaStack API Client                   │      │
│  │           (httpx async)                          │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │                                     │
          ▼                                     ▼
    MediaStack API                         RabbitMQ
    (external)                              (n8n workflows)
```

## Integration with n8n

See [n8n Workflow Documentation](../../docs/n8n/mediastack-workflows.md) for:
- Scheduled news fetching
- URL deduplication patterns
- Error handling with retries
- Best practices

**Example Workflow:**
```
Schedule → Check Usage → Fetch News → Dedupe URLs → Queue for Scraping
```

## Development

```bash
# Run tests
docker run --rm -v $(pwd):/app -w /app python:3.11-slim \
  bash -c "pip install -r requirements.txt && pytest tests/ -v"

# Local development (hot reload)
docker compose up mediastack-service

# View logs
docker compose logs -f mediastack-service
```

## Project Structure

```
mediastack-service/
├── app/
│   ├── api/v1/
│   │   └── news.py          # API endpoints
│   ├── clients/
│   │   └── mediastack_client.py  # MediaStack API client
│   ├── core/
│   │   └── config.py        # Configuration
│   ├── events/
│   │   └── publisher.py     # RabbitMQ publisher
│   ├── schemas/
│   │   └── news.py          # Pydantic models
│   ├── services/
│   │   └── usage_tracker.py # Redis rate limiting
│   └── main.py              # FastAPI app
├── tests/
│   ├── test_api_news.py
│   ├── test_events.py
│   ├── test_mediastack_client.py
│   ├── test_schemas.py
│   └── test_usage_tracker.py
├── Dockerfile.dev
├── requirements.txt
└── README.md
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors | Rate limit exceeded | Check `/usage`, wait for month reset |
| Empty results | Invalid params | Check category/country codes |
| Connection refused | Service not running | `docker compose up mediastack-service` |
| Redis errors | Redis unavailable | Check Redis container health |

## Dependencies

- **Redis:** Rate limiting and usage tracking
- **RabbitMQ:** Event publishing for n8n
- No database required (stateless service)

## Related

- [MediaStack API Documentation](https://mediastack.com/documentation)
- [n8n Workflow Guide](../../docs/n8n/mediastack-workflows.md)
- [Service Inventory](../../reports/phase-1-inventory/SERVICE_INVENTORY_SUMMARY.md)
