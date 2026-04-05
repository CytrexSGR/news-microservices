# Event Schemas Documentation

> **Epic 0.3: Event Schema Standardization**
>
> All services in news-microservices use standardized `EventEnvelope` for RabbitMQ messaging.
> This document is the single source of truth for event formats, types, and topology.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Event Envelope Structure](#2-event-envelope-structure)
3. [Event Types Registry](#3-event-types-registry)
4. [Exchange Topology](#4-exchange-topology)
5. [Usage Examples](#5-usage-examples)
6. [Library Reference](#6-library-reference)
7. [Validation](#7-validation)

---

## 1. Overview

All services publish events wrapped in a standardized `EventEnvelope` from the `news-intelligence-common` library. This ensures:

- **Consistency**: All events have the same structure across services
- **Traceability**: Correlation and causation IDs enable distributed tracing
- **Versioning**: Event versions allow for backward-compatible evolution
- **Validation**: JSON Schema validation on both publish and consume

### Key Principles

1. **Event Type Format**: All event types follow `domain.action_name` pattern (e.g., `article.created`, `analysis.v3_completed`)
2. **Envelope Wrapping**: Payloads are never sent raw - always wrapped in `EventEnvelope`
3. **Topic-Based Routing**: Events use topic exchange with routing key = event type
4. **Persistent Delivery**: All messages use `DeliveryMode.PERSISTENT` for durability

---

## 2. Event Envelope Structure

Every event published to RabbitMQ **MUST** use this envelope structure:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "article.created",
  "event_version": "1.0",
  "source_service": "feed-service",
  "source_instance": "feed-service-7d9f8b6c4-xk2j9",
  "timestamp": "2026-01-04T12:00:00.000000+00:00",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "causation_id": null,
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Example Article",
    "link": "https://example.com/article"
  },
  "metadata": {}
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID (string) | Yes | Unique identifier for this event. Auto-generated. |
| `event_type` | string | Yes | Event type in `domain.action_name` format (lowercase, dots and underscores only) |
| `event_version` | string | Yes | Semantic version (e.g., "1.0"). For schema evolution. |
| `source_service` | string | Yes | Name of the publishing service (from `SERVICE_NAME` env var) |
| `source_instance` | string | Yes | Hostname/container ID of publishing instance (from `HOSTNAME` env var) |
| `timestamp` | ISO 8601 | Yes | UTC timestamp when event was created |
| `correlation_id` | UUID (string) | Yes | ID linking related events across services. Auto-generated if not provided. |
| `causation_id` | UUID (string) or null | No | ID of the event that directly caused this one |
| `payload` | object | Yes | The actual event data (domain-specific) |
| `metadata` | object | Yes | Additional metadata (empty by default) |

### Validation Rules

- `event_type`: Must match pattern `^[a-z]+\.[a-z_]+$` (e.g., `article.created`, `analysis.v3_completed`)
- `event_version`: Must match pattern `^\d+\.\d+$` (e.g., `1.0`, `2.1`)
- `timestamp`: Must be valid ISO 8601 format
- `event_id`, `correlation_id`: Must be valid UUIDs

---

## 3. Event Types Registry

### 3.1 Feed Service Events

**Exchange:** `news.events` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `feed.created` | New feed was created | `feed_id`, `url`, `title` |
| `feed.updated` | Feed configuration updated | `feed_id`, `changed_fields` |
| `feed.deleted` | Feed was deleted | `feed_id` |
| `feed.fetch_completed` | Feed fetch completed successfully | `feed_id`, `items_count`, `new_items_count` |
| `feed.fetch_failed` | Feed fetch failed | `feed_id`, `error_message`, `error_code` |
| `article.created` | New article/item was ingested | `article_id`, `title`, `link`, `source_id`, `source_type` |
| `article.updated` | Article content was updated | `article_id`, `version`, `change_type`, `changed_fields` |

### 3.2 Content-Analysis-V3 Events

**Exchange:** `news.events` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `analysis.v3_completed` | V3 analysis pipeline finished successfully | `article_id`, `success`, `pipeline_version`, `tier0`, `tier1`, `tier2`, `metrics` |
| `analysis.v3_failed` | V3 analysis pipeline encountered error | `article_id`, `error_message`, `failed_at`, `tier_failed` |

**Example Payload (`analysis.v3_completed`):**

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "pipeline_version": "3.0",
  "tier0": {
    "language": "en",
    "word_count": 1250,
    "content_type": "news_article"
  },
  "tier1": {
    "entities": [...],
    "topics": [...],
    "sentiment": 0.65
  },
  "tier2": {
    "geopolitical": {...},
    "economic": {...},
    "military": {...}
  },
  "metrics": {
    "total_duration_ms": 2450,
    "tier0_duration_ms": 150,
    "tier1_duration_ms": 800,
    "tier2_duration_ms": 1500
  }
}
```

### 3.3 FMP Service Events

**Exchange:** `finance` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `finance.quote_updated` | Real-time quote update | `symbol`, `price`, `change_percent`, `volume`, `timestamp` |
| `finance.eod_ingested` | End-of-day data ingested | `symbol`, `date`, `close`, `volume` |
| `finance.earnings_announced` | Earnings announcement | `symbol`, `company`, `report_date`, `eps_actual`, `eps_estimate`, `eps_surprise_percent` |
| `finance.macro_updated` | Macro indicator update | `indicator`, `value`, `period`, `release_date` |
| `finance.news_item` | Financial news item | `title`, `url`, `published_at`, `symbols`, `sentiment`, `source` |
| `finance.market_data_updated` | Market data updated (triggers KG sync) | `symbol`, `name`, `asset_type`, `exchange`, `currency`, `is_active` |

### 3.4 Scraping Service Events

**Exchange:** `news.events` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `scraping.item_scraped` | Article content was scraped successfully | `feed_id`, `item_id`, `url`, `word_count`, `scrape_method`, `status` |
| `scraping.failed` | Scraping failed | `feed_id`, `item_id`, `url`, `error_message`, `scrape_status` |
| `analysis.request` | Request for content analysis (post-scrape) | `article_id`, `title`, `url`, `content`, `run_tier2`, `triggered_by` |

### 3.5 MediaStack Service Events

**Exchange:** `news` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `news.articles_fetched` | Articles fetched from MediaStack API | `source`, `article_count`, `query_params`, `articles` |
| `news.urls_discovered` | URLs discovered for scraping | `batch_id`, `url_count`, `urls` |

### 3.6 Prediction Service Events

**Exchange:** `news.events` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `prediction.generated` | New prediction was generated | `prediction_id`, `article_id`, `entity_symbol`, `entity_type`, `forecast_horizon`, `predicted_direction`, `confidence`, `created_at` |
| `prediction.updated` | Prediction updated with actual outcome | `prediction_id`, `actual_value`, `prediction_error`, `direction_correct`, `updated_at` |
| `prediction.failed` | Prediction generation failed | `article_id`, `entity_symbol`, `error_message`, `failed_at` |

### 3.7 Knowledge Graph Service Events

**Exchange:** `news.events` (topic)

| Event Type | Description | Key Payload Fields |
|------------|-------------|-------------------|
| `relationships.extracted` | Entity relationships extracted | `article_id`, `entities`, `relationships`, `graph_updates` |

---

## 4. Exchange Topology

### 4.1 Exchange Overview

```
RabbitMQ Broker
├── news.events (topic) - Main exchange for all services
│   ├── article.* → content-analysis-v3, search-service, clustering-service
│   ├── analysis.* → feed-service, prediction-service, knowledge-graph-service
│   ├── scraping.* → monitoring, analytics-service
│   ├── prediction.* → notification-service, analytics-service
│   └── relationships.* → sitrep-service
│
├── finance (topic) - Financial data events
│   ├── finance.quote_* → portfolio-service, alerting
│   ├── finance.earnings_* → prediction-service, analytics
│   └── finance.market_* → knowledge-graph-service
│
└── news (topic) - News aggregation events
    ├── news.articles_fetched → scraping-service, dedup-service
    └── news.urls_discovered → scraping-service
```

### 4.2 Queue Bindings

| Queue | Exchange | Routing Key | Consumer |
|-------|----------|-------------|----------|
| `content_analysis_v3_queue` | `news.events` | `article.created` | content-analysis-v3 |
| `analysis_v3_requests_queue` | `news.events` | `analysis.v3_request` | content-analysis-v3 |
| `feed_analysis_updates_queue` | `news.events` | `analysis.v3_completed` | feed-service |
| `prediction_analysis_queue` | `news.events` | `analysis.v3_completed` | prediction-service |
| `search_events_queue` | `news.events` | `article.*`, `analysis.*` | search-service |
| `kg_relationships_queue` | `news.events` | `analysis.v3_completed` | knowledge-graph-service |
| `kg_finance_queue` | `finance` | `finance.market_data_updated` | knowledge-graph-service |

### 4.3 Message Flow

```
1. Article Ingestion Flow
   feed-service → article.created → content-analysis-v3
                                 → search-service (indexing)

2. Analysis Flow
   content-analysis-v3 → analysis.v3_completed → feed-service (update article)
                                               → prediction-service (generate predictions)
                                               → knowledge-graph-service (extract relationships)

3. Prediction Flow
   prediction-service → prediction.generated → notification-service
                     → prediction.updated → analytics-service

4. Scraping Flow
   mediastack-service → news.urls_discovered → scraping-service
   scraping-service → scraping.item_scraped → monitoring
                   → analysis.request → content-analysis-v3
```

---

## 5. Usage Examples

### 5.1 Creating an Event with `create_event()`

```python
from news_intelligence_common import create_event

# Create an article.created event
envelope = create_event(
    event_type="article.created",
    payload={
        "article_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Breaking News: Example",
        "link": "https://example.com/article",
        "source_id": "550e8400-e29b-41d4-a716-446655440001",
        "source_type": "rss",
    },
    correlation_id="request-trace-id-123",  # Optional: for distributed tracing
    causation_id=None,  # Optional: ID of triggering event
    metadata={"origin": "scheduled_fetch"},  # Optional: additional context
)

# Convert to dict for JSON serialization
event_dict = envelope.to_dict()
```

### 5.2 Using `EventPublisherWrapper`

```python
import aio_pika
from news_intelligence_common import EventPublisherWrapper

async def publish_events():
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")

    async with connection.channel() as channel:
        # Create publisher with validation enabled
        publisher = EventPublisherWrapper(
            channel=channel,
            service_name="my-service",
            exchange_name="news.events",  # Default exchange
            validate=True,  # Enable schema validation before publishing
        )

        # Initialize (declares exchange)
        await publisher.initialize()

        # Publish event
        event_id = await publisher.publish(
            event_type="article.created",
            payload={
                "article_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Example Article",
                "link": "https://example.com",
                "source_id": "550e8400-e29b-41d4-a716-446655440001",
            },
            correlation_id="trace-123",
        )

        print(f"Published event: {event_id}")

    await connection.close()
```

### 5.3 Service-Specific Publisher Pattern

Each service implements its own `EventPublisher` class that wraps `create_event()`:

```python
"""Example: Service-specific event publisher."""

import os
import json
import aio_pika
from news_intelligence_common import create_event

# Set SERVICE_NAME for EventEnvelope
SERVICE_NAME = "my-service"
os.environ.setdefault("SERVICE_NAME", SERVICE_NAME)


class EventPublisher:
    """Service event publisher with circuit breaker protection."""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        """Connect to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(
            "amqp://guest:guest@localhost/",
            client_properties={"service": SERVICE_NAME}
        )
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            "news.events",
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def publish_event(
        self,
        event_type: str,
        payload: dict,
        correlation_id: str = None,
    ) -> bool:
        """Publish event wrapped in EventEnvelope."""
        try:
            # Create standardized envelope
            envelope = create_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
            )

            # Create message
            message = aio_pika.Message(
                body=json.dumps(envelope.to_dict()).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            # Publish with routing key = event_type
            await self.exchange.publish(message, routing_key=event_type)
            return True

        except ValueError as e:
            # Invalid event_type format
            print(f"Invalid event format: {e}")
            return False
```

### 5.4 Consuming and Validating Events

```python
import json
from news_intelligence_common import EventValidator, validate_event


async def handle_message(message: aio_pika.IncomingMessage):
    """Handle incoming RabbitMQ message with validation."""
    async with message.process():
        # Parse event
        event_data = json.loads(message.body)

        # Validate event envelope and payload
        is_valid, errors = validate_event(event_data, strict=False)

        if not is_valid:
            print(f"Invalid event: {errors}")
            # Handle gracefully - log and continue
            return

        # Extract fields
        event_type = event_data["event_type"]
        payload = event_data["payload"]
        correlation_id = event_data["correlation_id"]

        # Process based on event type
        if event_type == "article.created":
            await process_article_created(payload, correlation_id)
        elif event_type == "analysis.v3_completed":
            await process_analysis_completed(payload, correlation_id)
```

---

## 6. Library Reference

### 6.1 Installation

The `news-intelligence-common` library is included as a local dependency:

```bash
# In services/*/requirements.txt
-e ../../libs/news-intelligence-common
```

### 6.2 Imports

```python
from news_intelligence_common import (
    # Event creation
    EventEnvelope,          # Dataclass for event envelope
    create_event,           # Helper to create EventEnvelope
    EventPublisherWrapper,  # aio_pika wrapper with envelope support

    # Validation
    EventValidator,         # Class for validating events
    validate_event,         # Convenience function

    # Schemas
    EVENT_ENVELOPE_SCHEMA,  # JSON Schema for envelope
    EVENT_PAYLOAD_SCHEMAS,  # Dict of event type -> payload schema
)
```

### 6.3 Key Classes and Functions

| Component | Description |
|-----------|-------------|
| `EventEnvelope` | Dataclass representing the standard event envelope. Auto-generates `event_id`, `timestamp`, `correlation_id`. |
| `create_event(event_type, payload, ...)` | Factory function to create `EventEnvelope` instances with proper defaults. |
| `EventPublisherWrapper` | Wrapper for aio_pika that handles envelope creation, JSON serialization, and message properties. |
| `EventValidator` | Validates events against JSON schemas. Supports strict mode (raises) or graceful mode (returns errors). |
| `validate_event(data, strict=False)` | Convenience function for quick validation. Returns `(is_valid, errors)`. |

### 6.4 Source Location

```
libs/news-intelligence-common/
├── src/news_intelligence_common/
│   ├── __init__.py           # Public API exports
│   ├── event_envelope.py     # EventEnvelope dataclass
│   ├── publisher.py          # EventPublisherWrapper, create_event()
│   └── schemas/
│       ├── __init__.py
│       ├── event_schemas.py  # Payload schemas per event type
│       └── validator.py      # EventValidator class
└── tests/
    ├── test_event_envelope.py
    ├── test_publisher.py
    └── test_validator.py
```

---

## 7. Validation

### 7.1 Envelope Validation

All events are validated against the JSON Schema:

```python
EVENT_ENVELOPE_SCHEMA = {
    "type": "object",
    "required": [
        "event_id",
        "event_type",
        "event_version",
        "source_service",
        "timestamp",
        "payload",
    ],
    "properties": {
        "event_id": {"type": "string", "format": "uuid"},
        "event_type": {"type": "string", "pattern": "^[a-z]+\\.[a-z_]+$"},
        "event_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "source_service": {"type": "string"},
        "source_instance": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "correlation_id": {"type": "string"},
        "causation_id": {"type": ["string", "null"]},
        "payload": {"type": "object"},
        "metadata": {"type": "object"},
    },
}
```

### 7.2 Payload Validation

Domain-specific payload schemas are defined in `EVENT_PAYLOAD_SCHEMAS`:

```python
# Example: article.created payload schema
ARTICLE_CREATED_SCHEMA = {
    "type": "object",
    "required": ["article_id", "title", "link", "source_id"],
    "properties": {
        "article_id": {"type": "string", "format": "uuid"},
        "title": {"type": "string", "maxLength": 500},
        "link": {"type": "string", "format": "uri"},
        "source_id": {"type": "string", "format": "uuid"},
        "source_type": {"type": "string", "enum": ["rss", "api", "scraper"]},
        # ... additional fields
    },
}
```

### 7.3 Graceful Degradation

If `jsonschema` library is not installed, validation falls back to basic field checking:

```python
# With jsonschema installed: Full JSON Schema validation
# Without jsonschema: Basic required field check only

is_valid, errors = validate_event(data)
if not is_valid:
    # Log errors but continue processing (graceful degradation)
    logger.warning(f"Event validation warnings: {errors}")
```

---

## Related Documentation

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture overview
- [CLAUDE.backend.md](../../CLAUDE.backend.md) - Backend development guide
- [docs/api/rabbitmq-events-verification.md](rabbitmq-events-verification.md) - Event flow verification

---

**Last Updated:** 2026-01-04 (Epic 0.3 Event Schema Standardization)
