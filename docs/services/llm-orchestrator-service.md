# LLM Orchestrator Service Documentation

## Overview

Central orchestration service for the DIA (Dynamic Intelligence Augmentation) system, responsible for coordinating AI-powered verification workflows through two-stage LLM-based planning and tool orchestration.

**Key Responsibilities:**
- Consume `verification.required` events from RabbitMQ
- Execute two-stage LLM planning (Root Cause Analysis → Plan Generation)
- Transform vague uncertainty factors into precise problem hypotheses
- Generate structured, executable verification plans
- Coordinate with external verification tools (Perplexity, financial APIs, etc.)
- Provide health monitoring and observability

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 14+ (shared database)
- RabbitMQ 3.12+ (message broker)
- OpenAI API key (GPT-4o-mini)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd news-microservices/services/llm-orchestrator-service

# Configure environment
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Start service
docker compose up -d llm-orchestrator-service

# Check health
curl http://localhost:8109/health
```

### Docker Compose Configuration

```yaml
llm-orchestrator-service:
  build:
    context: ./services/llm-orchestrator-service
    dockerfile: Dockerfile.dev
  container_name: news-llm-orchestrator
  ports:
    - "8109:8109"
  environment:
    - DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - OPENAI_MODEL=gpt-4o-mini
    - DIA_STAGE1_TEMPERATURE=0.3
    - DIA_STAGE2_TEMPERATURE=0.2
  depends_on:
    - postgres
    - rabbitmq
```

## Architecture

### System Components

```
┌──────────────────────┐
│ Content Analysis     │
│ Service              │
└──────────┬───────────┘
           │ publishes verification.required
           v
┌──────────────────────┐
│ RabbitMQ             │
│ verification_exchange│
│ verification_queue   │
└──────────┬───────────┘
           │ consumes
           v
┌─────────────────────────────────────┐
│ LLM Orchestrator Service            │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ DIAPlanner (Phase 1)            │ │
│ │  Stage 1: Root Cause Analysis  │ │
│ │  Stage 2: Plan Generation      │ │
│ └─────────────────────────────────┘ │
│           │                          │
│           v                          │
│ ┌─────────────────────────────────┐ │
│ │ DIAVerifier (Phase 2) ✓         │ │
│ │  • Tool Execution (Parallel)   │ │
│ │  • Evidence Aggregation        │ │
│ │  • Confidence Calculation      │ │
│ └─────────────────────────────────┘ │
│           │                          │
│           v                          │
│ ┌─────────────────────────────────┐ │
│ │ DIACorrector (Phase 3)          │ │
│ │  (Future: Apply Corrections)   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
           │
           v (Phase 2: Evidence logged)
    ┌──────────────┐
    │ External     │
    │ Tools:       │
    │ • Perplexity │
    │ • Financial  │
    │   APIs       │
    └──────────────┘
```

### Two-Stage Planning Process

```
┌─────────────────────────────────────────────────────────────┐
│                     STAGE 1: ROOT CAUSE ANALYSIS            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input:                                                      │
│  • Article content (full text)                              │
│  • Vague uncertainty factors from UQ sensor                 │
│    - "Low confidence in claim accuracy"                     │
│    - "Numerical claim lacks verification"                   │
│  • Current analysis (potentially incorrect)                 │
│                                                              │
│  LLM Task:                                                   │
│  Perform deep analytical reasoning to identify the          │
│  PRECISE root cause of uncertainty.                         │
│                                                              │
│  Output: ProblemHypothesis                                   │
│  {                                                           │
│    "primary_concern": "The financial figure '$5 billion'...",│
│    "hypothesis_type": "factual_error",                      │
│    "confidence": 0.85,                                      │
│    "reasoning": "Historical Tesla profits are $3-4.5B...",  │
│    "verification_approach": "Cross-reference with SEC..."   │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                     STAGE 2: PLAN GENERATION                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: ProblemHypothesis (from Stage 1)                    │
│                                                              │
│  LLM Task:                                                   │
│  Create a structured, executable verification plan with     │
│  specific tool calls and authoritative sources.             │
│                                                              │
│  Output: VerificationPlan                                    │
│  {                                                           │
│    "priority": "critical",                                  │
│    "verification_methods": [                                │
│      "perplexity_deep_search(query='Tesla Q3 2024...')",   │
│      "financial_data_lookup(company='TSLA',...)"           │
│    ],                                                        │
│    "external_sources": [                                    │
│      "SEC EDGAR Database (10-Q filing)",                   │
│      "Tesla Investor Relations"                            │
│    ],                                                        │
│    "expected_corrections": [...],                          │
│    "estimated_verification_time_seconds": 120              │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Verification Execution (NEW)

**Status:** ✅ Implemented (2025-10-24)

```
┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: DIA-VERIFIER EXECUTION                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: VerificationPlan (from Phase 1 Stage 2)            │
│                                                              │
│  Step 1: Parse Verification Methods                         │
│  ├─ Extract tool names and parameters                       │
│  ├─ Validate tools exist in registry                        │
│  └─ Example: "perplexity_deep_search(query='...')"         │
│                                                              │
│  Step 2: Execute Tools in Parallel (asyncio.gather)        │
│  ├─ Tool 1: perplexity_deep_search                         │
│  │   └─ Search Perplexity API with citations              │
│  ├─ Tool 2: financial_data_lookup                          │
│  │   └─ Query Alpha Vantage for financial data            │
│  └─ All tools execute concurrently (faster)                │
│                                                              │
│  Step 3: Aggregate Evidence                                 │
│  ├─ Collect source citations                                │
│  ├─ Extract key findings                                    │
│  ├─ Calculate overall confidence                            │
│  ├─ Determine hypothesis confirmation                       │
│  └─ Identify corrected facts                                │
│                                                              │
│  Output: EvidencePackage                                     │
│  {                                                           │
│    "hypothesis_confirmed": true,                            │
│    "confidence_score": 0.92,                                │
│    "key_findings": ["Finding 1", "Finding 2"],             │
│    "corrected_facts": {...},                               │
│    "source_citations": [...],                              │
│    "tool_executions": [...]                                │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Available Tools:**

1. **perplexity_deep_search**
   - Purpose: Real-time web search with AI-powered analysis
   - API: Perplexity API (sonar-pro model)
   - Features: Automatic citations, domain filtering, recency filtering
   - Confidence: Based on citation quality (0.2-0.95)

2. **financial_data_lookup**
   - Purpose: Official financial data verification
   - API: Alpha Vantage (free tier: 25 req/day)
   - Metrics: Stock quotes, earnings, financial statements
   - Confidence: 0.9 (high - official financial data)

**Parallel Execution:**

All tools run concurrently using `asyncio.gather()`:
```python
# Execute 2 tools in parallel - completes in time of slowest tool
results = await asyncio.gather(
    perplexity_deep_search(query="..."),
    financial_data_lookup(company="TSLA", ...)
)
# Result: ~30s instead of 60s (2x speedup)
```

**Evidence Aggregation Logic:**

- **Hypothesis Confirmation:** Average tool confidence > 0.7
- **Overall Confidence:** Weighted average of tool results
  - 70% from average tool confidence
  - 30% from success rate
  - +0.1 boost if hypothesis confirmed
- **Source Reliability:**
  - Primary (1.0): .gov, sec.gov, official sources
  - Authoritative (0.8): reuters.com, bloomberg.com
  - Secondary (0.6): general sources

### Key Design Decisions

1. **Two-Stage Architecture**: Separates diagnostic reasoning from tactical planning
   - Stage 1 focuses on *what* is wrong (analytical, higher temperature 0.3)
   - Stage 2 focuses on *how* to fix it (structured, lower temperature 0.2)

2. **Event-Driven Consumption**: Uses RabbitMQ topic exchange for loose coupling
   - Exchange: `verification_exchange` (type: topic)
   - Queue: `verification_queue` (durable, with DLQ)
   - Routing Key Pattern: `verification.required.*`

3. **Structured LLM Output**: Uses OpenAI's JSON mode for reliable parsing
   - `response_format={"type": "json_object"}`
   - Pydantic validation for type safety
   - Retry logic (3 attempts) for robustness

4. **Background Consumer**: FastAPI lifespan management
   - Consumer runs in background task during app startup
   - Graceful shutdown on app termination
   - Robust connection with auto-reconnect

5. **Parallel Tool Execution** (Phase 2): Maximize throughput
   - All verification tools run concurrently
   - Uses `asyncio.gather()` for parallel async execution
   - Reduces verification time by 50-70%
   - Graceful error handling (one tool failure doesn't break others)

## Database Schema

**Note:** This service uses the shared database (`news_mcp`) but does not create its own tables in Phase 1. All event data is passed in-memory through RabbitMQ messages.

Future phases will add:
- Verification request tracking
- Evidence package storage
- Tool execution history
- Performance metrics

## API Endpoints

### Health & Monitoring

- `GET /health` - Service health check
- `GET /health/ready` - Readiness check (RabbitMQ + OpenAI status)
- `GET /metrics` - Prometheus metrics (future)
- `GET /` - Service information and endpoint listing

### Example Health Response

```json
{
  "status": "healthy",
  "service": "llm-orchestrator-service",
  "version": "1.0.0"
}
```

### Example Readiness Response

```json
{
  "status": "ready",
  "checks": {
    "rabbitmq": "connected",
    "openai": "configured"
  }
}
```

**Note:** This service does not expose HTTP endpoints for verification requests. All verification workflows are triggered via RabbitMQ events.

## Event Schemas

### Input: VerificationRequiredEvent

Published by `content-analysis-service` when UQ confidence score < 0.65.

```json
{
  "event_id": "uuid",
  "event_type": "verification.required",
  "timestamp": "2024-10-24T12:00:00Z",

  "analysis_result_id": "uuid",
  "article_id": "uuid",

  "article_title": "Article headline",
  "article_content": "Full article text (required for diagnosis)",
  "article_url": "https://...",
  "article_published_at": "2024-10-15T14:30:00Z",

  "uq_confidence_score": 0.62,
  "uncertainty_factors": [
    "Low confidence in claim accuracy",
    "Numerical claim lacks verification"
  ],

  "analysis_summary": "Current summary (potentially incorrect)",
  "extracted_entities": [...],
  "category_analysis": {...},

  "priority": "high"
}
```

### Output: ProblemHypothesis (Stage 1)

```json
{
  "primary_concern": "The financial figure '$5 billion' appears to be a factual error",
  "affected_content": "Tesla announced record profits of $5 billion...",
  "hypothesis_type": "factual_error",
  "confidence": 0.85,
  "reasoning": "Historical Tesla quarterly profits typically range $3-4.5B. This figure significantly exceeds normal ranges and requires fact-checking.",
  "verification_approach": "Cross-reference with SEC filings and financial databases"
}
```

### Output: VerificationPlan (Stage 2)

```json
{
  "priority": "critical",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount')",
    "financial_data_lookup(company='Tesla', metric='net_income', period='Q3 2024')",
    "fact_check_claim(claim='Tesla Q3 2024 profit $5 billion')"
  ],
  "external_sources": [
    "SEC EDGAR Database (10-Q filing)",
    "Tesla Investor Relations",
    "Bloomberg Terminal",
    "Reuters financial database",
    "Yahoo Finance"
  ],
  "expected_corrections": [
    {
      "field": "facts",
      "original": "Tesla Q3 profits: $5B",
      "corrected": "Tesla Q3 profits: $4.2B",
      "confidence_improvement": 0.15
    }
  ],
  "estimated_verification_time_seconds": 120
}
```

## Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=llm-orchestrator-service
PORT=8109
HOST=0.0.0.0

# Database (shared)
DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_VERIFICATION_EXCHANGE=verification_exchange
RABBITMQ_VERIFICATION_QUEUE=verification_queue
RABBITMQ_VERIFICATION_ROUTING_KEY=verification.required.*

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# DIA Configuration
DIA_STAGE1_TEMPERATURE=0.3  # Analytical reasoning
DIA_STAGE2_TEMPERATURE=0.2  # Structured output
DIA_MAX_RETRIES=3           # LLM call retries

# Logging
LOG_LEVEL=INFO
```

### Critical Configuration Notes

1. **OPENAI_API_KEY**: Required for both LLM stages
   - Must have access to GPT-4o-mini or compatible model
   - Verify API quota and rate limits

2. **Temperature Settings**:
   - Stage 1 (0.3): Higher for creative analytical reasoning
   - Stage 2 (0.2): Lower for consistent structured output

3. **RabbitMQ Credentials**:
   - Default: `guest:guest` (development)
   - Production: Use dedicated credentials with limited permissions

4. **Message TTL**: 24 hours (86400000ms) configured in queue
   - Messages expire if not processed within this window
   - Failed messages go to Dead Letter Queue

## Monitoring & Observability

### Logging

Structured logging with correlation IDs:

```
2024-10-24 12:00:00 - app.services.verification_consumer - INFO -
  [VerificationConsumer] Received message: routing_key=verification.required.xyz, delivery_tag=1

2024-10-24 12:00:00 - app.services.dia_planner - INFO -
  [DIAPlanner] Stage 1: Analyzing root cause...

2024-10-24 12:00:03 - app.services.dia_planner - INFO -
  [Stage 1] Root cause identified: factual_error (confidence: 0.85)

2024-10-24 12:00:03 - app.services.dia_planner - INFO -
  [DIAPlanner] Stage 2: Generating verification plan...

2024-10-24 12:00:08 - app.services.dia_planner - INFO -
  [Stage 2] Plan generated: 3 methods, priority=critical

2024-10-24 12:00:08 - app.services.verification_consumer - INFO -
  [VerificationConsumer] Planning completed successfully
```

### Health Checks

- **Liveness**: `/health` - Responds if service is running
- **Readiness**: `/health/ready` - Checks RabbitMQ connection
- **Docker Healthcheck**: `docker inspect news-llm-orchestrator`

### Metrics (Future)

Planned Prometheus metrics:
- `dia_verification_requests_total` - Total verification requests
- `dia_stage1_duration_seconds` - Stage 1 latency histogram
- `dia_stage2_duration_seconds` - Stage 2 latency histogram
- `dia_llm_calls_total` - OpenAI API call count
- `dia_llm_errors_total` - LLM call failures
- `dia_hypothesis_types` - Hypothesis type distribution
- `dia_plan_priorities` - Plan priority distribution

## Testing

### Manual Testing

1. **Publish Test Event**:

```bash
# Run RabbitMQ setup (creates exchange/queue)
./scripts/setup-rabbitmq.sh

# Publish test verification event
docker exec -i rabbitmq rabbitmqadmin \
  --username=guest \
  --password=guest \
  publish exchange=verification_exchange \
  routing_key="verification.required.test-123" \
  payload='{"event_id":"...","event_type":"verification.required",...}' \
  properties='{"content_type":"application/json","delivery_mode":2}'

# Monitor logs
docker logs -f news-llm-orchestrator
```

2. **Expected Log Output**:

```
✅ [Consumer] Processing verification for article_id=...
✅ [DIAPlanner] Stage 1: Analyzing root cause...
✅ [Stage 1] Root cause identified: factual_error (confidence: 0.85)
✅ [DIAPlanner] Stage 2: Generating verification plan...
✅ [Stage 2] Plan generated: 3 methods, priority=critical
✅ [Consumer] Planning completed successfully
```

### Integration Testing

See `tests/adversarial_test_framework/` for comprehensive test cases:

```bash
# Run adversarial tests (Phase 3)
python scripts/generate_adversarial_tests.py
python scripts/run_adversarial_tests.py
```

## Error Handling

### LLM Call Failures

- **Retry Logic**: 3 attempts with exponential backoff
- **JSON Parse Errors**: Logged and retried
- **Pydantic Validation Errors**: Logged with details
- **API Rate Limits**: Caught and logged (future: queue for retry)

### RabbitMQ Failures

- **Robust Connection**: Auto-reconnect on connection loss
- **Message Requeue**: `requeue=False` (prevents infinite loops)
- **Dead Letter Queue**: Failed messages go to `verification_dlq`
- **Message TTL**: 24 hours (expires old messages)

### Error Log Examples

```
ERROR - [Stage 2] Error (attempt 1): 4 validation errors for VerificationPlan
  expected_corrections.0: Input should be a valid dictionary

ERROR - [VerificationConsumer] Failed to connect:
  ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN
```

## Performance Considerations

### Latency

- **Stage 1 (Root Cause Analysis)**: ~3-5 seconds
- **Stage 2 (Plan Generation)**: ~4-6 seconds
- **Total Processing Time**: ~7-11 seconds per verification request

### Throughput

- **QoS Setting**: `prefetch_count=1` (processes one message at a time)
- **Rationale**: LLM calls are expensive and rate-limited
- **Scaling**: Deploy multiple instances for parallel processing

### Cost Optimization

- **Model Choice**: GPT-4o-mini (cost-effective, fast)
- **Temperature Settings**: Lower temperature = more deterministic = less retries
- **Token Optimization**: Truncate article content to 2000 chars if needed

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs news-llm-orchestrator --tail 50

# Common issues:
# 1. RabbitMQ not ready
# 2. OpenAI API key invalid
# 3. Port 8109 already in use
```

### RabbitMQ Connection Failed

```bash
# Verify RabbitMQ is running
docker ps | grep rabbitmq

# Check credentials
docker exec rabbitmq rabbitmqctl list_users

# Test connection
docker exec rabbitmq rabbitmqadmin --username=guest --password=guest list exchanges
```

### LLM Calls Failing

```bash
# Verify API key
echo $OPENAI_API_KEY | cut -c1-10  # Should show "sk-proj-..."

# Test API access
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits in logs
docker logs news-llm-orchestrator 2>&1 | grep -i "rate limit"
```

### Messages Not Being Consumed

```bash
# Check queue status
docker exec rabbitmq rabbitmqadmin list queues name messages

# Verify binding
docker exec rabbitmq rabbitmqadmin list bindings

# Check consumer connection
docker logs news-llm-orchestrator 2>&1 | grep "Starting to consume"
```

## Development

### Local Development

```bash
# Install dependencies
cd services/llm-orchestrator-service
pip install -r requirements.txt

# Run locally (outside Docker)
export OPENAI_API_KEY=sk-proj-...
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
python -m uvicorn app.main:app --reload --port 8109
```

### Code Structure

```
services/llm-orchestrator-service/
├── app/
│   ├── main.py                      # FastAPI app + lifespan
│   ├── core/
│   │   ├── config.py                # Environment configuration
│   │   └── prompts.py               # Stage 1 & 2 system prompts
│   └── services/
│       ├── dia_planner.py           # Two-stage LLM planning
│       └── verification_consumer.py # RabbitMQ consumer
├── Dockerfile.dev                   # Development container
├── requirements.txt                 # Python dependencies
└── .env                            # Environment variables
```

### Adding New Tools (Phase 2)

To add a new verification tool:

1. Update `app/core/prompts.py` (Stage 2 available tools)
2. Implement tool in Verifier service (Phase 2)
3. Update `expected_corrections` schema if needed
4. Test with adversarial test cases

## Related Documentation

- **ADR-018**: DIA-Planner & Verifier Architecture
- **ADR-016**: Uncertainty Quantification Module
- **ADR-017**: Adversarial Test Framework
- **Content Analysis Service**: Publishes verification.required events
- **API Documentation**: `docs/api/llm-orchestrator-api.md`
- **RabbitMQ Setup**: `scripts/setup-rabbitmq.sh`

## Deployment

### Production Checklist

- [ ] Configure production OpenAI API key with sufficient quota
- [ ] Set up dedicated RabbitMQ user (not `guest`)
- [ ] Configure message TTL based on SLA requirements
- [ ] Set up Prometheus metrics endpoint
- [ ] Configure log aggregation (ELK, Datadog, etc.)
- [ ] Set up alerting for LLM call failures
- [ ] Test failover with multiple instances
- [ ] Configure resource limits (CPU, memory)
- [ ] Set up database connection pooling (future)
- [ ] Document incident response procedures

### Scaling Strategy

**Horizontal Scaling**: Deploy multiple instances
- Each instance connects to the same RabbitMQ queue
- Messages distributed round-robin via QoS
- No shared state (stateless workers)

**Vertical Scaling**: Increase resources per instance
- More CPU for faster JSON parsing
- More memory for larger article content
- Faster network for reduced LLM latency

## Support

For questions or issues:
- **Architecture**: See ADR-018
- **API Issues**: Check `docs/api/llm-orchestrator-api.md`
- **Integration**: Review `docs/guides/dia-integration-guide.md` (future)
- **Performance**: See `docs/decisions/ADR-019-dia-performance-optimization.md` (future)

## Version History

- **1.0.0** (2024-10-24): Initial release
  - Two-stage LLM planning (Stage 1 + Stage 2)
  - RabbitMQ event consumption
  - OpenAI GPT-4o-mini integration
  - Health checks and monitoring
  - Docker deployment
