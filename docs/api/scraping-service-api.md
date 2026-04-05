# Scraping Service API

**Base URL:** `http://localhost:8109`

**Authentication:** Not required for health endpoints (event-driven service)

## Overview

The Scraping Service is an event-driven worker service that processes content scraping jobs from RabbitMQ. It has minimal REST API surface - only health check endpoints. All scraping operations are triggered by consuming `feed.item.created` events.

## Health Endpoints

### GET /health

Basic health check endpoint for load balancers and monitoring.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "scraping-service",
  "version": "1.0.0"
}
```

**Usage:**
```bash
curl http://localhost:8109/health
```

---

### GET /

Service information and capabilities.

**Response:** `200 OK`
```json
{
  "service": "scraping-service",
  "version": "1.0.0",
  "description": "Autonomous content scraping service",
  "methods": ["newspaper4k", "playwright"]
}
```

**Scraping Methods:**
- `newspaper4k` - NLP-based intelligent article extraction with automatic cookie banner handling (default, 80-90% success rate)
- `playwright` - Full browser automation for JavaScript-heavy sites and complex dynamic content

**Usage:**
```bash
curl http://localhost:8109/
```

---

## Event-Driven API

The primary interface for this service is event-based through RabbitMQ, not REST API.

### Event Consumption

**Queue:** `scraping.jobs`
**Exchange:** `news.events`
**Routing Key:** `feed.item.created`

**Consumed Event Schema:**
```json
{
  "event_type": "feed.item.created",
  "payload": {
    "feed_id": "uuid",
    "item_id": "uuid",
    "url": "https://example.com/article",
    "scrape_method": "newspaper4k"  // optional: newspaper4k (default) or playwright
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Processing Flow:**
1. Worker receives event from queue
2. Determines scraping strategy (newspaper4k or playwright)
3. Extracts content using newspaper4k NLP (title, authors, text, images, publish date) or Playwright browser automation
4. Tracks failures in Redis with per-feed threshold
5. Publishes `item_scraped` event with results and metadata
6. Updates Feed Service via REST API

---

### Event Publishing

**Exchange:** `news.events`
**Routing Key:** `item_scraped`

**Published Event Schema:**
```json
{
  "event_type": "item_scraped",
  "payload": {
    "feed_id": "uuid",
    "item_id": "uuid",
    "url": "https://example.com/article",
    "word_count": 850,
    "scrape_method": "newspaper4k",  // newspaper4k or playwright
    "status": "success",  // success, paywall, timeout, error, blocked
    "metadata": {  // Optional: only present with newspaper4k
      "extracted_authors": ["John Doe"],
      "extracted_title": "Article Title",
      "top_image": "https://example.com/image.jpg",
      "publish_date": "2025-01-19T09:00:00Z"
    }
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| `success` | Content extracted successfully |
| `paywall` | Content behind paywall or login |
| `timeout` | Request/page load timed out |
| `error` | General scraping error occurred |
| `blocked` | URL marked as blocked after repeated failures |

---

## Service-to-Service Integration

### Feed Service API Calls

The Scraping Service makes authenticated calls to Feed Service to update scraping results.

**Authentication:**
```http
X-Service-Key: <FEED_SERVICE_API_KEY>
X-Service-Name: scraping-service
```

**Update Feed Item:**
```http
PUT http://feed-service:8001/api/v1/feeds/{feed_id}/items/{item_id}
Content-Type: application/json
X-Service-Key: <FEED_SERVICE_API_KEY>

{
  "scraped_content": "Full article text...",
  "word_count": 850,
  "scrape_status": "success",
  "scraped_at": "2025-01-19T10:00:00Z"
}
```

---

## Configuration

The service is configured via environment variables. See [Service Documentation](../services/scraping-service.md#configuration) for complete reference.

**Key Configuration:**
- `SCRAPING_TIMEOUT`: HTTP/Playwright timeout (default: 30 seconds)
- `SCRAPING_MAX_RETRIES`: Retry attempts (default: 3)
- `SCRAPING_WORKER_CONCURRENCY`: Concurrent jobs (default: 3)
- `PLAYWRIGHT_HEADLESS`: Headless browser mode (default: true)

---

## Error Handling

### Failure Tracking

Failed scraping attempts are tracked in Redis:

**Redis Key Pattern:**
```
scraping:failures:{url_hash}
```

**Stored Data:**
```json
{
  "url": "https://example.com/article",
  "failure_count": 5,
  "last_error": "Timeout after 30s",
  "first_failed_at": "2025-01-19T09:00:00Z",
  "last_failed_at": "2025-01-19T10:00:00Z"
}
```

**Blocking Logic:**
- Each feed has a configurable `scrape_failure_threshold` (1-20, default: 5)
- After reaching the threshold, the feed's scraping is automatically disabled
- Feed-level failure tracking (not URL-level) allows per-source configuration
- Failures can be manually reset via Feed Service API endpoint: `POST /feeds/{id}/scraping/reset`
- Disabled feeds show `scrape_disabled_reason: "auto_threshold"` in feed metadata

### Retry Strategy

1. **First Attempt:** Use configured method (newspaper4k or playwright)
2. **Retry 1:** Same method with exponential backoff (5s)
3. **Retry 2:** Fallback to Playwright if newspaper4k failed (10s delay)
4. **Retry 3:** Final attempt with Playwright (20s delay)
5. **After Max Retries:** Increment feed failure counter, publish `error` status event
6. **Threshold Reached:** Auto-disable scraping when `scrape_failure_count >= scrape_failure_threshold`

---

## Monitoring

### Metrics

Prometheus metrics available at `/metrics`:

- `scraping_jobs_total{status}` - Total scraping jobs by status
- `scraping_duration_seconds{method}` - Scraping duration by method
- `scraping_failures_total{reason}` - Failures by reason
- `rabbitmq_messages_consumed_total` - Total messages consumed
- `rabbitmq_messages_processed_total{status}` - Messages processed by status

### Logging

Structured logs include:

```json
{
  "timestamp": "2025-01-19T10:00:00Z",
  "level": "INFO",
  "message": "Content scraped successfully",
  "url": "https://example.com/article",
  "method": "httpx",
  "word_count": 850,
  "duration_ms": 1234,
  "feed_id": "uuid",
  "item_id": "uuid"
}
```

---

## Performance Characteristics

### Scraping Method Comparison

| Method | Speed | JavaScript Support | Cookie Banner Handling | Memory Usage | Success Rate | Use Case |
|--------|-------|-------------------|----------------------|--------------|--------------|----------|
| **newspaper4k** | Fast (200-800ms) | No | Automatic (NLP) | Low (80MB) | 80-90% | Static HTML, news articles, blogs (recommended default) |
| **playwright** | Slow (2-5s) | Yes | Manual (must code) | High (500MB+) | 95%+ | SPAs, paywalls, complex dynamic content |

### Concurrency

- **Default:** 3 concurrent jobs (`SCRAPING_WORKER_CONCURRENCY=3`)
- **Low Memory:** Set to 1-2 for resource-constrained environments
- **High Throughput:** Set to 5-10 with 4GB+ memory allocation

### Throughput Estimates

- **newspaper4k only:** ~80-150 pages/minute (recommended for news feeds)
- **playwright only:** ~10-20 pages/minute
- **Mixed workload:** ~60-120 pages/minute (newspaper4k with playwright fallback)

---

## Related Documentation

- [Service Documentation](../services/scraping-service.md)
- [Event Architecture](../architecture/EVENT_DRIVEN_ARCHITECTURE.md)
- [Feed Service API](./feed-service-api.md)
