# Research Service Documentation

**Version:** 0.1.0
**Port:** 8003 (8103 in production)
**Status:** Production Ready
**Last Updated:** 2025-12-22

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Documentation](#api-documentation)
4. [Code Structure](#code-structure)
5. [Circuit Breaker & Resilience](#circuit-breaker--resilience)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)
11. [Performance & Optimization](#performance--optimization)
12. [MCP Integration](#mcp-integration)

---

## MCP Integration

**MCP Server**: `mcp-integration-server`
**Port**: `9005`
**Prefix**: `integration:`

The Research Service is accessible via the **mcp-integration-server** for AI/LLM integration.

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `research_query` | Execute AI-powered research query using Perplexity | `query` (required), `model` (sonar/sonar-pro), `max_tokens` |
| `research_batch` | Execute multiple research queries in batch | `queries[]` (required), `model` |
| `get_research_result` | Get research result by task ID | `task_id` (required) |
| `get_research_history` | Get research query history | `limit` |
| `list_research_templates` | List available research templates | - |
| `apply_research_template` | Apply research template with variables | `template_id` (required), `variables` (required) |

### Example Usage (Claude Desktop)

```
# Execute a research query
integration:research_query query="What are the latest developments in AI regulation?"

# Batch research
integration:research_batch queries=["AI regulation EU", "AI regulation US"]

# Get research history
integration:get_research_history limit=10
```

### Cost Information

- `research_query`: ~$0.005 per query
- `research_batch`: ~$0.005 per query
- Other tools: $0 (read-only)

---

## 1. Overview

### Purpose

The Research Service is an AI-powered research microservice that integrates with Perplexity AI to provide deep, contextual research capabilities on news articles, sources, and topics. It offers both standard and structured research modes with cost optimization, caching, and comprehensive analytics.

### Key Features

1. **AI-Powered Research**
   - Integration with Perplexity AI (sonar, sonar-pro, sonar-reasoning-pro models)
   - Three-tier cost optimization (Quick, Standard, Deep)
   - Structured JSON output with Pydantic validation
   - Real-time citations and source tracking

2. **Specialized Research Functions**
   - Feed Source Assessment (credibility, bias, reputation analysis)
   - Fact Checking (claim verification with evidence)
   - Trend Analysis (emerging patterns in news coverage)
   - 12 additional research functions (deep analysis, expert identification, timeline generation, etc.)

3. **Cost Management**
   - Intelligent cost optimization across three tiers
   - Budget tracking (daily/monthly limits)
   - Usage analytics with recommendations
   - Cache-first strategies to minimize API costs

4. **Template System**
   - Reusable research templates with variable substitution
   - Public and private template sharing
   - Usage statistics tracking
   - Scheduled/recurring research runs

5. **Performance Optimization**
   - Circuit breaker pattern for API failures
   - Multi-level caching (Redis + PostgreSQL)
   - Async processing with Celery workers
   - Health check caching (60s TTL)

### Dependencies

**Core Framework:**
- FastAPI 0.115.0
- Uvicorn 0.30.0
- Pydantic 2.8.0

**Database:**
- PostgreSQL (SQLAlchemy 2.0.35)
- Alembic 1.13.0 (migrations)
- Redis 5.0.1 (caching)

**Message Queue:**
- Celery 5.3.4 (async workers)
- RabbitMQ (via aio-pika 9.4.0)

**AI/Research:**
- Perplexity AI API
- Circuit breaker (news-mcp-common)

**Authentication:**
- JWT (python-jose 3.3.0)
- Shared auth service integration

---

## 2. Architecture

### Component Diagram

```mermaid
graph TB
    subgraph "Research Service (Port 8103)"
        API[FastAPI Application]
        RESEARCH[Research Service]
        TEMPLATE[Template Service]
        COST[Cost Optimizer]
        PERPLEXITY[Perplexity Client]

        API --> RESEARCH
        API --> TEMPLATE
        RESEARCH --> COST
        RESEARCH --> PERPLEXITY
        TEMPLATE --> RESEARCH
    end

    subgraph "External Services"
        AUTH[Auth Service]
        FEED[Feed Service]
        ANALYSIS[Content Analysis]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        CELERY[Celery Workers]
    end

    subgraph "External APIs"
        PPLX[Perplexity AI API]
    end

    API --> AUTH
    RESEARCH --> FEED
    RESEARCH --> ANALYSIS
    RESEARCH --> POSTGRES
    RESEARCH --> REDIS
    RESEARCH --> CELERY
    PERPLEXITY --> PPLX
    CELERY --> POSTGRES

    style API fill:#4A90E2
    style RESEARCH fill:#50C878
    style COST fill:#FFD700
    style PERPLEXITY fill:#FF6B6B
    style PPLX fill:#FF6B6B
```

### Data Flow

**Standard Research Request:**
```
User Request
    → API Authentication (JWT)
    → Cost Optimization Check
    → Cache Lookup (Redis/PostgreSQL)
    → [Cache Hit] Return cached result
    → [Cache Miss] Queue Celery task
    → Celery Worker:
        - Perplexity API call
        - Parse & validate response
        - Store in cache
        - Update cost tracking
    → Return result to user
```

**Structured Research Request:**
```
User Request + output_schema
    → Validation (Pydantic schema)
    → Celery Worker:
        - Build response_format from schema
        - Perplexity API (JSON mode)
        - Extract & validate JSON
        - Store structured_data
    → Return validated structured data
```

### Integration Points

1. **Auth Service** (Port 8100)
   - JWT token validation
   - User role checking
   - Permission management

2. **Feed Service** (Port 8101)
   - Feed metadata retrieval
   - Article content access
   - Feed source information

3. **Content Analysis Service** (Port 8102)
   - Analysis result linking
   - Article metadata
   - Content extraction

4. **Perplexity AI API**
   - Research queries
   - Citation extraction
   - Structured JSON output

5. **RabbitMQ**
   - Event publishing (research completed)
   - Inter-service messaging

### Database Schema

**Tables:**

1. **research_tasks** - Primary research task tracking
   - Core fields: id, user_id, query, model_name, depth, status
   - Result fields: result (JSON), structured_data (JSON), validation_status
   - Cost tracking: tokens_used, cost
   - Relationships: feed_id (UUID), article_id (UUID), run_id (FK)
   - Legacy support: legacy_feed_id (Integer), legacy_article_id (Integer)

2. **research_templates** - Reusable research templates
   - Template data: name, description, query_template, parameters
   - Configuration: default_model, default_depth, research_function
   - Schema: output_schema (JSON), function_parameters (JSON)
   - Status: is_active, is_public
   - Analytics: usage_count, last_used_at

3. **research_cache** - Query result caching
   - Cache key: cache_key (SHA256 hash)
   - Query info: query, model_name, depth
   - Cached data: result (JSON), tokens_used, cost
   - Management: hit_count, expires_at, last_accessed_at

4. **research_runs** - Scheduled research executions
   - Configuration: template_id (FK), parameters, model_name, depth
   - Scheduling: scheduled_at, is_recurring, recurrence_pattern
   - Status tracking: status, started_at, completed_at
   - Results: tasks_created, tasks_completed, tasks_failed
   - Aggregates: total_tokens_used, total_cost, results_summary

5. **cost_tracking** - Cost analytics and billing
   - User tracking: user_id, date
   - Usage data: model_name, tokens_used, cost, request_count
   - References: task_id (FK), run_id (FK)

**Indexes:**
- `ix_research_tasks_user_status` - Fast user task queries
- `ix_research_tasks_created` - Chronological sorting
- `ix_research_tasks_run_id` - Run association
- `ix_research_templates_user_active` - Active template lookup
- `ix_research_runs_scheduled` - Scheduled run processing
- `ix_research_cache_expires_at` - Cache cleanup

---

## 3. API Documentation

### Base Information

- **Base URL:** `http://localhost:8103/api/v1` (dev), `http://research-service:8000/api/v1` (docker)
- **Authentication:** Bearer JWT token (required for all endpoints)
- **Content-Type:** `application/json`
- **OpenAPI Spec:** Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### Endpoints Overview

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Health** | `/health` | GET | Health check with component status |
| **Status** | `/status/rate-limits` | GET | Rate limiting and cost control status |
| **Metrics** | `/metrics` | GET | Prometheus metrics (if enabled) |
| **Research** | `/api/v1/research` | POST | Create research task |
| **Research** | `/api/v1/research/{task_id}` | GET | Get task by ID |
| **Research** | `/api/v1/research` | GET | List tasks (paginated) |
| **Research** | `/api/v1/research/batch` | POST | Batch create tasks |
| **Research** | `/api/v1/research/feed/{feed_id}` | GET | Get tasks for feed |
| **Research** | `/api/v1/research/history` | GET | Get research history |
| **Research** | `/api/v1/research/stats` | GET | Get usage statistics |
| **Templates** | `/api/v1/templates` | POST | Create template |
| **Templates** | `/api/v1/templates` | GET | List templates |
| **Templates** | `/api/v1/templates/{id}` | GET | Get template by ID |
| **Templates** | `/api/v1/templates/{id}` | PUT | Update template |
| **Templates** | `/api/v1/templates/{id}` | DELETE | Delete template |
| **Templates** | `/api/v1/templates/{id}/preview` | POST | Preview template |
| **Templates** | `/api/v1/templates/{id}/apply` | POST | Apply template |
| **Templates** | `/api/v1/templates/functions` | GET | List research functions |
| **Runs** | `/api/v1/runs` | POST | Create research run |
| **Runs** | `/api/v1/runs/{run_id}` | GET | Get run by ID |
| **Runs** | `/api/v1/runs/{run_id}/status` | GET | Get run status |
| **Runs** | `/api/v1/runs` | GET | List runs (paginated) |
| **Runs** | `/api/v1/runs/{run_id}/cancel` | POST | Cancel run |
| **Runs** | `/api/v1/runs/template/{template_id}` | GET | Get runs for template |

#### GET /status/rate-limits - Rate Limiting Status

**Response (200 OK):**
```json
{
  "service": "research-service",
  "rate_limiting": {
    "enabled": true,
    "authenticated_user": {
      "per_minute": 10,
      "per_hour": 500,
      "description": "Limits applied to authenticated users (JWT token)"
    },
    "unauthenticated": {
      "per_minute": 5,
      "per_hour": 250,
      "description": "Limits applied to unauthenticated requests"
    },
    "note": "Unauthenticated limits are 50% of authenticated limits for fairness"
  },
  "cost_control": {
    "enabled": true,
    "per_request_limit": "$1.00",
    "daily_limit": "$50.00",
    "monthly_limit": "$1000.00",
    "alert_threshold": "80%",
    "description": "Cost limits to prevent runaway API expenses"
  },
  "perplexity_api": {
    "model": "sonar",
    "timeout_seconds": 60,
    "max_retries": 3,
    "description": "Perplexity AI API configuration"
  }
}
```

**Purpose:**
- View current rate limiting rules for authenticated and unauthenticated users
- Check cost control settings
- Verify Perplexity API configuration

### Key Endpoints Detail

#### POST /api/v1/research - Create Research Task

**Request:**
```json
{
  "query": "Analyze the credibility of example.com as a news source",
  "model_name": "sonar",
  "depth": "standard",
  "feed_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440001",
  "research_function": "feed_source_assessment",
  "function_parameters": {
    "domain": "example.com",
    "include_bias_analysis": true
  }
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "user_id": 1,
  "query": "Analyze the credibility of example.com...",
  "model_name": "sonar",
  "depth": "standard",
  "status": "pending",
  "result": null,
  "structured_data": null,
  "validation_status": null,
  "tokens_used": 0,
  "cost": 0.0,
  "feed_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440001",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z",
  "completed_at": null
}
```

**Supported Models:**
- `sonar` - Fast, cost-effective (default)
- `sonar-pro` - Advanced reasoning
- `sonar-reasoning-pro` - Highest quality

**Depth Levels:**
- `quick` - Simple queries, cache-first
- `standard` - Balanced approach (default)
- `deep` - Comprehensive research

#### GET /api/v1/research/{task_id} - Get Task Status

**Response (200 OK):**
```json
{
  "id": 123,
  "user_id": 1,
  "query": "...",
  "model_name": "sonar",
  "depth": "standard",
  "status": "completed",
  "result": {
    "content": "Research findings...",
    "citations": ["https://example.com/article1"],
    "sources": [
      {
        "url": "https://example.com/article1",
        "title": "Article Title",
        "snippet": "Relevant excerpt..."
      }
    ],
    "tokens_used": 1234,
    "cost": 0.0062,
    "model": "sonar",
    "timestamp": "2025-11-24T10:31:30Z"
  },
  "structured_data": {
    "credibility_tier": "tier_1",
    "reputation_score": 85,
    "founded_year": 2010,
    "organization_type": "traditional_media",
    "category": "General News",
    "editorial_standards": {
      "fact_checking_level": "high",
      "corrections_policy": "transparent",
      "source_attribution": "good"
    },
    "trust_ratings": {
      "media_bias_fact_check": "Least Biased",
      "allsides_rating": "Center",
      "newsguard_score": 90
    },
    "political_bias": "center",
    "recommendation": {
      "skip_waiting_period": true,
      "initial_quality_boost": 15,
      "bot_detection_threshold": "normal"
    },
    "summary": "Highly credible source..."
  },
  "validation_status": "valid",
  "tokens_used": 1234,
  "cost": 0.0062,
  "completed_at": "2025-11-24T10:31:30Z"
}
```

**Status Values:**
- `pending` - Queued for processing
- `processing` - Currently being processed
- `completed` - Successfully completed
- `failed` - Processing failed (see error_message)

#### POST /api/v1/templates - Create Template

**Request:**
```json
{
  "name": "Feed Source Assessment",
  "description": "Assess credibility and bias of news sources",
  "query_template": "Analyze the news source at {{domain}}",
  "parameters": {
    "domain": "string",
    "include_bias_analysis": "boolean"
  },
  "default_model": "sonar",
  "default_depth": "standard",
  "is_public": false,
  "research_function": "feed_source_assessment",
  "function_parameters": {
    "include_bias_analysis": true
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "credibility_tier": {"type": "string"},
      "reputation_score": {"type": "integer"}
    }
  }
}
```

**Response (201 Created):**
```json
{
  "id": 42,
  "user_id": 1,
  "name": "Feed Source Assessment",
  "description": "Assess credibility and bias...",
  "query_template": "Analyze the news source at {{domain}}",
  "parameters": {
    "domain": "string",
    "include_bias_analysis": "boolean"
  },
  "default_model": "sonar",
  "default_depth": "standard",
  "is_active": true,
  "is_public": false,
  "usage_count": 0,
  "last_used_at": null,
  "research_function": "feed_source_assessment",
  "function_parameters": {
    "include_bias_analysis": true
  },
  "output_schema": {...},
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

#### GET /health - Health Check

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "research-service",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok (2 workers)",
    "perplexity_api": "ok"
  }
}
```

**Response (degraded, 200 OK):**
```json
{
  "status": "degraded",
  "service": "research-service",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "no workers",
    "perplexity_api": "ok"
  }
}
```

### Specialized Research Functions

Available via `research_function` parameter:

1. **feed_source_assessment** - Assess news source credibility
   - Parameters: domain, include_bias_analysis
   - Output: Structured assessment with credibility tier, reputation score, bias analysis

2. **fact_check** - Verify claims with evidence
   - Parameters: claim, detailed, include_context
   - Output: Verdict, confidence, supporting/contradicting evidence

3. **trend_analysis** - Analyze news coverage trends
   - Parameters: topic, timeframe, include_geographic, include_narratives
   - Output: Trend strength, coverage intensity, geographic distribution

4. **deep_article_analysis** - Comprehensive article analysis
   - Parameters: article_title, article_content, article_url
   - Output: Main arguments, evidence quality, implications

5. **source_verification** - Verify source reliability
   - Parameters: sources (list), domain
   - Output: Authority, bias, credibility scores per source

6. **topic_extraction** - Extract topics and themes
   - Parameters: content, max_topics
   - Output: Topic hierarchy, relevance scores, semantic clusters

7. **related_content_discovery** - Find related articles
   - Parameters: topic, keywords, timeframe
   - Output: Related articles with URLs, summaries, relevance

8. **timeline_generation** - Create event timelines
   - Parameters: topic, start_date, end_date
   - Output: Chronological events with context

9. **expert_identification** - Find domain experts
   - Parameters: field, sub_topics
   - Output: Expert profiles with credentials, publications

10. **statistical_analysis** - Analyze data and trends
    - Parameters: topic, metrics
    - Output: Statistics, trends, projections

11. **claim_verification** - Verify specific claims
    - Parameters: claim, context
    - Output: Truthfulness assessment, evidence, confidence

12. **comparative_analysis** - Compare topics/approaches
    - Parameters: items (list), comparison_aspects
    - Output: Similarities, differences, recommendations

13. **impact_assessment** - Assess impact of events
    - Parameters: event_or_decision, stakeholders
    - Output: Immediate/long-term effects, implications

---

## 4. Code Structure

### Directory Tree

```
research-service/
├── alembic/                          # Database migrations
│   ├── env.py                        # Alembic environment config
│   └── versions/                     # Migration scripts
│       ├── 05b988c45bf9_*.py        # Add legacy ID fields
│       ├── 20251020_*.py            # Add output schema
│       └── d0ee82864a00_*.py        # Structured output support
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry
│   ├── api/                          # API endpoints
│   │   ├── __init__.py              # Router aggregation
│   │   ├── research.py              # Research task endpoints
│   │   ├── templates.py             # Template management
│   │   └── runs.py                  # Research run endpoints
│   ├── core/                         # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (Pydantic)
│   │   ├── database.py              # SQLAlchemy setup
│   │   └── auth.py                  # JWT authentication
│   ├── models/                       # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── research.py              # All database models
│   ├── schemas/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   └── research.py              # Request/response schemas
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   ├── research.py              # Core research service
│   │   ├── perplexity.py            # Perplexity AI client
│   │   ├── cost_optimizer.py        # 3-tier cost optimization
│   │   ├── specialized_functions.py # Structured research functions
│   │   ├── function_registry.py     # Function discovery
│   │   ├── run_service.py           # Research run management
│   │   ├── template_engine.py       # Template rendering
│   │   └── source_scorer.py         # Source credibility scoring
│   └── workers/                      # Async task processing
│       ├── __init__.py
│       ├── celery_app.py            # Celery configuration
│       └── tasks.py                 # Celery tasks
├── tests/                            # Test suite (5,455 lines)
│   ├── conftest.py                  # Pytest configuration
│   ├── test_api_endpoints.py       # API integration tests
│   ├── test_caching.py             # Cache functionality
│   ├── test_cost_optimization.py   # Cost optimizer tests
│   ├── test_error_handling.py      # Error scenarios
│   ├── test_health.py              # Health check tests
│   ├── test_integration.py         # Full integration tests
│   ├── test_models.py              # Database model tests
│   ├── test_perplexity.py          # Perplexity client tests
│   ├── test_research.py            # Research service tests
│   ├── test_specialized_functions.py # Function tests
│   ├── test_tasks.py               # Celery task tests
│   └── test_templates.py           # Template system tests
├── examples/
│   └── template_engine_demo.py      # Template usage examples
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── celery_worker.py                  # Celery worker entry
├── Dockerfile.dev                    # Development Docker image
├── .env.example                      # Environment template
└── README.md                         # Service documentation
```

### Key Components

#### 1. **app/main.py** - FastAPI Application
- Application lifecycle management (startup/shutdown)
- Database initialization
- Perplexity API health check
- CORS middleware configuration
- Global error handlers (404, 500)
- Health check endpoint with caching (60s TTL)

#### 2. **app/services/research.py** - Core Research Logic
- **ResearchFunction** base class for specialized functions
- **ResearchService** - Main research orchestration
  - Task creation with cost optimization
  - Cache management (Redis + PostgreSQL)
  - Cost limit enforcement
  - Celery task dispatching
- **TemplateService** - Template CRUD operations
- 12 pre-built research functions (DeepArticleAnalysis, FactChecking, etc.)

#### 3. **app/services/perplexity.py** - Perplexity AI Client
- **Circuit breaker pattern (Task 406):**
  - Uses `ResilientHTTPClient` from `news-mcp-common`
  - Failure threshold: 3 consecutive failures
  - Success threshold: 2 successes to close circuit
  - Timeout: 120 seconds (2 minutes before half-open retry)
  - Protects against cascading failures and cost escalation
  - Throws `CircuitBreakerOpenError` when circuit is open
- **Health check caching (60s TTL, Task 404):**
  - Reduces /health endpoint latency from 1.19s to <50ms
  - Time-based cache (not functools.lru_cache due to async)
  - Caches both success and failure states
  - Failures cached for shorter TTL (10s) for faster recovery
- Exponential backoff retry logic (2^attempt seconds)
- Structured output support (JSON schema mode)
- Citation and source extraction
- Cost calculation per request

#### 4. **app/services/cost_optimizer.py** - 3-Tier Cost System
- **CostTier enum:** QUICK, STANDARD, DEEP
- Intelligent tier selection based on:
  - User preference
  - Query complexity estimation
  - Budget remaining
  - Cache availability
- Budget limit checking (daily/monthly)
- Usage analytics with recommendations
- Cache freshness scoring

#### 5. **app/services/specialized_functions.py** - Structured Research
- **FeedSourceAssessment** - Credibility analysis
- **FactCheckFunction** - Claim verification
- **TrendAnalysisFunction** - News trend analysis
- Pydantic output schemas for validation
- Prompt engineering for structured JSON

#### 6. **app/workers/tasks.py** - Celery Tasks
- **research_task** - Process single research request
- **scheduled_research_task** - Run scheduled research
- **batch_research_task** - Process multiple tasks
- **cache_cleanup_task** - Remove expired cache entries
- **cost_aggregation_task** - Daily cost summaries
- Structured data extraction from JSON responses

---

## 5. Circuit Breaker & Resilience

### Circuit Breaker Implementation (Task 406)

The research service implements circuit breaker pattern for Perplexity API calls to prevent cascading failures and cost escalation.

**Configuration (app/services/perplexity.py):**
```python
cb_config = CircuitBreakerConfig(
    failure_threshold=3,      # Open after 3 failures (API errors/rate limits)
    success_threshold=2,      # Close after 2 successes
    timeout_seconds=120,      # Wait 2 minutes before retry (respects rate limits)
    enable_metrics=True,      # Track circuit breaker metrics
)
```

**Circuit States:**

1. **CLOSED (Normal Operation)**
   - All requests pass through to Perplexity API
   - Failure counter increments on errors (HTTP 429, 500, timeouts)
   - Opens circuit when `failure_threshold` (3) is reached

2. **OPEN (Circuit Tripped)**
   - All requests fail immediately with `CircuitBreakerOpenError`
   - No API calls made (prevents cost escalation)
   - Service returns "circuit breaker is OPEN" error
   - Health check reports API as unavailable
   - Waits `timeout_seconds` (120s) before attempting recovery

3. **HALF-OPEN (Testing Recovery)**
   - After 120s timeout, allows limited requests through
   - If `success_threshold` (2) consecutive successes: Close circuit
   - If any failure: Reopen circuit for another 120s

**Error Handling:**

```python
try:
    result = await perplexity_client.research(query, model="sonar")
except CircuitBreakerOpenError:
    # Circuit is open - stop trying immediately
    logger.error("Perplexity API circuit breaker is OPEN")
    raise HTTPException(
        status_code=503,
        detail="Research service temporarily unavailable - circuit breaker open"
    )
```

**Benefits:**

1. **Cost Protection:** Prevents runaway API costs during outages
2. **Fast Failure:** Immediate error response instead of waiting for timeout
3. **Automatic Recovery:** Self-healing after successful requests
4. **Service Stability:** Prevents cascading failures across microservices
5. **Rate Limit Respect:** 120s timeout respects Perplexity rate limits

**Monitoring:**

```bash
# Check circuit breaker status
curl http://localhost:8103/health | jq '.checks.perplexity_api'

# View circuit breaker metrics (if Prometheus enabled)
curl http://localhost:8103/metrics | grep circuit_breaker
```

### Perplexity API Integration

**API Details:**
- **Base URL:** https://api.perplexity.ai
- **Endpoint:** `/chat/completions` (OpenAI-compatible)
- **Authentication:** Bearer token (PERPLEXITY_API_KEY)
- **Timeout:** 60 seconds default
- **Max Retries:** 3 attempts with exponential backoff

**Request Flow:**

1. **Request Preparation:**
   - Model selection (sonar, sonar-pro, sonar-reasoning-pro)
   - Depth-based temperature: quick (0.3), standard (0.5), deep (0.7)
   - Recency filter: day, week, or month
   - Max tokens from model config

2. **Circuit Breaker Check:**
   - If circuit OPEN: Fail immediately
   - If circuit CLOSED/HALF-OPEN: Proceed

3. **API Call with Retry:**
   ```python
   for attempt in range(max_retries):
       try:
           response = await resilient_client.post("/chat/completions", ...)
           return parse_response(response)
       except CircuitBreakerOpenError:
           raise  # Stop immediately
       except HTTPStatusError as e:
           if e.status_code == 429:  # Rate limit
               await backoff(attempt)  # Wait 2^attempt seconds
               continue
           raise
   ```

4. **Response Processing:**
   - Extract content, citations, sources
   - Calculate token usage and cost
   - Validate structured output (if JSON schema provided)
   - Store in cache for future requests

**Structured Output (JSON Mode):**

The service supports structured JSON responses via Perplexity's response_format:

```python
# Define Pydantic schema
class SourceAssessment(BaseModel):
    credibility_tier: str
    reputation_score: int
    political_bias: str

# Request with schema
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "source_assessment",
        "schema": SourceAssessment.model_json_schema()
    }
}

result = await perplexity_client.research(
    query="Assess reuters.com",
    response_format=response_format
)
```

**Citation Extraction:**

Perplexity returns citations in the response:
```json
{
  "citations": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "snippet": "Relevant excerpt..."
    }
  ]
}
```

Service deduplicates citations and extracts unique sources for better UX.

**Cost Calculation:**

Token usage is multiplied by model's cost per 1K tokens:
- sonar: $0.005 per 1K tokens
- sonar-pro: $0.015 per 1K tokens
- sonar-reasoning-pro: $0.025 per 1K tokens

Example: 2,000 tokens on sonar = (2000 / 1000) * 0.005 = $0.01

---

## 6. Configuration

### Environment Variables

**Service Configuration:**
```bash
SERVICE_NAME=research-service
SERVICE_VERSION=0.1.0
SERVICE_PORT=8000
DEBUG=false
ENVIRONMENT=development  # development|staging|production
```

**API Settings:**
```bash
API_V1_PREFIX=/api/v1
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
```

**Database:**
```bash
DATABASE_URL=postgresql://news_user:your_db_password@localhost:5432/news_mcp
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
```

**Redis Cache:**
```bash
REDIS_URL=redis://:redis_secret_2024@localhost:6379/0
REDIS_CACHE_TTL=604800  # 7 days
CACHE_ENABLED=true
CACHE_RESEARCH_RESULTS_TTL=604800  # 7 days
CACHE_TEMPLATE_RESULTS_TTL=86400   # 1 day
```

**RabbitMQ:**
```bash
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_ROUTING_KEY_PREFIX=research
```

**Celery:**
```bash
CELERY_BROKER_URL=redis://:redis_secret_2024@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:redis_secret_2024@localhost:6379/2
CELERY_TASK_ALWAYS_EAGER=false
CELERY_TASK_EAGER_PROPAGATES=false
```

**Authentication:**
```bash
AUTH_SERVICE_URL=http://localhost:8000
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Service Integration:**
```bash
FEED_SERVICE_URL=http://localhost:8001
ANALYSIS_SERVICE_URL=http://localhost:8002
```

**Perplexity AI:**
```bash
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PERPLEXITY_BASE_URL=https://api.perplexity.ai
PERPLEXITY_DEFAULT_MODEL=sonar
PERPLEXITY_TIMEOUT=60
PERPLEXITY_MAX_RETRIES=3
```

**Cost Management:**
```bash
ENABLE_COST_TRACKING=true
MAX_COST_PER_REQUEST=1.0
MAX_DAILY_COST=50.0
MAX_MONTHLY_COST=1000.0
COST_ALERT_THRESHOLD=0.8  # Alert at 80% of limit

# Cost Optimization
ENABLE_COST_OPTIMIZATION=true
DEFAULT_COST_TIER=standard  # quick|standard|deep
AUTO_DOWNGRADE_ON_BUDGET_LIMIT=true
CACHE_PREFERENCE_THRESHOLD=0.6
```

**Rate Limiting:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10
RATE_LIMIT_REQUESTS_PER_HOUR=500
RATE_LIMIT_REQUESTS_PER_DAY=5000
```

**Research Configuration:**
```bash
MAX_QUERY_LENGTH=2000
DEFAULT_RESEARCH_DEPTH=standard  # quick|standard|deep
BATCH_SIZE=5
RESEARCH_TIMEOUT=300
MAX_TEMPLATES_PER_USER=50
TEMPLATE_VALIDATION_ENABLED=true
```

**Observability:**
```bash
ENABLE_TRACING=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces
LOG_LEVEL=INFO  # DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FORMAT=json  # json|text
```

### Model Configuration

Defined in `app/core/config.py`:

```python
PERPLEXITY_MODELS = {
    "sonar": {
        "name": "sonar",
        "cost_per_1k_tokens": 0.005,
        "max_tokens": 4000,
        "description": "Fast, cost-effective model for general research"
    },
    "sonar-pro": {
        "name": "sonar-pro",
        "cost_per_1k_tokens": 0.015,
        "max_tokens": 8000,
        "description": "Advanced model with better reasoning"
    },
    "sonar-reasoning-pro": {
        "name": "sonar-reasoning-pro",
        "cost_per_1k_tokens": 0.025,
        "max_tokens": 16000,
        "description": "Highest quality model for complex research"
    }
}
```

---

## 7. Usage Examples

### Example 1: Simple Research Query

```python
import httpx

# Authenticate
auth_response = httpx.post("http://localhost:8100/api/v1/auth/login", json={
    "email": "andreas@test.com",
    "password": "Aug2012#"
})
token = auth_response.json()["access_token"]

# Create research task
response = httpx.post(
    "http://localhost:8103/api/v1/research",
    json={
        "query": "What are the latest developments in renewable energy?",
        "model_name": "sonar",
        "depth": "standard"
    },
    headers={"Authorization": f"Bearer {token}"}
)

task = response.json()
task_id = task["id"]

# Poll for completion
import time
while True:
    status_response = httpx.get(
        f"http://localhost:8103/api/v1/research/{task_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    task = status_response.json()

    if task["status"] == "completed":
        print(f"Research completed!")
        print(f"Result: {task['result']['content']}")
        print(f"Cost: ${task['cost']:.4f}")
        break
    elif task["status"] == "failed":
        print(f"Research failed: {task['error_message']}")
        break

    time.sleep(2)
```

### Example 2: Feed Source Assessment

```python
# Assess news source credibility
response = httpx.post(
    "http://localhost:8103/api/v1/research",
    json={
        "query": "Assess the credibility of reuters.com",
        "model_name": "sonar",
        "depth": "standard",
        "research_function": "feed_source_assessment",
        "function_parameters": {
            "domain": "reuters.com",
            "include_bias_analysis": true,
            "include_publication_patterns": true
        }
    },
    headers={"Authorization": f"Bearer {token}"}
)

task = response.json()
# Wait for completion...

# Access structured data
assessment = task["structured_data"]
print(f"Credibility Tier: {assessment['credibility_tier']}")
print(f"Reputation Score: {assessment['reputation_score']}/100")
print(f"Political Bias: {assessment['political_bias']}")
print(f"Founded: {assessment['founded_year']}")
```

### Example 3: Using Templates

```python
# Create reusable template
template_response = httpx.post(
    "http://localhost:8103/api/v1/templates",
    json={
        "name": "Market Analysis",
        "description": "Analyze market trends for specific sectors",
        "query_template": "Analyze market trends in the {{sector}} sector over the last {{timeframe}}",
        "parameters": {
            "sector": "string",
            "timeframe": "string"
        },
        "default_model": "sonar-pro",
        "default_depth": "deep"
    },
    headers={"Authorization": f"Bearer {token}"}
)

template = template_response.json()
template_id = template["id"]

# Apply template with variables
apply_response = httpx.post(
    f"http://localhost:8103/api/v1/templates/{template_id}/apply",
    json={
        "variables": {
            "sector": "renewable energy",
            "timeframe": "6 months"
        }
    },
    headers={"Authorization": f"Bearer {token}"}
)

task = apply_response.json()
```

### Example 4: Batch Research

```python
# Create multiple research tasks
batch_response = httpx.post(
    "http://localhost:8103/api/v1/research/batch",
    json={
        "queries": [
            "Latest AI developments in healthcare",
            "Climate change policy updates 2025",
            "Cybersecurity trends in finance"
        ],
        "model_name": "sonar",
        "depth": "standard"
    },
    headers={"Authorization": f"Bearer {token}"}
)

tasks = batch_response.json()
for task in tasks:
    print(f"Task {task['id']}: {task['status']}")
```

### Example 5: Cost Optimization

```python
# Get usage analytics
stats_response = httpx.get(
    "http://localhost:8103/api/v1/research/stats?days=30",
    headers={"Authorization": f"Bearer {token}"}
)

stats = stats_response.json()
print(f"Total Cost (30 days): ${stats['total_cost']:.2f}")
print(f"Total Requests: {stats['total_requests']}")
print(f"Avg Cost/Request: ${stats['total_cost']/stats['total_requests']:.4f}")
print(f"\nCost by Model:")
for model, cost in stats['cost_by_model'].items():
    print(f"  {model}: ${cost:.2f}")
```

### Example 6: Scheduled Research

```python
from datetime import datetime, timedelta

# Create scheduled research run
run_response = httpx.post(
    "http://localhost:8103/api/v1/runs",
    json={
        "template_id": template_id,
        "parameters": {
            "sector": "technology",
            "timeframe": "week"
        },
        "model_name": "sonar",
        "depth": "standard",
        "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "is_recurring": True,
        "recurrence_pattern": "daily",
        "metadata": {
            "purpose": "Daily tech sector monitoring"
        }
    },
    headers={"Authorization": f"Bearer {token}"}
)

run = run_response.json()
print(f"Scheduled run {run['id']} will execute at {run['scheduled_at']}")
```

---

## 8. Deployment

### Docker Deployment

**Development (docker-compose.yml):**
```yaml
research-service:
  build:
    context: .
    dockerfile: ./services/research-service/Dockerfile.dev
  container_name: news-research-service
  restart: unless-stopped
  pids_limit: 512
  command: >
    sh -c "pip install --quiet -e /app/shared/news-mcp-common &&
           uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
  env_file:
    - ./services/research-service/.env
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: 5432
    REDIS_HOST: redis
    REDIS_PORT: 6379
  ports:
    - "8103:8000"
  volumes:
    - ./services/research-service:/app
    - ./shared:/app/shared
  depends_on:
    - postgres
    - redis
    - auth-service
  networks:
    - news-network

research-celery-worker:
  build:
    context: .
    dockerfile: ./services/research-service/Dockerfile.dev
  container_name: news-research-celery-worker
  restart: unless-stopped
  command: >
    sh -c "pip install --quiet -e /app/shared/news-mcp-common &&
           celery -A app.workers.celery_app worker --loglevel=info"
  env_file:
    - ./services/research-service/.env
  volumes:
    - ./services/research-service:/app
    - ./shared:/app/shared
  depends_on:
    - postgres
    - redis
    - research-service
  networks:
    - news-network
```

**Production (docker-compose.prod.yml):**
```yaml
research-service:
  image: news-research-service:latest
  restart: always
  environment:
    ENVIRONMENT: production
    DEBUG: false
    LOG_LEVEL: INFO
  deploy:
    replicas: 2
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
```

### Health Checks

**Docker Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Kubernetes Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Kubernetes Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

### Scaling Considerations

1. **Horizontal Scaling:**
   - Stateless API servers (scale to N instances)
   - Celery workers (scale based on queue depth)
   - Shared Redis cache for consistency

2. **Vertical Scaling:**
   - Memory: 512MB - 1GB per API instance
   - CPU: 0.5 - 1.0 cores per instance
   - Celery workers: 1GB+ memory for Perplexity API responses

3. **Database:**
   - Connection pool: 10 connections per API instance
   - Max overflow: 20 connections
   - Read replicas for analytics queries

4. **Cache:**
   - Redis memory: 2GB+ for 7-day cache TTL
   - Eviction policy: allkeys-lru
   - Maxmemory: 4GB recommended

---

## 9. Troubleshooting

### Common Issues

#### 1. **Perplexity API Failures**

**Symptoms:**
- Circuit breaker OPEN errors
- 429 rate limit errors
- Timeout errors

**Diagnosis:**
```bash
# Check circuit breaker status
curl http://localhost:8103/health | jq '.checks.perplexity_api'

# Check logs
docker logs news-research-service | grep "circuit breaker"
```

**Solutions:**
1. **Circuit Breaker Open:**
   - Wait 120 seconds for circuit to half-open
   - Check Perplexity API status
   - Verify API key is valid

2. **Rate Limits:**
   - Reduce `PERPLEXITY_MAX_RETRIES`
   - Increase cache TTL
   - Use Quick tier for simple queries

3. **Timeouts:**
   - Increase `PERPLEXITY_TIMEOUT` (default: 60s)
   - Check network connectivity
   - Monitor Perplexity API latency

#### 2. **Celery Worker Not Processing Tasks**

**Symptoms:**
- Tasks stuck in "pending" status
- Health check shows "no workers"

**Diagnosis:**
```bash
# Check Celery workers
celery -A app.workers.celery_app inspect active

# Check worker logs
docker logs news-research-celery-worker

# Check Redis queue
redis-cli -h localhost -p 6379 -a redis_secret_2024
> LLEN celery  # Queue length
```

**Solutions:**
1. **No Workers Running:**
```bash
# Start worker manually
docker-compose up -d research-celery-worker

# Or restart
docker-compose restart research-celery-worker
```

2. **Worker Crashes:**
   - Check logs for memory errors
   - Increase worker memory limit
   - Reduce concurrency: `celery worker --concurrency=2`

3. **Queue Backlog:**
   - Scale up workers: `docker-compose up -d --scale research-celery-worker=3`
   - Check for long-running tasks
   - Purge failed tasks: `celery -A app.workers.celery_app purge`

#### 3. **High Memory Usage**

**Symptoms:**
- OOM kills in Docker
- Slow response times
- Cache evictions

**Diagnosis:**
```bash
# Check service memory
docker stats news-research-service

# Check Redis memory
redis-cli -h localhost -p 6379 -a redis_secret_2024 INFO memory
```

**Solutions:**
1. **API Service:**
   - Reduce connection pool size
   - Enable response streaming for large results
   - Implement request size limits

2. **Redis Cache:**
   - Reduce cache TTL
   - Enable maxmemory-policy: allkeys-lru
   - Increase Redis memory limit

3. **Celery Workers:**
   - Restart workers periodically
   - Reduce max tasks per worker: `--max-tasks-per-child=100`
   - Monitor for memory leaks

#### 4. **Database Connection Exhaustion**

**Symptoms:**
- "Too many connections" errors
- Slow query performance
- Timeouts

**Diagnosis:**
```bash
# Check active connections
psql -U news_user -d news_mcp -c "SELECT count(*) FROM pg_stat_activity WHERE datname='news_mcp';"

# Check pool status in logs
docker logs news-research-service | grep "pool"
```

**Solutions:**
1. **Increase Pool Size:**
```bash
# In .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

2. **Connection Leaks:**
   - Check for unclosed sessions in code
   - Enable pool_pre_ping: True
   - Set pool_recycle: 3600

3. **Optimize Queries:**
   - Add indexes (see database schema)
   - Use query result caching
   - Implement pagination

#### 5. **Cost Budget Exceeded**

**Symptoms:**
- "Daily cost limit exceeded" errors
- Budget warnings in logs

**Diagnosis:**
```bash
# Check usage stats
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8103/api/v1/research/stats?days=1 | jq

# Check cost tracking
psql -U news_user -d news_mcp -c "SELECT user_id, SUM(cost), COUNT(*) FROM cost_tracking WHERE date >= CURRENT_DATE GROUP BY user_id;"
```

**Solutions:**
1. **Immediate:**
   - Enable cost optimization: `ENABLE_COST_OPTIMIZATION=true`
   - Use Quick tier: `DEFAULT_COST_TIER=quick`
   - Increase cache TTL

2. **Long-term:**
   - Analyze usage patterns: `/api/v1/research/stats`
   - Implement user quotas
   - Review and optimize queries
   - Adjust budget limits

#### 6. **Structured Output Validation Failures**

**Symptoms:**
- `validation_status: "invalid"` in results
- JSON parsing errors in logs

**Diagnosis:**
```bash
# Check task with validation error
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8103/api/v1/research/{task_id} | jq '.validation_status'

# Check logs for parsing errors
docker logs news-research-service | grep "validation"
```

**Solutions:**
1. **Schema Mismatch:**
   - Verify output_schema matches function
   - Use response_format mode
   - Test with template preview

2. **Perplexity Response Format:**
   - Try different models (sonar-pro better for JSON)
   - Adjust prompt instructions
   - Fallback to unstructured mode

### Debug Strategies

#### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
LOG_FORMAT=text  # More readable than JSON

# Restart service
docker-compose restart research-service
```

#### Monitor Celery Tasks

```bash
# Real-time task monitoring
celery -A app.workers.celery_app events

# Flower web UI (if installed)
celery -A app.workers.celery_app flower --port=5555
```

#### Database Query Analysis

```sql
-- Slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE query LIKE '%research%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT
  schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Redis Cache Analysis

```bash
# Connect to Redis
redis-cli -h localhost -p 6379 -a redis_secret_2024

# Check cache stats
INFO stats

# View cache keys
KEYS research:*

# Check specific cache entry
GET research:<cache_key>

# Monitor cache operations in real-time
MONITOR
```

### Log Locations

**Docker:**
```bash
# API service logs
docker logs news-research-service

# Celery worker logs
docker logs news-research-celery-worker

# Follow logs
docker logs -f news-research-service --tail=100
```

**Systemd:**
```bash
# Service logs
journalctl -u research-service -f

# Worker logs
journalctl -u research-celery-worker -f
```

**Application Logs:**
- Structured JSON logs (production)
- Text logs (development)
- Log rotation: 7 days retention

---

## 10. Development

### Setup Local Environment

```bash
# 1. Clone repository
cd /home/cytrex/news-microservices/services/research-service

# 2. Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install shared library
pip install -e ../../shared/news-mcp-common

# 5. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 6. Run database migrations
alembic upgrade head

# 7. Start development server
uvicorn app.main:app --reload --port 8000
```

### Start Celery Worker

```bash
# In separate terminal
source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### Testing

**Run Full Test Suite:**
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_research.py -v

# Specific test
pytest tests/test_research.py::test_create_research_task -v
```

**Test Categories:**
- API integration tests: `tests/test_api_endpoints.py`
- Service logic tests: `tests/test_research.py`
- Perplexity client: `tests/test_perplexity.py`
- Cost optimizer: `tests/test_cost_optimizer.py`
- Caching: `tests/test_caching.py`
- Templates: `tests/test_templates.py`
- Celery tasks: `tests/test_tasks.py`

**Test Coverage:**
- Current: ~5,455 lines of tests
- Target: 80%+ coverage
- Critical paths covered:
  - ✅ API endpoints
  - ✅ Research task creation
  - ✅ Cost optimization
  - ✅ Cache operations
  - ✅ Template system
  - ⚠️ Specialized functions (partial)
  - ⚠️ Error scenarios (partial)

### Code Quality

**Linting:**
```bash
# Flake8
flake8 app/ --max-line-length=100

# Black (formatter)
black app/ tests/

# isort (import sorting)
isort app/ tests/

# mypy (type checking)
mypy app/
```

**Pre-commit Hooks:**
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Adding New Research Functions

**1. Define Pydantic Output Schema:**
```python
# In app/services/specialized_functions.py

class MyFunctionOutput(BaseModel):
    """Structured output for my custom function."""
    field1: str = Field(..., description="Field description")
    field2: int = Field(..., ge=0, le=100)
    # ...
```

**2. Create Function Class:**
```python
class MyResearchFunction(ResearchFunction):
    """My custom research function."""

    def __init__(self):
        super().__init__(
            name="my_function",
            description="Description of what this function does",
            model="sonar",
            depth="standard",
            output_schema=MyFunctionOutput
        )

    def build_prompt(self, param1: str, param2: int = 10) -> str:
        """Build the research prompt."""
        return f"""Analyze {param1} with parameter {param2}.

        Return JSON in this structure:
        {{
          "field1": "value",
          "field2": 42
        }}
        """
```

**3. Register Function:**
```python
# Add to SPECIALIZED_FUNCTIONS dict
SPECIALIZED_FUNCTIONS = {
    "my_function": MyResearchFunction,
    # ... existing functions
}
```

**4. Add Tests:**
```python
# In tests/test_specialized_functions.py

async def test_my_research_function():
    function = MyResearchFunction()
    prompt = function.build_prompt("test", param2=20)
    assert "test" in prompt
    assert "20" in prompt
```

**5. Use Function:**
```python
# Via API
response = httpx.post(
    "http://localhost:8103/api/v1/research",
    json={
        "query": "...",  # Not used, prompt built by function
        "research_function": "my_function",
        "function_parameters": {
            "param1": "value",
            "param2": 15
        }
    }
)
```

### Adding Database Migrations

```bash
# 1. Modify models in app/models/research.py

# 2. Generate migration
alembic revision --autogenerate -m "Add new field to research_tasks"

# 3. Review migration file
# Edit alembic/versions/<hash>_*.py if needed

# 4. Test migration
alembic upgrade head
alembic downgrade -1  # Rollback test
alembic upgrade head  # Re-apply

# 5. Commit migration
git add alembic/versions/
git commit -m "feat: add new field to research_tasks"
```

### Contributing Guidelines

1. **Branch Naming:**
   - feature/description
   - bugfix/description
   - refactor/description

2. **Commit Messages:**
   - feat: Add new feature
   - fix: Bug fix
   - refactor: Code refactoring
   - docs: Documentation
   - test: Test updates

3. **Pull Request Process:**
   - Write tests for new features
   - Update documentation
   - Run full test suite
   - Update CHANGELOG.md

4. **Code Review Checklist:**
   - ✅ Tests pass
   - ✅ Code follows style guide
   - ✅ Documentation updated
   - ✅ No hardcoded secrets
   - ✅ Error handling implemented
   - ✅ Logging added
   - ✅ Performance considered

---

## 11. Performance & Optimization

### Performance Metrics

**Current Performance (Task 404):**
- Health check: < 100ms (cached)
- Simple research: 2-5 seconds (Perplexity API)
- Cache hit: < 50ms
- Structured research: 3-8 seconds
- Batch processing: N × 2-5 seconds (parallel)

**Optimization Strategies:**

1. **Caching (Implemented)**
   - Redis cache: 7-day TTL
   - PostgreSQL cache: Persistent with expiration
   - Health check cache: 60s TTL
   - Cache hit rate target: > 60%

2. **Circuit Breaker (Task 406)**
   - Failure threshold: 3 consecutive failures
   - Success threshold: 2 successes to close
   - Timeout: 120 seconds
   - Prevents cascading failures
   - Protects against cost escalation

3. **Cost Optimization (3-Tier System)**
   - Quick: Cache-first, minimal API calls
   - Standard: Balanced approach
   - Deep: Quality-first
   - Automatic tier selection
   - Budget enforcement

4. **Database Optimization**
   - Indexed columns: user_id, status, created_at, feed_id
   - Connection pooling: 10 connections + 20 overflow
   - Query optimization: Avoid N+1 queries
   - Pagination: Max 100 items per page

5. **Async Processing**
   - Celery workers for long-running tasks
   - Non-blocking API responses
   - Batch processing support
   - Queue-based load balancing

### Monitoring & Metrics

**Key Metrics to Track:**

1. **API Performance:**
   - Request latency (p50, p95, p99)
   - Error rate
   - Request rate
   - Concurrent connections

2. **Research Operations:**
   - Research task creation rate
   - Completion time distribution
   - Cache hit rate
   - Cost per request

3. **Cost Analytics:**
   - Daily/monthly spend
   - Cost by model
   - Cost by user
   - Budget utilization

4. **Celery Workers:**
   - Task queue depth
   - Task success/failure rate
   - Worker utilization
   - Task duration

5. **External APIs:**
   - Perplexity API latency
   - Circuit breaker state
   - Rate limit hits
   - Error rate

### Optimization Recommendations

1. **Short-term:**
   - ✅ Enable cost optimization: `ENABLE_COST_OPTIMIZATION=true`
   - ✅ Increase cache TTL for stable queries
   - ✅ Use Quick tier for simple queries
   - ⚠️ Monitor circuit breaker metrics

2. **Medium-term:**
   - Implement request deduplication
   - Add query similarity detection
   - Optimize database indexes
   - Implement response streaming

3. **Long-term:**
   - Multi-region deployment
   - Read replicas for analytics
   - Advanced caching strategies
   - ML-based cost prediction

---

## Appendices

### A. Glossary

- **Research Function:** Specialized research operation with structured output
- **Cost Tier:** Performance/cost trade-off level (Quick/Standard/Deep)
- **Template:** Reusable research query with variable substitution
- **Research Run:** Scheduled or recurring research execution
- **Circuit Breaker:** Failure protection pattern for external APIs
- **Structured Output:** Validated JSON response matching Pydantic schema

### B. References

- [Perplexity AI API Documentation](https://docs.perplexity.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### C. Troubleshooting Quick Reference

| Issue | Quick Fix | Details |
|-------|-----------|---------|
| Circuit breaker open | Wait 120s | Section 5 (Circuit Breaker), Section 9.1 |
| No Celery workers | `docker-compose restart research-celery-worker` | Section 9.2 |
| Budget exceeded | Enable cost optimization | Section 9.5 |
| Cache miss rate high | Increase TTL | Section 11 |
| Slow queries | Add indexes | Section 2 |
| Memory issues | Reduce pool size | Section 9.3 |

---

**Document Version:** 1.1
**Last Updated:** 2025-12-22
**Changes:**
- Added comprehensive circuit breaker implementation details (Section 5)
- Added Perplexity API integration details (Section 5)
- Added /status/rate-limits endpoint documentation
- Updated endpoint table with status and metrics endpoints
- Updated section numbering (new Section 5 added)

**Maintained By:** Development Team
**Contact:** andreas@test.com
