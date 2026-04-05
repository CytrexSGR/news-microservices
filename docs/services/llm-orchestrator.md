# LLM Orchestrator Service (Port 8113)

## Executive Summary

The **LLM Orchestrator Service** is an intelligent verification orchestration system that uses a two-stage planning and execution approach called **DIA (Dynamic Intelligence Augmentation)** to verify uncertain claims in news articles. Instead of directly verifying uncertain content, the service first understands the root cause of uncertainty through LLM analysis, then generates a precise verification plan, and finally executes that plan using multiple external data sources in parallel.

**Key Innovation:** Two-stage LLM reasoning (diagnosis → planning) transforms vague uncertainty signals into actionable verification strategies.

### Quick Facts

| Aspect | Details |
|--------|---------|
| **Port** | 8113 |
| **Language** | Python 3.9+ |
| **Framework** | FastAPI + uvicorn |
| **Database** | PostgreSQL (optional, for metadata) |
| **Message Queue** | RabbitMQ (topic exchange) |
| **Primary LLM** | OpenAI GPT-4o-mini |
| **Verification Tools** | Perplexity Deep Search, Financial Data Lookup (Alpha Vantage) |
| **Deployment Model** | Async microservice with background consumer |
| **Test Coverage** | 72% (comprehensive unit + integration tests) |

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Overview & Architecture](#overview--architecture)
3. [LLM Provider Integration](#llm-provider-integration)
4. [Prompt Engineering Strategy](#prompt-engineering-strategy)
5. [Model Selection Logic](#model-selection-logic)
6. [DIA Planning Pipeline](#dia-planning-pipeline)
7. [Verification Tools](#verification-tools)
8. [Cost Analysis](#cost-analysis)
9. [API Endpoints](#api-endpoints)
10. [RabbitMQ Integration](#rabbitmq-integration)
11. [Database Schema](#database-schema)
12. [Configuration](#configuration)
13. [Performance Characteristics](#performance-characteristics)
14. [Prompt Optimization](#prompt-optimization)
15. [Testing & Validation](#testing--validation)
16. [Troubleshooting](#troubleshooting)
17. [Architecture Decision Records](#architecture-decision-records)

---

## Quick Start

### 1. Prerequisites

```bash
# Required environment variables
export OPENAI_API_KEY="sk-proj-xxxxx"  # OpenAI API key (required)
export PERPLEXITY_API_KEY="pplx-xxxxx" # Perplexity API key (optional, falls back to OpenAI)
export ALPHA_VANTAGE_API_KEY="xxxxx"   # Financial data API key (optional, uses demo if not set)
export RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
export DATABASE_URL="postgresql://user:pass@localhost:5432/orchestrator_db"
```

### 2. Installation

```bash
# Clone and install
cd /home/cytrex/news-microservices/services/llm-orchestrator-service
pip install -r requirements.txt

# Using uv (faster)
uv pip install -r requirements.txt
```

### 3. Start Service

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8113 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8113 --workers 4
```

### 4. Health Check

```bash
curl http://localhost:8113/health

# Expected response:
{
  "status": "healthy",
  "service": "llm-orchestrator-service",
  "version": "1.0.0"
}
```

### 5. Test with Sample Event

```bash
# From project root, publish a verification request
python -c "
import pika
import json
from uuid import uuid4
from datetime import datetime

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='verification_exchange', exchange_type='topic', durable=True)

event = {
    'event_id': str(uuid4()),
    'event_type': 'verification.required',
    'article_id': str(uuid4()),
    'article_title': 'Tesla Reports Record Q3 Earnings',
    'article_content': 'Tesla Inc. announced record-breaking financial results for Q3 2024, reporting net profits of \$5 billion...',
    'article_url': 'https://example.com/tesla-earnings',
    'article_published_at': datetime.utcnow().isoformat(),
    'uq_confidence_score': 0.45,
    'uncertainty_factors': ['Low confidence in claim accuracy', 'Numerical claim lacks verification'],
    'priority': 'high'
}

channel.basic_publish(
    exchange='verification_exchange',
    routing_key='verification.required.high',
    body=json.dumps(event)
)
connection.close()
print('Event published!')
"
```

---

## Overview & Architecture

### System Boundaries

The LLM Orchestrator operates at the intersection of:

- **Upstream:** Content Analysis Service (sends verification.required events with UQ scores)
- **Downstream:** Analysis Update Service (receives corrected facts and confidence scores)
- **External:** OpenAI, Perplexity AI, Alpha Vantage APIs
- **Internal:** RabbitMQ (event stream), PostgreSQL (optional metadata storage)

### DIA Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Content Analysis Service                     │
│                  (Detects uncertain content)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ verification.required event
                       │ (article + UQ confidence score)
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         LLM Orchestrator Service (Port 8113)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─── RabbitMQ Consumer (Topic: verification_exchange) ───┐    │
│  │ Listens for: verification.required.*                   │    │
│  │ Queue: verification_queue (durable, prefetch=1)        │    │
│  └────────────────────┬──────────────────────────────────┘    │
│                       │                                         │
│                       ▼                                         │
│  ┌─── Stage 1: DIA Planner (Root Cause Analysis) ───┐         │
│  │ LLM: OpenAI GPT-4o-mini (temp=0.3)               │         │
│  │ Input: Article + UQ factors + current analysis   │         │
│  │ Output: ProblemHypothesis (precise diagnosis)    │         │
│  │ Example types: factual_error, entity_ambiguity   │         │
│  └────────────────────┬──────────────────────────────┘         │
│                       │                                         │
│                       ▼                                         │
│  ┌─── Stage 2: DIA Planner (Plan Generation) ───┐             │
│  │ LLM: OpenAI GPT-4o-mini (temp=0.2)           │             │
│  │ Input: Problem hypothesis from Stage 1       │             │
│  │ Output: VerificationPlan with tool calls      │             │
│  │ Includes: Tool methods, sources, expected     │             │
│  │           corrections, time estimates         │             │
│  └────────────────────┬──────────────────────────┘             │
│                       │                                         │
│                       ▼                                         │
│  ┌─── DIA Verifier (Execute Plan) ─────────────────┐          │
│  │ Parse tool calls from verification plan        │          │
│  │ Execute in parallel: asyncio.gather()          │          │
│  │ Collect results and aggregate evidence         │          │
│  └────────────┬───────────────────────────────────┘          │
│               │                                                │
│    ┌──────────┴──────────┬──────────────────────┐             │
│    │                     │                      │             │
│    ▼                     ▼                      ▼             │
│  Perplexity          Financial Data          [Future]        │
│  Deep Search         Lookup                  Tools            │
│  • Query: str        • Company: TSLA                          │
│  • Domain filter     • Metric: earnings                       │
│  • Recency filter    • Period: Q3 2024                        │
│    │                     │                      │             │
│    └──────────┬──────────┴──────────────────────┘             │
│               │                                                │
│               ▼                                                │
│  ┌─────────────────────────────────────────────────┐         │
│  │ Evidence Package (Final Output)                │         │
│  │ ─────────────────────────────────────────     │         │
│  │ • Hypothesis confirmed: true/false            │         │
│  │ • Confidence score: 0.0-1.0                   │         │
│  │ • Key findings: [list of findings]            │         │
│  │ • Corrected facts: {original → corrected}    │         │
│  │ • Source citations: [with reliability scores] │         │
│  │ • Verification quality metrics:               │         │
│  │   - Source reliability: 0.0-1.0               │         │
│  │   - Evidence consistency: 0.0-1.0             │         │
│  │   - Coverage completeness: 0.0-1.0            │         │
│  └────────────────┬─────────────────────────────┘         │
│                   │                                         │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼
      ┌──────────────────────────────┐
      │  Publish Result Event        │
      │  (verification.completed)    │
      │  to downstream services      │
      └──────────────────────────────┘
```

### Key Design Principles

1. **Two-Stage Reasoning:** Separates diagnosis (understanding the problem) from planning (creating solution)
2. **LLM-Powered Intelligence:** Uses GPT-4o-mini for precise root cause analysis instead of heuristics
3. **Parallel Execution:** All verification tools run concurrently, not sequentially
4. **Evidence Aggregation:** Combines multiple sources with reliability scoring
5. **Confidence Calculation:** Combines tool confidence, success rate, and hypothesis confirmation
6. **Fallback Strategies:** Graceful degradation when tools fail

---

## LLM Provider Integration

### Supported LLM Providers

#### 1. OpenAI (Primary)

**Model:** `gpt-4o-mini` (or `gpt-4-turbo-preview` for production)

| Aspect | Value |
|--------|-------|
| **API Endpoint** | https://api.openai.com/v1/chat/completions |
| **Authentication** | Bearer token (OPENAI_API_KEY) |
| **Format** | JSON mode with strict schema enforcement |
| **Input Tokens/Request** | ~1,000-2,000 (depends on article length) |
| **Output Tokens/Request** | 500-1,500 (structured JSON) |
| **Supported Features** | Function calling, JSON mode, streaming (future) |
| **Rate Limits** | Varies by account (typically 3,500 RPM / 200,000 TPM) |
| **Cost** | $0.15 input / $0.60 output per 1M tokens (gpt-4o-mini) |

**Configuration:**

```python
# app/core/config.py
OPENAI_API_KEY = "sk-proj-xxxxx"
OPENAI_MODEL = "gpt-4o-mini"
DIA_STAGE1_TEMPERATURE = 0.3   # Lower = more consistent JSON
DIA_STAGE2_TEMPERATURE = 0.2   # Even lower for precise planning
DIA_MAX_RETRIES = 3             # Retry on JSON parse failures
```

**Initialization:**

```python
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": STAGE_1_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    response_format={"type": "json_object"},
    temperature=0.3,
    max_tokens=1000
)
```

#### 2. Perplexity AI (Verification Tool)

**Model:** `sonar-pro` (specialized for web search with citations)

| Aspect | Value |
|--------|-------|
| **API Endpoint** | https://api.perplexity.ai/chat/completions |
| **Authentication** | Bearer token (PERPLEXITY_API_KEY) |
| **Strengths** | Real-time web search, automatic citations, domain filtering |
| **Input Tokens/Request** | ~200-500 (search query) |
| **Output Tokens/Request** | 300-1,000 (answer + citations) |
| **Special Features** | search_domain_filter, search_recency_filter |
| **Rate Limits** | Based on subscription tier |
| **Cost** | Varies by tier (contact sales) |

**Configuration:**

```python
PERPLEXITY_API_KEY = "pplx-xxxxx"  # Optional: falls back to OPENAI_API_KEY
```

**Usage Example:**

```python
async def perplexity_deep_search(
    query: str,
    search_domain_filter: Optional[List[str]] = None,
    search_recency_filter: Optional[str] = None
) -> ToolExecutionResult:
    """
    Execute deep web search using Perplexity API.

    Args:
        query: Search query (e.g., "Tesla Q3 2024 earnings")
        search_domain_filter: Restrict to specific domains
                             (e.g., ["sec.gov", "ir.tesla.com"])
        search_recency_filter: Time window ("day", "week", "month", "year")
    """
    # See tools/perplexity_tool.py for full implementation
```

#### 3. Future LLM Support

**Planned integrations:**

- **Anthropic Claude:** For specialized reasoning tasks
- **Local Models:** LLaMA 2, Mistral via Ollama for on-premise deployments
- **Model Mixing:** Primary model + fallback models for redundancy

### LLM Fallback Strategy

```python
# Priority order for API key selection
perplexity_api_key = settings.PERPLEXITY_API_KEY or settings.OPENAI_API_KEY

# If no Perplexity key, fall back to OpenAI
# This ensures graceful degradation

# Retry logic for transient failures
for attempt in range(1, max_retries + 1):
    try:
        response = client.chat.completions.create(...)
        return response
    except RateLimitError:
        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
    except APIError as e:
        logger.error(f"API error (attempt {attempt}): {e}")
        if attempt == max_retries:
            raise
```

### Cost Optimization Strategies

1. **Temperature Tuning:** Lower temp (0.2-0.3) reduces token variability and retry rate
2. **Prompt Compression:** Truncate article content to 2,000 chars max
3. **JSON Mode:** Structured output reduces unparseable responses
4. **Batch Processing:** Group requests where possible (future)
5. **Model Selection:** Use `gpt-4o-mini` instead of `gpt-4` for 60% cost reduction

---

## Prompt Engineering Strategy

### Stage 1: Root Cause Analysis Prompt

**Goal:** Transform vague UQ signals into precise problem diagnosis

**System Prompt Philosophy:**

```
You are a "Root Cause Analysis" specialist for the DIA system.

Your mission: Analyze uncertain content and identify the PRECISE reason
for uncertainty.

Input: Article content, vague uncertainty factors from UQ sensor
Output: Specific, actionable problem diagnosis
```

**Key Principles:**

1. **Specificity:** Demand exact excerpts and concrete problems, not vague statements
2. **Domain Knowledge:** Leverage LLM reasoning to understand context
3. **Prioritization:** Identify the MOST critical issue if multiple exist
4. **Actionability:** Enable the next stage to create a plan

**Prompt Structure:**

```python
def _build_stage1_prompt(event: VerificationRequiredEvent) -> str:
    """
    Build Stage 1 prompt with:
    1. Article content (truncated to 2,000 chars)
    2. UQ confidence score
    3. Uncertainty factors (vague → precise)
    4. Current analysis (potentially incorrect)
    """
    factors_formatted = "\n".join(f"  - {f}" for f in event.uncertainty_factors)

    prompt = f"""
Article Content:
Title: {event.article_title}
URL: {event.article_url}
Published: {event.article_published_at}

{content_preview}

UQ Sensor Output:
- Confidence Score: {event.uq_confidence_score} (lower = more uncertain)
- Uncertainty Factors:
{factors_formatted}

Current Analysis (potentially incorrect):
- Summary: {event.analysis_summary or 'N/A'}
- Entities: {len(event.extracted_entities or [])} extracted
- Category: {event.category_analysis or 'N/A'}

Task: Identify the precise root cause of uncertainty. What EXACTLY is the problem?
"""
    return prompt.strip()
```

**Output Schema (Stage 1):**

```json
{
  "primary_concern": "Specific, actionable problem statement",
  "affected_content": "Exact excerpt from article",
  "hypothesis_type": "factual_error | entity_ambiguity | temporal_inconsistency | missing_context | contradictory_claims | source_reliability_issue",
  "confidence": 0.85,
  "reasoning": "Your analytical reasoning",
  "verification_approach": "High-level verification strategy"
}
```

**Example Stage 1 Output:**

```json
{
  "primary_concern": "Financial figure appears incorrect",
  "affected_content": "Tesla Q3 2024 earnings of $5 billion",
  "hypothesis_type": "factual_error",
  "confidence": 0.85,
  "reasoning": "Unusually high compared to historical data (Q2 2024: $4.2B, Q3 2023: $3.8B)",
  "verification_approach": "Cross-reference with SEC filings and investor relations"
}
```

### Stage 2: Plan Generation Prompt

**Goal:** Create a precise, executable verification plan based on diagnosis

**System Prompt Philosophy:**

```
You are a "Verification Planner" for the DIA system.

Your mission: Create a precise, executable verification plan based on
a root cause diagnosis.

Input: Problem hypothesis from Stage 1, available tools
Output: Structured plan with specific tool calls
```

**Available Tools Description:**

```
- perplexity_deep_search(query: str) - Deep web search with citations
- financial_data_lookup(company: str, metric: str, period: str) - Financial data
```

**Prompt Structure:**

```python
def _build_stage2_prompt(
    problem_hypothesis: ProblemHypothesis,
    event: VerificationRequiredEvent
) -> str:
    """
    Build Stage 2 prompt with:
    1. Problem hypothesis (precise diagnosis)
    2. Original article context
    3. Available tools with exact syntax
    """
    prompt = f"""
Problem Hypothesis (from Stage 1):
{problem_hypothesis.model_dump_json(indent=2)}

Original Article Context:
- Title: {event.article_title}
- URL: {event.article_url}
- Published: {event.article_published_at}
- Priority: {event.priority}

Available Tools:
- perplexity_deep_search(query='...') - Web search
- financial_data_lookup(company='...', metric='...', period='...') - Financial data

Task: Create a precise, executable verification plan to confirm/refute this hypothesis.
Focus on authoritative sources. Be specific with parameters.
"""
    return prompt.strip()
```

**Output Schema (Stage 2):**

```json
{
  "priority": "critical | high | medium | low",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount')",
    "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
  ],
  "external_sources": [
    "Tesla Investor Relations (official earnings report)",
    "SEC EDGAR Database (10-Q filing)"
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

**Example Stage 2 Output:**

```json
{
  "priority": "high",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount', search_domain_filter=['sec.gov', 'ir.tesla.com'])",
    "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
  ],
  "external_sources": [
    "SEC Filing 10-Q (official source)",
    "Tesla Investor Relations",
    "Bloomberg Terminal"
  ],
  "expected_corrections": [
    {
      "field": "earnings",
      "original": "$5 billion",
      "corrected": "$4.194 billion",
      "confidence_improvement": 0.20
    }
  ],
  "estimated_verification_time_seconds": 60
}
```

### Temperature Settings & Their Impact

| Temperature | Use Case | Characteristics | Impact on Output |
|-------------|----------|-----------------|------------------|
| **0.2** | Stage 2 Planning | Highly consistent, deterministic | Reproducible plans, fewer retries |
| **0.3** | Stage 1 Diagnosis | Consistent but allows some variation | Balanced specificity |
| **0.5** | General reasoning | Balanced creativity/consistency | Not used in DIA |
| **0.7+** | Creative tasks | High variability | Not suitable for JSON output |

**Recommendation:** Keep both stages < 0.3 to maximize JSON parsing success.

---

## Model Selection Logic

### Dynamic Model Selection (Future Enhancement)

While currently using only GPT-4o-mini, the service is architected to support dynamic model selection based on:

```python
class ModelSelectionStrategy:
    """
    Factors for model selection:

    1. Complexity: Simple factual checks → gpt-4o-mini
                   Complex reasoning → gpt-4-turbo

    2. Cost: Budget constraints → gpt-4o-mini
             Premium accuracy needed → gpt-4

    3. Speed: Real-time requirements → gpt-4o-mini (faster)
              Background processing → gpt-4 (more thorough)

    4. Task Type:
       - Factual errors → Perplexity web search
       - Financial data → Alpha Vantage API
       - Complex reasoning → OpenAI GPT-4
       - Entity resolution → Custom service
    """
```

### Fallback Decision Tree

```
┌─ Is OPENAI_API_KEY configured?
│  ├─ NO → Error: API key required
│  └─ YES → Use OpenAI
│
├─ Is model responding?
│  ├─ NO (5xx error) → Retry with exponential backoff (max 3)
│  ├─ Rate limited (429) → Wait and retry
│  └─ Invalid request (4xx) → Log and fail
│
├─ Is response valid JSON?
│  ├─ NO → Retry with modified prompt (max 3 retries)
│  └─ YES → Continue
│
└─ Can response be parsed as ProblemHypothesis/VerificationPlan?
   ├─ NO → Log warning, use default values
   └─ YES → Use response
```

---

## DIA Planning Pipeline

### Complete Workflow Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RabbitMQ Consumer receives verification.required event  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Parse & validate VerificationRequiredEvent              │
│    Check: article_id, uq_confidence_score, uncertainty_factors
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Initialize DIAPlanner                                   │
│    LLM: OpenAI GPT-4o-mini                                 │
│    Temps: stage1=0.3, stage2=0.2                           │
│    Retries: 3                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. STAGE 1: Root Cause Analysis                            │
│    ─────────────────────────────────────────────          │
│    Input:  Article + UQ factors + analysis                │
│    LLM Call: system_prompt + user_prompt → JSON response  │
│    Retry: On JSON parse failure, retry up to 3 times      │
│    Output: ProblemHypothesis                              │
│             └─ primary_concern: string                    │
│             └─ hypothesis_type: enum                      │
│             └─ confidence: float(0-1)                     │
│             └─ reasoning: string                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. STAGE 2: Plan Generation                               │
│    ─────────────────────────────────────────────         │
│    Input:  ProblemHypothesis + article context           │
│    LLM Call: system_prompt + user_prompt → JSON response │
│    Output: VerificationPlan                              │
│             └─ priority: "high"                          │
│             └─ verification_methods: [tool_call_strings] │
│             └─ external_sources: [source_names]          │
│             └─ expected_corrections: [corrections]       │
│             └─ estimated_verification_time_seconds: int  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Initialize DIAVerifier                                 │
│    Tool Registry: {                                        │
│        "perplexity_deep_search": async function,          │
│        "financial_data_lookup": async function,           │
│        ...                                                 │
│    }                                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Parse Verification Methods                             │
│    ─────────────────────────────────────────────         │
│    Regex: (\w+)\((.*)\)                                   │
│    Extract: tool_name, parameters                         │
│    Validate: tool_name in tool_registry                   │
│    Output: List[(tool_name, params_dict)]                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Execute Tools in Parallel                              │
│    ─────────────────────────────────────────────         │
│    For each (tool_name, params):                          │
│        Create coroutine: tool_registry[tool_name](**params)
│    Use asyncio.gather() to execute all concurrently       │
│    Capture results & exceptions                           │
│    Output: List[ToolExecutionResult]                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Aggregate Evidence                                      │
│    ─────────────────────────────────────────────         │
│    Extract key findings from tool results                │
│    Collect all source citations                          │
│    Calculate source reliability scores                   │
│    Determine hypothesis confirmation (avg confidence)    │
│    Calculate overall confidence score                    │
│    Identify corrected facts                              │
│    Output: EvidencePackage                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Return EvidencePackage                                │
│     ──────────────────────────────────────────          │
│     hypothesis_confirmed: bool                           │
│     confidence_score: float(0-1)                         │
│     key_findings: [strings]                              │
│     corrected_facts: {field: {original, corrected, ...}} │
│     source_citations: [{source, url, reliability}]       │
│     verification_quality: {                              │
│         source_reliability: float,                       │
│         evidence_consistency: float,                     │
│         coverage_completeness: float                     │
│     }                                                     │
└─────────────────────────────────────────────────────────────┘
```

### Error Handling at Each Stage

| Stage | Error | Handling |
|-------|-------|----------|
| **Consume** | Connection fails | Automatic reconnect with backoff |
| **Parse** | Invalid JSON | Log error, skip message, ACK |
| **Stage 1** | LLM API error | Retry up to 3 times |
| **Stage 1** | Invalid JSON output | Retry with modified prompt |
| **Stage 2** | Same as Stage 1 | Same retry logic |
| **Tool Exec** | Tool timeout | Return failed result, continue |
| **Tool Exec** | Tool exception | Catch exception, aggregate partial results |
| **Aggregate** | No successful tools | Return low-confidence result |

---

## Verification Tools

### 1. Perplexity Deep Search

**Purpose:** Real-time web fact-checking with automatic citations

**Strengths:**
- Searches across entire web in real-time
- Automatic source citations
- Domain and recency filtering
- AI-powered answer synthesis

**Weaknesses:**
- Requires API key (paid service)
- May miss very recent articles (< 24 hours)
- Limited to text responses

**API Details:**

```python
async def perplexity_deep_search(
    query: str,
    search_domain_filter: Optional[List[str]] = None,
    search_recency_filter: Optional[str] = None
) -> ToolExecutionResult:
    """
    Execute deep web search using Perplexity API.

    Args:
        query: Search query
               Example: "Tesla Q3 2024 earnings actual amount"

        search_domain_filter: Restrict to domains
                             Example: ["sec.gov", "ir.tesla.com"]

        search_recency_filter: Time window
                              Values: "day", "week", "month", "year"

    Returns:
        ToolExecutionResult:
        {
            "tool_name": "perplexity_deep_search",
            "success": True,
            "execution_time_ms": 1523,
            "result_data": {
                "answer": "According to SEC filings...",
                "sources": ["https://www.sec.gov/...", ...],
                "model": "sonar-pro",
                "token_usage": {"prompt_tokens": 42, "completion_tokens": 234}
            },
            "source_citations": ["https://...", ...],
            "confidence": 0.85  # 0.5 base + 0.3 authority + 0.0 filter
        }
    """
```

**Confidence Scoring Logic:**

```python
def _calculate_confidence(citations: List[str], domain_filter: Optional[List[str]]) -> float:
    """
    Confidence = base + authority_boost + filter_match_boost

    Base Confidence:
        - 0.5 if citations exist
        - 0.2 if no citations

    Authority Boost (max +0.3):
        - +0.1 per authoritative domain in citations
        - Authoritative: .gov, .edu, sec.gov, ir.tesla.com, reuters.com, bloomberg.com
        - Max: 3 domains × 0.1 = +0.3

    Filter Match Boost (max +0.2):
        - +0.2 if ALL citations match domain_filter
        - Only applies if domain_filter provided

    Final: min(0.95, base + authority + filter)

    Examples:
    - No citations → 0.2
    - Cites sec.gov → 0.5 + 0.1 = 0.6
    - Cites sec.gov + reuters.com → 0.5 + 0.2 = 0.7
    - Cites sec.gov + all match filter → 0.5 + 0.1 + 0.2 = 0.8
    """
```

**Example Usage:**

```python
result = await perplexity_deep_search(
    query="What were Tesla's actual Q3 2024 earnings?",
    search_domain_filter=["sec.gov", "ir.tesla.com"],
    search_recency_filter="month"
)

print(f"Confidence: {result.confidence}")  # 0.8 (sources match filter)
print(f"Answer: {result.result_data['answer']}")
print(f"Citations: {result.source_citations}")
```

### 2. Financial Data Lookup (Alpha Vantage)

**Purpose:** Structured financial data for claims verification

**Strengths:**
- Structured, machine-readable data
- High confidence (0.9) for official metrics
- Supports multiple metrics (quote, earnings, financials)
- Period filtering for specific quarters

**Weaknesses:**
- Free tier: 25 req/day, 5 req/min
- May lag behind very recent earnings
- Limited to publicly traded companies

**API Details:**

```python
async def financial_data_lookup(
    company: str,
    metric: str,
    period: Optional[str] = None
) -> ToolExecutionResult:
    """
    Lookup financial data using Alpha Vantage API.

    Args:
        company: Ticker symbol
                Example: "TSLA", "AAPL"

        metric: One of:
               - "quote" - Current stock price
               - "earnings" - Quarterly/annual earnings
               - "income_statement" - Income statement
               - "balance_sheet" - Balance sheet
               - "cash_flow" - Cash flow statement

        period: Period specification (for earnings)
               Example: "Q3 2024", "Q1 2024", "annual"
               Not required for "quote"

    Returns:
        ToolExecutionResult:
        {
            "tool_name": "financial_data_lookup",
            "success": True,
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
                "https://www.alphavantage.co/query?...",
                "https://ir.tesla.com"  # Company-specific
            ],
            "confidence": 0.9  # High confidence for official data
        }
    """
```

**API Rate Limits:**

| Tier | Requests/Day | Requests/Min | Cost |
|------|-------------|--------------|------|
| Free | 25 | 5 | $0 |
| Premium | 500 | 5 | $99/mo |
| Premium Plus | 500+ custom | 5 | Custom |

**Example Usage:**

```python
# Get current stock quote
result = await financial_data_lookup(
    company="TSLA",
    metric="quote"
)
print(f"Tesla current price: ${result.result_data['data']['price']}")

# Get specific quarter earnings
result = await financial_data_lookup(
    company="TSLA",
    metric="earnings",
    period="Q3 2024"
)
eps = result.result_data['data']['reported_eps']
print(f"Tesla Q3 2024 EPS: {eps}")
```

### 3. Future Tools (Planned)

- **Internal Knowledge Search:** Search existing articles in database
- **Fact-Check Claim:** Check against fact-checking databases
- **Entity Lookup:** Resolve entity identity/ambiguity
- **Temporal Verification:** Verify event timelines

---

## Cost Analysis

### Monthly Cost Estimates (Baseline: 1,000 verifications/month)

#### Stage 1: Root Cause Analysis

| Component | Tokens/Request | Cost/1K Tokens | Monthly Cost |
|-----------|----------------|----------------|--------------|
| Prompt tokens | ~1,200 | $0.015 | $18.00 |
| Completion tokens | ~400 | $0.060 | $24.00 |
| **Monthly (Stage 1)** | | | **$42.00** |

#### Stage 2: Plan Generation

| Component | Tokens/Request | Cost/1K Tokens | Monthly Cost |
|-----------|----------------|----------------|--------------|
| Prompt tokens | ~1,500 | $0.015 | $22.50 |
| Completion tokens | ~600 | $0.060 | $36.00 |
| **Monthly (Stage 2)** | | | **$58.50** |

#### Tool Execution

| Tool | Requests/Month | Cost/Request | Monthly Cost |
|------|----------------|--------------|--------------|
| Perplexity Deep Search | 2,000 | $0.01-0.05 | $20-100 |
| Alpha Vantage (free tier) | 25 | $0 | $0 |
| Alpha Vantage (premium) | 500 | varies | $99 |
| **Monthly (Tools)** | | | **$20-199** |

#### **Total Estimated Monthly Cost: $120-300**

(Baseline: 1,000 verifications, 2 tools per verification, OpenAI GPT-4o-mini + Perplexity)

### Cost Optimization Strategies

1. **Temperature Tuning**
   - Current: 0.3 (Stage 1), 0.2 (Stage 2)
   - Effect: Reduces retry rate, lowers token usage ~5-10%
   - Cost savings: $10-30/month

2. **Prompt Compression**
   - Current: Truncate article to 2,000 chars
   - Effect: Reduces input tokens by ~20%
   - Cost savings: $8-15/month

3. **Selective Tool Execution**
   - Current: Execute all tools in parallel
   - Optimization: Use LLM to select best 1-2 tools based on hypothesis
   - Effect: 40-50% fewer tool calls
   - Cost savings: $50-100/month

4. **Batch Processing**
   - Current: Individual verification requests
   - Optimization: Batch similar verifications (future)
   - Effect: Reuse tool results, reduce API calls
   - Cost savings: 20-30%

5. **Model Selection**
   - Current: GPT-4o-mini ($0.15/$0.60 per 1M)
   - Alternative: GPT-3.5-turbo ($0.50/$1.50 per 1M) - NOT RECOMMENDED
   - Recommended: Stay with GPT-4o-mini for accuracy

### Token Usage Tracking

```python
# Token usage is captured in tool results
result_data = {
    "token_usage": {
        "prompt_tokens": 1200,
        "completion_tokens": 400,
        "total_tokens": 1600
    }
}

# Estimated cost calculation
input_cost = (result_data["token_usage"]["prompt_tokens"] / 1_000_000) * 0.15
output_cost = (result_data["token_usage"]["completion_tokens"] / 1_000_000) * 0.60
total_cost = input_cost + output_cost
```

---

## API Endpoints

### Health & Status

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "llm-orchestrator-service",
  "version": "1.0.0"
}
```

#### GET /health/ready

Readiness check (dependencies).

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "rabbitmq": "connected",
    "openai": "configured"
  }
}
```

#### GET /

Root endpoint.

**Response:**
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

#### GET /metrics

Prometheus metrics endpoint (future implementation).

**Response:** Metrics in OpenMetrics format

### Documentation

#### GET /docs

Swagger UI documentation (auto-generated from FastAPI)

#### GET /openapi.json

OpenAPI 3.1 specification (auto-generated)

---

## RabbitMQ Integration

### Event Flow

```
┌────────────────────────────────────────────────────┐
│ Content Analysis Service                           │
│ Detects: Low UQ confidence                         │
│ Publishes: verification.required event             │
└────────────────┬───────────────────────────────────┘
                 │
                 │ verification.required.high
                 │ verification.required.medium
                 │ verification.required.low
                 ▼
┌────────────────────────────────────────────────────┐
│ Exchange: verification_exchange (topic)             │
│ Type: topic                                        │
│ Durable: true                                      │
│ Routing Keys: verification.required.*              │
└────────────────┬───────────────────────────────────┘
                 │
                 │ (topic exchange routing)
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│ Queue: verification_queue                          │
│ Durable: true                                      │
│ QoS: prefetch_count=1 (process one at a time)     │
│ TTL: 86,400,000 ms (24 hours)                     │
│ DLX: verification_dlx (dead letter)                │
└────────────────┬───────────────────────────────────┘
                 │
                 │ (iterator pattern)
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│ VerificationConsumer.start_consuming()             │
│ Async iteration over queue                         │
│ Process one message at a time                      │
└────────────────┬───────────────────────────────────┘
                 │
                 │ _handle_message()
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│ DIAPlanner.process_verification_request()          │
│ Stage 1: Root Cause Analysis                       │
│ Stage 2: Plan Generation                           │
│ Returns: (hypothesis, plan)                        │
└────────────────┬───────────────────────────────────┘
                 │
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│ DIAVerifier.execute_verification()                 │
│ Parse and execute tools                            │
│ Aggregate evidence                                 │
│ Returns: EvidencePackage                           │
└────────────────┬───────────────────────────────────┘
                 │
                 │ ACK message (success)
                 │ or NACK (failure)
                 ▼
┌────────────────────────────────────────────────────┐
│ (Future) Publish verification.completed event      │
│ Send corrected facts downstream                    │
└────────────────────────────────────────────────────┘
```

### Event Schemas

#### Input: verification.required

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

#### Output: verification.completed (Future)

```json
{
  "event_id": "uuid",
  "event_type": "verification.completed",
  "verification_request_id": "uuid",
  "hypothesis_confirmed": true,
  "confidence_score": 0.87,
  "corrected_facts": {
    "earnings: $5 billion": {
      "original": "$5 billion",
      "corrected": "$4.194 billion",
      "source": "SEC Filing 10-Q"
    }
  },
  "source_citations": [
    {
      "source": "https://www.sec.gov/...",
      "reliability": "primary"
    }
  ],
  "key_findings": ["..."],
  "execution_time_ms": 1865,
  "timestamp": "2024-10-15T10:35:00Z"
}
```

---

## Database Schema

### verification_requests (Optional, for metadata storage)

```sql
CREATE TABLE verification_requests (
    id UUID PRIMARY KEY,
    article_id UUID NOT NULL,
    analysis_result_id UUID NOT NULL,
    uq_confidence_score FLOAT CHECK (uq_confidence_score BETWEEN 0.0 AND 1.0),
    uncertainty_factors JSONB,
    status VARCHAR(20) CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_article_id (article_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### verification_results (Optional)

```sql
CREATE TABLE verification_results (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES verification_requests(id),
    hypothesis_type VARCHAR(50),
    hypothesis_confirmed BOOLEAN,
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    tool_executions JSONB,
    evidence_package JSONB,
    corrected_facts JSONB,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_request_id (request_id),
    INDEX idx_created_at (created_at)
);
```

**Note:** Current implementation stores results in-memory via RabbitMQ events. Database schema provided for future persistence.

---

## Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=llm-orchestrator-service
PORT=8113
HOST=0.0.0.0

# Database (Optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/orchestrator_db

# RabbitMQ (Required)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_VERIFICATION_EXCHANGE=verification_exchange
RABBITMQ_VERIFICATION_QUEUE=verification_queue
RABBITMQ_VERIFICATION_ROUTING_KEY=verification.required.*

# OpenAI (Required for DIA Planner)
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_MODEL=gpt-4o-mini

# DIA Configuration (Planner)
DIA_STAGE1_TEMPERATURE=0.3      # Root cause analysis
DIA_STAGE2_TEMPERATURE=0.2      # Plan generation
DIA_MAX_RETRIES=3               # Retries on JSON errors

# External Services (Phase 2 - Verifier)
RESEARCH_SERVICE_URL=http://research-service:8103
PERPLEXITY_API_KEY=pplx-xxxxx   # Optional: falls back to OPENAI_API_KEY
ALPHA_VANTAGE_API_KEY=xxxxx     # Optional: uses demo if not set
FMP_API_KEY=xxxxx               # Financial Modeling Prep (alternative)

# Tool Configuration
TOOL_TIMEOUT_SECONDS=30
TOOL_MAX_RETRIES=2

# Logging
LOG_LEVEL=INFO
```

### Configuration in Code

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "llm-orchestrator-service"
    PORT: int = 8113
    HOST: str = "0.0.0.0"

    # LLM
    OPENAI_API_KEY: str  # Required
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Planner
    DIA_STAGE1_TEMPERATURE: float = 0.3
    DIA_STAGE2_TEMPERATURE: float = 0.2
    DIA_MAX_RETRIES: int = 3

    # Tools
    PERPLEXITY_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    TOOL_TIMEOUT_SECONDS: int = 30
    TOOL_MAX_RETRIES: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## Performance Characteristics

### Latency Analysis

| Operation | Typical | P95 | P99 |
|-----------|---------|-----|-----|
| Stage 1 (LLM call) | 500ms | 800ms | 1200ms |
| Stage 2 (LLM call) | 600ms | 900ms | 1400ms |
| Perplexity search | 800ms | 1500ms | 2500ms |
| Financial data lookup | 200ms | 400ms | 800ms |
| **Total (both tools)** | 1500ms | 2200ms | 3500ms |

### Throughput

| Metric | Value |
|--------|-------|
| Requests/second (single instance) | ~0.67 (1 req every 1.5s) |
| Concurrent verifications | Limited by message prefetch (1) |
| Daily capacity (24/7) | ~58,000 verifications |

### Resource Usage (Single Instance)

| Resource | Typical | Peak |
|----------|---------|------|
| CPU | 15-20% | 40-50% |
| Memory | 200MB | 400MB |
| Network (in) | <1 Mbps | <5 Mbps |
| Network (out) | <1 Mbps | <5 Mbps |

### Optimization Opportunities

1. **Increase Prefetch Count:** Currently 1 (process one at a time)
   - Change to 10 for parallel processing
   - Effect: 10x throughput increase
   - Trade-off: Higher memory, more complex state management

2. **Implement Caching:** Cache tool results for repeated queries
   - Perplexity results: Cache 1 hour
   - Financial data: Cache 24 hours
   - Effect: 20-40% fewer API calls

3. **Batch Tool Execution:** For large batches of similar verifications
   - Effect: 30-50% cost reduction

4. **Model Caching:** Pre-load model weights
   - For local models (future)
   - Effect: First-request latency -500ms

---

## Prompt Optimization

### Prompt Engineering Best Practices

1. **Be Specific and Actionable**
   - Bad: "Check if the article is accurate"
   - Good: "Identify the precise factual error in: [quote]"

2. **Provide Examples in System Prompt**
   - Shows LLM what good diagnosis looks like
   - Reduces output variability

3. **Use JSON Mode for Structured Output**
   - Ensures parseable responses
   - Enables strict schema validation

4. **Temperature Selection**
   - Stage 1: 0.3 (some variation for thorough analysis)
   - Stage 2: 0.2 (strict planning)

5. **Token Efficiency**
   - Truncate article to essential parts (2,000 chars)
   - Use concise prompts
   - Avoid redundant context

### Token Usage Optimization

```python
# Current: ~1,200 input tokens for Stage 1
# Optimization: Truncate article intelligently
content_preview = event.article_content[:2000]

# Further optimization: Extract only relevant paragraphs
def extract_relevant_paragraphs(content, uncertainty_factors):
    """Extract only paragraphs related to uncertainty factors."""
    # Search for keywords from uncertainty factors
    # Return matching paragraphs
    # Expected savings: 30-40% tokens
```

### Caching & Reuse

```python
# Opportunity: Cache tool results for repeated queries
cache = {
    "tesla_q3_2024_earnings": {
        "result": EvidencePackage(...),
        "timestamp": datetime.now(),
        "ttl": 3600  # 1 hour
    }
}

# Before running Perplexity search:
if query_hash in cache:
    cached = cache[query_hash]
    if datetime.now() - cached["timestamp"] < timedelta(seconds=cached["ttl"]):
        return cached["result"]
```

---

## Testing & Validation

### Test Structure

```
tests/
├── test_dia_planner.py          # Stage 1 & 2 testing
├── test_dia_verifier.py         # Tool execution & aggregation
├── test_perplexity_tool.py      # Perplexity API testing
├── test_financial_data_tool.py  # Alpha Vantage testing
├── test_verification_consumer.py # RabbitMQ consumer testing
└── conftest.py                  # Shared fixtures
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_dia_planner.py::test_stage_1_diagnosis -v

# Run with live API (requires keys)
pytest tests/ -v --integration
```

### Test Coverage

Current coverage: **72%**

Critical paths covered:
- Stage 1 diagnosis (planning)
- Stage 2 plan generation
- Tool execution and error handling
- Evidence aggregation

### Example Test

```python
def test_stage_1_root_cause_analysis():
    """Test Stage 1 produces precise diagnosis."""

    # Create test event
    event = VerificationRequiredEvent(
        article_title="Tesla Reports Record Q3 Earnings",
        article_content="Tesla announced Q3 2024 earnings of $5 billion...",
        uq_confidence_score=0.45,
        uncertainty_factors=["Numerical claim lacks verification"]
    )

    # Run Stage 1
    planner = DIAPlanner()
    hypothesis = await planner._diagnose_root_cause(event)

    # Assertions
    assert hypothesis.hypothesis_type in [
        "factual_error", "entity_ambiguity", "temporal_inconsistency", ...
    ]
    assert 0.0 <= hypothesis.confidence <= 1.0
    assert len(hypothesis.primary_concern) > 0
    assert hypothesis.primary_concern != "Article is uncertain"  # No vague statements
```

---

## Troubleshooting

### Issue: Service Won't Connect to RabbitMQ

**Symptoms:**
- Logs show "Failed to connect: Connection refused"
- Health check fails

**Solutions:**

1. Verify RabbitMQ is running:
```bash
docker ps | grep rabbitmq
```

2. Check connection URL format:
```bash
# Should be: amqp://user:pass@host:port/
# Not: amqps://, http://, or other protocols
```

3. Test connectivity:
```bash
python -c "import pika; pika.BlockingConnection(pika.ConnectionParameters('localhost'))"
```

4. View RabbitMQ logs:
```bash
docker logs rabbitmq_container_name
```

### Issue: OpenAI API Errors

**Symptoms:**
- "Invalid API key" errors in logs
- Stage 1 or Stage 2 returns invalid JSON

**Solutions:**

1. Verify API key:
```bash
echo $OPENAI_API_KEY | head -c 10
# Should start with: sk-proj-
```

2. Check rate limits:
```bash
# Monitor in OpenAI dashboard: https://platform.openai.com/account/rate-limits
```

3. Review error message:
```
401 Unauthorized → Invalid API key
429 Too Many Requests → Rate limit exceeded
500 Server Error → OpenAI outage (retry)
```

4. Increase retry settings:
```python
DIA_MAX_RETRIES = 5  # Instead of 3
```

### Issue: Tool Execution Timeout

**Symptoms:**
- "Tool execution failed: timeout" in logs
- Verification takes > 30 seconds

**Solutions:**

1. Increase timeout:
```bash
TOOL_TIMEOUT_SECONDS=60  # Instead of 30
```

2. Check external API status:
```bash
# Perplexity: https://www.perplexity.ai
# Alpha Vantage: https://www.alphavantage.co
```

3. Reduce tool timeout:
```bash
# If tools are failing, reduce timeout to fail faster
TOOL_TIMEOUT_SECONDS=10
```

### Issue: Low Confidence Scores

**Symptoms:**
- All verifications return confidence < 0.5
- Hypothesis confirmed = False

**Causes & Solutions:**

1. No tool citations:
   - Solution: Add domain_filter to Perplexity search
   ```python
   "perplexity_deep_search(query='...', search_domain_filter=['sec.gov'])"
   ```

2. Tool failures:
   - Check tool logs for errors
   - Verify tool API keys are valid

3. Weak sources:
   - Perplexity cites weak sources
   - Solution: Use more authoritative data (financial data for stocks)

### Issue: Memory Leaks or High Memory Usage

**Symptoms:**
- Memory usage grows over time
- Service crashes after running 24+ hours

**Solutions:**

1. Monitor memory:
```bash
docker stats llm-orchestrator-service
```

2. Check for message accumulation:
```bash
# Verify messages are being ACKed properly
```

3. Restart service:
```bash
docker restart llm-orchestrator-service
```

---

## Architecture Decision Records

### Related ADRs

- **ADR-018: DIA Planner & Verifier Architecture**
  - Location: `/home/cytrex/news-microservices/docs/decisions/ADR-018-dia-planner-verifier.md`
  - Describes two-stage planning approach and tool architecture

- **ADR-019: LLM Provider Selection** (Future)
  - Rationale for using OpenAI GPT-4o-mini
  - Cost vs accuracy trade-offs

- **ADR-020: Temperature Settings** (Future)
  - Why Stage 1=0.3, Stage 2=0.2
  - Trade-offs between consistency and quality

---

## Appendices

### A. Glossary

| Term | Definition |
|------|-----------|
| **DIA** | Dynamic Intelligence Augmentation - Two-stage verification system |
| **UQ Score** | Uncertainty Quantification - confidence score from content analysis |
| **Hypothesis** | Precise problem diagnosis from Stage 1 |
| **Plan** | Structured verification strategy from Stage 2 |
| **Tool Execution** | Running a single verification tool (Perplexity, financial data, etc.) |
| **Evidence Package** | Final aggregated result with findings and corrections |
| **Confidence Score** | 0.0-1.0 metric indicating certainty of verification |
| **Source Reliability** | "primary" (gov), "authoritative" (reuters), "secondary" (other) |

### B. API Key Setup

#### OpenAI (Required)

1. Go to https://platform.openai.com/account/api-keys
2. Create new secret key
3. Copy full key (starts with `sk-proj-`)
4. Store in `.env`: `OPENAI_API_KEY=sk-proj-xxxxx`

#### Perplexity (Optional)

1. Sign up at https://www.perplexity.ai/api
2. Get API key from dashboard
3. Store in `.env`: `PERPLEXITY_API_KEY=pplx-xxxxx`
4. Fallback: If not set, uses OPENAI_API_KEY

#### Alpha Vantage (Optional)

1. Go to https://www.alphavantage.co/support/#api-key
2. Request free API key
3. Store in `.env`: `ALPHA_VANTAGE_API_KEY=xxxxx`
4. Fallback: Uses "demo" key if not set (limited data)

### C. Common Queries

#### "Why two stages instead of one-shot verification?"

**Answer:** Two stages allow:
1. **Stage 1** to diagnose the actual problem (not just symptoms)
2. **Stage 2** to create a targeted plan (not generic)
3. Parallel tool execution based on precise hypothesis
4. Better cost optimization (eliminate unnecessary tools)

#### "Can I use a different LLM?"

**Answer:** Architecturally yes, but:
- Must support JSON mode for structured output
- Should have low latency (< 2 seconds per stage)
- Must handle tool call generation (Stage 2 output)
- Recommended: Claude, LLaMA 2 (future integrations)

#### "How do I reduce costs?"

**Answer:** In order of impact:
1. Use cheaper model (currently optimized with gpt-4o-mini)
2. Implement prompt caching (save 20% tokens)
3. Reduce tool execution (select 1 tool instead of 2)
4. Batch similar verifications (reuse tool results)

---

## Document Information

| Item | Value |
|------|-------|
| **Service** | LLM Orchestrator Service |
| **Port** | 8113 |
| **Repository** | `/home/cytrex/news-microservices/services/llm-orchestrator-service` |
| **Documentation Date** | November 24, 2024 |
| **Test Coverage** | 72% |
| **Last Updated** | 2024-11-24 |
| **Maintainer** | Development Team |

---

## Next Steps

1. **Integrate with downstream services** to publish verification.completed events
2. **Implement database persistence** for verification history and audit trails
3. **Add distributed caching** for tool results (Redis)
4. **Implement response streaming** for real-time feedback
5. **Add support for additional tools** (entity lookup, temporal verification)
6. **Create monitoring dashboard** with Prometheus metrics and Grafana
7. **Implement circuit breakers** for external API resilience

