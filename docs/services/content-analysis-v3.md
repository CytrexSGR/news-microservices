# Content-Analysis-V3 Service Documentation

**Service Name:** content-analysis-v3
**API Port:** 8117
**Status:** Production-Ready
**Version:** 1.1.0 (Last Updated: 2025-11-21)
**Deployment:** Docker + RabbitMQ + PostgreSQL

---

## Executive Summary

Content-Analysis-V3 is a cost-optimized, 4-tier AI analysis pipeline that achieves **96.7% cost reduction** compared to V2 ($0.0085 → $0.00028 per article) while maintaining sophisticated analysis through intelligent budget allocation and 2-stage prompting.

### Key Metrics

| Metric | V2 | V3 | Improvement |
|--------|----|----|-------------|
| **Cost per Article** | $0.0085 | $0.00028 | **96.7% reduction** |
| **Token Efficiency** | ~15,000 | ~10,242 | 31.7% reduction |
| **Analysis Time** | 8-12s | 6-9s | 25-33% faster |
| **Model** | Claude 3.5 Sonnet | Gemini 2.0 Flash | 67x cheaper |
| **Discard Rate** | 22% | 60% | Smart filtering |

### Architecture Innovation

V3 combines three cost-optimization techniques:

1. **Progressive Tiering**: Fast triage eliminates 60% of articles before expensive analysis
2. **2-Stage Prompting**: Relevance checking before deep dives saves 94.5% on irrelevant content
3. **Budget Redistribution**: Unused specialist tokens reallocated to active analyzers

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Pipeline Components](#pipeline-components)
3. [API Specification](#api-specification)
4. [Data Model & Storage](#data-model--storage)
5. [Performance & Cost Analysis](#performance--cost-analysis)
6. [Operational Guide](#operational-guide)
7. [Comparison with V2](#comparison-with-v2)
8. [Troubleshooting](#troubleshooting)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Content-Analysis-V3 Service                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  RabbitMQ Event Flow                                                      │
│  ═════════════════════════════════════════════════════════════════       │
│                                                                           │
│  analysis.v3.request  →  AnalysisRequestConsumer  →  Processing         │
│  (from feed-service)      (3 parallel workers)         Pipeline          │
│                                                           ↓              │
│                    ┌─────────────────────────────────────────────┐       │
│                    │  PIPELINE STAGES                            │       │
│                    ├─────────────────────────────────────────────┤       │
│                    │ Tier 0: TRIAGE                              │       │
│                    │ - Priority scoring (0-10)                  │       │
│                    │ - Keep/Discard decision                    │       │
│                    │ - Budget: 800 tokens (~$0.00005)           │       │
│                    │ - Discard Rate: 60% ✓                      │       │
│                    └──────────────┬──────────────────────────────┘       │
│                                   │                                       │
│                            [Keep?] │                                      │
│                         ┌──────────┴──────────┐                          │
│                    [No] │                    [Yes]                       │
│                         │                     │                          │
│                    (Discard)         ┌────────▼─────────────────┐        │
│                         │            │ Tier 1: FOUNDATION       │        │
│                         │            ├──────────────────────────┤        │
│                         │            │ - Entity extraction      │        │
│                         │            │ - Relation extraction    │        │
│                         │            │ - Topic classification   │        │
│                         │            │ - Impact/Credibility/    │        │
│                         │            │   Urgency scoring        │        │
│                         │            │ - Budget: 2000 tokens    │        │
│                         │            │   (~$0.0001)             │        │
│                         │            └────────┬─────────────────┘        │
│                         │                     │                          │
│                         │            ┌────────▼──────────────────┐       │
│                         │            │ Tier 2: SPECIALISTS      │       │
│                         │            ├───────────────────────────┤       │
│                         │            │ Phase 1: Quick Checks    │       │
│                         │            │ - Topic Classifier       │       │
│                         │            │ - Entity Extractor       │       │
│                         │            │ - Financial Analyst      │       │
│                         │            │ - Geopolitical Analyst   │       │
│                         │            │ - Sentiment Analyzer     │       │
│                         │            │ - Bias Scorer            │       │
│                         │            │                          │       │
│                         │            │ Phase 2: Budget Redist   │       │
│                         │            │ Phase 3: Deep Dives      │       │
│                         │            │ - Budget: 8000 tokens    │       │
│                         │            │   (~$0.0005)             │       │
│                         │            └────────┬──────────────────┘       │
│                         │                     │                          │
│                         │                     ▼                          │
│                    [Store Results]  analysis.v3.completed event          │
│                         │                     │                          │
│                         └─────────┬───────────┘                          │
│                                   │                                       │
│                                   ▼                                       │
│                    ┌──────────────────────────────┐                      │
│                    │ RabbitMQ Event Publisher     │                      │
│                    │ Publishes to feed-service    │                      │
│                    └──────────────┬───────────────┘                      │
│                                   │                                       │
│                                   ▼                                       │
│                    PostgreSQL: article_analysis table                    │
│                    (Unified storage for all versions)                    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Components

| Component | Port | Purpose | Technology |
|-----------|------|---------|-------------|
| **API Server** | 8117 | REST endpoints for analysis | FastAPI + Uvicorn |
| **Consumer Workers** | N/A | RabbitMQ message processing | aio-pika (async) |
| **Database** | 5432 | Result storage | PostgreSQL + asyncpg |
| **Message Broker** | 5672 | Event-driven communication | RabbitMQ |
| **LLM Providers** | N/A | AI analysis backend | Gemini 2.0 Flash (primary) |
| **Neo4j** | 7687 | Knowledge graph (future) | Neo4j async driver |

### Deployment Architecture

**Docker Services (docker-compose.yml):**

```yaml
content-analysis-v3-api:
  - Main FastAPI application
  - Handles HTTP requests for on-demand analysis
  - Lifespan: Database pool, RabbitMQ publisher, Neo4j client

content-analysis-v3-consumer (3 instances):
  - RabbitMQ worker processes (async message consumption)
  - Queue: analysis_v3_requests_queue (bound to analysis.v3.request routing key)
  - Prefetch: 10 messages per worker (configurable via V3_QUEUE_PREFETCH_COUNT)
  - Capacity: 30 concurrent analyses (3 workers × 10 prefetch)
  - Dead Letter Queue: analysis_v3_requests_queue_dlq (24-hour TTL)
  - Auto-reconnect: aio-pika.connect_robust (handles connection failures)
  - Neo4j Integration: Publishes Tier1/Tier2 results to Knowledge Graph (optional)
```

---

## Pipeline Components

### Tier 0: Triage

**Purpose:** Fast relevance filtering with objective scoring criteria

**Budget:** 800 tokens, $0.00005 per article

**Inputs:**
- Article title, URL, content preview

**Outputs:**
- `PriorityScore` (0-10 numeric)
- `Category` (CONFLICT, FINANCE, POLITICS, HUMANITARIAN, SECURITY, TECHNOLOGY, HEALTH, OTHER)
- `keep` (boolean) - if false, stops pipeline

**Key Algorithm: Objective Scoring (2025-11-21 Update)**

The triage scoring uses concrete criteria instead of subjective language:

```
Score 0-2: NOISE → DISCARD
- Entertainment, sports, lifestyle
- Product reviews, tech launches
- Local events < 100,000 people affected
Examples: "Taylor Swift wins Grammy", "iPhone 16 Review"

Score 3-4: LOW RELEVANCE → DISCARD ⚠️ (THRESHOLD CHANGED)
- Regional news (non-G20 countries)
- Routine politics (appointments, minor laws)
- Climate conferences (routine updates)
- Regional conflicts (< 1000 casualties)
Examples: "COP30 goes to overtime", "Senator fears for safety"

Score 5-6: MODERATE → KEEP ✓ (NEW MINIMUM THRESHOLD)
- G20 national policy changes
- Central bank rate changes (≥ 0.25%)
- Fortune 100 major events
- Economic shocks (> 1% deviation)
- Disasters affecting 100k-1M people

Score 7-8: IMPORTANT → KEEP
- G7 elections
- Active wars/armed conflicts
- Major diplomatic crises
- Market crashes 3-7%

Score 9-10: CRITICAL → PRIORITY
- G7 presidential elections
- Wars between major powers
- Market crashes > 7%
- Nuclear incidents
```

**Critical Rule:** Minimum keep threshold = score ≥5 (Changed 2025-11-21)

**Impact:** 60% discard rate (down from 22%), saving ~$72/day

**Code Location:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier0/triage.py` (430 lines)

**Field Validators:** Normalizes LLM output variations before validation (e.g., "PEOPLE" → "PERSON")

---

### Tier 1: Foundation Extraction

**Purpose:** Core entity/relation/topic extraction with credibility scoring

**Budget:** 2000 tokens, $0.0001 per article

**Inputs:**
- Full article (title, URL, content)
- Tier 0 triage decision

**Outputs:**

```python
{
  "entities": [
    {
      "name": "Federal Reserve",
      "type": "ORGANIZATION",
      "confidence": 0.95,
      "mentions": 2,
      "aliases": ["Fed"],
      "role": "Central Bank"
    }
  ],
  "relations": [
    {
      "subject": "Federal Reserve",
      "predicate": "RAISES",
      "object": "Interest Rates",
      "confidence": 0.92
    }
  ],
  "topics": [
    {
      "keyword": "FINANCE",
      "confidence": 0.98,
      "parent_category": "Economic"
    }
  ],
  "impact_score": 8.0,      # 0-10 global significance
  "credibility_score": 7.0,  # 0-10 source reliability
  "urgency_score": 7.0,      # 0-10 time sensitivity
  "tokens_used": 4094,
  "cost_usd": 0.000154,
  "model": "gemini-2.0-flash-exp"
}
```

**Scoring Scale:**

- **Impact Score (0-10):** How significant for global markets/politics?
  - 0-3: Local/niche impact
  - 4-6: Regional significance
  - 7-8: National importance
  - 9-10: Global/market-moving

- **Credibility Score (0-10):** How reliable is the source?
  - 0-3: Unverified claims, questionable
  - 4-6: Mainstream media, some verification
  - 7-8: Established outlets, multiple sources
  - 9-10: Official statements, primary sources

- **Urgency Score (0-10):** How time-sensitive?
  - 0-3: Background/analysis, no time pressure
  - 4-6: Recent development, moderate sensitivity
  - 7-8: Breaking news, developing situation
  - 9-10: Critical alert, immediate action

**Entity Types (Normalized):**

| Type | Examples |
|------|----------|
| PERSON | Politicians, CEOs, individuals |
| ORGANIZATION | Companies, governments, agencies |
| LOCATION | Countries, cities, regions |
| EVENT | Specific events (elections, wars) |
| CONCEPT | Ideas, theories, movements |
| TECHNOLOGY | Software, AI, hardware |
| PRODUCT | Commercial products, services |
| CURRENCY | USD, EUR, cryptocurrencies |
| FINANCIAL_INSTRUMENT | Stocks, bonds, derivatives |
| LAW | Legislation, regulations |
| POLICY | Government policies, rules |
| TIME | Temporal expressions |
| OTHER | Catch-all category |

**Code Location:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier1/foundation.py` (203 lines)

**Key Features:**
- Schema validation with field validators
- Handles LLM variations (plural forms, abbreviations, case)
- No direct database writes (event-driven storage)

---

### Tier 2: Specialist Analysis

**Purpose:** Specialized deep-dive analysis with 6 expert modules

**Budget:** 8000 tokens total, $0.0005, distributed across specialists using weighted allocation

**Current Specialists:** 6 modules (as of 2025-12-22)
1. Topic Classifier
2. Entity Extractor
3. Financial Analyst
4. Geopolitical Analyst
5. Sentiment Analyzer
6. Bias Scorer

**Architecture: 2-Stage Prompting**

All specialists follow a two-stage process:

```
┌─────────────────────────────────────┐
│ Stage 1: QUICK CHECK (~200 tokens)  │
│ - Determine relevance               │
│ - Fast heuristics or LLM call       │
│ - Returns: is_relevant, confidence  │
├─────────────────────────────────────┤
│                                     │
│ [Is relevant?] ──NO──→ SKIP         │
│     │                               │
│    YES                              │
│     ▼                               │
│ Stage 2: DEEP DIVE (~1500 tokens)   │
│ - Detailed specialist analysis      │
│ - Full extraction with context      │
│ - Returns: specialist_data          │
└─────────────────────────────────────┘
```

**Savings:** 94.5% token reduction on irrelevant content

#### Specialist 1: Topic Classifier

**Purpose:** Hierarchical topic extraction

**Quick Check:** Does article need detailed topic hierarchy?
- Heuristic: Check Tier1 topics for non-generic categories
- Cost: 0 tokens (logic-based)

**Deep Dive:** Extract parent-child topic relationships
```python
{
  "topics": [
    {"keyword": "FINANCE", "parent": "ECONOMIC", "confidence": 0.98},
    {"keyword": "CENTRAL_BANKING", "parent": "FINANCE", "confidence": 0.95}
  ],
  "hierarchies": [["ECONOMIC", "FINANCE", "CENTRAL_BANKING"]]
}
```

**Code:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/topic_classifier.py`

#### Specialist 2: Entity Extractor

**Purpose:** Enrich Tier1 entities with contextual details

**Quick Check:** Do entities need enrichment?
- Heuristic: Check entity count and types
- Cost: 0 tokens

**Deep Dive:** Add industry, role, affiliations, stock symbols
```python
{
  "enriched_entities": [
    {
      "name": "Federal Reserve",
      "type": "ORGANIZATION",
      "industry": "Financial Services",
      "role": "Central Bank",
      "headquarters": "Washington, DC",
      "key_officials": ["Jerome Powell"],
      "market_symbols": []
    }
  ]
}
```

**Code:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/entity_extractor.py`

#### Specialist 3: Financial Analyst

**Purpose:** Market impact assessment

**Quick Check:** Is article about finance?
- Heuristic: Check Tier1 topics for FINANCE keyword
- Cost: 0 tokens (no LLM call)

**Deep Dive:** Extract market metrics
```python
{
  "metrics": {
    "market_impact": 0.85,           # 0-1 expected market movement
    "volatility_expected": 0.70,      # 0-1 expected volatility increase
    "price_direction_bias": "BULLISH" # BULLISH, BEARISH, NEUTRAL
  },
  "affected_symbols": ["SPY", "QQQ", "BND"],
  "impact_estimate": "Likely 2-4% market movement"
}
```

**Code:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/financial_analyst.py`

#### Specialist 4: Geopolitical Analyst

**Purpose:** Conflict and diplomatic impact assessment

**Quick Check:** Is article about geopolitical events?
- Checks Tier1 topics for CONFLICT, POLITICS
- Cost: 200 tokens (LLM quick check)

**Deep Dive:** Analyze conflict dynamics
```python
{
  "conflict_severity": 7,              # 0-10 scale
  "affected_countries": ["Ukraine", "Russia"],
  "international_implications": "NATO involvement risk",
  "diplomatic_impact": "Potential for sanctions escalation",
  "risk_level": "HIGH"
}
```

**Code:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/geopolitical_analyst.py`

#### Specialist 5: Sentiment Analyzer

**Purpose:** Market and general sentiment analysis

**Quick Check:** Does article contain sentiment-bearing content?
- Heuristic: Check for subjective language markers
- Cost: 0 tokens

**Deep Dive:** Extract sentiment metrics
```python
{
  "sentiment_type": "FINANCIAL",  # FINANCIAL or GENERAL
  "bullish_ratio": 0.72,           # For financial content
  "bearish_ratio": 0.28,
  "confidence": 0.88,
  "summary": "Moderately bullish"
}
```

**Code:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/sentiment_analyzer.py`

#### Specialist 6: Bias Scorer

**Purpose:** Political bias detection with 7-level scale

**Quick Check:** Always returns relevant=True
- Applied to ALL articles (not selective like other specialists)
- Non-political articles score as "center" with minimal strength
- Cost: 0 tokens (no LLM call needed)

**Deep Dive:** Analyze political bias
```python
{
  "political_direction": "CENTER_LEFT",  # 7-level scale
  "bias_score": -0.35,                    # -1.0 (left) to +1.0 (right)
  "bias_strength": "MODERATE",            # minimal, weak, moderate, strong, extreme
  "confidence": 0.82
}
```

**Scale:**
```
Left Side (Negative):
  far_left:     -1.0 to -0.7
  left:         -0.7 to -0.4
  center_left:  -0.4 to -0.15

Center:        -0.15 to +0.15

Right Side (Positive):
  center_right: +0.15 to +0.4
  right:        +0.4 to +0.7
  far_right:    +0.7 to +1.0
```

**Optimization (2025-11-20):** Prompt compression and smart content truncation
- Prompt: Compressed to 800 characters (52 lines)
- Content: Truncated to 2,000 characters with sentence-boundary awareness
- Average tokens: ~300 per analysis
- Token reduction: 65% from initial implementation

**Implementation Details:**
- File: `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/specialists/bias_scorer.py` (222 lines)
- Smart truncation: Cuts at sentence boundaries (`. `, `.\n`, `? `, `! `) when content > 2000 chars
- Fallback handling: Returns center/minimal on parse errors (neutral fallback)
- Budget allocation weight: 0.7 (focused scoring task, lower than other specialists)

### Budget Redistribution Algorithm

Tier2 uses **weighted budget allocation** with 3-phase execution to optimize token distribution:

**Specialist Weight Configuration:**
```python
SPECIALIST_WEIGHTS = {
    SpecialistType.FINANCIAL_ANALYST: 1.5,      # More tokens for detailed market analysis
    SpecialistType.GEOPOLITICAL_ANALYST: 1.3,   # Complex relationship analysis
    SpecialistType.ENTITY_EXTRACTOR: 1.2,       # May have many entities to enrich
    SpecialistType.SENTIMENT_ANALYZER: 1.0,     # Standard analysis
    SpecialistType.TOPIC_CLASSIFIER: 0.8,       # Simpler classification task
    SpecialistType.BIAS_SCORER: 0.7,            # Focused scoring task
}
```

**3-Phase Execution Process:**
```
Phase 1: QUICK CHECKS (All 6 specialists)
─────────────────────────────────────────
for specialist in all_specialists:
    result = await specialist.quick_check(article)
    if result.is_relevant:
        relevant_specialists.append(specialist)

Phase 2: WEIGHTED BUDGET REDISTRIBUTION
───────────────────────────────────────
quick_check_tokens = sum(result.tokens for result in quick_checks)
remaining_budget = 8000 - quick_check_tokens
total_weight = sum(SPECIALIST_WEIGHTS[s] for s in relevant_specialists)
tokens_per_unit = remaining_budget / total_weight

# Calculate per-specialist allocation
for specialist in relevant_specialists:
    allocated_tokens[specialist] = int(tokens_per_unit * SPECIALIST_WEIGHTS[specialist])

Phase 3: DEEP DIVES (Relevant specialists only)
───────────────────────────────────────────────
for specialist in relevant_specialists:
    findings = await specialist.deep_dive(
        ...,
        max_tokens=allocated_tokens[specialist]
    )
```

**Example 1:** If all 6 specialists are relevant (8000 token budget):
- Phase 1: ~0 tokens (BiasScorer returns relevant=true instantly, others use heuristics)
- Phase 2 Allocation:
  - FINANCIAL_ANALYST: 1,636 tokens (1.5 weight)
  - GEOPOLITICAL_ANALYST: 1,418 tokens (1.3 weight)
  - ENTITY_EXTRACTOR: 1,309 tokens (1.2 weight)
  - SENTIMENT_ANALYZER: 1,091 tokens (1.0 weight)
  - TOPIC_CLASSIFIER: 873 tokens (0.8 weight)
  - BIAS_SCORER: 763 tokens (0.7 weight)
- Phase 3: 7,090 tokens total (weighted distribution)

**Example 2:** If 3 specialists relevant (Financial, Entity, Bias):
- Phase 1: ~0 tokens
- Phase 2 Allocation:
  - FINANCIAL_ANALYST: 3,529 tokens (1.5 weight)
  - ENTITY_EXTRACTOR: 2,823 tokens (1.2 weight)
  - BIAS_SCORER: 1,647 tokens (0.7 weight)
- Phase 3: ~8,000 tokens total (more per specialist)

**Why Weighted Allocation?**
- Financial analysis requires detailed market metrics (higher weight)
- Bias scoring is focused task with short prompts (lower weight)
- Prevents under/over-allocation based on complexity
- Ensures critical specialists get adequate budget

**Code Location:** `/home/cytrex/news-microservices/services/content-analysis-v3/app/pipeline/tier2/orchestrator.py` (256 lines)

---

### Tier 3: Intelligence Modules (Planned)

**Status:** Not implemented

**Purpose:** Event timelines, multi-document reasoning, impact forecasting

**Budget:** 3000 tokens, $0.001 per article

**Planned Modules:**
- Event Timeline Construction: Sequence events from multiple sources
- Multi-Document Reasoning: Synthesize analysis across articles
- Impact Forecasting: Predict market/political consequences
- Relationship Network: Map entity relationships over time

---

## API Specification

### Authentication

No authentication required for local development. Production: Use API Gateway authentication.

### Health Check Endpoints

#### GET /health
**Response:** Simple health status

```json
{
  "status": "healthy"
}
```

#### GET /health/detailed
**Response:** Detailed status with dependencies

```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T10:30:00Z",
  "database": {
    "status": "connected",
    "pool_size": 5,
    "available": 5
  },
  "rabbitmq": {
    "status": "connected",
    "queue_name": "analysis_v3_requests_queue",
    "messages_pending": 12
  },
  "gemini": {
    "status": "operational",
    "api_key_configured": true
  }
}
```

#### GET /health/ready (Kubernetes)
**Response:** 200 if ready to accept traffic

```json
{
  "status": "ready"
}
```

#### GET /health/live (Kubernetes)
**Response:** 200 if service is alive

```json
{
  "status": "alive"
}
```

### Analysis Endpoints

#### POST /api/v1/analyze

**Request:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Federal Reserve Raises Interest Rates by 0.5%",
  "url": "https://example.com/fed-rates-2025",
  "content": "The Federal Reserve announced today that it is raising the federal funds rate...",
  "run_tier2": true
}
```

**Response (Synchronous):**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis submitted to RabbitMQ consumer queue",
  "tier0_complete": false,
  "tier1_complete": false,
  "tier2_complete": false
}
```

**Process Flow:**
1. Request submitted to API
2. API returns immediately with status
3. RabbitMQ consumer processes asynchronously
4. Results available via status/results endpoints

**Response Time:** < 100ms (just message publishing)

#### GET /api/v1/status/{article_id}

**Response:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "tier2_complete",
  "tier0_complete": true,
  "tier1_complete": true,
  "tier2_complete": true,
  "created_at": "2025-11-24T10:30:00Z",
  "completed_at": "2025-11-24T10:30:15Z"
}
```

**Status Values:**
- `pending`: Queued in RabbitMQ
- `tier0_complete`: Triage finished
- `tier0_failed`: Triage error (check error field)
- `tier1_complete`: Foundation extraction finished
- `tier1_failed`: Tier1 error
- `tier2_complete`: All specialist analysis finished
- `tier2_failed`: Tier2 error
- `failed`: Pipeline failed (check error field)

#### GET /api/v1/results/{article_id}

**Response:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier0": {
    "priority_score": 8,
    "category": "FINANCE",
    "keep": true,
    "tokens_used": 1148,
    "cost_usd": 0.000025,
    "model": "gemini-2.0-flash-exp"
  },
  "tier1": {
    "entities": [
      {
        "name": "Federal Reserve",
        "type": "ORGANIZATION",
        "confidence": 0.95,
        "mentions": 2,
        "aliases": ["Fed"],
        "role": "Central Bank"
      }
    ],
    "relations": [
      {
        "subject": "Federal Reserve",
        "predicate": "RAISES",
        "object": "Interest Rates",
        "confidence": 0.92
      }
    ],
    "topics": [
      {
        "keyword": "FINANCE",
        "confidence": 0.98,
        "parent_category": "Economic"
      }
    ],
    "scores": {
      "impact_score": 8.0,
      "credibility_score": 7.0,
      "urgency_score": 7.0
    },
    "tokens_used": 4094,
    "cost_usd": 0.000154,
    "model": "gemini-2.0-flash-exp"
  },
  "tier2": {
    "TOPIC_CLASSIFIER": {
      "topics": [...],
      "hierarchies": [...],
      "tokens_used": 1200,
      "cost_usd": 0.00003
    },
    "ENTITY_EXTRACTOR": {
      "enriched_entities": [...],
      "tokens_used": 1100,
      "cost_usd": 0.000027
    },
    "FINANCIAL_ANALYST": {
      "metrics": {...},
      "affected_symbols": ["SPY", "QQQ"],
      "tokens_used": 900,
      "cost_usd": 0.000022
    },
    "GEOPOLITICAL_ANALYST": null,
    "SENTIMENT_ANALYZER": {
      "sentiment_type": "FINANCIAL",
      "bullish_ratio": 0.72,
      "bearish_ratio": 0.28,
      "tokens_used": 800,
      "cost_usd": 0.00002
    },
    "BIAS_SCORER": {
      "political_direction": "CENTER",
      "bias_score": 0.05,
      "bias_strength": "MINIMAL",
      "confidence": 0.91,
      "tokens_used": 300,
      "cost_usd": 0.000007
    },
    "total_tokens": 4300,
    "total_cost_usd": 0.000116,
    "specialists_executed": 5
  },
  "metadata": {
    "total_tokens": 9542,
    "total_cost_usd": 0.000295,
    "analysis_time_ms": 14850,
    "pipeline_version": "3.0"
  }
}
```

#### GET /api/v1/results/{article_id}/tier0

**Response:** Tier 0 results only (TriageDecision)

#### GET /api/v1/results/{article_id}/tier1

**Response:** Tier 1 results only (Tier1Results with entities, relations, topics, scores)

#### GET /api/v1/results/{article_id}/tier2

**Response:** Tier 2 results only (all specialist findings)

### Error Handling

**400 Bad Request:**
```json
{
  "detail": "article_id is not a valid UUID"
}
```

**404 Not Found:**
```json
{
  "detail": "Article analysis not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "LLM provider error: API rate limit exceeded"
}
```

---

## Data Model & Storage

### Storage Architecture

**Important:** V3 does NOT write directly to databases. All data flows through event-driven architecture:

```
V3 Consumer Executes
        ↓
Publishes analysis.v3.completed event
        ↓
RabbitMQ exchanges event
        ↓
feed-service consumes event
        ↓
feed-service writes to article_analysis table
        ↓
Frontend queries feed-service API (not V3 directly)
```

### Unified Storage Table

**Table:** `public.article_analysis` (PostgreSQL)

**Key Columns:**

| Column | Type | Purpose |
|--------|------|---------|
| `article_id` | UUID | Primary key |
| `pipeline_version` | TEXT | '3.0' for V3 |
| `triage_results` | JSONB | Tier 0 output |
| `tier1_results` | JSONB | Tier 1 output |
| `tier2_results` | JSONB | Tier 2 output |
| `metrics` | JSONB | Cost, token, time tracking |
| `created_at` | TIMESTAMP | Analysis start time |
| `completed_at` | TIMESTAMP | Pipeline completion time |

**Example JSONB Record:**

```json
{
  "triage_results": {
    "priority_score": 8,
    "category": "FINANCE",
    "keep": true,
    "tokens_used": 1148,
    "cost_usd": 0.000025,
    "model": "gemini-2.0-flash-exp"
  },
  "tier1_results": {
    "entities": [...],
    "relations": [...],
    "topics": [...],
    "scores": {
      "impact_score": 8.0,
      "credibility_score": 7.0,
      "urgency_score": 7.0
    },
    "tokens_used": 4094,
    "cost_usd": 0.000154,
    "model": "gemini-2.0-flash-exp"
  },
  "tier2_results": {
    "TOPIC_CLASSIFIER": {...},
    "ENTITY_EXTRACTOR": {...},
    "FINANCIAL_ANALYST": {...},
    "GEOPOLITICAL_ANALYST": null,
    "SENTIMENT_ANALYZER": {...},
    "BIAS_SCORER": {...},
    "total_tokens": 4300,
    "total_cost_usd": 0.000116,
    "specialists_executed": 5
  },
  "metrics": {
    "tier0_cost_usd": 0.000025,
    "tier1_cost_usd": 0.000154,
    "tier2_cost_usd": 0.000116,
    "total_cost_usd": 0.000295,
    "total_tokens": 9542,
    "analysis_time_ms": 14850
  }
}
```

### Schema Validation with Field Validators

Pydantic validators normalize LLM output before database storage:

```python
@field_validator('type', mode='before')
@classmethod
def normalize_entity_type(cls, v):
    """Normalize common LLM variations to canonical entity types."""
    TYPE_MAPPINGS = {
        "PEOPLE": "PERSON",
        "PERSONS": "PERSON",
        "ORGANIZATIONS": "ORGANIZATION",
        "ORG": "ORGANIZATION",
        "LOCATIONS": "LOCATION",
        "PLACE": "LOCATION",
        # ... 15+ mappings
    }

    if isinstance(v, str):
        v_upper = v.upper().strip()
        return TYPE_MAPPINGS.get(v_upper, v_upper)
    return v
```

**Benefits:**
- ✓ Prevents validation errors from common LLM variations
- ✓ Reduces Dead Letter Queue accumulation
- ✓ Gracefully handles plural/singular, abbreviations, case variations

---

## Performance & Cost Analysis

### Measured Performance (Real Articles)

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| **Total Cost** | $0.000279 | $0.00065 | ✓ 57% under budget |
| **Total Tokens** | 10,242 | 10,800 | ✓ Within budget |
| **Budget Util** | 42.9% | 100% | ✓ Healthy margin |
| **Cost Reduction** | 96.7% | 83.5% | ✓ Exceeded goal |

### Cost Breakdown by Tier

| Tier | Tokens | Cost | % of Total | Budget |
|------|--------|------|-----------|--------|
| Tier0 (Triage) | 1,148 | $0.000025 | 8.9% | 50% |
| Tier1 (Foundation) | 4,094 | $0.000154 | 55% | 154% |
| Tier2 (Specialists) | 5,000 (est) | $0.0001 (est) | 36% | 20% |
| **TOTAL** | **10,242** | **$0.000279** | **100%** | **42.9%** |

**Note:** Tier1 exceeded individual budget but well within total pipeline budget.

### Provider Cost Comparison

| Provider | Model | Cost per 1M Tokens | Input / Output |
|----------|-------|-------------------|----------------|
| **Gemini** | 2.0 Flash | $0.075 / $0.30 | Primary V3 |
| **OpenAI** | GPT-4 Turbo | $10 / $30 | Fallback |
| **Claude** | 3.5 Sonnet | $3 / $15 | V2 baseline |

**Why Gemini 2.0 Flash?**
- 67x cheaper than Claude 3.5 Sonnet
- Comparable quality for structured extraction
- Native JSON schema support (reduces parsing errors)
- 1M token window (handles long documents)

### Token Efficiency Breakdown

**Tier0 (Triage):**
- Input tokens: ~400 (title + preview + prompt)
- Output tokens: ~150 (JSON + reasoning)
- Total: ~550 (budget: 800) - 69% efficiency

**Tier1 (Foundation):**
- Input tokens: ~800 (full article + prompt)
- Output tokens: ~1,200 (entities + relations + topics + scores)
- Total: ~4,094 (budget: 2000) - 205% of budget (acceptable for high-quality extraction)

**Tier2 Specialists (average):**
- Quick checks: ~150 tokens per specialist × 6 = 900 total
- Deep dives (4 specialists): ~1,075 tokens average each
- Total: ~5,000 tokens (budget: 8000) - 62% efficiency

### Cost Per Article Over Time

**Daily Cost Projection (1000 articles/day):**
```
Tier0 only: 1000 × $0.000025 = $25/day
Tier0 + Tier1 (40% kept): 400 × $0.000179 = $72/day
Full pipeline (40% kept): 400 × $0.000295 = $118/day

Monthly: ~$3,540 (40% discard rate after hardening)
Previous (V2): ~$25,500 (22% discard rate)
SAVINGS: ~$22,000/month = 86%
```

**Annual Projection:** ~$42,480 (vs ~$306,000 for V2)

---

## Operational Guide

### Deployment

#### Docker Compose

```bash
# Start all services (API + 3 consumers)
docker compose up -d content-analysis-v3-api content-analysis-v3-consumer

# View logs
docker logs -f content-analysis-v3-api
docker logs -f content-analysis-v3-consumer

# Stop services
docker compose down
```

#### Configuration

**Environment Variables (.env):**

```bash
# Service
SERVICE_NAME=content-analysis-v3
PORT=8117

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=content_analysis_v3

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# LLM Providers
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional

# Tier Configuration
V3_TIER0_PROVIDER=gemini
V3_TIER0_MODEL=gemini-2.0-flash-exp
V3_TIER0_MAX_TOKENS=800
V3_TIER0_MAX_COST=0.001

V3_TIER1_PROVIDER=gemini
V3_TIER1_MODEL=gemini-2.0-flash-exp
V3_TIER1_MAX_TOKENS=4000
V3_TIER1_MAX_COST=0.001

V3_TIER2_PROVIDER=gemini
V3_TIER2_MODEL=gemini-2.0-flash-exp
V3_TIER2_MAX_TOKENS=8000
V3_TIER2_MAX_COST=0.005

# Feature Flags
V3_ENABLED=true
V3_ROLLOUT_PERCENTAGE=100

# Performance
V3_MAX_WORKERS=4
V3_QUEUE_PREFETCH_COUNT=10

# Cost Monitoring
V3_DAILY_BUDGET_USD=5.0
V3_COST_ALERT_THRESHOLD=0.003
V3_COST_CIRCUIT_BREAKER=0.005
```

### Monitoring

#### Consumer Status

```bash
# Check if consumers are running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep content-analysis-v3

# Expected output:
# content-analysis-v3-api            Up 2 hours
# content-analysis-v3-consumer       Up 2 hours
# content-analysis-v3-consumer-2     Up 2 hours
# content-analysis-v3-consumer-3     Up 2 hours
```

#### Queue Status

```bash
# Check RabbitMQ queue
docker exec rabbitmq rabbitmqctl list_queues name messages | grep analysis

# Expected:
# analysis_v3_requests_queue           12
# analysis_v3_requests_queue_dlq       0
```

#### Database Monitoring

**Check triage distribution (last 24 hours):**

```sql
SELECT
    (triage_results->>'priority_score')::int as score,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage,
    ROUND(AVG((triage_results->>'cost_usd')::float)::numeric, 6) as avg_cost
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND created_at > NOW() - INTERVAL '24 hours'
  AND triage_results IS NOT NULL
GROUP BY score
ORDER BY score;
```

**Expected Distribution (After 2025-11-21 hardening):**
- Scores 0-4 (discard): 60-70%
- Scores 5-6 (moderate): 20-25%
- Scores 7-10 (high): 10-15%

**Check total cost (daily):**

```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as articles,
    ROUND(SUM((metrics->>'total_cost_usd')::float)::numeric, 2) as total_cost_usd,
    ROUND(AVG((metrics->>'total_cost_usd')::float)::numeric, 6) as avg_cost,
    ROUND(SUM((metrics->>'total_tokens')::int)::numeric, 0) as total_tokens
FROM article_analysis
WHERE pipeline_version = '3.0'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 7;
```

#### RabbitMQ Event Publishing

**Event Flow:**
1. Consumer executes pipeline (Tier0 → Tier1 → Tier2)
2. Consumer publishes `analysis.v3.completed` event (or `analysis.v3.failed` on error)
3. Feed-service consumes event and stores in `article_analysis` table

**Published Event Types:**
- `analysis.v3.completed` - Successful analysis (includes full Tier0/Tier1/Tier2 data)
- `analysis.v3.failed` - Pipeline error (includes error_type and error_message)

**Event Payload Structure:**
```json
{
  "event_type": "analysis.v3.completed",
  "service": "content-analysis-v3",
  "timestamp": "2025-11-24T10:30:15.000Z",
  "payload": {
    "article_id": "uuid",
    "correlation_id": "trace-id",
    "success": true,
    "pipeline_version": "3.0",
    "tier0": {...},
    "tier1": {
      "entities": [...],      // Full arrays for frontend
      "relations": [...],
      "topics": [...],
      "impact_score": 8.0,
      "credibility_score": 7.0,
      "urgency_score": 7.0,
      "tokens_used": 4094,
      "cost_usd": 0.000154,
      "model": "gemini-2.0-flash-exp"
    },
    "tier2": {
      "TOPIC_CLASSIFIER": {...},
      "ENTITY_EXTRACTOR": {...},
      "FINANCIAL_ANALYST": {...},
      "GEOPOLITICAL_ANALYST": null,
      "SENTIMENT_ANALYZER": {...},
      "BIAS_SCORER": {...},
      "total_tokens": 4300,
      "total_cost_usd": 0.000116,
      "specialists_executed": 5
    },
    "metrics": {...}
  }
}
```

**Verify completion events:**

```bash
# Monitor RabbitMQ logs
docker logs -f rabbitmq | grep "analysis.v3"

# Watch feed-service consuming events
docker logs -f feed-service | grep "analysis.v3.completed"

# Check event publisher logs
docker logs -f content-analysis-v3-consumer | grep "publish_event"
```

**Error Handling:**
- **Transient errors** (rate limits, timeouts): Message requeued for retry
- **Permanent errors** (validation, malformed JSON): Message sent to DLQ
- **Unknown errors**: Message requeued for safety
- All errors publish `analysis.v3.failed` event before rejection

### Scaling

#### Horizontal Scaling (Add More Workers)

To add 2 more consumer workers:

```yaml
# docker-compose.yml
content-analysis-v3-consumer-4:
  image: content-analysis-v3:latest
  environment:
    - WORKER_ID=4
  depends_on:
    - postgres
    - rabbitmq
  # ... same configuration

content-analysis-v3-consumer-5:
  image: content-analysis-v3:latest
  environment:
    - WORKER_ID=5
  depends_on:
    - postgres
    - rabbitmq
  # ... same configuration
```

**Capacity Calculation:**
- Per worker: 10 prefetch (messages processed in parallel)
- 5 workers: 50 concurrent articles
- Average processing time: 15-20 seconds
- Throughput: 150-200 articles/minute

#### Vertical Scaling (Increase Prefetch)

```python
# app/core/config.py
V3_QUEUE_PREFETCH_COUNT: int = 20  # Increased from 10

# Careful: Each article holds a database connection
# Monitor pool utilization: max_size should be > prefetch_count × workers
```

### Troubleshooting

#### Issue: "Database pool not initialized"

```bash
# Verify database is running
docker ps | grep postgres

# Test connection
docker exec postgres psql -U news_user -d content_analysis_v3 -c "SELECT 1"

# Restart service
docker compose restart content-analysis-v3-api
```

#### Issue: "RabbitMQ connection refused"

```bash
# Check RabbitMQ status
docker ps | grep rabbitmq

# Test connection
docker exec rabbitmq rabbitmqctl status

# Restart RabbitMQ
docker compose restart rabbitmq

# Consumers will auto-reconnect (aio-pika.connect_robust)
```

#### Issue: "Gemini API rate limit exceeded"

**Error:** `429 Too Many Requests`

**Solution:**
- Gemini free tier: 10 requests/minute
- Upgrade to Gemini API paid tier
- Implement exponential backoff (already in place via tenacity)
- Check quota usage: https://console.cloud.google.com/apis

#### Issue: "Articles stuck in processing"

```bash
# Check DLQ for failed messages
docker exec rabbitmq rabbitmqctl list_queues name messages | grep dlq

# If DLQ has messages, check consumer logs for errors
docker logs content-analysis-v3-consumer | grep ERROR

# Requeue from DLQ (manual)
docker exec rabbitmq rabbitmqctl purge_queue analysis_v3_requests_queue_dlq
```

---

## Comparison with V2

### Cost Comparison

| Aspect | V2 (Claude 3.5 Sonnet) | V3 (Gemini 2.0 Flash) | Improvement |
|--------|------------------------|----------------------|-------------|
| **Model** | claude-3.5-sonnet | gemini-2.0-flash | 67x cheaper |
| **Cost per article** | $0.0085 | $0.00028 | **96.7% reduction** |
| **Tokens per article** | ~15,000 | ~10,242 | 31.7% fewer |
| **Analysis time** | 8-12s | 6-9s | 25-33% faster |
| **Architecture** | Single-stage (all-in-one) | 4-tier progressive | Modular |
| **Specialists** | 5 modules | 6 modules (+ Bias) | +1 new module |
| **Discard rate** | 22% | 60% | Better filtering |

### Architecture Differences

**V2 Single-Stage:**
```
Article → Claude 3.5 Sonnet → Full Analysis → Storage
         (15,000 tokens)     (~8-12 seconds)
```

**V3 Multi-Tier:**
```
Article → Tier0 Triage (800 tokens)
            ↓
          Keep? NO → Discard (60% of articles saved here)
            ↓ YES
          Tier1 Foundation (2000 tokens)
            ↓
          Tier2 Specialists (8000 tokens, only relevant ones run)
            ↓
          Storage via Event
```

### Feature Comparison

| Feature | V2 | V3 |
|---------|----|----|
| Triage/filtering | None (all analyzed) | Yes (60% discard rate) |
| Entity extraction | Yes | Yes (+ enrichment) |
| Relation extraction | Yes | Yes |
| Topic classification | Yes | Yes (+ hierarchical) |
| Impact/Credibility/Urgency | Yes | Yes |
| Financial analysis | Yes | Yes (improved) |
| Geopolitical analysis | Yes | Yes (improved) |
| Sentiment analysis | Yes | Yes (improved) |
| Political bias detection | No | **Yes (NEW)** |
| 2-stage prompting | No | **Yes** |
| Budget redistribution | No | **Yes** |
| Event-driven storage | No | **Yes** |

### Storage Differences

| Aspect | V2 | V3 |
|--------|----|----|
| Storage location | Multiple tables (content_analysis_v2) | Unified table (article_analysis) |
| Data write pattern | Direct from service | Event-driven via feed-service |
| Database dependency | Tight coupling | Loose coupling |
| Access pattern | Direct query | Via feed-service API |
| Consistency | Eventually consistent | Strong consistency |

### Migration Considerations

**V3 is NOT a replacement for V2.** They are run in parallel:

1. **V2 (ARCHIVED 2025-11-24):** Legacy service, still processes articles for backward compatibility
2. **V3 (ACTIVE):** New default, used for all new articles

**Data Unification:** Both versions write to `public.article_analysis` table (unified storage)

---

## Troubleshooting

### Common Issues

#### 1. High Discard Rate (> 75%)

**Symptoms:**
- Too few articles kept for analysis
- Business logic requires lower quality articles

**Root Cause:**
- Tier0 threshold may be too strict (score ≥5 minimum)

**Solution:**
1. Check triage distribution:
```sql
SELECT
    (triage_results->>'keep')::boolean as kept,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM article_analysis
WHERE pipeline_version = '3.0'
GROUP BY kept;
```

2. Review low-scoring discarded articles:
```sql
SELECT
    article_id,
    (triage_results->>'priority_score')::int as score,
    (triage_results->>'category')::text as category,
    (triage_results->>'keep')::boolean as kept
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND (triage_results->>'priority_score')::int >= 4
  AND (triage_results->>'keep')::boolean = false
LIMIT 10;
```

3. Adjust threshold in `app/pipeline/tier0/triage.py` if needed (currently ≥5)

#### 2. High Cost Per Article (> $0.001)

**Symptoms:**
- Actual cost exceeds budget
- Cost per article trending upward

**Root Cause:**
- Tier1 or Tier2 exceeding allocated tokens
- All 6 specialists running (poor quick_check filtering)

**Solution:**
1. Check cost distribution:
```sql
SELECT
    ROUND(AVG((metrics->>'tier0_cost_usd')::float)::numeric, 6) as tier0_avg,
    ROUND(AVG((metrics->>'tier1_cost_usd')::float)::numeric, 6) as tier1_avg,
    ROUND(AVG((metrics->>'tier2_cost_usd')::float)::numeric, 6) as tier2_avg,
    ROUND(AVG((metrics->>'total_cost_usd')::float)::numeric, 6) as total_avg
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND created_at > NOW() - INTERVAL '1 day';
```

2. Check specialist execution:
```sql
SELECT
    (tier2_results->>'specialists_executed')::int as specialists_count,
    COUNT(*) as articles,
    ROUND(AVG((tier2_results->>'total_cost_usd')::float)::numeric, 6) as avg_cost
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND tier2_results IS NOT NULL
GROUP BY specialists_count
ORDER BY specialists_count;
```

3. Improve quick_check filtering in specialists to reduce deep_dive execution

#### 3. Articles Stuck in "processing" Status

**Symptoms:**
- Status never changes from "processing"
- Articles never complete analysis

**Root Cause:**
- Consumer crashed or queue disconnected
- Message processing error → DLQ

**Solution:**
1. Check consumer status:
```bash
docker ps | grep content-analysis-v3-consumer
```

2. If not running, check logs:
```bash
docker logs content-analysis-v3-consumer | tail -50
```

3. Check DLQ:
```bash
docker exec rabbitmq rabbitmqctl list_queues name messages | grep dlq
```

4. Inspect DLQ message (if present):
```bash
# Use RabbitMQ UI: http://localhost:15672
# Username: guest, Password: guest
# Navigate to: Queues → analysis_v3_requests_queue_dlq → Messages
```

5. Restart consumer:
```bash
docker compose restart content-analysis-v3-consumer
```

#### 4. Foundation Scores Display as "N/A"

**Issue (Fixed 2025-11-23):**

Backend transformation nests scores into `scores` object:

```python
# ❌ Wrong (data not found)
tier1.impact_score
tier1.credibility_score
tier1.urgency_score

# ✅ Correct
tier1.scores.impact_score
tier1.scores.credibility_score
tier1.scores.urgency_score
```

**Resolution:**
- Frontend updated to use nested structure
- TypeScript types document the structure
- Backend transformation includes clear comments

**Verification:**
```bash
# Check API response structure
curl http://localhost:8117/api/v1/results/{article_id} | jq '.tier1'

# Should show:
# {
#   "scores": {
#     "impact_score": 8.0,
#     "credibility_score": 7.0,
#     "urgency_score": 7.0
#   },
#   ...
# }
```

---

## Implementation Details

### Database Connections

**Connection Pool Configuration:**

```python
# app/core/database.py
await asyncpg.create_pool(
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    database=settings.POSTGRES_DB,
    min_size=2,      # Minimum connections
    max_size=10,     # Maximum connections
    command_timeout=60
)
```

**Optimal Settings:**
- min_size: 2 (background connections)
- max_size: 10 + (5 workers × 10 prefetch) = 60 recommended for production
- For development: max_size=10 is sufficient

### RabbitMQ Message Flow

**Request → Processing → Completion:**

```
1. PUBLISH (from feed-service)
   Exchange: news.events
   Routing Key: analysis.v3.request
   Payload: {article_id, title, url, content, run_tier2}

2. CONSUME (content-analysis-v3-consumer)
   Queue: analysis_v3_requests_queue
   Prefetch: 10
   Processing: Tier0 → Tier1 → Tier2

3. PUBLISH (from content-analysis-v3)
   Exchange: news.events
   Routing Key: analysis.v3.completed or analysis.v3.failed
   Payload: {article_id, success, tier0, tier1, tier2, metrics}

4. CONSUME (feed-service)
   Queue: analysis_v3_completed_queue
   Processing: Store in article_analysis table
```

**Failure Handling:**

```
Consumer Error
      ↓
Exception Caught
      ↓
Message REJECTED
      ↓
Sent to DLQ
      ↓
publish analysis.v3.failed event
      ↓
Manual intervention needed
```

### Testing

**Run Tests:**

```bash
# All tests
pytest tests/ -v

# Specific tier
pytest tests/test_tier0_triage.py -v
pytest tests/test_tier1_foundation.py -v
pytest tests/test_tier2_specialists.py -v

# Integration checkpoint
pytest tests/test_tier0_tier1_tier2_checkpoint.py -v
```

**Test Coverage (as of 2025-12-22):**
- ✓ Tier0 (Triage): 4/4 tests passing
- ✓ Tier1 (Foundation): 6/6 tests passing
- ✓ Tier2 (Specialists): 9/9 tests passing (with mocks for LLM calls)
- ✓ Integration: Full pipeline tested (Tier0→Tier1→Tier2)
- ✓ Consumer: Message handling, error recovery, DLQ routing
- ✓ Event Publishing: Completion and failure events

**Test Optimization:**
- Mocking: LLM provider calls mocked to avoid API costs during testing
- Speed: Full test suite completes in < 10 seconds
- Isolation: Each tier tested independently before integration
- Coverage: 100% of code paths covered (excluding error branches requiring live API failures)

---

## References

### Key Files

| File | Purpose |
|------|---------|
| `/app/main.py` | FastAPI application setup |
| `/app/core/config.py` | Configuration management |
| `/app/core/database.py` | Database connection pool |
| `/app/api/analysis.py` | REST API endpoints |
| `/app/pipeline/tier0/triage.py` | Tier0 triage module |
| `/app/pipeline/tier1/foundation.py` | Tier1 foundation extraction |
| `/app/pipeline/tier2/orchestrator.py` | Tier2 orchestrator |
| `/app/pipeline/tier2/specialists/` | 6 specialist modules |
| `/app/providers/base.py` | LLM provider abstraction |
| `/app/providers/gemini/provider.py` | Gemini implementation |
| `/app/messaging/request_consumer.py` | RabbitMQ consumer |
| `/app/messaging/event_publisher.py` | RabbitMQ publisher |
| `/app/models/schemas.py` | Pydantic models |

### Documentation Links

- **README:** `/home/cytrex/news-microservices/services/content-analysis-v3/README.md`
- **Changelog:** `/home/cytrex/news-microservices/services/content-analysis-v3/CHANGELOG.md`
- **Implementation Status:** `/home/cytrex/news-microservices/services/content-analysis-v3/IMPLEMENTATION_STATUS.md`
- **Bias Scorer Optimization:** `/home/cytrex/news-microservices/services/content-analysis-v3/BIAS_SCORER_OPTIMIZATION.md`
- **Postmortem Incidents:** `/home/cytrex/news-microservices/POSTMORTEMS.md`

### Environment & Deployment

- **Docker Compose:** `/home/cytrex/news-microservices/docker-compose.yml`
- **Python Version:** 3.12+
- **Dependencies:** See `requirements.txt` (43 packages)
- **API Documentation:** http://localhost:8117/docs (Swagger UI)

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.1.1 | 2025-12-22 | Documentation update - weighted budget allocation, BiasScorer details, consumer configuration |
| 1.1.0 | 2025-11-21 | Tier0 triage hardening, minimum threshold ≥5 |
| 1.0.0 | 2025-11-20 | Initial release with 6 specialists, 96.7% cost reduction |

---

**Last Updated:** 2025-12-22
**Maintainer:** Andreas (andreas@test.com)
**Status:** Production-Ready ✓

**Recent Documentation Updates (2025-12-22):**
- ✅ BiasScorer specialist details verified (always runs on all articles)
- ✅ Weighted budget allocation algorithm documented with examples
- ✅ Consumer configuration updated (3 workers, DLQ, Neo4j integration)
- ✅ RabbitMQ event handling expanded (error types, retry logic)
- ✅ Test coverage status updated
- ✅ Current specialist count confirmed: 6 modules (not 5)
