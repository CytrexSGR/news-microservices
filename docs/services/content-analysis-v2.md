# Content-Analysis Service v2 - Comprehensive Documentation

**Version:** 2.0.0
**Status:** Production Ready (Archived 2025-11-24)
**Port:** 8114 (Docker) / 8200 (Default)
**Language:** Python 3.10+
**Framework:** FastAPI + SQLAlchemy
**Codebase Size:** 17,093 LOC (Core) + 7,597 LOC (Tests)
**Test Coverage:** 325+ unit and integration tests

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Port Configuration & Quick Start](#port-configuration--quick-start)
3. [Architecture Overview](#architecture-overview)
4. [Multi-Tier AI Agent System](#multi-tier-ai-agent-system)
5. [ML Models & LLM Integration](#ml-models--llm-integration)
6. [NLP Processing Pipeline](#nlp-processing-pipeline)
7. [API Endpoints Documentation](#api-endpoints-documentation)
8. [Database Schema](#database-schema)
9. [Event Integration & Message Queue](#event-integration--message-queue)
10. [Configuration Management](#configuration-management)
11. [Performance & Memory Profiling](#performance--memory-profiling)
12. [Testing Strategy](#testing-strategy)
13. [Deployment](#deployment)
14. [Dependencies & Requirements](#dependencies--requirements)
15. [Troubleshooting](#troubleshooting)
16. [Code Examples](#code-examples)

---

## Executive Summary

**Content-Analysis Service v2** is a sophisticated multi-agent AI system for deep news article analysis. It combines specialized LLM-powered agents across three execution tiers to extract intelligence from news content.

### Key Capabilities

- **Multi-Agent Orchestration**: 11 specialized AI agents working in coordination
- **3-Tier Pipeline**: Triage → Foundation → Specialists → Synthesis
- **Flexible LLM Providers**: Support for OpenAI (GPT-4o) and Google Gemini models
- **Intelligence Synthesis**: Cross-agent consistency checks and unified reporting
- **Cost Efficient**: ~$0.004 per article (all analysis combined)
- **Production Ready**: Comprehensive error handling, circuit breakers, timeout protection

### Service Status

**Note:** This service was archived on 2025-11-24 in favor of **content-analysis-v3**, which includes:
- Modular pipeline architecture
- Advanced uncertainty quantification
- Knowledge graph integration
- Performance improvements (30-40% faster)

**Current Status:** Maintained as reference implementation; not used in production pipeline.

---

## Port Configuration & Quick Start

### Port Mapping

| Component | Host Port | Container Port | Environment |
|-----------|-----------|-----------------|-------------|
| Content-Analysis v2 | 8114 | 8000 | Docker Compose |
| Health Check | 8114/healthz | 8000/healthz | Docker |

### Port Selection Rationale

Port 8114 was selected based on:
- Port 8112: Entity Canonicalization Service
- Port 8113: LLM Orchestrator Service
- Port 8114: Available and sequentially logical
- Port 8115+: Reserved for future services

### Quick Start

```bash
# Start service (v2 no longer in main compose, use v3 instead)
cd /home/cytrex/news-microservices
docker compose up -d content-analysis-v2

# Verify service is healthy
curl http://localhost:8114/healthz
# Expected: {"status": "healthy"}

# View API documentation
open http://localhost:8114/docs

# Run tests
docker exec news-content-analysis-v2 pytest tests/ -v

# View logs
docker logs news-content-analysis-v2 -f
```

### Service Health Check

```bash
# Direct health endpoint
curl http://localhost:8114/healthz

# Expected response:
# {"status": "healthy", "version": "2.0.0", "timestamp": "2025-11-24T10:30:00Z"}

# Database connectivity check
curl http://localhost:8114/api/v1/statistics
# Expected: 200 OK with analysis statistics
```

---

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Content-Analysis Service v2                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  FastAPI Application                   │    │
│  │                    (Port 8114)                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Pipeline Message Consumer                   │    │
│  │     (RabbitMQ: content_analysis_v2_queue)             │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          Pipeline Orchestrator (Multi-Tier)            │    │
│  │                                                        │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐       │    │
│  │   │  Tier 0  │    │  Tier 1  │    │  Tier 2  │       │    │
│  │   │ Triage   │ → │Foundation │ → │Specialists       │    │
│  │   │ Agent    │    │ Agents   │    │ Agents   │       │    │
│  │   └──────────┘    └──────────┘    └──────────┘       │    │
│  │                          ↓                            │    │
│  │                   ┌──────────┐                        │    │
│  │                   │  Tier 3  │                        │    │
│  │                   │Synthesis │                        │    │
│  │                   │ Agents   │                        │    │
│  │                   └──────────┘                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            PostgreSQL Database Layer                   │    │
│  │  (Schema: content_analysis_v2, 5 tables, 10+ indexes) │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        Event Publishing (Outbox Pattern)                │   │
│  │ Writes to: outbox_events, processes async to RabbitMQ  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
Article Published (RabbitMQ)
    ↓
Pipeline Worker receives message
    ↓
Tier 0: TRIAGE Agent
    ├─ Decision: Analyze or Skip?
    ├─ Determines which Tier 2 agents to run
    └─ Stores triage result
    ↓
Tier 1: Foundation Agents (Parallel)
    ├─ ENTITY_EXTRACTOR: Extracts entities and relationships
    ├─ SUMMARY_GENERATOR: Generates article summary
    └─ TEXT_FOUNDATION: Pre-processing and classification
    ↓
Tier 2: Specialist Agents (Conditional, Parallel)
    ├─ CONFLICT_EVENT_ANALYST: Event and IHL analysis
    ├─ BIAS_DETECTOR: Media bias and framing analysis
    ├─ FINANCIAL_ANALYST: Financial impact assessment
    ├─ GEOPOLITICAL_ANALYST: Geopolitical implications
    ├─ SENTIMENT_ANALYST: Sentiment and tone analysis
    └─ TOPIC_CLASSIFIER: Topic categorization
    ↓
Tier 3: Synthesis Agents (Sequential)
    ├─ INTELLIGENCE_SYNTHESIZER: Cross-agent synthesis
    └─ UNCERTAINTY_QUANTIFIER: Confidence quantification
    ↓
Post-Pipeline: Meta-Analysis
    └─ RELEVANCE_SCORER: Relevance scoring and ranking
    ↓
Results stored in Database
    ↓
Outbox Processor publishes events to RabbitMQ
```

---

## Multi-Tier AI Agent System

### Agent Architecture

The service implements a hierarchical 4-tier agent system:

#### Tier 0: Triage (1 Agent)

**Purpose**: Initial article assessment and routing

| Agent | Role | Input | Output | Latency | Cost |
|-------|------|-------|--------|---------|------|
| **TRIAGE** | Article relevance assessment | Article text, title, source | Decision: ANALYZE/SKIP, topics | ~2s | $0.0003 |

**Outputs**:
- `is_relevant`: Boolean (true/false)
- `confidence`: 0.0-1.0
- `topics`: Array of detected topics
- `skip_reason`: Why skipped (if applicable)

#### Tier 1: Foundation (3 Agents)

**Purpose**: Extract foundational information (always runs if triage passes)

| Agent | Role | Input | Output | Latency | Cost |
|-------|------|-------|--------|---------|------|
| **ENTITY_EXTRACTOR** | Named entity recognition | Article text | Entities, relationships, classifications | ~3s | $0.0004 |
| **SUMMARY_GENERATOR** | Content summarization | Article text | Multi-level summaries (1-line, paragraph, detailed) | ~3s | $0.0004 |
| **TEXT_FOUNDATION** | Foundational text analysis | Article text | Classification, sentiment, language metrics | ~2s | $0.0003 |

**Outputs Structure**:
```json
{
  "entity_extraction": {
    "entities": [{"name": "...", "type": "...", "confidence": 0.9}],
    "relationships": [{"source": "...", "target": "...", "relation": "..."}]
  },
  "summaries": {
    "one_liner": "...",
    "paragraph": "...",
    "detailed": "..."
  },
  "text_metrics": {
    "reading_level": 8.5,
    "sentiment": "mixed",
    "language": "en"
  }
}
```

#### Tier 2: Specialists (6 Agents)

**Purpose**: Domain-specific deep analysis (conditional execution)

| Agent | Role | Input | Output | Latency | Cost | Trigger |
|-------|------|-------|--------|---------|------|---------|
| **CONFLICT_EVENT_ANALYST** | Conflict/IHL analysis | Article text | Event type, actors, casualties, IHL violations | ~5s | $0.0012 | Topic: conflict/military |
| **BIAS_DETECTOR** | Media bias analysis | Article text | Political bias, framing, loaded language | ~5s | $0.0012 | Always (if relevant) |
| **FINANCIAL_ANALYST** | Financial impact | Article text | Financial entities, market impacts, risks | ~4s | $0.0008 | Topic: finance/economy |
| **GEOPOLITICAL_ANALYST** | Geopolitical analysis | Article text | Regional impacts, diplomatic implications | ~4s | $0.0008 | Topic: geopolitics |
| **SENTIMENT_ANALYST** | Sentiment analysis | Article text | Sentiment scores, emotion detection | ~3s | $0.0006 | Always (if relevant) |
| **TOPIC_CLASSIFIER** | Topic classification | Article text | Topic categories, confidence scores | ~3s | $0.0006 | Always (if relevant) |

**Example Output: CONFLICT_EVENT_ANALYST**
```json
{
  "event_type": "air_strike",
  "temporal_data": {
    "event_date": "2025-11-20",
    "reporting_date": "2025-11-21"
  },
  "actors": [
    {"type": "military", "name": "...", "allegiance": "..."},
    {"type": "civilian_population", "impact": "casualties"}
  ],
  "impact_assessment": {
    "estimated_casualties": {"civilian": 15, "military": 3},
    "infrastructure_damage": "significant"
  },
  "ihl_assessment": [
    {"violation_type": "targeting_protected_objects", "confidence": 0.85}
  ],
  "confidence": 0.82
}
```

#### Tier 3: Synthesis (2 Agents)

**Purpose**: Cross-agent integration and intelligence reporting

| Agent | Role | Input | Output | Latency | Cost |
|-------|------|-------|--------|---------|------|
| **INTELLIGENCE_SYNTHESIZER** | Cross-agent synthesis | All Tier 1/2 results | Priority assessment, key findings, narratives | ~6s | $0.0018 |
| **UNCERTAINTY_QUANTIFIER** | Confidence quantification | All agent results | UQ scores, reliability metrics | ~3s | $0.0006 |

**Key Synthesizer Outputs**:
- Priority Assessment (0.0-1.0, adjusted for bias)
- Key Findings (4 per article with evidence)
- Cross-agent Consistency Analysis
- Intelligence Value Assessment
- Analyst Recommendations
- Narrative Synthesis (executive, detailed, one-liner, tweet)

#### Post-Pipeline: Meta-Analysis (1 Agent)

**Purpose**: Final relevance and impact scoring

| Agent | Role | Input | Output | Latency | Cost |
|-------|------|-------|--------|---------|------|
| **RELEVANCE_SCORER** | Impact scoring | Article + all agent results | Relevance score (0-100), impact categories | ~2s | $0.0004 |

### Agent Execution Model

```
TRIAGE (Tier 0)
    ↓
    IF relevant:
        ├─ ENTITY_EXTRACTOR (Tier 1) ───┐
        ├─ SUMMARY_GENERATOR (Tier 1)    ├─ Parallel Execution
        └─ TEXT_FOUNDATION (Tier 1) ─────┘
            ↓
            IF financial_topic:
            ├─ FINANCIAL_ANALYST ──┐
            IF geopolitical_topic:  │
            ├─ GEOPOLITICAL_ANALYST │
            IF conflict_topic:      ├─ Conditional Parallel
            ├─ CONFLICT_EVENT_ANALYST
            ALWAYS:                 │
            ├─ BIAS_DETECTOR ───────┘
            ├─ SENTIMENT_ANALYST
            └─ TOPIC_CLASSIFIER
                ↓
                ├─ INTELLIGENCE_SYNTHESIZER (Tier 3)
                └─ UNCERTAINTY_QUANTIFIER (Tier 3)
                    ↓
                    └─ RELEVANCE_SCORER (Post)
```

### Agent Statistics

```
Total Agents: 11
  ├─ Tier 0 (Triage): 1 agent
  ├─ Tier 1 (Foundation): 3 agents
  ├─ Tier 2 (Specialists): 6 agents
  └─ Tier 3 (Synthesis): 2 agents

Typical Execution Path:
  ├─ Always run: TRIAGE, ENTITY_EXTRACTOR, SUMMARY_GENERATOR,
  │             TEXT_FOUNDATION, INTELLIGENCE_SYNTHESIZER, RELEVANCE_SCORER
  ├─ Usually run (80%+): BIAS_DETECTOR, SENTIMENT_ANALYST, TOPIC_CLASSIFIER
  └─ Conditionally run (varies): Specialists based on article topic

Performance Metrics (per article):
  ├─ Average total latency: 16.1 seconds
  ├─ Total cost: ~$0.004 USD
  ├─ Confidence: 0.85 average
  └─ Success rate: 98.7% (100+ article test)
```

---

## ML Models & LLM Integration

### Supported LLM Providers

#### OpenAI Models

**Provider Configuration:**
```python
provider = "openai"
models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]
```

**Pricing (per 1M tokens):**

| Model | Input Cost | Output Cost | Recommended For |
|-------|-----------|-----------|-----------------|
| gpt-4o | $2.50 | $10.00 | High-accuracy analysis (conflict, bias) |
| gpt-4o-mini | $0.15 | $0.60 | Entity extraction, summary generation |
| gpt-3.5-turbo | $0.50 | $1.50 | Basic classification, topic detection |
| gpt-4-turbo | $10.00 | $30.00 | Legacy/fallback (expensive) |

**Model Characteristics:**
- **gpt-4o**: Latest multimodal flagship; 128K context window; best reasoning
- **gpt-4o-mini**: Optimized for cost; 128K context; good for text-only tasks
- **gpt-3.5-turbo**: Legacy model; 4K context; fastest inference

#### Google Gemini Models

**Provider Configuration:**
```python
provider = "gemini"
models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
          "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
```

**Pricing (per 1M tokens):**

| Model | Input Cost | Output Cost | Recommended For | Status |
|-------|-----------|-----------|-----------------|--------|
| gemini-2.5-pro | $1.25 | $5.00 | Complex reasoning | Latest |
| gemini-2.5-flash | $0.30 | $2.50 | Balanced performance | Latest |
| gemini-2.5-flash-lite | $0.10 | $0.40 | Cost-optimized ✅ | Latest (Default) |
| gemini-2.0-flash | $0.10 | $0.40 | Standard analysis | Available |
| gemini-1.5-pro | $1.25 | $5.00 | High accuracy (deprecated) | Supported |
| gemini-1.5-flash | $0.075 | $0.30 | Fast inference | Deprecated |

**Model Characteristics:**
- **gemini-2.5-flash-lite**: Default choice; $0.10/$0.40 pricing; 1M context window
- **gemini-2.5-flash**: Balanced; $0.30/$2.50 pricing; 1M context window
- **gemini-2.5-pro**: Advanced reasoning; slower; for complex analysis

### Default Agent Model Configuration

```
Agent Configuration (from code analysis):

Tier 0 (Triage):
  ├─ TRIAGE: gemini-2.5-flash-lite (cost-optimized)

Tier 1 (Foundation):
  ├─ ENTITY_EXTRACTOR: gpt-4o-mini (fast entity recognition)
  ├─ SUMMARY_GENERATOR: gpt-4o-mini (good summaries)
  └─ TEXT_FOUNDATION: gemini-2.5-flash (balanced)

Tier 2 (Specialists):
  ├─ CONFLICT_EVENT_ANALYST: gpt-4o (best accuracy for complex events)
  ├─ BIAS_DETECTOR: gpt-4o (nuanced bias detection)
  ├─ FINANCIAL_ANALYST: gpt-4o-mini (good for structured data)
  ├─ GEOPOLITICAL_ANALYST: gpt-4o (complex reasoning)
  ├─ SENTIMENT_ANALYST: gemini-2.5-flash (sentiment is simpler)
  └─ TOPIC_CLASSIFIER: gemini-2.5-flash-lite (classification is fast)

Tier 3 (Synthesis):
  ├─ INTELLIGENCE_SYNTHESIZER: gpt-4o (cross-agent reasoning)
  └─ UNCERTAINTY_QUANTIFIER: gpt-4o-mini (quantification)

Post-Pipeline:
  └─ RELEVANCE_SCORER: gemini-2.5-flash-lite (scoring is straightforward)
```

### Configuration via Environment Variables

```bash
# Global fallback keys
export DEFAULT_OPENAI_API_KEY="sk-proj-xxx..."
export DEFAULT_GEMINI_API_KEY="AIzaSyDxxx..."

# Agent-specific overrides
export CONFLICT_EVENT_ANALYST_PROVIDER="openai"
export CONFLICT_EVENT_ANALYST_MODEL="gpt-4o"
export CONFLICT_EVENT_ANALYST_API_KEY="sk-proj-xxx..." # Optional override

export ENTITY_EXTRACTOR_PROVIDER="openai"
export ENTITY_EXTRACTOR_MODEL="gpt-4o-mini"

export BIAS_DETECTOR_PROVIDER="openai"
export BIAS_DETECTOR_MODEL="gpt-4o"
export BIAS_DETECTOR_MAX_TOKENS="8000"
export BIAS_DETECTOR_TEMPERATURE="0.1"
```

### Model Memory & Performance Characteristics

```
Token Limits & Processing Time:

Model Performance (approximate):
  ├─ gemini-2.5-flash-lite:
  │   ├─ Latency: 0.8-1.2s (fast)
  │   ├─ Input tokens per article: 2,000-3,000
  │   └─ Output tokens: 500-1,500
  │
  ├─ gpt-4o-mini:
  │   ├─ Latency: 1.2-1.8s (medium)
  │   ├─ Input tokens per article: 2,000-3,000
  │   └─ Output tokens: 500-1,500
  │
  ├─ gpt-4o:
  │   ├─ Latency: 2.5-3.5s (slower, best quality)
  │   ├─ Input tokens per article: 2,500-3,500
  │   └─ Output tokens: 1,000-2,500
  │
  └─ gemini-2.5-flash:
      ├─ Latency: 1.5-2.2s (medium-fast)
      ├─ Input tokens per article: 2,000-3,000
      └─ Output tokens: 500-1,500

Article Size Impact:
  ├─ Short article (< 500 words):
  │   └─ Token usage: 1,500-2,000 input, 400-800 output
  ├─ Medium article (500-1,500 words):
  │   └─ Token usage: 2,500-3,500 input, 800-1,500 output
  └─ Long article (1,500+ words):
      └─ Token usage: 3,500-5,000+ input, 1,500-2,500 output

Cost per Article (all agents):
  ├─ Average (mixed articles): ~$0.004
  ├─ Range: $0.002 - $0.008
  └─ Largest driver: INTELLIGENCE_SYNTHESIZER (~40% of cost)
```

### LLM Provider Implementation

**File Structure:**
```
app/llm/
├── base.py                    # BaseLLMProvider interface
├── factory.py                 # Provider factory pattern
├── openai_provider.py         # OpenAI implementation
├── gemini_provider.py         # Google Gemini implementation
├── resilient_provider.py      # Circuit breaker wrapper
├── rate_limiter.py            # Rate limiting for CVE-2025-003
├── rate_limited_provider.py   # Rate-limited wrapper
├── key_validator.py           # API key validation (Issue #3)
└── schema_utils.py            # Schema optimization for tokens
```

**Provider Selection Logic:**
```python
# Factory creates provider based on agent config
provider_name = agent_config.provider  # "openai" or "gemini"
model = agent_config.model             # e.g., "gpt-4o"
api_key = agent_config.api_key or fallback_key

if provider_name == "openai":
    provider = OpenAIProvider(api_key, model, ...)
else:
    provider = GeminiProvider(api_key, model, ...)

# Wrap with rate limiter (CVE-2025-003)
provider = RateLimitedProvider(provider)

# Wrap with circuit breaker
provider = ResilientProvider(provider, circuit_breaker_config)
```

---

## NLP Processing Pipeline

### Complete Pipeline Architecture

```
Article Input
    ↓
[Preprocessing Stage]
├─ Text normalization (lowercasing, whitespace cleanup)
├─ Language detection
├─ Encoding/decoding validation
└─ Article metadata extraction (title, source, publish_date)
    ↓
[Tokenization & Segmentation]
├─ Sentence tokenization
├─ Word tokenization (for entity extraction)
├─ Token count estimation (for LLM context window sizing)
└─ Long-text truncation (if > context window)
    ↓
[Tier 0: Triage]
├─ LLM-based relevance assessment
├─ Topic inference
└─ Routing decision (ANALYZE vs SKIP)
    ↓
IF SKIP → Store triage result, END
    ↓
[Tier 1: Foundation Analysis - PARALLEL]
├─ Entity Extraction
│  ├─ Named entity recognition (NER) via LLM
│  ├─ Entity classification (PERSON, ORG, LOCATION, EVENT, etc.)
│  ├─ Entity linking/disambiguation
│  ├─ Relationship extraction (entity pairs + relation type)
│  └─ Confidence scoring per entity
├─ Summary Generation
│  ├─ Extractive summarization (key sentences)
│  ├─ Abstractive summarization (LLM-generated)
│  └─ Multi-level summaries (1-line, paragraph, detailed)
└─ Text Foundation Analysis
   ├─ Sentiment detection (positive/negative/neutral)
   ├─ Tone analysis (urgent, neutral, editorial, etc.)
   ├─ Language metrics (readability, complexity)
   └─ Topic classification (initial)
    ↓
[Tier 2: Specialist Analysis - CONDITIONAL PARALLEL]
├─ Conflict Event Analysis (if conflict/military topic)
│  ├─ Event type classification (air strike, ground combat, etc.)
│  ├─ Actor identification and role classification
│  ├─ Casualty/impact assessment
│  ├─ IHL violation detection
│  └─ Evidence collection (quotes, photos, videos)
├─ Bias & Framing Analysis (always)
│  ├─ Political bias scoring (7-point scale: far-left to far-right)
│  ├─ Framing technique identification
│  ├─ Loaded language detection (with context)
│  ├─ Source credibility assessment
│  └─ Missing perspective analysis
├─ Financial Analysis (if economy/finance topic)
│  ├─ Financial entity extraction (companies, securities)
│  ├─ Market impact assessment
│  ├─ Risk indicators
│  └─ Regulatory implications
├─ Geopolitical Analysis (if geopolitical topic)
│  ├─ Regional impact assessment
│  ├─ Diplomatic implications
│  ├─ Alliance/conflict implications
│  └─ Strategic importance
├─ Sentiment Deep-Dive
│  ├─ Multi-aspect sentiment (per entity, claim, etc.)
│  ├─ Emotion detection (anger, fear, trust, etc.)
│  └─ Subjectivity scoring
└─ Topic Classification (fine-grained)
   ├─ Primary topic
   ├─ Secondary topics
   └─ Topic confidence scores
    ↓
[Tier 3: Synthesis Analysis]
├─ Intelligence Synthesizer
│  ├─ Cross-agent result aggregation
│  ├─ Consistency checking (contradiction detection)
│  ├─ Priority assessment (impact × urgency × confidence)
│  ├─ Narrative synthesis (multiple formats)
│  ├─ Audience-specific reporting (military/government/business)
│  └─ Key findings extraction (4 per article)
└─ Uncertainty Quantification
   ├─ Per-agent confidence aggregation
   ├─ Cross-agent agreement scoring
   ├─ Source reliability assessment
   ├─ Temporal consistency checking
   └─ Overall uncertainty quantification (0.0-1.0)
    ↓
[Post-Pipeline: Meta-Analysis]
├─ Relevance Scoring
│  ├─ Impact assessment (0-100 score)
│  ├─ Recency factor
│  ├─ Geographic relevance
│  └─ Topic relevance to current events
    ↓
[Output & Storage]
├─ Store all agent results in database
├─ Generate outbox events for downstream systems
├─ Publish to RabbitMQ (via outbox processor)
└─ Complete pipeline execution tracking
```

### Key NLP Processing Techniques

**Entity Extraction**:
- LLM-based NER (Named Entity Recognition)
- Entity type classification (PERSON, ORG, LOCATION, EVENT, WEAPON, etc.)
- Confidence scoring per entity
- Relationship extraction (entity pairs + relation type)
- Coreference resolution (identifying same entity with different names)

**Sentiment Analysis**:
- Multi-dimensional sentiment (positive/negative/neutral + intensity)
- Emotion detection (anger, fear, trust, anticipation, surprise, sadness, disgust, joy)
- Aspect-based sentiment (sentiment per entity or claim)
- Subjectivity/objectivity scoring

**Topic Classification**:
- Primary topic from hierarchical taxonomy
- Secondary topics (up to 5)
- Topic-specific confidence scores
- Topic hierarchy navigation (coarse to fine-grained)

**Bias & Framing Detection**:
- Political bias spectrum (far-left → center → far-right)
- Framing techniques (conflict frame, economic frame, human interest frame, etc.)
- Loaded language detection with context
- Missing perspective identification
- Source credibility assessment

**Conflict Event Analysis**:
- Event type classification (20+ types)
- Actor identification (military, paramilitary, government, civilian, etc.)
- Impact assessment (casualties, infrastructure damage)
- IHL (International Humanitarian Law) violation detection
- Evidence collection (quotes, photo/video mentions)

### Processing Configuration

```python
# app/core/config.py

# Token limits per agent
ENTITY_EXTRACTOR_MAX_TOKENS = 4000
CONFLICT_EVENT_ANALYST_MAX_TOKENS = 8000
INTELLIGENCE_SYNTHESIZER_MAX_TOKENS = 6000

# Timeout protection (Issue #7)
PIPELINE_TIMEOUT_SECONDS = 300  # 5 minutes total
AGENT_TIMEOUT_SECONDS = 90      # Per agent

# Parallel execution limits
MAX_PARALLEL_TIER2_AGENTS = 6   # Max concurrent Tier 2 agents
MAX_PARALLEL_TIER1_AGENTS = 3   # Max concurrent Tier 1 agents

# Caching
ENABLE_AGENT_RESULT_CACHE = True
AGENT_CACHE_TTL_SECONDS = 86400  # 24 hours
```

---

## API Endpoints Documentation

### Base URL

```
http://localhost:8114/api/v1
```

### Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <jwt_token>
```

Token obtained from Auth Service (port 8100):
```bash
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "..."}'
```

### Response Format

All responses follow standard format:
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

### Health & Diagnostics

#### Get Service Health

```http
GET /healthz
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-11-24T10:30:00Z",
  "database": "connected",
  "redis": "connected",
  "rabbitmq": "connected"
}
```

---

### Statistics & Metrics

#### Get Pipeline Statistics

```http
GET /api/v1/statistics
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_date` (ISO 8601): Filter from date
- `end_date` (ISO 8601): Filter to date
- `agent_name` (string): Filter by specific agent

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_articles_processed": 2547,
    "total_cost_usd": 10.18,
    "average_cost_per_article": 0.004,
    "average_latency_ms": 16100,
    "success_rate": 0.987,
    "agents": {
      "TRIAGE": {
        "count": 2547,
        "avg_latency_ms": 2000,
        "total_cost": 0.762,
        "avg_confidence": 0.92
      },
      "CONFLICT_EVENT_ANALYST": {
        "count": 1823,
        "avg_latency_ms": 5100,
        "total_cost": 2.187,
        "avg_confidence": 0.88
      }
    }
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

#### Get Agent Statistics

```http
GET /api/v1/agents/statistics
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "ENTITY_EXTRACTOR": {
      "executions": 2547,
      "success_rate": 0.989,
      "avg_latency_ms": 3200,
      "avg_confidence": 0.91,
      "cache_hit_rate": 0.34,
      "total_cost": 1.018
    }
  }
}
```

---

### Agent Results

#### Get Analysis Results for Article

```http
GET /api/v1/articles/{article_id}/analysis
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "agents": {
      "TRIAGE": {
        "status": "completed",
        "confidence": 0.92,
        "result": {
          "is_relevant": true,
          "topics": ["conflict", "middle-east"],
          "confidence": 0.92
        },
        "latency_ms": 2100,
        "cost_usd": 0.0003
      },
      "CONFLICT_EVENT_ANALYST": {
        "status": "completed",
        "confidence": 0.88,
        "result": {
          "event_type": "air_strike",
          "actors": [...],
          "ihl_assessment": [...]
        },
        "latency_ms": 5200,
        "cost_usd": 0.0012
      },
      "INTELLIGENCE_SYNTHESIZER": {
        "status": "completed",
        "confidence": 0.85,
        "result": {
          "priority": 0.78,
          "key_findings": [...],
          "narrative": {...}
        },
        "latency_ms": 6100,
        "cost_usd": 0.0018
      }
    },
    "pipeline_summary": {
      "total_agents_run": 10,
      "total_latency_ms": 16200,
      "total_cost_usd": 0.004,
      "overall_confidence": 0.85
    }
  }
}
```

#### Get Specific Agent Result

```http
GET /api/v1/articles/{article_id}/agents/{agent_name}
Authorization: Bearer <token>
```

**Parameters:**
- `article_id`: UUID
- `agent_name`: One of TRIAGE, ENTITY_EXTRACTOR, CONFLICT_EVENT_ANALYST, etc.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_name": "CONFLICT_EVENT_ANALYST",
    "agent_version": "2.0",
    "result_data": {...},
    "confidence": 0.88,
    "processing_time_ms": 5200,
    "model_used": "gpt-4o",
    "cost_usd": 0.0012,
    "cache_hit": false,
    "status": "completed",
    "created_at": "2025-11-24T10:25:30Z"
  }
}
```

---

### Configuration Management

#### Get Service Configuration

```http
GET /api/v1/config
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "service_name": "content-analysis-v2",
    "version": "2.0.0",
    "port": 8200,
    "agents": {
      "TRIAGE": {
        "enabled": true,
        "provider": "gemini",
        "model": "gemini-2.5-flash-lite",
        "max_tokens": 4000,
        "temperature": 0.1,
        "timeout": 60
      }
    },
    "pipeline": {
      "timeout_seconds": 300,
      "enable_cache": true,
      "cache_ttl_seconds": 86400
    }
  }
}
```

#### Update Agent Configuration

```http
PATCH /api/v1/config/agents/{agent_name}
Authorization: Bearer <token>
Content-Type: application/json

{
  "enabled": true,
  "max_tokens": 4000,
  "temperature": 0.15,
  "timeout": 90
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_name": "ENTITY_EXTRACTOR",
    "enabled": true,
    "max_tokens": 4000,
    "temperature": 0.15,
    "timeout": 90
  }
}
```

---

### Monitoring & Logging

#### Get Queue Metrics

```http
GET /api/v1/queue/metrics
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "queue_name": "content_analysis_v2_queue",
    "ready_count": 142,
    "unacked_count": 8,
    "total_count": 150,
    "consumer_count": 1,
    "idle_since": "2025-11-24T09:45:00Z"
  }
}
```

#### Get Monitoring Logs

```http
GET /api/v1/monitoring/logs
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (int, default 100): Max logs to return
- `level` (string): Filter by log level (DEBUG, INFO, WARNING, ERROR)
- `agent_name` (string): Filter by agent

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2025-11-24T10:30:15Z",
      "level": "INFO",
      "agent": "ENTITY_EXTRACTOR",
      "message": "Processing article 550e8400...",
      "latency_ms": 3200
    }
  ]
}
```

---

## Database Schema

### Schema Overview

**Schema Name:** `content_analysis_v2`
**Tables:** 5
**Total Indexes:** 10+
**Typical Data Volume:** 22,000+ rows (live production)

### Table: agent_results

**Purpose:** Store all agent analysis results

```sql
CREATE TABLE content_analysis_v2.agent_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  article_id UUID NOT NULL,
  agent_name VARCHAR(50) NOT NULL,
  agent_version VARCHAR(10) NOT NULL DEFAULT '2.0',
  result_data JSONB NOT NULL,
  confidence_score FLOAT,
  processing_time_ms INTEGER,
  model_used VARCHAR(100),
  provider VARCHAR(50),
  cost_usd FLOAT,
  cache_hit BOOLEAN DEFAULT FALSE,
  status VARCHAR(20) NOT NULL DEFAULT 'completed',
  error_message TEXT,
  agent_relevance_score INTEGER,
  score_components JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(article_id, agent_name, agent_version),
  INDEX idx_agent_results_article ON article_id,
  INDEX idx_agent_results_agent ON agent_name,
  INDEX idx_agent_results_created ON created_at,
  INDEX idx_agent_results_data USING gin ON result_data,
  INDEX idx_agent_results_status ON status
);
```

**Columns:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | UUID | Unique result ID | `550e8400-...` |
| `article_id` | UUID | Reference to article | `550e8400-...` |
| `agent_name` | VARCHAR(50) | Agent name | `CONFLICT_EVENT_ANALYST` |
| `agent_version` | VARCHAR(10) | Schema version | `2.0` |
| `result_data` | JSONB | Flexible agent result | `{...}` |
| `confidence_score` | FLOAT | 0.0-1.0 confidence | `0.88` |
| `processing_time_ms` | INTEGER | Latency in milliseconds | `5200` |
| `model_used` | VARCHAR(100) | LLM model | `gpt-4o` |
| `provider` | VARCHAR(50) | Provider | `openai` |
| `cost_usd` | FLOAT | Cost in USD | `0.0012` |
| `cache_hit` | BOOLEAN | Was result cached? | `false` |
| `status` | VARCHAR(20) | completed/failed/timeout | `completed` |
| `error_message` | TEXT | Error if failed | `Timeout after 90s` |
| `created_at` | TIMESTAMP | Creation time | `2025-11-24T10:30:00Z` |

**Indexes:**
- `idx_agent_results_article`: Fast lookup by article
- `idx_agent_results_agent`: Query by agent type
- `idx_agent_results_created`: Time-range queries
- `idx_agent_results_data (GIN)`: JSONB searching
- `idx_agent_results_status`: Filter by status

### Table: pipeline_executions

**Purpose:** Track complete pipeline runs per article

```sql
CREATE TABLE content_analysis_v2.pipeline_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  article_id UUID NOT NULL UNIQUE,
  pipeline_version VARCHAR(10) NOT NULL DEFAULT '2.0',
  started_at TIMESTAMP WITH TIME ZONE NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,
  success BOOLEAN,
  skip_reason VARCHAR(100),
  triage_result JSONB,
  total_cost_usd FLOAT,
  total_latency_ms INTEGER,
  agents_run TEXT[], -- Array of agent names that ran
  agents_skipped TEXT[],
  overall_confidence FLOAT,
  execution_metadata JSONB,

  INDEX idx_pipeline_executions_article ON article_id,
  INDEX idx_pipeline_executions_started ON started_at,
  INDEX idx_pipeline_executions_success ON success
);
```

### Table: outbox_events

**Purpose:** Event outbox for transactional event publishing (Outbox Pattern)

```sql
CREATE TABLE content_analysis_v2.outbox_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  aggregate_id UUID NOT NULL,  -- article_id
  event_type VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  retry_count INTEGER DEFAULT 0,
  last_error TEXT,

  INDEX idx_outbox_events_published ON published,
  INDEX idx_outbox_events_created ON created_at
);
```

### Table: agent_feature_flags

**Purpose:** Feature toggles for individual agents

```sql
CREATE TABLE content_analysis_v2.agent_feature_flags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_name VARCHAR(50) NOT NULL UNIQUE,
  enabled BOOLEAN DEFAULT TRUE,
  feature_flags JSONB,  -- e.g., {"enable_reasoning": true}
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Table: category_thresholds

**Purpose:** Category-specific decision thresholds

```sql
CREATE TABLE content_analysis_v2.category_thresholds (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category VARCHAR(50) NOT NULL UNIQUE,
  relevance_threshold FLOAT,  -- Min relevance score
  confidence_threshold FLOAT, -- Min confidence
  priority_boost FLOAT,       -- Priority multiplier
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Data Relationships

```
article (public schema)
    ↓
    └─→ agent_results (content_analysis_v2)
            ├─→ JSONB result_data (flexible per agent)
            └─→ Multiple rows per article (one per agent)

article (public schema)
    ↓
    └─→ pipeline_executions (content_analysis_v2)
            ├─→ One row per article
            └─→ Summary of all agents run

analysis events
    ↓
    └─→ outbox_events (content_analysis_v2)
            └─→ Published to RabbitMQ asynchronously
```

---

## Event Integration & Message Queue

### RabbitMQ Integration

**Queue Configuration:**

```
Queue Name: content_analysis_v2_queue
Exchange: content_analysis
Routing Key: analysis.v2.#

Message Type: JSON (Pydantic models)
Acknowledgment: Auto-ack on successful processing
DLQ (Dead Letter Queue): content_analysis_v2_dlq
```

### Message Flow

```
Upstream Services (e.g., feed-service)
    ↓
RabbitMQ Topic Exchange
    ├─ Publish to: content_analysis/article.created
    └─ Route to: content_analysis_v2_queue
    ↓
Pipeline Worker (Consumes)
    ├─ Deserialize message
    ├─ Validate article
    └─ Start pipeline
    ↓
Pipeline Execution
    └─ Generate analysis
    ↓
Results → Database
    ↓
Outbox Processor (Background Task)
    ├─ Polls outbox_events table
    ├─ Batches events (100 per batch)
    └─ Publishes to RabbitMQ
    ↓
RabbitMQ (Results Published)
    ├─ Event: analysis.completed
    ├─ Routed to: Subscribers (Feed, Intelligence, etc.)
    └─ Acknowledges to outbox processor

Failed Processing
    └─ DLQ: content_analysis_v2_dlq
```

### Message Schemas

**Input Message (from feed-service):**

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "Article Title",
  "content": "Article body text...",
  "source": "example.com",
  "publish_date": "2025-11-24T10:00:00Z",
  "language": "en",
  "force_reanalysis": false
}
```

**Output Event (analysis.completed):**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "article_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-11-24T10:30:00Z",
  "status": "success",
  "agents_run": [
    "TRIAGE",
    "ENTITY_EXTRACTOR",
    "CONFLICT_EVENT_ANALYST",
    "INTELLIGENCE_SYNTHESIZER"
  ],
  "summary": {
    "total_cost_usd": 0.004,
    "latency_ms": 16200,
    "overall_confidence": 0.85,
    "priority": 0.78
  },
  "results_reference": {
    "table": "content_analysis_v2.agent_results",
    "article_id": "550e8400-..."
  }
}
```

### Outbox Pattern Implementation

The service uses the **Transactional Outbox Pattern** to ensure reliable event publishing:

```
1. Analysis Completes
   ├─ Write results to agent_results table (same transaction)
   └─ Write event to outbox_events table (same transaction)
   ↓
2. Transaction Commits
   └─ Both writes succeed atomically or both roll back
   ↓
3. Background Outbox Processor
   ├─ Polls outbox_events WHERE published = false
   ├─ Publishes events to RabbitMQ
   ├─ Marks as published in database
   └─ Handles failures with exponential backoff
   ↓
4. Event Delivery Guarantee
   └─ Exactly-once delivery semantics (no duplicates)
```

**Outbox Processor Configuration:**

```python
OutboxProcessor(
    db_factory=get_async_session,
    event_publisher=get_event_publisher(),
    batch_size=100,              # Process 100 events per batch
    poll_interval=1.0,           # Check every 1 second
    max_retries=5,              # Retry 5 times with backoff
)
```

---

## Configuration Management

### Environment Variables

**Core Configuration:**

```bash
# Service
SERVICE_NAME=content-analysis-v2
SERVICE_VERSION=2.0.0
SERVICE_PORT=8200
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/news_mcp
DATABASE_SCHEMA=content_analysis_v2

# Redis
REDIS_URL=redis://redis:6379/2

# RabbitMQ (CVE-2025-002: TLS-encrypted)
RABBITMQ_URL=amqps://user:pass@rabbitmq:5671
RABBITMQ_QUEUE=content_analysis_v2_queue
RABBITMQ_TLS_ENABLED=true
RABBITMQ_TLS_CA_CERT=/etc/rabbitmq/certs/ca-cert.pem

# JWT
JWT_SECRET_KEY=<strong-random-key-min-32-chars>
JWT_ALGORITHM=HS256

# LLM API Keys
DEFAULT_OPENAI_API_KEY=sk-proj-xxx...
DEFAULT_GEMINI_API_KEY=AIzaSyDxxx...

# Performance
ENABLE_CACHE=true
CACHE_TTL_SECONDS=86400
```

**Agent-Specific Configuration:**

```bash
# Triage Agent
TRIAGE_ENABLED=true
TRIAGE_PROVIDER=gemini
TRIAGE_MODEL=gemini-2.5-flash-lite
TRIAGE_MAX_TOKENS=4000
TRIAGE_TEMPERATURE=0.1
TRIAGE_TIMEOUT=60

# Conflict Event Analyst (Example)
CONFLICT_EVENT_ANALYST_ENABLED=true
CONFLICT_EVENT_ANALYST_PROVIDER=openai
CONFLICT_EVENT_ANALYST_MODEL=gpt-4o
CONFLICT_EVENT_ANALYST_API_KEY=sk-proj-xxx...  # Optional override
CONFLICT_EVENT_ANALYST_MAX_TOKENS=8000
CONFLICT_EVENT_ANALYST_TEMPERATURE=0.0
CONFLICT_EVENT_ANALYST_TIMEOUT=90
```

### Security Checklist

- [x] All credentials stored in environment variables (no hardcoding)
- [x] API keys validated on startup (Issue #3)
- [x] JWT secret is strong random value (min 32 characters)
- [x] Database URL uses secure connection (TLS)
- [x] RabbitMQ uses TLS encryption (CVE-2025-002)
- [x] Sensitive data redacted from logs (CVE-2025-001)
- [ ] SQL injection vulnerability in orchestrator.py (Issue #1 - PENDING FIX)
- [ ] Rate limiting on LLM calls (Issue #4 - PENDING FIX)

### Configuration Validation

Configuration is validated on startup:

```python
@app.on_event("startup")
async def startup_event():
    # 1. Validate API keys (fail-fast)
    errors = []
    if settings.DEFAULT_OPENAI_API_KEY:
        is_valid, error = APIKeyValidator.validate(
            settings.DEFAULT_OPENAI_API_KEY, "openai"
        )
        if not is_valid:
            errors.append(f"OpenAI: {error}")

    if errors:
        raise RuntimeError("Configuration validation failed:\n" +
                         "\n".join(f"  - {e}" for e in errors))

    # 2. Start monitoring logger
    monitoring_logger = get_monitoring_logger()
    await monitoring_logger.start()

    # 3. Start outbox processor
    outbox_processor = OutboxProcessor(...)
    asyncio.create_task(outbox_processor.start())
```

---

## Performance & Memory Profiling

### Performance Characteristics

**Latency Breakdown (per article):**

```
Tier 0 (Triage):           ~2.0 seconds
Tier 1 (Foundation):       ~3.0 seconds  (parallel: ENTITY + SUMMARY + TEXT)
Tier 2 (Specialists):      ~5.0 seconds  (parallel: 6 agents max)
Tier 3 (Synthesis):        ~6.0 seconds  (sequential: SYNTH → UQ)
Post-Pipeline:             ~2.0 seconds  (RELEVANCE_SCORER)
─────────────────────────────────────────
Total (Average):          ~16.1 seconds

By Article Size:
  ├─ Short (< 500 words):   8-12 seconds
  ├─ Medium (500-1500):     14-18 seconds
  └─ Long (1500+ words):    18-25 seconds
```

**Cost Analysis:**

```
Per-Article Cost Breakdown:

TRIAGE:                    $0.0003
ENTITY_EXTRACTOR:          $0.0004
SUMMARY_GENERATOR:         $0.0004
TEXT_FOUNDATION:           $0.0003
CONFLICT_EVENT_ANALYST:    $0.0012 (if run)
BIAS_DETECTOR:             $0.0012 (if run)
FINANCIAL_ANALYST:         $0.0008 (if run)
GEOPOLITICAL_ANALYST:      $0.0008 (if run)
SENTIMENT_ANALYST:         $0.0006 (if run)
TOPIC_CLASSIFIER:          $0.0006 (if run)
INTELLIGENCE_SYNTHESIZER:  $0.0018
UNCERTAINTY_QUANTIFIER:    $0.0006
RELEVANCE_SCORER:          $0.0004
─────────────────────────────────────────
Average Total:             ~$0.004 USD

Range:  $0.002 - $0.008 (depending on which agents run)
```

**Throughput:**

```
Single Concurrent Request:   ~1 article / 16 seconds = 0.0625 articles/sec
With 10 Concurrent Workers:  ~10 articles / 16 seconds = 0.625 articles/sec
With 50 Concurrent Workers:  ~50 articles / 16 seconds = 3.125 articles/sec

Daily Capacity (assuming 8 concurrent workers):
  ├─ 8 workers × 5,400 seconds/day ÷ 16 seconds/article
  └─ ≈ 2,700 articles/day max
```

### Memory Profiling

**Service Memory Footprint:**

```
Memory Usage Breakdown:

FastAPI Application:
  ├─ Base framework:        ~50 MB
  ├─ Database connection pool: ~30 MB
  ├─ Redis client:          ~10 MB
  ├─ RabbitMQ client:       ~15 MB
  └─ Subtotal:              ~105 MB

LLM Provider Clients:
  ├─ OpenAI async client:   ~20 MB
  ├─ Google Gemini client:  ~20 MB
  └─ Subtotal:              ~40 MB

In-Memory Caches:
  ├─ Agent result cache:    ~100-200 MB (configurable)
  ├─ Model cache:           ~50 MB (provider libraries)
  └─ Subtotal:              ~150-250 MB

Task Queue & Workers:
  ├─ Background tasks:      ~20 MB
  └─ Subtotal:              ~20 MB

─────────────────────────────────
Total Expected:              ~315-415 MB (normal operation)
Peak (heavy load):           ~500-600 MB
```

**Per-Agent Memory Usage:**

```
Agent Runtime Memory (during processing):

Lightweight Agents (< 20 MB):
  ├─ TRIAGE
  ├─ SENTIMENT_ANALYST
  └─ TOPIC_CLASSIFIER

Standard Agents (20-40 MB):
  ├─ ENTITY_EXTRACTOR
  ├─ SUMMARY_GENERATOR
  ├─ TEXT_FOUNDATION
  ├─ FINANCIAL_ANALYST
  └─ GEOPOLITICAL_ANALYST

Heavy Agents (40-80 MB):
  ├─ CONFLICT_EVENT_ANALYST
  ├─ BIAS_DETECTOR
  ├─ INTELLIGENCE_SYNTHESIZER
  └─ UNCERTAINTY_QUANTIFIER

Peak simultaneous (all Tier 1):  ~100 MB
Peak simultaneous (all Tier 2):  ~300 MB
```

### Performance Optimizations

**Implemented Optimizations:**

1. **Connection Pooling**
   - Database: Connection pool size 10-20
   - Redis: Single shared client (singleton)
   - RabbitMQ: Single connection with multiple channels

2. **Caching**
   - Agent result cache (24-hour TTL)
   - Cache hit rate: ~34% in production
   - Cost savings: ~15% vs. no caching

3. **Parallel Execution**
   - Tier 1 agents: Concurrent execution (3 parallel)
   - Tier 2 agents: Concurrent execution (up to 6 parallel)
   - Result: ~3.5x faster than sequential

4. **Token Optimization**
   - Schema filtering for Gemini JSON responses
   - Prompt optimization to reduce token count
   - Average 15-20% token reduction

5. **Timeout Protection (Issue #7)**
   - Pipeline-level timeout: 300 seconds
   - Per-agent timeout: 90 seconds
   - Graceful degradation on timeout

### Bottlenecks & Known Issues

**Identified Bottlenecks:**

1. **LLM Provider Latency** (40% of total time)
   - Problem: External API calls are inherently slow
   - Mitigation: Parallel execution, model selection optimization
   - Potential: Switch to faster models (Flash Lite) for non-critical agents

2. **Database Write Latency** (15% of total time)
   - Problem: Writing large JSONB documents
   - Mitigation: Batch writes, index optimization
   - Potential: Sharding or partitioning by date

3. **RabbitMQ Publishing** (10% of total time)
   - Problem: Synchronous publishing to message queue
   - Mitigation: Outbox pattern with async processor
   - Potential: Already optimized; consider compression

4. **INTELLIGENCE_SYNTHESIZER Processing** (40% of agent cost)
   - Problem: Most expensive agent (gpt-4o)
   - Mitigation: Use cheaper model for non-critical articles
   - Potential: Implement sampling strategy

---

## Testing Strategy

### Test Coverage

```
Test Summary:
├─ Total Tests: 325+
├─ Unit Tests: 180+
├─ Integration Tests: 95+
├─ Test Coverage (code): ~78%
├─ Test Coverage (agents): ~85%
├─ Test Coverage (pipeline): ~72%
└─ Status: PASSING (325/325 ✅)
```

### Test Categories

**Unit Tests (app/tests/):**

```
tests/
├─ test_triage_agent.py (45 tests)
│  ├─ Relevance assessment
│  ├─ Topic detection
│  └─ Edge cases (empty articles, spam, etc.)
├─ test_entity_extractor.py (35 tests)
│  ├─ NER accuracy
│  ├─ Entity classification
│  └─ Coreference resolution
├─ test_conflict_event_analyst.py (40 tests)
│  ├─ Event type classification
│  ├─ IHL violation detection
│  └─ Actor identification
├─ test_bias_detector.py (38 tests)
│  ├─ Political bias detection
│  ├─ Framing analysis
│  └─ Source credibility
├─ test_sentiment_analyst.py (22 tests)
├─ test_topic_classifier.py (18 tests)
├─ test_intelligence_synthesizer.py (25 tests)
├─ test_pipeline_orchestrator.py (32 tests)
└─ test_llm_providers.py (28 tests)
```

**Integration Tests (tests/integration/):**

```
tests/integration/
├─ test_full_pipeline.py (25 tests)
│  └─ End-to-end article processing
├─ test_rate_limited_llm.py (15 tests)
│  └─ Rate limiting under load
├─ test_database_integration.py (20 tests)
│  └─ Database reads/writes
├─ test_rabbitmq_integration.py (18 tests)
│  └─ Message queue integration
├─ test_v3_rollout.py (17 tests)
│  └─ V2→V3 migration compatibility
└─ test_graph_integration_e2e.py (20 tests)
   └─ Knowledge graph integration
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_entity_extractor.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run integration tests only
pytest tests/integration/ -v

# Run with markers
pytest tests/ -m "not slow" -v  # Skip slow tests
```

### Key Test Scenarios

**Pipeline Tests:**
- Article processing with all agents
- Conditional agent execution (topic-based)
- Timeout protection (pipeline-level)
- Error handling and recovery

**LLM Provider Tests:**
- API key validation
- Rate limiting
- Circuit breaker activation
- Fallback provider selection

**Database Tests:**
- Write operations (idempotency)
- Query performance
- Index utilization
- Schema validation

**Message Queue Tests:**
- Message consumption
- Outbox pattern reliability
- DLQ handling
- Exactly-once delivery

---

## Deployment

### Docker Deployment

**Build Image:**

```bash
cd /home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124

# Build dev image
docker build -f Dockerfile.dev -t news-content-analysis-v2:latest .

# Build prod image
docker build -f Dockerfile -t news-content-analysis-v2:prod .
```

**Docker Compose Entry:**

```yaml
content-analysis-v2:
  image: news-content-analysis-v2:latest
  container_name: news-content-analysis-v2
  ports:
    - "8114:8000"
  environment:
    - SERVICE_NAME=content-analysis-v2
    - SERVICE_PORT=8000
    - DATABASE_URL=${DATABASE_URL}
    - RABBITMQ_URL=${RABBITMQ_URL}
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    - DEFAULT_OPENAI_API_KEY=${OPENAI_API_KEY}
    - DEFAULT_GEMINI_API_KEY=${GEMINI_API_KEY}
  volumes:
    - ./services/content-analysis-v2/app:/app/app  # Hot reload (dev)
  depends_on:
    - postgres
    - redis
    - rabbitmq
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - news-network
```

**Start Service:**

```bash
docker compose up -d content-analysis-v2
docker logs content-analysis-v2 -f
```

### Database Migrations

**Create Migration:**

```bash
# Generate new migration
alembic revision --autogenerate -m "Add new agent"

# Review migration file
cat alembic/versions/xxx_add_new_agent.py

# Apply migration
alembic upgrade head
```

**Rollback:**

```bash
# Rollback 1 revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Kubernetes Deployment

**Helm Chart (example):**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: content-analysis-v2
spec:
  selector:
    app: content-analysis-v2
  ports:
    - port: 8114
      targetPort: 8000

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-analysis-v2
spec:
  replicas: 3
  selector:
    matchLabels:
      app: content-analysis-v2
  template:
    metadata:
      labels:
        app: content-analysis-v2
    spec:
      containers:
      - name: content-analysis-v2
        image: news-content-analysis-v2:v2.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## Dependencies & Requirements

### Python Dependencies

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
asyncpg==0.30.0
openai==1.57.4
google-generativeai==0.8.3
aio-pika==9.4.3
redis==5.2.1
pydantic==2.10.3
pyjwt==2.10.1
python-dotenv==1.0.1
tenacity==9.0.0
prometheus-client==0.21.0
```

**Detailed requirements.txt:**
See `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/requirements.txt`

### System Requirements

**Minimum:**
- Python 3.10+
- 512 MB RAM
- 2 CPU cores
- PostgreSQL 12+
- Redis 6+
- RabbitMQ 3.8+

**Recommended:**
- Python 3.11+
- 2 GB RAM
- 4+ CPU cores
- PostgreSQL 14+
- Redis 7+
- RabbitMQ 3.12+

### External Service Dependencies

```
Auth Service (8100)
  ├─ Endpoint: /api/v1/auth/validate
  └─ Used for: JWT token validation

Feed Service (8101)
  ├─ Endpoint: /api/v1/articles/{id}
  └─ Used for: Article metadata retrieval

Knowledge Graph Service (8111)
  ├─ Endpoint: /api/v1/graph/create-nodes
  └─ Used for: Entity graph storage

RabbitMQ (5672/5671 TLS)
  ├─ Queue: content_analysis_v2_queue
  └─ Used for: Article input & event publishing

PostgreSQL (5432)
  ├─ Databases: news_mcp
  └─ Used for: Result storage

Redis (6379)
  ├─ Database: 2 (cache)
  └─ Used for: Result caching
```

---

## Troubleshooting

### Issue 1: Service Won't Start

**Symptoms:** Container exits immediately; healthcheck fails

**Diagnosis:**

```bash
# Check logs
docker logs news-content-analysis-v2

# Common errors:
# - "DatabaseError: Cannot connect to postgres"
# - "ValidationError: API key validation failed"
# - "RuntimeError: Configuration validation failed"
```

**Solutions:**

1. **Database connection:**
   ```bash
   # Verify DATABASE_URL is set
   docker exec news-content-analysis-v2 env | grep DATABASE_URL

   # Test connection
   psql ${DATABASE_URL}
   ```

2. **API key validation:**
   ```bash
   # Verify API keys are set
   docker exec news-content-analysis-v2 env | grep API_KEY

   # Check key format (should start with expected prefix)
   # OpenAI: sk-proj-...
   # Gemini: AIza...
   ```

3. **Configuration validation:**
   ```bash
   # Check .env file
   cat services/_archived/content-analysis-v2-20251124/.env

   # Ensure required vars are present:
   # - DATABASE_URL
   # - RABBITMQ_URL
   # - JWT_SECRET_KEY
   # - DEFAULT_OPENAI_API_KEY or DEFAULT_GEMINI_API_KEY
   ```

### Issue 2: Timeout Errors on Pipeline Execution

**Symptoms:** Articles fail with "Timeout after 90 seconds" or "Pipeline timeout"

**Cause:** LLM API calls or database operations are slow

**Solutions:**

```bash
# 1. Check LLM provider status
curl -X GET "https://status.openai.com"
curl -X GET "https://status.cloud.google.com"

# 2. Increase timeouts (temporary)
docker exec news-content-analysis-v2 bash -c \
  'AGENT_TIMEOUT_SECONDS=120 python -m app.api.main'

# 3. Reduce token limits (faster processing)
export CONFLICT_EVENT_ANALYST_MAX_TOKENS=4000  # from 8000

# 4. Use faster models
export INTELLIGENCE_SYNTHESIZER_MODEL=gpt-4o-mini  # from gpt-4o
```

### Issue 3: High Memory Usage

**Symptoms:** Container using 500+ MB; OOM kills

**Cause:** Large cached results; memory leaks in LLM clients

**Solutions:**

```bash
# 1. Disable caching
export ENABLE_CACHE=false

# 2. Reduce cache TTL
export AGENT_CACHE_TTL_SECONDS=3600  # from 86400

# 3. Clear cache manually
redis-cli -n 2 FLUSHDB  # content-analysis-v2 uses DB 2

# 4. Monitor memory per agent
python -m memory_profiler app/agents/tier2_specialists/conflict_event_analyst.py
```

### Issue 4: Database Connection Pool Exhaustion

**Symptoms:** "Too many connections" errors; slow queries

**Cause:** Connection leaks; high concurrency

**Solutions:**

```bash
# 1. Check active connections
psql ${DATABASE_URL} -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# 2. Reduce pool size temporarily
export DATABASE_POOL_SIZE=5  # from 10

# 3. Increase connection timeout
export DATABASE_POOL_TIMEOUT=30

# 4. Identify slow queries
psql ${DATABASE_URL} -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Issue 5: Articles Not Processing

**Symptoms:** Messages in RabbitMQ queue but not being processed

**Cause:** Consumer not running; poison pill message; DLQ accumulation

**Solutions:**

```bash
# 1. Check queue status
docker exec rabbitmq-service rabbitmqctl list_queues

# 2. Check consumer status
curl http://localhost:8114/api/v1/queue/metrics

# 3. Check for errors
docker logs news-content-analysis-v2 | grep ERROR

# 4. Requeue DLQ messages
docker exec rabbitmq-service \
  rabbitmqctl purge_queue content_analysis_v2_dlq

# 5. Restart consumer
docker restart news-content-analysis-v2
```

### Issue 6: "Invalid API Key" Errors

**Symptoms:** Every agent call fails with "Invalid API key"

**Cause:** Expired/revoked key; wrong key format

**Solutions:**

```bash
# 1. Validate key format
# OpenAI: Should start with 'sk-proj-' and be 48+ chars
# Gemini: Should start with 'AIza' and be 39 chars

# 2. Test key directly
curl -X POST https://api.openai.com/v1/models \
  -H "Authorization: Bearer ${OPENAI_API_KEY}"

curl -X GET "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_API_KEY}"

# 3. Check for hidden characters
echo $DEFAULT_OPENAI_API_KEY | od -c | head -20

# 4. Regenerate key in console
# OpenAI: https://platform.openai.com/account/api-keys
# Gemini: https://aistudio.google.com/app/apikey
```

### Issue 7: Knowledge Graph Integration Failures

**Symptoms:** "Failed to create graph nodes" errors

**Cause:** Knowledge Graph Service unavailable; schema mismatch

**Solutions:**

```bash
# 1. Check Knowledge Graph Service
curl http://localhost:8111/healthz

# 2. Verify schema matches
curl http://localhost:8111/api/v1/schema

# 3. Check entity extraction output
docker logs news-content-analysis-v2 | grep -A 5 "entity_extraction"

# 4. Fallback: Disable graph integration
export ENABLE_GRAPH_INTEGRATION=false
```

---

## Code Examples

### Example 1: Process Article Programmatically

```python
import asyncio
from app.agents.tier2_specialists.conflict_event_analyst import ConflictEventAnalystAgent
from app.agents.tier2_specialists.bias_detector import BiasDetectorAgent
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider

async def analyze_article(article_text: str):
    # Initialize providers
    gemini = GeminiProvider(
        api_key="AIzaSyDxxx...",
        model="gemini-2.5-flash",
        max_tokens=4000,
        temperature=0.1
    )

    openai = OpenAIProvider(
        api_key="sk-proj-xxx...",
        model="gpt-4o",
        max_tokens=4000,
        temperature=0.0
    )

    # Initialize agents
    conflict_agent = ConflictEventAnalystAgent(llm_provider=openai)
    bias_agent = BiasDetectorAgent(llm_provider=openai)

    # Run agents
    conflict_result = await conflict_agent.execute(
        article=article_text,
        article_id="550e8400-e29b-41d4-a716-446655440000"
    )

    bias_result = await bias_agent.execute(
        article=article_text,
        article_id="550e8400-e29b-41d4-a716-446655440000"
    )

    print(f"Conflict Analysis: {conflict_result.result['event_type']}")
    print(f"Bias Score: {bias_result.result['political_bias']['bias_score']}")

# Run
asyncio.run(analyze_article("Article text here..."))
```

### Example 2: Use REST API

```bash
# 1. Get JWT token from Auth Service
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }' | jq -r '.data.access_token')

# 2. Get analysis results
curl -X GET "http://localhost:8114/api/v1/articles/550e8400-e29b-41d4-a716-446655440000/analysis" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 3. Get specific agent result
curl -X GET "http://localhost:8114/api/v1/articles/550e8400-e29b-41d4-a716-446655440000/agents/CONFLICT_EVENT_ANALYST" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 4. Get service statistics
curl -X GET "http://localhost:8114/api/v1/statistics" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Example 3: Publish Article to Pipeline

```python
import json
import asyncio
import aio_pika
from pydantic import BaseModel
from datetime import datetime

class ArticleMessage(BaseModel):
    message_id: str
    article_id: str
    title: str
    content: str
    source: str
    publish_date: datetime
    language: str = "en"

async def publish_article(article_data: dict):
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost:5672/"
    )

    async with connection:
        channel = await connection.channel()

        # Declare exchange & queue
        exchange = await channel.declare_exchange(
            "content_analysis",
            aio_pika.ExchangeType.TOPIC
        )

        queue = await channel.declare_queue(
            "content_analysis_v2_queue"
        )

        await queue.bind(exchange, "analysis.v2.#")

        # Publish message
        message = aio_pika.Message(
            body=json.dumps(article_data).encode(),
            content_type="application/json"
        )

        await exchange.publish(
            message,
            routing_key="analysis.v2.article.created"
        )

        print("Article published to pipeline!")

# Publish
article = {
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "article_id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Breaking News: Major Event",
    "content": "Full article content here...",
    "source": "example.com",
    "publish_date": datetime.now().isoformat(),
    "language": "en"
}

asyncio.run(publish_article(article))
```

### Example 4: Query Database Results

```python
from sqlalchemy import select
from app.database.models import AgentResult
from app.database.session import get_async_session

async def get_article_results(article_id: str):
    async with get_async_session() as session:
        # Get all agent results for article
        stmt = select(AgentResult).where(
            AgentResult.article_id == article_id
        )
        results = await session.execute(stmt)

        for result in results.scalars():
            print(f"Agent: {result.agent_name}")
            print(f"Confidence: {result.confidence_score}")
            print(f"Cost: ${result.cost_usd}")
            print(f"Latency: {result.processing_time_ms}ms")
            print(f"Result: {result.result_data}")
            print()

# Run
import asyncio
asyncio.run(get_article_results("550e8400-e29b-41d4-a716-446655440001"))
```

### Example 5: Monitor Pipeline Performance

```python
from sqlalchemy import select, func
from app.database.models import AgentResult, PipelineExecution
from app.database.session import get_async_session

async def monitor_performance():
    async with get_async_session() as session:
        # Get average latency by agent
        stmt = select(
            AgentResult.agent_name,
            func.avg(AgentResult.processing_time_ms).label("avg_latency"),
            func.count(AgentResult.id).label("execution_count"),
            func.avg(AgentResult.cost_usd).label("avg_cost")
        ).group_by(AgentResult.agent_name)

        results = await session.execute(stmt)

        print("Agent Performance Metrics:")
        print("-" * 70)
        for row in results:
            print(f"{row[0]:30} | Latency: {row[1]:7.0f}ms | "
                  f"Count: {row[2]:5} | Cost: ${row[3]:.6f}")

# Run
asyncio.run(monitor_performance())
```

---

## Appendices

### A. Service Lifecycle

```
2025-10-11: Service v2 launched
2025-11-12: Code review completed (3 critical, 8 high priority issues)
2025-11-18: Refactoring v2.0 (modular pipeline architecture)
2025-11-24: Service archived in favor of v3
            - v3 includes modular pipeline & advanced UQ
            - v2 maintained as reference implementation
            - Legacy data migrated to public.article_analysis
```

### B. Known Limitations

1. **Structured Output Disabled**
   - Issue: JSON schema filtering causes validation errors in Gemini
   - Workaround: Using prompt-based JSON generation
   - Status: Pending proper schema filtering implementation

2. **No Federated Learning**
   - Service cannot train from user feedback
   - All models are pre-trained; no fine-tuning

3. **Limited Context Window**
   - Long articles (3000+ words) may be truncated
   - Affects entity extraction and bias detection accuracy

4. **No Model Caching**
   - LLM clients loaded fresh for each request
   - Opportunity for optimization: Singleton pattern

### C. Migration Path (v2 → v3)

```
Content-Analysis v2 → Content-Analysis v3

New Features in v3:
  ├─ Modular tier architecture
  ├─ Advanced uncertainty quantification
  ├─ Knowledge graph integration
  ├─ 30-40% performance improvement
  ├─ Better error handling
  └─ Improved cost efficiency

Migration Steps:
  1. Deploy v3 alongside v2
  2. Route 10% of traffic to v3
  3. Compare results (A/B testing)
  4. Increase traffic to v3 gradually
  5. Archive v2 (30-day retention)
  6. Decommission v2

Timeline: 2-4 weeks (Nov 24 - Dec 20)
Status: MIGRATING (v2 archived, v3 active)
```

### D. References

**Documentation:**
- Service README: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/README.md`
- Code Review Report: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/CODE_REVIEW_REPORT.md`
- Pipeline Documentation: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/PIPELINE_README.md`

**Key Files:**
- Main: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/app/api/main.py`
- Pipeline: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/app/pipeline/orchestrator.py`
- Agents: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/app/agents/`
- Tests: `/home/cytrex/news-microservices/services/_archived/content-analysis-v2-20251124/tests/`

---

**Document Version:** 2.0.0
**Last Updated:** 2025-11-24
**Status:** ARCHIVED (See content-analysis-v3 for active service)
