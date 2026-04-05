# RabbitMQ Best Practices

**Last Updated:** 2025-11-01
**Related:** Incident #9 (n8n Message Theft), ADR-033

This guide documents best practices for using RabbitMQ in the News Microservices architecture, based on lessons learned from production incidents.

---

## Table of Contents

1. [Consumer Management](#consumer-management)
2. [Access Control](#access-control)
3. [Event Publishing](#event-publishing)
4. [Queue Configuration](#queue-configuration)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Troubleshooting](#troubleshooting)
7. [Common Pitfalls](#common-pitfalls)

---

## Consumer Management

### Know Your Expected Consumers

**Always document expected consumers for each queue:**

```yaml
# config/rabbitmq-consumers.yml
queues:
  content_analysis_v2_queue:
    expected_consumers: 3
    consumer_services:
      - content-analysis-v2-worker-1
      - content-analysis-v2-worker-2
      - content-analysis-v2-worker-3
    prefetch_count: 20
```

**Why:** Incident #9 showed that an unexpected 4th consumer (n8n) went undetected for 3 hours, stealing 27 messages.

### Set Appropriate Prefetch Count

**DO:**
```python
# Set reasonable prefetch count
channel.basic_qos(prefetch_count=20)
```

**DON'T:**
```python
# Never use unlimited prefetch
channel.basic_qos(prefetch_count=0)  # ❌ Dangerous!
```

**Why:**
- `prefetch_count=0` allows unlimited unacknowledged messages
- Consumer can starve other consumers
- Can cause memory issues
- Hard to balance load across workers

**Recommended Values:**
- CPU-bound tasks: 5-10
- I/O-bound tasks: 20-50
- Mixed workload: 20 (our default)

### Monitor Consumer Count

**Set up monitoring:**
```python
# Prometheus metric
consumer_count = Gauge(
    'rabbitmq_queue_consumers',
    'Number of consumers on queue',
    ['queue']
)

# Check actual vs expected
def validate_consumer_count(queue_name, expected):
    actual = get_queue_consumer_count(queue_name)
    if actual != expected:
        alert(f"Queue {queue_name} has {actual} consumers (expected {expected})")
```

**Alert on changes:**
- Alert immediately if consumer count != expected
- Track consumer additions/removals
- Log consumer tag, IP, and prefetch count

### Use Consumer Tags Meaningfully

**DO:**
```python
consumer_tag = f"{service_name}-{worker_id}-{uuid4()}"
# Example: "content-analysis-v2-worker-1-a1b2c3d4"
```

**DON'T:**
```python
consumer_tag = None  # RabbitMQ generates random tag
# Example: "amq.ctag-XyZ123..." (meaningless)
```

**Why:** Meaningful tags help identify consumers during debugging.

---

## Access Control

### Use Virtual Hosts

**Separate environments:**
```
/                    # Admin only
/news-production     # Production queues
/news-development    # Development/testing
/n8n                 # n8n workflows (isolated)
```

**Benefits:**
- Isolation between environments
- Prevents accidental production access
- Clear separation of concerns

### Configure User Permissions

**Principle of Least Privilege:**
```yaml
# Feed Service - publisher only
- user: feed-service
  vhost: /news-production
  configure: .*
  write: news\.events        # Can publish to exchange
  read: ^$                   # Cannot consume

# Content Analysis - consumer only
- user: content-analysis-v2
  vhost: /news-production
  configure: content_analysis_v2_.*
  write: ^$                  # Cannot publish to exchange
  read: content_analysis_v2_queue  # Can only consume from own queue

# n8n - isolated vhost
- user: n8n
  vhost: /n8n               # Cannot access /news-production
  configure: .*
  write: .*
  read: .*
```

**Key Points:**
- Publishers should NOT be able to consume
- Consumers should NOT be able to publish to main exchange
- Development tools (n8n) should use separate vhosts

### IP Whitelisting (Optional)

For critical queues, whitelist consumer IPs:
```yaml
queues:
  content_analysis_v2_queue:
    allowed_consumer_ips:
      - 172.18.0.4  # worker-1
      - 172.18.0.5  # worker-2
      - 172.18.0.6  # worker-3
```

---

## Event Publishing

### Validate Before Publishing

**DO:**
```python
async def publish_article_created(item: FeedItem):
    # Validate prerequisites
    if not item.content or len(item.content.strip()) < 10:
        logger.warning(f"Skipping article {item.id} - no content")
        return  # Don't publish event

    # Publish only if valid
    await event_publisher.publish_event(
        event_type="article.created",
        payload={...}
    )
```

**DON'T:**
```python
# Publishing without validation
await event_publisher.publish_event(
    event_type="article.created",
    payload={...}
)
# Event will be consumed and rejected by handler ❌
```

**Why:**
- Saves RabbitMQ bandwidth (~10-15% reduction)
- Prevents unnecessary processing
- Cleaner event logs
- Easier debugging

### Use Transactional Outbox Pattern

**Always persist events before publishing:**
```python
async def create_article(item: FeedItem):
    async with transaction():
        # 1. Persist domain changes
        await db.execute(insert_feed_item, item)

        # 2. Persist event in outbox
        await db.execute(
            insert_event_outbox,
            event_type="article.created",
            payload=item.to_dict(),
            status="pending"
        )
        # Commit transaction

    # 3. Separate process publishes from outbox
    # (handled by outbox_processor)
```

**Benefits:**
- No events lost if RabbitMQ is down
- All events auditable in database
- Can replay events if needed
- Transactional guarantee with domain changes

**See:** `services/feed-service/app/tasks/outbox_processor.py`

### Include Correlation IDs

**Always include correlation ID for tracing:**
```python
await publisher.publish_event(
    event_type="article.created",
    payload={...},
    correlation_id=f"feed-fetch-{feed_id}-{timestamp}"
)
```

**Use cases:**
- Trace event flow across services
- Debug event processing
- Link events to source operations

---

## Queue Configuration

### Set Queue Limits

**Prevent unbounded growth:**
```python
queue_arguments = {
    'x-max-length': 10000,              # Max messages
    'x-max-length-bytes': 104857600,    # 100 MB
    'x-overflow': 'reject-publish',     # Reject new messages
}

channel.queue_declare(
    queue='content_analysis_v2_queue',
    durable=True,
    arguments=queue_arguments
)
```

**Alternative overflow behaviors:**
- `drop-head`: Drop oldest messages (default)
- `reject-publish`: Reject new messages (recommended for critical queues)

### Configure Dead Letter Exchange

**Capture failed messages:**
```python
queue_arguments = {
    'x-dead-letter-exchange': 'news.dlx',
    'x-dead-letter-routing-key': 'article.failed',
}
```

**Use cases:**
- Messages rejected by consumers
- Messages that exceed retry limit
- Manual inspection of failures

### Use Durable Queues

**DO:**
```python
channel.queue_declare(
    queue='content_analysis_v2_queue',
    durable=True  # ✅ Survives RabbitMQ restart
)
```

**DON'T:**
```python
channel.queue_declare(
    queue='content_analysis_v2_queue',
    durable=False  # ❌ Lost on restart
)
```

---

## Monitoring & Alerting

### Essential Metrics

**Consumer Metrics:**
```python
# Number of consumers
rabbitmq_queue_consumers{queue="content_analysis_v2_queue"}

# Consumer prefetch count
rabbitmq_consumer_prefetch{queue="...", consumer_tag="..."}

# Consumer IP addresses
rabbitmq_consumer_ip{queue="...", consumer_tag="..."}
```

**Queue Metrics:**
```python
# Messages ready
rabbitmq_queue_messages_ready{queue="..."}

# Messages unacknowledged
rabbitmq_queue_messages_unacked{queue="..."}

# Message age
rabbitmq_message_age_seconds{queue="..."}
```

**Processing Metrics:**
```python
# Processing rate
article_processing_rate_percentage{hour="..."}

# Event publish rate
event_publish_rate{event_type="..."}

# Event consume rate
event_consume_rate{queue="..."}
```

### Critical Alerts

**1. Unexpected Consumer Count**
```yaml
- alert: UnexpectedConsumerCount
  expr: rabbitmq_queue_consumers{queue="content_analysis_v2_queue"} != 3
  for: 1m
  severity: critical
  annotations:
    summary: "Queue has {{ $value }} consumers (expected 3)"
    runbook: "Check docker ps, validate consumer IPs"
```

**2. Low Processing Rate**
```yaml
- alert: LowProcessingRate
  expr: article_processing_rate_percentage < 90
  for: 5m
  severity: warning
  annotations:
    summary: "Processing rate {{ $value }}% (expected >95%)"
    runbook: "Check worker logs, verify RabbitMQ consumers"
```

**3. Messages Stuck in Queue**
```yaml
- alert: MessagesStuckInQueue
  expr: rabbitmq_message_age_seconds{queue="content_analysis_v2_queue"} > 300
  for: 2m
  severity: warning
  annotations:
    summary: "Messages stuck for {{ $value }}s"
    runbook: "Check worker health, verify consumers active"
```

**4. Unlimited Prefetch Consumer**
```yaml
- alert: UnlimitedPrefetchConsumer
  expr: rabbitmq_consumer_prefetch == 0
  for: 30s
  severity: critical
  annotations:
    summary: "Consumer {{ $labels.consumer_tag }} has unlimited prefetch"
    runbook: "Identify and stop unauthorized consumer"
```

### Dashboards

**RabbitMQ Overview Dashboard:**
- Queue depth over time
- Consumer count per queue
- Publish/consume rates
- Message age

**Processing Health Dashboard:**
- Hourly processing rate
- Events published vs processed
- Error rate
- Consumer status

---

## Troubleshooting

### Identifying Unauthorized Consumers

**1. Check RabbitMQ Management UI:**
```
http://localhost:15672
→ Queues → content_analysis_v2_queue → Consumers
```

**2. Use RabbitMQ API:**
```bash
curl -u guest:guest http://localhost:15672/api/queues/%2F/content_analysis_v2_queue | jq '.consumer_details'
```

**3. Identify container by IP:**
```bash
# Get consumer IP from RabbitMQ
consumer_ip="172.18.0.30"

# Find container
docker ps --format "{{.Names}} {{.Networks}}" | while read name network; do
    container_ip=$(docker inspect $name | jq -r '.[0].NetworkSettings.Networks["'$network'"].IPAddress')
    if [ "$container_ip" = "$consumer_ip" ]; then
        echo "Found: $name ($container_ip)"
    fi
done
```

**4. Close unauthorized connection:**
```bash
# Get connection name from RabbitMQ
connection_name="172.18.0.30:12345 -> 172.18.0.2:5672"

# Close connection
curl -u guest:guest -X DELETE \
  "http://localhost:15672/api/connections/${connection_name}"
```

### Debugging Processing Rate Issues

**1. Check consumer count:**
```bash
curl -s http://localhost:15672/api/queues/%2F/content_analysis_v2_queue | \
  jq '.consumers'
```

**2. Check worker logs:**
```bash
docker logs content-analysis-v2-worker-1 --tail 100 | \
  grep -E "Processing article|Successfully processed|ERROR"
```

**3. Check event outbox:**
```sql
SELECT COUNT(*), status
FROM event_outbox
WHERE event_type = 'article.created'
GROUP BY status;
```

**4. Check processing rate:**
```sql
SELECT
    DATE_TRUNC('hour', eo.created_at) as hour,
    COUNT(eo.id) as total_events,
    COUNT(pe.id) as processed_events,
    ROUND(100.0 * COUNT(pe.id) / NULLIF(COUNT(eo.id), 0), 2) as processing_rate
FROM event_outbox eo
LEFT JOIN content_analysis_v2.pipeline_executions pe ON
    (eo.payload->>'item_id')::uuid = pe.article_id
WHERE eo.created_at >= NOW() - INTERVAL '24 hours'
  AND eo.event_type = 'article.created'
GROUP BY DATE_TRUNC('hour', eo.created_at)
ORDER BY hour DESC;
```

### Recovering Lost Events

**1. Identify unprocessed articles:**
```sql
SELECT fi.id, fi.title
FROM public.feed_items fi
WHERE fi.id NOT IN (
    SELECT article_id
    FROM content_analysis_v2.pipeline_executions
    WHERE success = true
)
AND fi.created_at > NOW() - INTERVAL '24 hours'
AND fi.content IS NOT NULL
AND LENGTH(fi.content) >= 10;
```

**2. Re-publish events:**
```sql
INSERT INTO public.event_outbox (event_type, payload, status, retry_count, created_at)
SELECT
    'article.created' as event_type,
    jsonb_build_object(
        'item_id', fi.id::text,
        'feed_id', fi.feed_id::text,
        'title', fi.title,
        'link', fi.link,
        'description', fi.description,
        'has_content', true,
        'analysis_config', jsonb_build_object(
            'enable_summary', true,
            'enable_categorization', true,
            'enable_entity_extraction', true
        )
    ) as payload,
    'pending' as status,
    0 as retry_count,
    NOW() as created_at
FROM public.feed_items fi
WHERE [same WHERE clause as above];
```

**3. Verify republishing:**
```bash
# Watch outbox processor
docker logs feed-service-celery-worker --follow | grep "Processing.*pending events"

# Verify workers processing
docker logs content-analysis-v2-worker-1 --follow | grep "Processing article"
```

---

## Common Pitfalls

### ❌ DON'T: Use Auto-Delete Queues in Production

```python
# Bad
channel.queue_declare(queue='my_queue', auto_delete=True)
```

**Why:** Queue deleted when last consumer disconnects. Service restart = queue loss.

---

### ❌ DON'T: Forget to ACK Messages

```python
# Bad
def callback(ch, method, properties, body):
    process(body)
    # Missing: ch.basic_ack(method.delivery_tag)
```

**Why:** Messages stay in "unacked" state forever, eventually causing memory issues.

---

### ❌ DON'T: ACK Before Processing

```python
# Bad
def callback(ch, method, properties, body):
    ch.basic_ack(method.delivery_tag)  # Too early!
    process(body)  # Might fail, but message already ACKed
```

**Why:** If processing fails, message is lost.

**Correct:**
```python
def callback(ch, method, properties, body):
    try:
        process(body)
        ch.basic_ack(method.delivery_tag)  # ✅ After successful processing
    except Exception as e:
        ch.basic_nack(method.delivery_tag, requeue=True)  # Requeue on failure
```

---

### ❌ DON'T: Connect Every Tool to Production Queues

```python
# Bad - n8n workflow consuming from production queue
n8n_trigger:
  type: rabbitmq
  queue: content_analysis_v2_queue  # ❌ Production queue!
```

**Why:** Testing/development tools can steal production messages (Incident #9).

**Correct:** Use separate virtual host for development tools:
```python
# Good - n8n uses isolated environment
n8n_trigger:
  type: rabbitmq
  vhost: /n8n                        # ✅ Isolated
  queue: n8n_test_queue
```

---

### ❌ DON'T: Ignore Processing Rate Drops

**Bad:** Processing rate drops from 100% to 75%, no investigation.

**Why:** Indicates messages being lost or not processed. May be unauthorized consumer, worker crash, or misconfiguration.

**Correct:** Alert on processing rate < 90%, investigate immediately.

---

### ❌ DON'T: Use Synchronous Publishing in Request Handler

```python
# Bad - blocks request thread
@app.post("/articles")
def create_article(article: Article):
    db.create(article)
    rabbitmq.publish("article.created", article)  # ❌ Blocks!
    return {"id": article.id}
```

**Why:** If RabbitMQ is slow/down, API requests timeout.

**Correct:** Use transactional outbox pattern:
```python
@app.post("/articles")
async def create_article(article: Article):
    async with transaction():
        await db.create(article)
        await outbox.create_event("article.created", article)
    return {"id": article.id}
    # Outbox processor publishes asynchronously
```

---

## References

- **Official RabbitMQ Docs:** https://www.rabbitmq.com/documentation.html
- **Transactional Outbox Pattern:** `services/feed-service/app/tasks/outbox_processor.py`
- **Consumer Implementation:** `services/content-analysis-v2/app/messaging/pipeline_handler.py`
- **Incident #9:** POSTMORTEMS.md
- **ADR-033:** RabbitMQ Consumer Monitoring
- **ADR-012:** Event-Driven Architecture

---

## Checklist for New Queues

Before deploying a new queue to production:

- [ ] Queue is durable (`durable=True`)
- [ ] Queue has length limits configured
- [ ] Dead letter exchange configured
- [ ] Expected consumer count documented
- [ ] Consumer permissions configured (user can only read this queue)
- [ ] Monitoring configured (consumer count, processing rate)
- [ ] Alerts configured (unexpected consumers, low processing rate)
- [ ] Prefetch count set appropriately (not 0!)
- [ ] Consumers use meaningful tags
- [ ] Integration tests verify consumer behavior
- [ ] Documentation updated (this guide, ARCHITECTURE.md)

---

**Last Updated:** 2025-11-01
**Maintainer:** Engineering Team
**Review Frequency:** After each RabbitMQ-related incident
