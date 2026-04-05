# RabbitMQ Events - Verification Workflow

**Service:** content-analysis-v2
**Exchange:** news.events
**Version:** 1.0
**Last Updated:** 2025-11-02

---

## Overview

This document describes the RabbitMQ events published by the content-analysis-v2 service as part of the **Uncertainty Quantification (UQ) Module** verification workflow.

---

## Event: `verification.required`

### Description

Published when the UQ module detects low confidence or quality issues in article analysis that require verification.

### When Published

This event is triggered when **ANY** of the following conditions are met:

1. **Low Overall Quality**: Overall quality score < 50
2. **Low Verification Score**: Verification score < 40
3. **High Financial Uncertainty**: Uncertainty metric > 0.75
4. **Low Credibility**: Credibility score < 40

### Routing

| Property | Value |
|----------|-------|
| **Exchange** | `news.events` |
| **Type** | Topic |
| **Routing Key** | `verification.required` |
| **Durable** | Yes |
| **Persistent** | Yes (survives broker restarts) |

### Message Properties

| Property | Value | Description |
|----------|-------|-------------|
| `content_type` | `application/json` | JSON-encoded message body |
| `delivery_mode` | `2` | Persistent delivery |
| `app_id` | `content-analysis-v2` | Publishing service |
| `type` | `verification.required` | Message type |
| `timestamp` | UTC timestamp | When event was published |
| `correlation_id` | Pipeline execution UUID | For request tracing |

---

## Message Schema

### Message Envelope

```json
{
  "event_type": "verification.required",
  "service": "content-analysis-v2",
  "timestamp": "2025-11-02T10:30:00.123456Z",
  "correlation_id": "660e8400-e29b-41d4-a716-446655440001",
  "payload": {
    // See Payload Schema below
  }
}
```

### Envelope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | Yes | Always `"verification.required"` |
| `service` | string | Yes | Always `"content-analysis-v2"` |
| `timestamp` | string (ISO8601) | Yes | UTC timestamp when event was published |
| `correlation_id` | string (UUID) | No | Pipeline execution ID for tracing |
| `payload` | object | Yes | Event-specific data (see below) |

### Payload Schema

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "pipeline_execution_id": "660e8400-e29b-41d4-a716-446655440001",
  "uq_score": 35.0,
  "trigger_reason": "financial_uncertainty_high",
  "uncertainty_factors": [
    "uncertainty: 0.85 (high market uncertainty)",
    "volatility: 0.90 (extreme market volatility expected)",
    "economic_impact: 0.95 (major systemic impact)",
    "Overall quality score: 35.0 (very low)",
    "Verification score: 25.0 (unverified content)"
  ],
  "affected_agents": [
    "FINANCIAL_ANALYST",
    "CONFLICT_EVENT_ANALYST"
  ],
  "quality_scores": {
    "overall": 35.0,
    "credibility": 42.0,
    "objectivity": 55.0,
    "verification": 25.0,
    "relevance": 68.0,
    "completeness": 48.0,
    "consistency": 32.0
  }
}
```

### Payload Fields

| Field | Type | Required | Nullable | Description |
|-------|------|----------|----------|-------------|
| `article_id` | string (UUID) | Yes | No | Unique identifier of analyzed article |
| `pipeline_execution_id` | string (UUID) | Yes | No | Unique identifier of pipeline execution |
| `uq_score` | number (float) | Yes | No | Overall quality score (0-100) |
| `trigger_reason` | string (enum) | Yes | No | Primary reason verification was triggered |
| `uncertainty_factors` | array[string] | Yes | No | Human-readable list of uncertainty factors |
| `affected_agents` | array[string] | Yes | No | Agents that reported low confidence |
| `quality_scores` | object | Yes | No | Detailed breakdown of quality scores |
| `quality_scores.overall` | number (float) | Yes | No | Overall quality (0-100) |
| `quality_scores.credibility` | number (float) | Yes | No | Credibility score (0-100) |
| `quality_scores.objectivity` | number (float) | Yes | No | Objectivity score (0-100) |
| `quality_scores.verification` | number (float) | Yes | No | Verification score (0-100) |
| `quality_scores.relevance` | number (float) | Yes | No | Relevance score (0-100) |
| `quality_scores.completeness` | number (float) | Yes | No | Completeness score (0-100) |
| `quality_scores.consistency` | number (float) | Yes | No | Consistency score (0-100) |

---

## Trigger Reasons

### Enum Values

| Trigger Reason | Condition | Description |
|---------------|-----------|-------------|
| `low_overall_quality` | `overall_score < 50` | General low quality across multiple dimensions |
| `low_verification_score` | `verification_score < 40` | Unverified or disputed content |
| `financial_uncertainty_high` | `uncertainty > 0.75` | High uncertainty in financial/economic analysis |
| `low_credibility` | `credibility_score < 40` | Unreliable source or extreme bias |
| `multiple_triggers` | Multiple conditions met | Combined quality issues |

### Trigger Reason Details

#### `low_overall_quality`

**Condition:** `overall_score < 50`

**Typical Uncertainty Factors:**
- "Overall quality score: 35.0 (very low)"
- Multiple low scores across dimensions
- Data completeness < 60%

**Example:**
```json
{
  "trigger_reason": "low_overall_quality",
  "uq_score": 42.0,
  "uncertainty_factors": [
    "Overall quality score: 42.0 (low)",
    "Credibility: 38.0 (unreliable source)",
    "Verification: 35.0 (unverified)",
    "Completeness: 45.0 (missing key information)"
  ]
}
```

---

#### `low_verification_score`

**Condition:** `verification_score < 40`

**Typical Uncertainty Factors:**
- "Verification score: 25.0 (unverified content)"
- "No photo/video evidence"
- "Single-source article (no corroboration)"
- "Disputed claims"

**Example:**
```json
{
  "trigger_reason": "low_verification_score",
  "uq_score": 65.0,
  "quality_scores": {
    "overall": 65.0,
    "verification": 25.0
  },
  "uncertainty_factors": [
    "Verification score: 25.0 (unverified)",
    "No visual evidence provided",
    "Single-source article",
    "0 witness testimonies"
  ]
}
```

---

#### `financial_uncertainty_high`

**Condition:** `uncertainty > 0.75`

**Typical Uncertainty Factors:**
- "uncertainty: 0.85 (high market uncertainty)"
- "volatility: 0.90 (extreme market volatility)"
- "Conflicting economic indicators"
- "Ambiguous policy statements"

**Example:**
```json
{
  "trigger_reason": "financial_uncertainty_high",
  "uq_score": 58.0,
  "uncertainty_factors": [
    "uncertainty: 0.85 (high market uncertainty)",
    "volatility: 0.90 (extreme market volatility expected)",
    "economic_impact: 0.95 (major systemic impact)",
    "Conflicting statements from officials",
    "Unclear regulatory timeline"
  ],
  "affected_agents": ["FINANCIAL_ANALYST"]
}
```

---

#### `low_credibility`

**Condition:** `credibility_score < 40`

**Typical Uncertainty Factors:**
- "Credibility: 35.0 (unreliable source)"
- "Extreme bias detected"
- "Low fact/opinion ratio (25%)"
- "Source transparency: 0.20"

**Example:**
```json
{
  "trigger_reason": "low_credibility",
  "uq_score": 48.0,
  "quality_scores": {
    "overall": 48.0,
    "credibility": 35.0
  },
  "uncertainty_factors": [
    "Credibility: 35.0 (unreliable source)",
    "Bias level: extreme",
    "Source transparency: 0.20 (very low)",
    "Fact percentage: 25% (opinion-heavy)"
  ],
  "affected_agents": ["BIAS_DETECTOR"]
}
```

---

#### `multiple_triggers`

**Condition:** Multiple threshold breaches

**Typical Uncertainty Factors:**
- Combines factors from all triggered conditions

**Example:**
```json
{
  "trigger_reason": "multiple_triggers",
  "uq_score": 32.0,
  "quality_scores": {
    "overall": 32.0,
    "credibility": 35.0,
    "verification": 28.0
  },
  "uncertainty_factors": [
    "Overall quality score: 32.0 (very low)",
    "Credibility: 35.0 (unreliable source)",
    "Verification: 28.0 (unverified)",
    "uncertainty: 0.80 (high market uncertainty)",
    "Bias level: extreme",
    "No evidence provided"
  ],
  "affected_agents": [
    "BIAS_DETECTOR",
    "FINANCIAL_ANALYST",
    "CONFLICT_EVENT_ANALYST"
  ]
}
```

---

## Consumer Implementation Guide

### Queue Setup

```python
import aio_pika
import json
import logging

logger = logging.getLogger(__name__)

async def setup_verification_queue():
    """
    Set up RabbitMQ queue for verification events.

    Creates:
    - Durable queue: verification.queue
    - Binding to news.events exchange
    - Routing key: verification.required
    """
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@rabbitmq:5672/"
    )

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    # Declare exchange (idempotent - safe to call multiple times)
    exchange = await channel.declare_exchange(
        "news.events",
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    # Declare queue
    queue = await channel.declare_queue(
        "verification.queue",
        durable=True,
        arguments={
            "x-max-length": 10000,  # Limit queue size
            "x-message-ttl": 86400000,  # 24 hours TTL
            "x-dead-letter-exchange": "dlx.verification",  # DLX for failed messages
        }
    )

    # Bind to verification.required events
    await queue.bind(exchange, routing_key="verification.required")

    logger.info("Verification queue setup complete")

    return channel, queue
```

### Consumer Class

```python
class VerificationConsumer:
    """
    Consumer for verification.required events.

    Processes verification requests from content-analysis-v2 service.
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

    async def start(self):
        """Start consuming verification events."""
        self.channel, self.queue = await setup_verification_queue()

        logger.info("Verification consumer started, waiting for events...")

        # Consume messages
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        await self.process_verification(message.body)
                    except Exception as e:
                        logger.error(f"Failed to process verification: {e}")
                        raise  # Requeue message

    async def process_verification(self, body: bytes):
        """
        Process verification event.

        Args:
            body: Message body (JSON bytes)
        """
        # Parse message
        data = json.loads(body)

        # Validate envelope
        if data.get('event_type') != 'verification.required':
            logger.warning(f"Unexpected event type: {data.get('event_type')}")
            return  # Acknowledge and skip

        if data.get('service') != 'content-analysis-v2':
            logger.warning(f"Unexpected service: {data.get('service')}")
            return  # Acknowledge and skip

        # Extract payload
        payload = data['payload']

        article_id = payload['article_id']
        pipeline_execution_id = payload['pipeline_execution_id']
        uq_score = payload['uq_score']
        trigger_reason = payload['trigger_reason']
        uncertainty_factors = payload['uncertainty_factors']
        quality_scores = payload['quality_scores']

        logger.info(
            f"Verification triggered: "
            f"article={article_id}, "
            f"score={uq_score}, "
            f"reason={trigger_reason}"
        )

        # Dispatch to appropriate verification handler
        if trigger_reason == 'financial_uncertainty_high':
            await self.verify_financial_analysis(
                article_id, pipeline_execution_id, payload
            )
        elif trigger_reason == 'low_verification_score':
            await self.verify_evidence(
                article_id, pipeline_execution_id, payload
            )
        elif trigger_reason == 'low_credibility':
            await self.verify_source_credibility(
                article_id, pipeline_execution_id, payload
            )
        else:
            await self.generic_verification(
                article_id, pipeline_execution_id, payload
            )

    async def verify_financial_analysis(
        self,
        article_id: str,
        pipeline_execution_id: str,
        payload: dict
    ):
        """
        Verify financial analysis with high uncertainty.

        Steps:
        1. Cross-reference with financial data APIs
        2. Check multiple news sources
        3. Verify economic indicators mentioned
        4. Flag for financial analyst review
        """
        logger.info(f"Starting financial verification for {article_id}")

        # TODO: Implement financial verification logic
        # - Query financial APIs (Bloomberg, Reuters)
        # - Cross-reference with other news sources
        # - Verify economic indicators
        # - Update article status in database

    async def verify_evidence(
        self,
        article_id: str,
        pipeline_execution_id: str,
        payload: dict
    ):
        """
        Verify evidence-based claims.

        Steps:
        1. Search for corroborating sources
        2. Check image/video authenticity (if available)
        3. Cross-reference witness testimonies
        4. Flag for editor review
        """
        logger.info(f"Starting evidence verification for {article_id}")

        # TODO: Implement evidence verification logic
        # - Search for corroborating sources (Google News API)
        # - Image reverse search (TinEye, Google Images)
        # - Video verification (InVID)
        # - Update verification status

    async def verify_source_credibility(
        self,
        article_id: str,
        pipeline_execution_id: str,
        payload: dict
    ):
        """
        Verify source credibility.

        Steps:
        1. Check source against credibility databases
        2. Analyze bias patterns
        3. Review source history
        4. Flag for editorial review
        """
        logger.info(f"Starting source verification for {article_id}")

        # TODO: Implement source verification logic
        # - Query credibility databases (Media Bias/Fact Check)
        # - Check source history
        # - Flag for editorial review

    async def generic_verification(
        self,
        article_id: str,
        pipeline_execution_id: str,
        payload: dict
    ):
        """
        Generic verification for multiple triggers.

        Steps:
        1. Create verification task
        2. Flag for human review
        3. Update article status
        """
        logger.info(f"Starting generic verification for {article_id}")

        # TODO: Implement generic verification logic
        # - Create verification task in database
        # - Flag for human review queue
        # - Update article status to "pending_verification"
```

### Error Handling

```python
async def process_verification(self, body: bytes):
    """Process verification with error handling."""
    try:
        data = json.loads(body)
        payload = data['payload']

        # Process verification
        await self.handle_verification(payload)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        # Don't requeue - message is malformed
        return

    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        # Don't requeue - message is invalid
        return

    except Exception as e:
        logger.error(f"Verification processing failed: {e}", exc_info=True)
        # Requeue message (raise exception)
        raise
```

### Monitoring

```python
from prometheus_client import Counter, Histogram

# Metrics
verification_events_received = Counter(
    'verification_events_received_total',
    'Total verification events received',
    ['trigger_reason']
)

verification_events_processed = Counter(
    'verification_events_processed_total',
    'Total verification events processed successfully',
    ['trigger_reason']
)

verification_events_failed = Counter(
    'verification_events_failed_total',
    'Total verification events failed',
    ['trigger_reason']
)

verification_processing_duration = Histogram(
    'verification_processing_duration_seconds',
    'Time taken to process verification event',
    ['trigger_reason']
)

# Usage in consumer
async def process_verification(self, body: bytes):
    data = json.loads(body)
    payload = data['payload']
    trigger_reason = payload['trigger_reason']

    verification_events_received.labels(trigger_reason=trigger_reason).inc()

    start_time = time.time()
    try:
        await self.handle_verification(payload)

        verification_events_processed.labels(trigger_reason=trigger_reason).inc()

    except Exception as e:
        verification_events_failed.labels(trigger_reason=trigger_reason).inc()
        raise
    finally:
        duration = time.time() - start_time
        verification_processing_duration.labels(trigger_reason=trigger_reason).observe(duration)
```

---

## Testing

### Publishing Test Events

```python
import asyncio
import json
from app.messaging.event_publisher import EventPublisher

async def publish_test_verification_event():
    """Publish test verification event for testing consumers."""
    publisher = EventPublisher()
    await publisher.connect()

    payload = {
        "article_id": "test-550e8400-e29b-41d4-a716-446655440000",
        "pipeline_execution_id": "test-660e8400-e29b-41d4-a716-446655440001",
        "uq_score": 35.0,
        "trigger_reason": "low_overall_quality",
        "uncertainty_factors": [
            "Test: Overall quality score: 35.0 (very low)",
            "Test: Credibility: 30.0 (unreliable source)"
        ],
        "affected_agents": ["TRIAGE"],
        "quality_scores": {
            "overall": 35.0,
            "credibility": 30.0,
            "objectivity": 45.0,
            "verification": 25.0,
            "relevance": 40.0,
            "completeness": 38.0,
            "consistency": 32.0
        }
    }

    success = await publisher.publish_event(
        "verification.required",
        payload,
        correlation_id="test-correlation-id"
    )

    print(f"Test event published: {success}")

    await publisher.disconnect()

# Run
asyncio.run(publish_test_verification_event())
```

### Consuming Test Events

```bash
# Terminal 1: Start consumer
docker exec -it verification-service \
  python3 -m app.consumers.verification_consumer

# Terminal 2: Publish test event
docker exec -it content-analysis-v2 \
  python3 -c "
from app.messaging.event_publisher import get_event_publisher
import asyncio
# ... (use code from above)
"

# Terminal 1: Should show:
# [INFO] Verification triggered: article=test-550e8400..., score=35.0, reason=low_overall_quality
```

---

## Troubleshooting

### Issue: Consumer Not Receiving Events

**Check 1: Queue Binding**
```bash
# RabbitMQ Management UI
# http://localhost:15672
# Login: guest/guest
# Exchanges → news.events → Bindings
# Should show: verification.queue → verification.required
```

**Check 2: Consumer Connection**
```bash
# Check consumer logs
docker logs verification-service | grep -i "rabbitmq\|verification"

# Expected: "Verification consumer started, waiting for events..."
# If missing: Connection failed
```

**Check 3: Message in Queue**
```bash
# RabbitMQ Management UI
# Queues → verification.queue → Get messages
# Should show pending messages

# Or CLI:
docker exec rabbitmq rabbitmqctl list_queues name messages
# Expected: verification.queue 5 (or > 0)
```

### Issue: Events Not Being Published

**Check 1: EventPublisher Connection**
```bash
# Check publisher logs
docker logs content-analysis-v2 | grep -i "event\|rabbitmq"

# Expected: "Connected to RabbitMQ exchange: news.events"
# If missing: Check RABBITMQ_URL in .env
```

**Check 2: UQ Module Enabled**
```bash
docker exec content-analysis-v2 cat /app/.env | grep UQ_ENABLED

# Expected: UQ_ENABLED=true
# If false: Module disabled
```

**Check 3: Threshold Configuration**
```bash
# Check if thresholds too strict
docker exec content-analysis-v2 cat /app/.env | grep UQ_VERIFICATION

# Adjust if needed:
# UQ_VERIFICATION_THRESHOLD_OVERALL=40  # Lower = more triggers
```

---

## Future Events

### Planned Events

**1. `verification.completed`**
- Published when verification finishes
- Includes verification result (approved/rejected/flagged)

**2. `verification.escalated`**
- Published when verification requires human review
- Includes escalation reason and priority

**3. `analysis.low_confidence`**
- Published for individual agent low confidence
- More granular than verification.required

**4. `analysis.high_quality`**
- Published for exceptionally high-quality analyses
- Used for training data collection

---

## References

1. **Related Documentation:**
   - [ADR-034: UQ Module Implementation](../decisions/ADR-034-uq-module-implementation.md)
   - [Content Analysis V2 - UQ Module](../services/content-analysis-v2-uq-module.md)
   - [RabbitMQ Architecture](../architecture/rabbitmq-architecture.md)

2. **Implementation Files:**
   - Event Publisher: `services/content-analysis-v2/app/messaging/event_publisher.py`
   - Pipeline Orchestrator: `services/content-analysis-v2/app/pipeline/orchestrator.py`
   - Quality Indicators: `services/content-analysis-v2/app/quality_scoring/quality_indicators.py`

3. **External Resources:**
   - [RabbitMQ Topic Exchange](https://www.rabbitmq.com/tutorials/tutorial-five-python.html)
   - [aio_pika Documentation](https://aio-pika.readthedocs.io/)

---

**Last Updated:** 2025-11-02
**Version:** 1.0
**Maintainer:** Content Analysis V2 Team
