# Event Emission in Scraping Service

## Overview

The Scraping Service now emits RabbitMQ events after scraping operations, enabling downstream processing like OSINT Event Analysis in the Content Analysis Service.

## Events Emitted

### 1. `item.scraped` (Routing Key: `item_scraped`)

**Trigger:** Successfully scraped article with ≥500 words

**Payload:**
```json
{
  "event_type": "item.scraped",
  "service": "scraping-service",
  "timestamp": "2025-10-14T12:34:56.789Z",
  "correlation_id": "article-uuid",
  "payload": {
    "feed_id": "feed-uuid",
    "item_id": "article-uuid",
    "url": "https://example.com/article",
    "scrape_word_count": 1234,
    "scrape_method": "httpx"  // or "playwright"
  }
}
```

**Purpose:**
- Triggers Event Analysis in Content Analysis Service
- Only emitted for articles with substantial content (≥500 words)
- Used for deep analysis, OSINT intelligence extraction

**Consumer:** Content Analysis Service (`item_scraped` event consumer)

---

### 2. `scraping.failed` (Routing Key: `scraping_failed`)

**Trigger:** Scraping operation failed

**Payload:**
```json
{
  "event_type": "scraping.failed",
  "service": "scraping-service",
  "timestamp": "2025-10-14T12:34:56.789Z",
  "correlation_id": "article-uuid",
  "payload": {
    "feed_id": "feed-uuid",
    "item_id": "article-uuid",
    "url": "https://example.com/blocked-article",
    "error_message": "403 Forbidden - bot detected",
    "scrape_status": "blocked"  // or "timeout", "error"
  }
}
```

**Purpose:**
- Monitoring and alerting
- Failure analysis
- Retry queue processing (future)

**Consumer:** Notification Service (monitoring/alerting)

---

## Implementation Details

### Files Modified

1. **`app/services/event_publisher.py`** (NEW)
   - EventPublisher class for RabbitMQ integration
   - JSON encoder for UUID/datetime/Decimal serialization
   - Connection management and error handling

2. **`app/workers/scraping_worker.py`** (MODIFIED)
   - Added `event_publisher` initialization in `start()`
   - Added `_publish_item_scraped_event()` method
   - Added `_publish_scraping_failed_event()` method
   - Integrated event emission into scraping workflow

### Configuration

**RabbitMQ Settings** (`.env`):
```env
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin_password_2024
RABBITMQ_VHOST=news_mcp
RABBITMQ_EXCHANGE=news_events
```

**Event Publisher:**
- Uses robust connection for fault tolerance
- Topic exchange for flexible routing
- Persistent messages (delivery_mode=2)
- Correlation IDs for request tracking

---

## Testing

### Manual Test with RabbitMQ Tracing

1. **Enable RabbitMQ tracing:**
   ```bash
   # Access Management UI
   http://localhost:15673

   # Admin → Tracing → Add trace
   # - Name: scraping_events
   # - Pattern: item_scraped  (or # for all)
   # - Format: JSON
   ```

2. **Trigger scraping:**
   ```bash
   # Via Feed Service API
   curl -X POST http://localhost:8101/api/v1/feeds/{feed_id}/fetch \
     -H "X-Service-Key: feed-service-secret-key-2024" \
     -H "X-Service-Name: scheduler-service"
   ```

3. **Check trace results:**
   ```
   Admin → Tracing → scraping_events → "Get messages"
   ```

4. **Verify event structure:**
   - ✅ event_type: "item.scraped"
   - ✅ service: "scraping-service"
   - ✅ payload.scrape_word_count ≥ 500
   - ✅ routing_key: "item_scraped"

### Integration Test

```python
# tests/integration/test_event_emission.py

async def test_item_scraped_event_published():
    """Test that item_scraped event is published after successful scrape"""

    # Setup: Create scraping job
    job = {
        "feed_id": str(uuid4()),
        "item_id": str(uuid4()),
        "url": "https://www.dw.com/en/test-article",
        "scrape_method": "httpx"
    }

    # Setup: RabbitMQ consumer
    received_events = []
    async def event_consumer(message):
        event = json.loads(message.body.decode())
        received_events.append(event)

    # Execute: Process scraping job
    await scraping_worker._process_message(create_mock_message(job))

    # Wait for event
    await asyncio.sleep(1)

    # Assert: Event was published
    assert len(received_events) == 1
    event = received_events[0]

    assert event["event_type"] == "item.scraped"
    assert event["service"] == "scraping-service"
    assert event["payload"]["item_id"] == job["item_id"]
    assert event["payload"]["scrape_word_count"] >= 500


async def test_short_articles_do_not_emit_event():
    """Test that articles <500 words do NOT emit item_scraped event"""

    # Mock scraper to return short article
    with patch('app.services.scraper.scrape') as mock_scrape:
        mock_scrape.return_value = ScrapeResult(
            status=ScrapeStatus.SUCCESS,
            content="Short article",
            word_count=250,  # Below threshold
            method_used="httpx"
        )

        # Execute scraping
        await scraping_worker._process_message(create_mock_message(job))

        # Assert: NO event published
        assert len(received_events) == 0
```

---

## Event Flow Diagram

```
┌─────────────────┐
│  Feed Service   │
└────────┬────────┘
         │ publishes: feed_item_created
         ▼
┌─────────────────┐
│ Scraping Worker │
└────────┬────────┘
         │ 1. Receives job
         │ 2. Scrapes content
         │ 3. Updates Feed Service (PATCH API)
         │ 4. Publishes event
         ▼
┌──────────────────────────┐
│   RabbitMQ Exchange      │
│   (news_events, topic)   │
└──────────┬───────────────┘
           │ Routing Key: item_scraped
           ▼
┌─────────────────────────────┐
│  Content Analysis Service   │
│  (Event Analysis Consumer)  │
└─────────────────────────────┘
           │ 1. Receives item_scraped event
           │ 2. Fetches article content
           │ 3. Performs Event Analysis
           │ 4. Stores structured event data
           ▼
┌─────────────────────────────┐
│   event_analyses table      │
└─────────────────────────────┘
```

---

## Next Steps

1. ✅ **BLOCKER REMOVED:** `item_scraped` event now exists
2. ⏳ **Implement Event Analysis Consumer** in Content Analysis Service
3. ⏳ **Create event_analyses database table**
4. ⏳ **Implement Event Analysis logic** (claim extraction, confidence scoring, etc.)

---

## Troubleshooting

### Event not appearing in trace

**Check:**
1. Scraping Service logs: `make logs SERVICE=scraping-service`
   - Look for: "Published item_scraped event for {item_id}"
2. RabbitMQ exchange exists: `docker exec news-rabbitmq rabbitmqctl list_exchanges`
3. Article word count ≥ 500: Event only emitted for substantial articles

### Connection errors

**Check:**
1. RabbitMQ is running: `docker ps | grep rabbitmq`
2. Credentials match: `.env` vs `docker-compose.yml`
3. Network connectivity: `docker network inspect news_network`

### Consumer not receiving events

**Check:**
1. Queue is bound to exchange: `docker exec news-rabbitmq rabbitmqctl list_bindings`
2. Routing key matches: "item_scraped" (with underscore, not dot)
3. Consumer is running: Check Content Analysis Service logs

---

## References

- **RabbitMQ Tracing:** https://www.rabbitmq.com/docs/firehose
- **aio-pika Documentation:** https://aio-pika.readthedocs.io/
- **Event-Driven Architecture:** `/docs/ARCHITECTURE.md`
