# LLM Orchestrator Service

DIA (Dynamic Intelligence Augmentation) service for intelligent verification orchestration with two-stage planning and multi-tool execution.

## Features

- **Two-Stage DIA Planning**:
  - **Stage 1**: Root Cause Analysis - Transform vague uncertainty into precise problem diagnosis
  - **Stage 2**: Plan Generation - Create structured verification strategies
  - LLM-powered reasoning with OpenAI GPT-4

- **Parallel Tool Execution**:
  - Execute multiple verification tools concurrently
  - Aggregate evidence from diverse sources
  - Calculate confidence scores based on source reliability

- **Verification Tools**:
  - **Perplexity Deep Search**: Web-based fact verification with automatic citations
  - **Financial Data Lookup**: Real-time and historical financial data (Alpha Vantage)

- **RabbitMQ Integration**: Consume verification.required events from content-analysis-service
- **Evidence Aggregation**: Structured evidence packages with key findings and corrected facts
- **Source Quality Scoring**: Categorize sources (primary/authoritative/secondary)

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required API keys:
```bash
OPENAI_API_KEY=sk-xxx           # Required for DIA Planner
PERPLEXITY_API_KEY=pplx-xxx     # Optional (falls back to OPENAI_API_KEY)
ALPHA_VANTAGE_API_KEY=xxx       # Optional (uses demo key if not set)
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Dependencies

```bash
# PostgreSQL (for metadata)
docker run -d --name orchestrator-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=orchestrator_db \
  -p 5432:5432 postgres:15

# RabbitMQ (for events)
docker run -d --name orchestrator-rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
```

### 4. Initialize Database

```bash
# Database migrations will run automatically on startup
python -m app.main
```

### 5. Start API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8113 --reload
```

## Architecture

### DIA (Dynamic Intelligence Augmentation) Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  Content Analysis Service                    │
│            (Detects low confidence analysis)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ verification.required event
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               LLM Orchestrator Service (Port 8113)          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RabbitMQ Consumer                                    │   │
│  │  - verification_exchange (topic)                      │   │
│  │  - verification_queue                                 │   │
│  │  - Routing: verification.required.*                   │   │
│  └─────────────┬─────────────────────────────────────────┘   │
│                │                                             │
│                ▼                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 1: DIA Planner - Root Cause Analysis         │   │
│  │  ──────────────────────────────────────────          │   │
│  │  Input:  Vague uncertainty factors                   │   │
│  │  Output: Precise problem hypothesis                  │   │
│  │  LLM:    OpenAI GPT-4 (temp=0.2)                     │   │
│  └─────────────┬─────────────────────────────────────────┘   │
│                │                                             │
│                ▼                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 2: DIA Planner - Plan Generation             │   │
│  │  ──────────────────────────────────────────          │   │
│  │  Input:  Problem hypothesis                          │   │
│  │  Output: Verification plan with tool calls           │   │
│  │  LLM:    OpenAI GPT-4 (temp=0.2)                     │   │
│  └─────────────┬─────────────────────────────────────────┘   │
│                │                                             │
│                ▼                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DIA Verifier - Parallel Tool Execution             │   │
│  │  ──────────────────────────────────────────          │   │
│  │  • Parse verification methods                         │   │
│  │  • Execute tools in parallel (asyncio.gather)        │   │
│  │  • Aggregate results into EvidencePackage            │   │
│  └─────────────┬─────────────────────────────────────────┘   │
│                │                                             │
│                ▼                                             │
│  ┌──────────────────────┬──────────────────────────────┐   │
│  │  Perplexity Tool      │  Financial Data Tool         │   │
│  │  ───────────────      │  ──────────────────          │   │
│  │  • sonar-pro model    │  • Alpha Vantage API         │   │
│  │  • Domain filtering   │  • Quote, Earnings           │   │
│  │  • Auto-citations     │  • Period filtering          │   │
│  └──────────────────────┴──────────────────────────────┘   │
│                │                                             │
│                ▼                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Evidence Package                                     │   │
│  │  ──────────────────                                   │   │
│  │  • Hypothesis confirmation (true/false)              │   │
│  │  • Confidence score (0.0-1.0)                        │   │
│  │  • Key findings (list)                               │   │
│  │  • Corrected facts (dict)                            │   │
│  │  • Source citations (with reliability scores)        │   │
│  │  • Verification quality metrics                      │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## RabbitMQ Integration

The service consumes verification requests from content-analysis-service:

**Exchange**: `verification_exchange` (topic)
**Queue**: `verification_queue` (durable)
**Routing Key**: `verification.required.*`

### Event Format: verification.required

```json
{
  "event_id": "uuid",
  "event_type": "verification.required",
  "analysis_result_id": "uuid",
  "article_id": "uuid",
  "article_title": "Tesla Reports Record Q3 Earnings",
  "article_content": "Full article text...",
  "article_url": "https://example.com/article",
  "article_published_at": "2024-10-15T10:30:00Z",
  "uq_confidence_score": 0.45,
  "uncertainty_factors": [
    "Low confidence in claim accuracy",
    "Numerical claim lacks verification"
  ],
  "analysis_summary": "Current analysis summary",
  "extracted_entities": ["Tesla", "Elon Musk"],
  "category_analysis": "Business",
  "priority": "high"
}
```

### Publishing Verification Request

```python
import pika
import json
from datetime import datetime
from uuid import uuid4

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='verification_exchange', exchange_type='topic', durable=True)

# Publish verification request
event = {
    "event_id": str(uuid4()),
    "event_type": "verification.required",
    "analysis_result_id": str(uuid4()),
    "article_id": str(uuid4()),
    "article_title": "Tesla Reports Record Q3 Earnings",
    "article_content": "Tesla Inc. announced today...",
    "article_url": "https://example.com/tesla-earnings",
    "article_published_at": datetime.utcnow().isoformat(),
    "uq_confidence_score": 0.45,
    "uncertainty_factors": [
        "Low confidence in claim accuracy",
        "Numerical claim lacks verification"
    ],
    "priority": "high"
}

channel.basic_publish(
    exchange='verification_exchange',
    routing_key='verification.required.high',
    body=json.dumps(event)
)

connection.close()
```

## DIA Planning Process

### Stage 1: Root Cause Analysis

Transforms vague uncertainty factors into precise problem diagnosis.

**Input:**
- Article content
- UQ confidence score (0.0-1.0)
- Uncertainty factors (list of vague descriptions)
- Current analysis (potentially incorrect)

**Output (ProblemHypothesis):**
```json
{
  "primary_concern": "Financial figure appears incorrect",
  "affected_content": "Q3 earnings of $5 billion",
  "hypothesis_type": "factual_error",
  "confidence": 0.85,
  "reasoning": "Unusually high compared to historical data",
  "verification_approach": "Cross-reference with official sources"
}
```

**Hypothesis Types:**
- `factual_error` - Incorrect facts or figures
- `source_reliability` - Questionable source credibility
- `temporal_inconsistency` - Timeline doesn't match
- `entity_ambiguity` - Unclear entity identification
- `claim_unverifiable` - Claim cannot be verified
- `contextual_misrepresentation` - Missing important context

### Stage 2: Plan Generation

Creates structured verification strategy based on precise diagnosis.

**Input:**
- Problem hypothesis from Stage 1
- Original verification request
- Available tools

**Output (VerificationPlan):**
```json
{
  "priority": "high",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount', search_domain_filter=['sec.gov', 'ir.tesla.com'])",
    "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
  ],
  "external_sources": [
    "SEC filings",
    "Tesla Investor Relations",
    "Authoritative financial news"
  ],
  "expected_corrections": [
    {
      "field": "earnings",
      "original": "$5 billion",
      "corrected": "$4.2 billion",
      "confidence_improvement": 0.20
    }
  ],
  "estimated_verification_time_seconds": 60
}
```

## Verification Tools

### 1. Perplexity Deep Search

Web-based fact verification with automatic citations.

**API:** Perplexity AI (sonar-pro model)

**Parameters:**
- `query` (required): Search query
- `search_domain_filter` (optional): List of domains to search (e.g., ["sec.gov", "ir.tesla.com"])
- `search_recency_filter` (optional): Time filter ("day", "week", "month", "year")

**Response:**
```json
{
  "tool_name": "perplexity_deep_search",
  "success": true,
  "execution_time_ms": 1523,
  "result_data": {
    "answer": "According to SEC filings, Tesla reported Q3 2024 earnings of...",
    "sources": [
      "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605",
      "https://ir.tesla.com/press-release/tesla-q3-2024-update"
    ],
    "model": "sonar-pro"
  },
  "source_citations": ["https://www.sec.gov/...", "https://ir.tesla.com/..."],
  "confidence": 0.85
}
```

**Confidence Scoring:**
- Base: 0.5 if citations exist, 0.2 if none
- +0.1 per authoritative domain (.gov, .edu, sec.gov, reuters.com)
- +0.2 if all citations match domain filter
- Capped at 0.95 (never 100% certain)

### 2. Financial Data Lookup

Real-time and historical financial data using Alpha Vantage API.

**API:** Alpha Vantage (free tier: 25 req/day, 5 req/min)

**Parameters:**
- `company` (required): Ticker symbol (e.g., "TSLA", "AAPL")
- `metric` (required): "quote", "earnings", "income_statement", "balance_sheet", "cash_flow"
- `period` (optional): For earnings - "Q1 2024", "Q3 2024", "annual"

**Response:**
```json
{
  "tool_name": "financial_data_lookup",
  "success": true,
  "execution_time_ms": 342,
  "result_data": {
    "company": "TSLA",
    "metric": "earnings",
    "period": "Q3 2024",
    "data": {
      "fiscal_date_ending": "2024-09-30",
      "reported_eps": "0.72",
      "estimated_eps": "0.60",
      "surprise": "0.12",
      "surprise_percentage": "20.0",
      "reported_date": "2024-10-23"
    },
    "api_source": "Alpha Vantage"
  },
  "source_citations": [
    "Alpha Vantage Financial Data API",
    "https://ir.tesla.com"
  ],
  "confidence": 0.9
}
```

## Evidence Package

The final output from DIA Verifier:

```json
{
  "verification_request_id": "uuid",
  "problem_hypothesis": {
    "primary_concern": "Financial figure appears incorrect",
    "hypothesis_type": "factual_error",
    "confidence": 0.85
  },
  "verification_plan": {
    "priority": "high",
    "verification_methods": [...]
  },
  "tool_executions": [
    {
      "tool_name": "perplexity_deep_search",
      "success": true,
      "execution_time_ms": 1523,
      "confidence": 0.85
    },
    {
      "tool_name": "financial_data_lookup",
      "success": true,
      "execution_time_ms": 342,
      "confidence": 0.9
    }
  ],
  "total_execution_time_ms": 1865,
  "hypothesis_confirmed": true,
  "confidence_score": 0.87,
  "key_findings": [
    "[Perplexity] According to SEC filings, Tesla reported Q3 2024 earnings of $4.194 billion...",
    "[Financial Data] TSLA reported EPS of 0.72 for period ending 2024-09-30"
  ],
  "corrected_facts": {
    "earnings: $5 billion": {
      "original": "$5 billion",
      "corrected": "$4.194 billion",
      "source": "SEC Filing 10-Q",
      "source_url": "https://www.sec.gov/..."
    }
  },
  "source_citations": [
    {
      "source": "https://www.sec.gov/...",
      "url": "https://www.sec.gov/...",
      "reliability": "primary"
    },
    {
      "source": "https://ir.tesla.com/...",
      "url": "https://ir.tesla.com/...",
      "reliability": "authoritative"
    }
  ],
  "verification_quality": {
    "source_reliability": 0.9,
    "evidence_consistency": 0.85,
    "coverage_completeness": 1.0
  }
}
```

## Database Schema

### verification_requests (PostgreSQL)
- `id` - UUID primary key
- `article_id` - Article being verified
- `analysis_result_id` - Original analysis result
- `uq_confidence_score` - Uncertainty quantification score
- `uncertainty_factors` - JSON array of factors
- `status` - "pending", "processing", "completed", "failed"
- `created_at` - Request timestamp
- `completed_at` - Completion timestamp

### verification_results
- `id` - UUID primary key
- `request_id` - Foreign key to verification_requests
- `hypothesis_type` - Type of problem identified
- `hypothesis_confirmed` - Boolean
- `confidence_score` - Final confidence (0.0-1.0)
- `tool_executions` - JSON array of tool results
- `evidence_package` - Complete evidence (JSON)
- `corrected_facts` - JSON dict of corrections
- `execution_time_ms` - Total processing time
- `created_at` - Result timestamp

**Indexes:**
- Index on `article_id` for quick lookups
- Index on `status` for queue management
- Index on `created_at` for time-based queries

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Test DIA Planner
pytest tests/test_planner.py -v

# Test DIA Verifier
pytest tests/test_verifier.py -v

# Test tools
pytest tests/test_tools.py -v
```

## Monitoring

### Health Check
```bash
curl http://localhost:8113/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "rabbitmq": "connected",
  "consumer": "running",
  "tools": {
    "perplexity": "configured",
    "alpha_vantage": "configured"
  }
}
```

### Prometheus Metrics
- `dia_verifications_total` - Total verification requests processed
- `dia_verification_duration_seconds` - Verification execution time
- `dia_planner_stage1_duration_seconds` - Stage 1 execution time
- `dia_planner_stage2_duration_seconds` - Stage 2 execution time
- `dia_tool_execution_duration_seconds` - Individual tool execution time
- `dia_hypothesis_confirmation_rate` - Percentage of confirmed hypotheses
- `dia_average_confidence_score` - Average confidence scores

### Metrics Endpoint
```bash
curl http://localhost:8113/metrics
```

## Production Deployment

### Docker Build
```bash
docker build -t llm-orchestrator-service:latest .
```

### Docker Run
```bash
docker run -d \
  --name llm-orchestrator-service \
  -p 8113:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e RABBITMQ_URL=amqp://... \
  -e OPENAI_API_KEY=sk-... \
  -e PERPLEXITY_API_KEY=pplx-... \
  -e ALPHA_VANTAGE_API_KEY=... \
  llm-orchestrator-service:latest
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `RABBITMQ_URL` | RabbitMQ connection URL | Required |
| `OPENAI_API_KEY` | OpenAI API key for DIA Planner | Required |
| `OPENAI_MODEL` | OpenAI model | gpt-4-turbo-preview |
| `PERPLEXITY_API_KEY` | Perplexity API key | Falls back to OPENAI_API_KEY |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Uses "demo" if not set |
| `SERVICE_PORT` | API server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `DIA_STAGE1_TEMPERATURE` | Stage 1 LLM temperature | 0.2 |
| `DIA_STAGE2_TEMPERATURE` | Stage 2 LLM temperature | 0.2 |
| `DIA_MAX_RETRIES` | Max LLM retries on failure | 3 |
| `TOOL_TIMEOUT_SECONDS` | Tool execution timeout | 30 |
| `RABBITMQ_VERIFICATION_EXCHANGE` | Exchange name | verification_exchange |
| `RABBITMQ_VERIFICATION_QUEUE` | Queue name | verification_queue |
| `RABBITMQ_VERIFICATION_ROUTING_KEY` | Routing key pattern | verification.required.* |

## Troubleshooting

### RabbitMQ Connection Issues
1. Verify RabbitMQ is running: `docker ps | grep rabbitmq`
2. Check connection URL format: `amqp://user:pass@host:5672/`
3. Verify exchange and queue exist in RabbitMQ UI (http://localhost:15672)
4. Check consumer logs: `docker logs llm-orchestrator-service`

### OpenAI API Errors
1. Verify API key: `echo $OPENAI_API_KEY`
2. Check rate limits in OpenAI dashboard
3. Review LLM response format (expects JSON)
4. Check Stage 1/Stage 2 temperature settings (too high = inconsistent JSON)

### Perplexity API Issues
1. Verify API key: `echo $PERPLEXITY_API_KEY`
2. Check daily quota (varies by plan)
3. Fallback: Uses OPENAI_API_KEY if PERPLEXITY_API_KEY not set
4. Test manually: `curl -H "Authorization: Bearer $PERPLEXITY_API_KEY" https://api.perplexity.ai/...`

### Alpha Vantage Rate Limits
1. Free tier: 25 requests/day, 5 requests/minute
2. Response includes rate limit warning in `Note` field
3. Fallback: Service uses demo key if ALPHA_VANTAGE_API_KEY not set
4. Upgrade: Premium plans available at https://www.alphavantage.co/premium/

### Tool Execution Timeouts
1. Increase `TOOL_TIMEOUT_SECONDS` (default: 30)
2. Check tool logs for specific errors
3. Verify external APIs are responding
4. Consider retry logic for transient failures

### Low Confidence Scores
1. Review source citations quality
2. Check if authoritative domains (.gov, .edu) are being used
3. Verify domain filters in Perplexity calls
4. Consider adjusting confidence calculation thresholds

### Missing Verification Results
1. Check RabbitMQ message delivery
2. Verify consumer is running: `GET /health`
3. Check dead letter queue for failed messages
4. Review consumer logs for processing errors

## License

MIT License

## Documentation

- [Architecture Decision Record: ADR-018](../../docs/decisions/ADR-018-dia-planner-verifier.md)
- [Service Documentation](../../docs/services/llm-orchestrator-service.md)
- [API Documentation](../../docs/api/llm-orchestrator-service-api.md)
