# Event-Driven Architecture

_Last updated: 2025-10-18_

RabbitMQ powers asynchronous workflows across the News MCP platform. All domain services attach to a shared topic exchange (`news.events`) and publish well-structured JSON messages. Durable queues, DLQs, and consumer back-pressure keep the event mesh reliable both in Docker Compose and Kubernetes deployments.

---

## 1. Topology Overview

```
Producers                                                Consumers
─────────                                                ─────────
Feed Service ── article.created ─┐                       Content Analysis
Scraping Service ── item.scraped ┼──►  news.events  ──►  Search
Content Analysis ── analysis.completed ─┘                Notification
Research Service ── research.completed ──────────────►   Analytics (HTTP ingest)
Scheduler Service ── analysis.job.created ───────────►   Celery / workers
Notification Service ── delivery.failed ─────────────►   Dead Letter / Ops
```

- **Exchange**: `news.events` (topic) – declared by Feed Service (`EventPublisher`) and reused by every producer.
- **Dead Letter Exchange**: `news.events.dlq` – created by content-analysis consumer; other services bind DLQs as needed.
- **Message Format**:

```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2025-10-18T09:12:31.412Z",
  "correlation_id": "uuid-optional",
  "payload": { ... domain object ... }
}
```

All producers use `JSONEncoder` implementations to serialize UUID, datetime, and Decimal values (see `services/feed-service/app/services/event_publisher.py` and `shared/news-mcp-common/news_mcp_common/events.py`).

---

## 2. Producers

| Service | File | Events Published | Notes |
| --- | --- | --- | --- |
| **Feed Service** | `app/services/feed_fetcher.py`, `app/api/feeds.py` | `article.created`, `article.updated`, `feed.fetch_completed`, `feed.fetch_failed` | Triggered after RSS fetch, CRUD actions, Celery tasks |
| **Scraping Service** | `app/workers/scraping_worker.py` | `item.scraped`, `scrape.failed` | Emits once full content has been fetched |
| **Content Analysis** | `app/services/event_service.py`, `app/services/message_handler.py` | `analysis.started`, `analysis.completed`, `analysis.failed`, `analysis.anomaly_detected` | Publishes results after LLM workflow; also forwards generated insights |
| **Research Service** | `app/services/perplexity.py` + workflow | `research.started`, `research.completed`, `research.failed` | Integration available for downstream notifications |
| **Scheduler Service** | `app/services/job_processor.py` | `analysis.job.created`, `analysis.job.completed` | Keeps analytics up to date |
| **Notification Service** | `app/events/rabbitmq_consumer.py` (optional) | `notification.delivered`, `notification.failed` | Delivered through the same exchange for auditing/analytics |

`EventPublisher` ensures connections are resilient (robust connection, QoS, persistent delivery). Producers automatically reconnect if RabbitMQ restarts.

---

## 3. Consumers & Queues

| Service | Queue | Routing Keys | Handler |
| --- | --- | --- | --- |
| **Content Analysis** | `content-analysis.article_created` | `article.created` | `app/workers/article_consumer.py` – creates analysis jobs in scheduler DB |
|  | `content-analysis.item_scraped` | `item.scraped`, `feed_fetch_completed` | `app/services/rabbitmq_consumer.py` – kicks off in-service pipelines |
|  | `content-analysis.item_scraped_jobs` | `item.scraped` | `app/workers/item_scraped_consumer.py` – generates OSINT jobs |
| **Search** | `search_indexing_events` | `article_created`, `article_updated`, `analysis_completed`, `feed_fetch_completed` | `app/events/consumer.py` – fetches article content and updates PostgreSQL index |
| **Notification** | `notification_events` | `osint.alert.triggered`, `research.completed`, `analysis.completed`, `feed.new_article` | `app/events/rabbitmq_consumer.py` – renders templates, queues Celery tasks for email/webhook |
| **Scheduler** | Internal | `analysis.job.*` | Feeds job monitor / processor (`app/services/feed_monitor.py`) |
| **Analytics** | HTTP ingest | All events (via service integrations) | `app/services/metrics_service.py` persists derived metrics |

Consumers consistently:
- Use `aio_pika.connect_robust`.
- Declare queues as durable with TTL and dead-letter bindings.
- Apply `prefetch_count` (typically 10) to limit concurrency.
- Log structured telemetry for Prometheus and Loki.

---

## 4. Reliability Features

- **Dead Letter Queues**:
  - Content Analysis: `<queue>.dlq` bound to `news.events.dlq` with 24h TTL (see `app/services/rabbitmq_consumer.py`).
  - Other services rely on built-in retries (Celery) or can opt into the same pattern via `news_mcp_common.events`.
- **Back-pressure**: Each consumer sets `set_qos(prefetch_count=N)` before subscribing.
- **Graceful Shutdown**: Consumers intercept `SIGINT`/`SIGTERM`, stop accepting new messages, finish in-flight work, and close channels (e.g., `RabbitMQConsumer.stop()`).
- **Resiliency**: Circuit breaker in Feed Service prevents event storms if external feeds misbehave; scheduler batches ensure rate limiting.

---

## 5. Configuration & Operations

Environment variables (per service `.env`):

```
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_PREFETCH_COUNT=10
RABBITMQ_QUEUE_NAME=content-analysis.item_scraped   # example
RABBITMQ_CONSUMER_ENABLED=true
```

- **Local**: Compose exposes management UI on `http://localhost:15672` (guest/guest).
- **Kubernetes**: Exchange/queue declarations happen at runtime; no manual manifests required. HorizontalPodAutoscalers scale consumers using `rabbitmq_queue_messages_ready` metrics (example manifests in `docs/event-architecture.md` and `k8s/` overlays).
- **Monitoring**: Content Analysis exports counters like `rabbitmq_messages_received_total`; Search/Notification log structured processing stats. Extend with RabbitMQ Prometheus exporter if deeper broker metrics are needed.
- **Replay / Testing**: Use `shared/event_publisher.py` CLI helpers or `scripts/requeue_old_articles.py` to republish events for regression testing.

---

## 6. Next Steps

1. **Schema Registry** – formalize JSON schema definitions for `event_type` payloads and validate before publishing/processing.
2. **DLQ Dashboarding** – surface DLQ counts in Grafana and wire to alerting.
3. **At-Least-Once Guarantees** – add idempotency keys to downstream services (especially Notification and Analytics) to guard against replays.
4. **Observability** – propagate correlation IDs from gateway to events (Auth → Feed → Content Analysis → Notification) for end-to-end tracing.

The event system is production-ready and underpins cross-service workflows today. Enhancements above will streamline future scaling and observability.

