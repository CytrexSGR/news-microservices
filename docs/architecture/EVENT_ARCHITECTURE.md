# Event-Driven Architecture - News Microservices

## Overview

The News Microservices platform uses **RabbitMQ** as an event bus to enable asynchronous, decoupled communication between services. This document describes the complete event architecture, schemas, and integration patterns.

## Table of Contents

1. [Architecture](#architecture)
2. [Event Catalog](#event-catalog)
3. [RabbitMQ Topology](#rabbitmq-topology)
4. [Integration Guide](#integration-guide)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Architecture

### Overview Diagram

```
┌─────────────────┐      article.created      ┌──────────────────────┐
│  Feed Service   │─────────────────────────> │ Content Analysis     │
└─────────────────┘                            │     Service          │
                                               └──────────────────────┘
                                                         │
                                                         │ analysis.completed
                                                         ▼
                                               ┌──────────────────────┐
                    research.completed         │   Research Service   │
                   ┌──────────────────────────>│                      │
                   │                            └──────────────────────┘
                   │                                      │
                   │                                      │ research.completed
                   │                                      ▼
┌──────────────────┴─┐                          ┌──────────────────────┐
│   OSINT Service    │<─────────────────────────│   Analysis Data      │
└────────────────────┘  analysis.completed      └──────────────────────┘
         │
         │ alert.triggered
         ▼
┌────────────────────┐      notification.sent   ┌──────────────────────┐
│ Notification       │─────────────────────────>│  Analytics Service   │
│    Service         │                           │  (Consumes All)      │
└────────────────────┘                           └──────────────────────┘
                                                           ▲
                                                           │
                                        All Events (#)─────┘
```

### Key Principles

1. **Loose Coupling**: Services communicate via events, not direct API calls
2. **Asynchronous Processing**: Events are processed independently
3. **Scalability**: Multiple consumers can process events in parallel
4. **Reliability**: Persistent messages with dead-letter queue handling
5. **Traceability**: Correlation IDs for request tracing

---

## Event Catalog

### Event Types

| Event Type | Source Service | Consumer Services | Description |
|------------|---------------|-------------------|-------------|
| `article.created` | feed-service | content-analysis, search | New article fetched |
| `article.updated` | feed-service | search | Existing article updated |
| `analysis.completed` | content-analysis | research, osint, analytics | Content analysis finished |
| `research.completed` | research-service | osint, analytics | Research task completed |
| `alert.triggered` | osint-service | notification, analytics | Alert condition detected |
| `notification.sent` | notification-service | analytics | Notification delivered |
| `user.registered` | auth-service | analytics | New user registered |
| `search.executed` | search-service | analytics | Search query executed |

### Event Schemas

#### 1. article.created

**Source**: Feed Service
**Routing Key**: `article.created`
**Consumers**: Content Analysis, Search

```json
{
  "event_type": "article.created",
  "event_id": "uuid",
  "timestamp": "2025-10-12T10:00:00Z",
  "source_service": "feed-service",
  "correlation_id": "uuid (optional)",
  "data": {
    "article_id": "uuid",
    "feed_id": "uuid",
    "title": "Breaking News Title",
    "url": "https://example.com/article",
    "content": "Full article content...",
    "author": "John Doe (optional)",
    "published_at": "2025-10-12T09:00:00Z",
    "metadata": {
      "tags": ["technology", "ai"],
      "source": "TechCrunch"
    }
  }
}
```

#### 2. analysis.completed

**Source**: Content Analysis Service
**Routing Key**: `analysis.completed`
**Consumers**: Research, OSINT, Analytics

```json
{
  "event_type": "analysis.completed",
  "event_id": "uuid",
  "timestamp": "2025-10-12T10:05:00Z",
  "source_service": "content-analysis-service",
  "correlation_id": "uuid",
  "data": {
    "article_id": "uuid",
    "analysis_id": "uuid",
    "sentiment": {
      "score": 0.85,
      "label": "positive",
      "confidence": 0.92
    },
    "entities": [
      {"text": "OpenAI", "type": "ORG", "confidence": 0.95},
      {"text": "ChatGPT", "type": "PRODUCT", "confidence": 0.88}
    ],
    "topics": ["AI", "Technology", "Machine Learning"],
    "keywords": ["artificial intelligence", "language model", "gpt-4"],
    "summary": "Article discusses recent advances in AI...",
    "language": "en",
    "processing_time_ms": 1234
  }
}
```

#### 3. alert.triggered

**Source**: OSINT Service
**Routing Key**: `alert.triggered`
**Consumers**: Notification, Analytics

```json
{
  "event_type": "alert.triggered",
  "event_id": "uuid",
  "timestamp": "2025-10-12T10:10:00Z",
  "source_service": "osint-service",
  "correlation_id": "uuid",
  "data": {
    "alert_id": "uuid",
    "alert_type": "anomaly",
    "severity": "high",
    "title": "Unusual Activity Detected",
    "description": "Spike in negative sentiment detected across multiple sources",
    "indicators": [
      "sentiment_score < -0.5",
      "mention_count > 100",
      "growth_rate > 500%"
    ],
    "confidence_score": 0.87,
    "recommended_actions": [
      "investigate_sources",
      "verify_facts",
      "notify_stakeholders"
    ]
  }
}
```

*(See `/infrastructure/events/schemas.json` for complete schema definitions)*

---

## RabbitMQ Topology

### Exchange

**Name**: `news.events`
**Type**: Topic
**Durable**: Yes
**Auto-delete**: No

### Queues and Bindings

| Queue | Routing Keys | Service | TTL | Max Length | DLX |
|-------|-------------|---------|-----|------------|-----|
| `content-analysis.articles` | `article.created` | Content Analysis | 24h | 10,000 | Yes |
| `search.articles` | `article.created`, `article.updated` | Search | 24h | 10,000 | Yes |
| `research.analysis` | `analysis.completed` | Research | 24h | 10,000 | Yes |
| `osint.intelligence` | `analysis.completed`, `research.completed` | OSINT | 24h | 10,000 | Yes |
| `notification.alerts` | `alert.triggered` | Notification | 24h | 10,000 | Yes |
| `analytics.all` | `#` (all events) | Analytics | 24h | 50,000 | Yes |

### Dead-Letter Queue

**Exchange**: `news.events.dlx`
**Queue**: `news.events.dlq`
**Retention**: 7 days
**Purpose**: Store failed messages for manual inspection

### Policies

**High Availability**: All queues replicated across all RabbitMQ nodes

---

## Integration Guide

### For Service Developers

#### 1. Publishing Events (Producer)

```python
import os
from shared.event_integration import FeedServiceEvents

# Initialize publisher
publisher = FeedServiceEvents.get_publisher(os.getenv("RABBITMQ_URL"))
await publisher.initialize()

# Publish event
await FeedServiceEvents.publish_article_created(
    publisher=publisher,
    article_id="550e8400-e29b-41d4-a716-446655440000",
    feed_id="660e8400-e29b-41d4-a716-446655440001",
    title="Breaking News",
    url="https://example.com/news",
    content="Full article content...",
    author="John Doe",
    published_at="2025-10-12T10:00:00Z",
    correlation_id="req-12345"  # Optional
)

# Cleanup
await publisher.close()
```

#### 2. Consuming Events (Consumer)

```python
import os
from shared.event_integration import ContentAnalysisServiceEvents, EventTypes

# Define event handler
async def handle_article_created(event):
    article_id = event["data"]["article_id"]
    title = event["data"]["title"]

    print(f"Processing article: {title}")
    # Your processing logic here...

# Create consumer
consumer = await ContentAnalysisServiceEvents.create_consumer(
    rabbitmq_url=os.getenv("RABBITMQ_URL"),
    handlers={
        EventTypes.ARTICLE_CREATED: handle_article_created,
    }
)

# Start consuming (blocking)
await consumer.run_forever()
```

#### 3. Service Startup Integration

```python
# app/main.py (FastAPI example)
from fastapi import FastAPI
from shared.event_integration import ContentAnalysisServiceEvents, EventTypes
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize event consumer
    consumer = await ContentAnalysisServiceEvents.create_consumer(
        handlers={
            EventTypes.ARTICLE_CREATED: process_article,
        }
    )

    # Start consuming in background
    asyncio.create_task(consumer.run_forever())

async def process_article(event):
    # Your logic here
    pass
```

### Docker Integration

The RabbitMQ topology is automatically initialized when running `docker-compose up`:

```bash
# Start all services (includes RabbitMQ init)
docker-compose up -d

# Check RabbitMQ init logs
docker logs news-rabbitmq-init

# Access RabbitMQ Management UI
# http://localhost:15672
# Username: admin
# Password: rabbit_secret_2024
```

---

## Testing

### Unit Tests

Test individual publishers and consumers:

```bash
# Run event integration tests
cd /home/cytrex/news-microservices
pytest tests/integration/test_events.py -v
```

### End-to-End Test

Test complete event flow:

```bash
# 1. Start infrastructure
docker-compose up -d postgres redis rabbitmq

# 2. Wait for RabbitMQ init
docker logs -f news-rabbitmq-init

# 3. Run end-to-end test
pytest tests/integration/test_events.py::TestEndToEndFlow::test_article_to_notification_flow -v -s
```

### Manual Testing

Use RabbitMQ Management UI:

1. Navigate to http://localhost:15672
2. Go to **Exchanges** > `news.events`
3. Publish test message:
   - Routing key: `article.created`
   - Payload: (see event schemas above)
4. Go to **Queues** > `content-analysis.articles`
5. Click **Get messages** to verify delivery

---

## Troubleshooting

### Issue: Events not being consumed

**Symptoms**: Messages stuck in queue, consumers not processing

**Diagnosis**:
```bash
# Check consumer is running
docker ps | grep content-analysis

# Check consumer logs
docker logs news-content-analysis-service

# Check queue bindings
curl -u admin:rabbit_secret_2024 http://localhost:15672/api/queues/news_mcp/content-analysis.articles
```

**Solutions**:
1. Verify consumer service is running
2. Check consumer registered correct event handlers
3. Verify queue bindings in RabbitMQ UI
4. Check for consumer errors in logs

### Issue: Messages going to Dead-Letter Queue

**Symptoms**: Messages accumulate in `news.events.dlq`

**Diagnosis**:
```bash
# Inspect DLQ messages
curl -u admin:rabbit_secret_2024 http://localhost:15672/api/queues/news_mcp/news.events.dlq/get -d '{"count":10,"ackmode":"ack_requeue_false","encoding":"auto"}'
```

**Common Causes**:
1. Consumer handler throwing exceptions
2. Invalid message format
3. Consumer not acknowledging messages
4. Message TTL expired

**Solutions**:
1. Fix consumer handler errors
2. Validate message schema before publishing
3. Ensure proper message acknowledgment
4. Increase queue TTL if needed

### Issue: RabbitMQ connection errors

**Symptoms**: Services failing to connect to RabbitMQ

**Diagnosis**:
```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# Check RabbitMQ logs
docker logs news-rabbitmq

# Test connection
docker exec news-rabbitmq rabbitmq-diagnostics ping
```

**Solutions**:
1. Verify RabbitMQ container is healthy
2. Check RABBITMQ_URL environment variable
3. Verify vhost exists: `news_mcp`
4. Check firewall rules (ports 5672, 15672)

### Issue: Slow event processing

**Symptoms**: High message latency, queue backlog

**Diagnosis**:
```bash
# Check queue metrics
curl -u admin:rabbit_secret_2024 http://localhost:15672/api/queues/news_mcp

# Monitor consumer rate
watch -n 1 'curl -s -u admin:rabbit_secret_2024 http://localhost:15672/api/queues/news_mcp/content-analysis.articles | jq ".message_stats.deliver_get_details.rate"'
```

**Solutions**:
1. Scale consumer service (increase replicas)
2. Increase prefetch count for consumers
3. Optimize handler processing logic
4. Add consumer parallelization

---

## Performance Metrics

### Target Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Event publish latency | < 10ms | > 50ms |
| Consumer processing latency | < 500ms | > 5s |
| Queue depth | < 100 | > 1000 |
| Dead-letter queue depth | 0 | > 10 |
| Consumer throughput | > 100 msg/s | < 10 msg/s |

### Monitoring

Prometheus metrics are exposed via RabbitMQ Prometheus plugin:

- `rabbitmq_queue_messages_ready`
- `rabbitmq_queue_messages_unacknowledged`
- `rabbitmq_queue_consumers`
- `rabbitmq_channel_messages_published_total`
- `rabbitmq_channel_messages_delivered_total`

Grafana dashboards available at http://localhost:3001 (see RabbitMQ dashboard)

---

## Best Practices

1. **Always use correlation IDs** for request tracing
2. **Validate events** before publishing (use schemas)
3. **Handle errors gracefully** in consumers (don't crash)
4. **Monitor queue depths** regularly
5. **Test end-to-end flows** in staging environment
6. **Use dead-letter queue** for failed message inspection
7. **Implement idempotency** in consumers (handle duplicates)
8. **Log all event processing** with structured logging
9. **Set appropriate TTLs** based on business requirements
10. **Scale consumers** based on queue backlog

---

## Additional Resources

- RabbitMQ Documentation: https://www.rabbitmq.com/documentation.html
- Event Schemas: `/infrastructure/events/schemas.json`
- Publisher Library: `/shared/event_publisher.py`
- Consumer Library: `/shared/event_consumer.py`
- Integration Helpers: `/shared/event_integration.py`
- Integration Tests: `/tests/integration/test_events.py`

---

**Last Updated**: 2025-10-12
**Maintained By**: Platform Team
