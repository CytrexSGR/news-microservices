# LLM Orchestrator Service API Documentation

## Base URL

- Development: `http://localhost:8109`
- Production: `https://api.news-mcp.com/llm-orchestrator`

## Overview

The LLM Orchestrator Service provides monitoring and health check endpoints for the DIA (Dynamic Intelligence Augmentation) system. This service is primarily event-driven via RabbitMQ and does not expose HTTP endpoints for triggering verification workflows.

**Event-Driven Architecture**: Verification requests are handled through RabbitMQ events, not HTTP calls.

## Authentication

⚠️ **Phase 1**: No authentication required for health endpoints.

🔒 **Future Phases**: Will require service-to-service API key authentication for management endpoints.

## Endpoints

### Health & Monitoring

#### GET /health

Service liveness check - responds if the service is running.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "llm-orchestrator-service",
  "version": "1.0.0"
}
```

**Error Responses:**
- `503 Service Unavailable`: Service is not responding

**Usage Example:**
```bash
curl http://localhost:8109/health
```

---

#### GET /health/ready

Service readiness check - verifies that all dependencies are connected and configured.

**Response:** `200 OK`
```json
{
  "status": "ready",
  "checks": {
    "rabbitmq": "connected",
    "openai": "configured"
  }
}
```

**Response Fields:**
- `status`: Overall readiness status (`ready` or `not_ready`)
- `checks.rabbitmq`: RabbitMQ connection status
  - `"connected"`: Successfully connected to RabbitMQ
  - `"disconnected"`: Connection failed
- `checks.openai`: OpenAI API configuration status
  - `"configured"`: API key is set
  - `"missing"`: API key not configured

**Error Responses:**
- `503 Service Unavailable`: Service dependencies are not ready

**Usage Example:**
```bash
curl http://localhost:8109/health/ready
```

**Use Cases:**
- Kubernetes readiness probes
- Load balancer health checks
- Deployment verification

---

#### GET /

Root endpoint providing service information and documentation links.

**Response:** `200 OK`
```json
{
  "service": "llm-orchestrator-service",
  "description": "LLM Orchestrator Service for DIA",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "readiness": "/health/ready",
    "docs": "/docs"
  }
}
```

**Usage Example:**
```bash
curl http://localhost:8109/
```

---

#### GET /metrics

Prometheus metrics endpoint for monitoring and observability.

**Status:** 🚧 To be implemented (Phase 2)

**Future Response:** `200 OK`
```
# HELP dia_verification_requests_total Total verification requests processed
# TYPE dia_verification_requests_total counter
dia_verification_requests_total{status="success"} 42
dia_verification_requests_total{status="failure"} 3

# HELP dia_stage1_duration_seconds Stage 1 (Root Cause Analysis) duration
# TYPE dia_stage1_duration_seconds histogram
dia_stage1_duration_seconds_bucket{le="1.0"} 5
dia_stage1_duration_seconds_bucket{le="3.0"} 38
dia_stage1_duration_seconds_bucket{le="5.0"} 42
dia_stage1_duration_seconds_sum 127.5
dia_stage1_duration_seconds_count 42

# HELP dia_stage2_duration_seconds Stage 2 (Plan Generation) duration
# TYPE dia_stage2_duration_seconds histogram
dia_stage2_duration_seconds_bucket{le="2.0"} 10
dia_stage2_duration_seconds_bucket{le="5.0"} 39
dia_stage2_duration_seconds_bucket{le="10.0"} 42
dia_stage2_duration_seconds_sum 168.2
dia_stage2_duration_seconds_count 42

# HELP dia_hypothesis_types Problem hypothesis type distribution
# TYPE dia_hypothesis_types counter
dia_hypothesis_types{type="factual_error"} 25
dia_hypothesis_types{type="entity_ambiguity"} 12
dia_hypothesis_types{type="temporal_inconsistency"} 5

# HELP dia_plan_priorities Verification plan priority distribution
# TYPE dia_plan_priorities counter
dia_plan_priorities{priority="critical"} 8
dia_plan_priorities{priority="high"} 22
dia_plan_priorities{priority="medium"} 10
dia_plan_priorities{priority="low"} 2
```

**Usage Example:**
```bash
curl http://localhost:8109/metrics
```

---

#### GET /docs

Interactive API documentation (Swagger UI).

**Response:** `200 OK` (HTML)

OpenAPI/Swagger interface for exploring the API interactively.

**Usage Example:**
```bash
# Open in browser
open http://localhost:8109/docs
```

---

## Event-Driven Interface

### RabbitMQ Events

The primary interface for the LLM Orchestrator Service is through RabbitMQ events.

#### Input Event: verification.required

**Exchange:** `verification_exchange` (type: topic)
**Queue:** `verification_queue`
**Routing Key Pattern:** `verification.required.*`

**Event Schema:**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "verification.required",
  "timestamp": "2024-10-24T12:00:00Z",

  "analysis_result_id": "660e8400-e29b-41d4-a716-446655440001",
  "article_id": "770e8400-e29b-41d4-a716-446655440002",

  "article_title": "Tesla Reports Record Q3 2024 Earnings",
  "article_content": "Tesla Inc. announced record-breaking third-quarter earnings today, with net income reaching $5 billion...",
  "article_url": "https://example.com/tesla-q3-2024-earnings",
  "article_published_at": "2024-10-15T14:30:00Z",

  "uq_confidence_score": 0.62,
  "uncertainty_factors": [
    "Low confidence in claim accuracy",
    "Numerical claim lacks verification",
    "Financial data requires fact-checking"
  ],

  "analysis_summary": "Tesla reports record $5B profit in Q3 2024, beating expectations.",
  "extracted_entities": [
    {"entity": "Tesla Inc.", "type": "ORGANIZATION"},
    {"entity": "$5 billion", "type": "MONEY"},
    {"entity": "Q3 2024", "type": "DATE"}
  ],
  "category_analysis": {
    "primary_category": "business",
    "subcategories": ["automotive", "earnings"]
  },

  "priority": "high"
}
```

**Required Fields:**
- `event_id` (UUID): Unique event identifier
- `event_type` (string): Must be `"verification.required"`
- `timestamp` (ISO8601): Event creation time
- `analysis_result_id` (UUID): ID of analysis result to verify
- `article_id` (UUID): ID of article being analyzed
- `article_title` (string): Article headline
- `article_content` (string): Full article text (required for root cause analysis)
- `article_url` (string): Article source URL
- `article_published_at` (ISO8601): Article publication date
- `uq_confidence_score` (float 0.0-1.0): UQ sensor confidence score
- `uncertainty_factors` (array): List of uncertainty reasons

**Optional Fields:**
- `analysis_summary` (string): Current summary (may be incorrect)
- `extracted_entities` (array): Current entity extraction
- `category_analysis` (object): Current category classification
- `priority` (string): Processing priority (`low`, `medium`, `high`, `critical`)

**Publishing Example:**

```bash
# Using rabbitmqadmin
docker exec -i rabbitmq rabbitmqadmin \
  --username=guest \
  --password=guest \
  publish exchange=verification_exchange \
  routing_key="verification.required.660e8400-e29b-41d4-a716-446655440001" \
  payload='{"event_id":"...","event_type":"verification.required",...}' \
  properties='{"content_type":"application/json","delivery_mode":2}'
```

```python
# Using Python (aio-pika)
import json
import aio_pika

async def publish_verification_request(event_data):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()
    exchange = await channel.get_exchange("verification_exchange")

    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(event_data).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=f"verification.required.{event_data['analysis_result_id']}"
    )

    await connection.close()
```

---

## Internal Processing Flow

When a `verification.required` event is received, the service executes a two-stage LLM planning process:

### Stage 1: Root Cause Analysis

**Input:** VerificationRequiredEvent (from RabbitMQ)

**LLM Task:** Analyze article content and uncertainty factors to identify the precise root cause of uncertainty.

**Output:** ProblemHypothesis

```json
{
  "primary_concern": "The financial figure '$5 billion' appears to be a factual error",
  "affected_content": "Tesla announced record-breaking third-quarter earnings today, with net income reaching $5 billion",
  "hypothesis_type": "factual_error",
  "confidence": 0.85,
  "reasoning": "Historical Tesla quarterly profits typically range $3-4.5B. The claimed $5B figure significantly exceeds normal ranges and historical data. This specific numerical claim requires fact-checking against official SEC filings and Tesla's investor relations releases.",
  "verification_approach": "Cross-reference with SEC EDGAR database, Tesla investor relations, and verified financial data sources"
}
```

**Hypothesis Types:**
- `factual_error`: Incorrect facts, numbers, or claims
- `entity_ambiguity`: Unclear entity references (which John Smith?)
- `temporal_inconsistency`: Date/time conflicts
- `missing_context`: Missing critical information
- `contradictory_claims`: Internal contradictions
- `source_reliability_issue`: Questionable source credibility

---

### Stage 2: Plan Generation

**Input:** ProblemHypothesis (from Stage 1)

**LLM Task:** Create a structured, executable verification plan with specific tool calls and authoritative sources.

**Output:** VerificationPlan

```json
{
  "priority": "critical",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual net income amount official report')",
    "financial_data_lookup(company='Tesla', metric='net_income', period='Q3 2024', source='SEC')",
    "fact_check_claim(claim='Tesla Q3 2024 profit $5 billion', sources=['SEC EDGAR', 'Tesla IR'])"
  ],
  "external_sources": [
    "SEC EDGAR Database (Tesla 10-Q filing Q3 2024)",
    "Tesla Investor Relations (Official earnings report)",
    "Bloomberg Terminal (Verified financial data)",
    "Reuters financial database",
    "Yahoo Finance (Consensus analyst estimates)"
  ],
  "expected_corrections": [
    {
      "field": "facts",
      "original": "Tesla Q3 2024 net income: $5 billion",
      "corrected": "Tesla Q3 2024 net income: $4.2 billion (pending verification)",
      "confidence_improvement": 0.15
    },
    {
      "field": "summary",
      "original": "record-breaking...with net income reaching $5 billion",
      "corrected": "strong performance...with net income of approximately $4.2 billion",
      "confidence_improvement": 0.12
    }
  ],
  "estimated_verification_time_seconds": 120
}
```

**Priority Levels:**
- `critical`: Severe factual error, immediate correction needed
- `high`: Significant uncertainty, verification required before publication
- `medium`: Minor uncertainty, can be verified asynchronously
- `low`: Optional verification, low impact

**Verification Methods:**

Available tools (Phase 2 implementation):
- `perplexity_deep_search(query: str)` - Deep web search with citations
- `financial_data_lookup(company: str, metric: str, period: str)` - Financial API
- `fact_check_claim(claim: str)` - Fact-checking databases
- `entity_lookup(entity_name: str, entity_type: str)` - Entity resolution
- `temporal_verification(event: str, date: str)` - Timeline verification
- `source_credibility_check(source_url: str)` - Source reliability

---

## Logging & Observability

### Log Format

All logs use structured JSON format with correlation IDs:

```json
{
  "timestamp": "2024-10-24T12:00:18.279Z",
  "level": "INFO",
  "logger": "app.services.verification_consumer",
  "message": "Processing verification for article_id=770e8400-e29b-41d4-a716-446655440002",
  "context": {
    "article_id": "770e8400-e29b-41d4-a716-446655440002",
    "analysis_result_id": "660e8400-e29b-41d4-a716-446655440001",
    "routing_key": "verification.required.660e8400-e29b-41d4-a716-446655440001",
    "delivery_tag": 1
  }
}
```

### Key Log Entries

**Consumer Activity:**
```
[VerificationConsumer] Received message: routing_key=..., delivery_tag=1
[VerificationConsumer] Processing verification for article_id=..., analysis_result_id=...
[VerificationConsumer] Planning completed successfully: hypothesis_type=factual_error, plan_priority=critical
```

**Stage 1 Activity:**
```
[DIAPlanner] Stage 1: Analyzing root cause...
[Stage 1] Root cause identified: factual_error (confidence: 0.85)
[DIAPlanner] Stage 1 Complete: hypothesis_type=factual_error, confidence=0.85
```

**Stage 2 Activity:**
```
[DIAPlanner] Stage 2: Generating verification plan...
[Stage 2] Plan generated: 3 methods, priority=critical
[DIAPlanner] Stage 2 Complete: priority=critical, methods=3, sources=5
```

**Error Logs:**
```
[Stage 2] Error (attempt 1): 4 validation errors for VerificationPlan
[VerificationConsumer] Error processing message: <error details>
```

### Monitoring Commands

```bash
# Follow real-time logs
docker logs -f news-llm-orchestrator

# Filter for errors only
docker logs news-llm-orchestrator 2>&1 | grep ERROR

# Check Stage 1 performance
docker logs news-llm-orchestrator 2>&1 | grep "Stage 1 Complete"

# Check Stage 2 performance
docker logs news-llm-orchestrator 2>&1 | grep "Stage 2 Complete"

# Monitor RabbitMQ consumption
docker logs news-llm-orchestrator 2>&1 | grep "Processing verification"
```

---

## Error Handling

### Error Response Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 200 | OK | Request successful |
| 503 | Service Unavailable | Service or dependencies not ready |

### Event Processing Errors

Errors during event processing do not return HTTP responses (event-driven). Instead:

1. **Logged**: Error details written to logs with `ERROR` level
2. **Message ACK**: Message is acknowledged (not requeued to prevent infinite loops)
3. **Dead Letter Queue**: Failed messages sent to `verification_dlq` for manual inspection

**Common Processing Errors:**

| Error Type | Cause | Handling |
|------------|-------|----------|
| JSON Parse Error | Invalid event payload | Logged, message NACKed |
| Pydantic Validation Error | Event schema mismatch | Logged, message NACKed |
| OpenAI API Error | Rate limit, timeout | Retry 3x, then DLQ |
| LLM Response Parse Error | Invalid JSON from LLM | Retry 3x, then DLQ |

**Example Error Log:**

```
ERROR - [Stage 2] Error (attempt 1): 4 validation errors for VerificationPlan
  expected_corrections.0: Input should be a valid dictionary or instance of ExpectedCorrection
  estimated_verification_time_seconds: Field required
```

**Dead Letter Queue Inspection:**

```bash
# Check DLQ messages
docker exec rabbitmq rabbitmqadmin list queues name messages | grep verification_dlq

# Get messages from DLQ
docker exec rabbitmq rabbitmqadmin get queue=verification_dlq count=10
```

---

## Performance Characteristics

### Latency

| Operation | Typical Duration | 95th Percentile |
|-----------|------------------|-----------------|
| Stage 1 (Root Cause Analysis) | 3-5 seconds | 7 seconds |
| Stage 2 (Plan Generation) | 4-6 seconds | 9 seconds |
| Total Processing Time | 7-11 seconds | 16 seconds |
| Health Check | < 50ms | 100ms |
| Readiness Check | < 100ms | 200ms |

### Throughput

- **Sequential Processing**: 1 message at a time (`prefetch_count=1`)
- **Theoretical Max**: ~5-8 verifications per minute per instance
- **Practical Max**: ~4-6 verifications per minute (accounting for retries)

**Scaling:**
- Deploy multiple instances for parallel processing
- Each instance consumes from same queue
- Messages distributed round-robin

### Resource Usage

- **Memory**: ~200-400 MB per instance
- **CPU**: Low (mostly I/O bound waiting for LLM responses)
- **Network**: High during LLM calls (~10-50 KB per request)

---

## Rate Limits

### OpenAI API

- **Tier 1**: 500 RPM, 10,000 TPM (tokens per minute)
- **Tier 2**: 5,000 RPM, 200,000 TPM
- **Tier 3**: 10,000 RPM, 1,000,000 TPM

**Mitigation:**
- Retry with exponential backoff
- Queue messages during rate limit periods
- Monitor rate limit headers in responses

---

## Testing

### Manual Testing

```bash
# 1. Check service health
curl http://localhost:8109/health

# 2. Check readiness
curl http://localhost:8109/health/ready

# 3. Publish test event
docker exec -i rabbitmq rabbitmqadmin \
  --username=guest \
  --password=guest \
  publish exchange=verification_exchange \
  routing_key="verification.required.test-123" \
  payload='{"event_id":"...","event_type":"verification.required",...}' \
  properties='{"content_type":"application/json","delivery_mode":2}'

# 4. Monitor logs
docker logs -f news-llm-orchestrator

# Expected output:
# ✅ [Consumer] Processing verification for article_id=...
# ✅ [Stage 1] Root cause identified: factual_error (confidence: 0.85)
# ✅ [Stage 2] Plan generated: 3 methods, priority=critical
```

### Integration Testing

See `docs/guides/dia-integration-testing.md` for comprehensive integration tests with adversarial test cases.

---

## Version History

- **1.0.0** (2024-10-24): Initial release
  - Health check endpoints
  - RabbitMQ event consumption
  - Two-stage LLM planning
  - Logging and observability

---

## Related Documentation

- **Service Documentation**: `docs/services/llm-orchestrator-service.md`
- **Architecture Decision Record**: `docs/decisions/ADR-018-dia-planner-verifier.md`
- **Event Schemas**: `models/verification_events.py`
- **Setup Guide**: `scripts/setup-rabbitmq.sh`

---

## Support

For API questions or issues:
- **Endpoint Issues**: Check health/readiness endpoints first
- **Event Format Issues**: Validate against schema in `models/verification_events.py`
- **Integration Issues**: Review ADR-018 for architecture details
- **Performance Issues**: Check logs for latency metrics
