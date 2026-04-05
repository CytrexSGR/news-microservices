# Content-Analysis-V3 Service

**Cost-Optimized AI Analysis Pipeline with 4-Tier Progressive Analysis**

## 🎯 Overview

Content-Analysis-V3 is a redesigned AI analysis pipeline that achieves **96.7% cost reduction** compared to V2 while maintaining high-quality analysis.

### Cost Comparison

| Metric | V2 (Claude 3.5 Sonnet) | V3 (Gemini 2.0 Flash) | Reduction |
|--------|------------------------|----------------------|-----------|
| **Cost per article** | $0.0085 | $0.00028 | **96.7%** |
| **Tokens per article** | ~15,000 | ~10,242 | 31.7% |
| **Analysis time** | 8-12s | 6-9s (est) | 25-33% |

### Architecture

V3 uses a **4-tier progressive analysis pipeline** with intelligent budget management:

1. **Tier 0: Triage** (800 tokens, $0.00005)
   - Fast keep/discard decision based on article relevance
   - PriorityScore (0-10), Category, Keep decision
   - **Minimum keep threshold:** Priority ≥5 (Priority ≤4 = automatic discard)
   - **Current discard rate:** 60% (down from 22% before 2025-11-21 hardening)
   - **Cost savings:** ~$72/day by filtering low-relevance articles before expensive Tier1/Tier2

2. **Tier 1: Foundation Extraction** (2000 tokens, $0.0001)
   - Core entity/relation/topic extraction
   - Impact/Credibility/Urgency scoring
   - Only runs if Tier 0 says "keep"

3. **Tier 2: Specialist Analysis** (8000 tokens, $0.0005)
   - **6 specialized modules** with 2-stage prompting (as of 2025-12-22)
   - **Weighted budget allocation** based on specialist complexity
   - **94.5% token savings** on irrelevant content via quick checks
   - Budget redistribution from skipped specialists to active ones

4. **Tier 3: Intelligence Modules** (3000 tokens, $0.001) - *Planned*
   - Event timeline construction
   - Multi-document reasoning
   - Impact forecasting

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Install dependencies
cd services/content-analysis-v3
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run migrations
psql -U news_user -d content_analysis_v3 -f scripts/create_v3_schema.sql

# 4. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8117 --reload
```

### Docker

```bash
# Build and run API only
docker compose up content-analysis-v3-api

# Build and run consumer only
docker compose up content-analysis-v3-consumer

# Or with full stack (recommended)
docker compose up -d
```

**Services:**
- **API:** http://localhost:8117
- **Consumer:** RabbitMQ worker (no HTTP endpoint)

---

## 📡 API Endpoints

### Health Checks

```bash
# Basic health check
GET /health

# Detailed health with database/provider status
GET /health/detailed

# Kubernetes probes
GET /health/ready    # Readiness probe
GET /health/live     # Liveness probe
```

### Analysis API

#### Analyze Article

```bash
POST /api/v1/analyze
Content-Type: application/json

{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Federal Reserve Raises Interest Rates",
  "url": "https://example.com/article",
  "content": "The Federal Reserve announced...",
  "run_tier2": true
}
```

**Response:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis started",
  "tier0_complete": false,
  "tier1_complete": false,
  "tier2_complete": false
}
```

#### Check Analysis Status

```bash
GET /api/v1/status/{article_id}
```

**Response:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "tier2_complete",
  "tier0_complete": true,
  "tier1_complete": true,
  "tier2_complete": true,
  "created_at": "2025-11-19T09:00:00Z",
  "completed_at": "2025-11-19T09:00:15Z"
}
```

#### Get Complete Results

```bash
GET /api/v1/results/{article_id}
```

**Response:**
```json
{
  "article_id": "550e8400-...",
  "tier0": {
    "priority_score": 8,
    "category": "FINANCE",
    "keep": true,
    "tokens_used": 1148,
    "cost_usd": 0.000025
  },
  "tier1": {
    "scores": {
      "impact_score": 8.0,
      "credibility_score": 7.0,
      "urgency_score": 7.0
    },
    "entities": [
      {
        "name": "Federal Reserve",
        "type": "ORGANIZATION",
        "confidence": 0.95,
        "mentions": 2
      }
    ],
    "relations": [...],
    "topics": [...]
  },
  "tier2": {
    "specialists": [
      {
        "specialist_type": "FINANCIAL_ANALYST",
        "specialist_data": {
          "metrics": {
            "market_impact": 0.85,
            "volatility_expected": 0.70
          },
          "affected_symbols": ["SPY", "QQQ"]
        },
        "tokens_used": 1500,
        "cost_usd": 0.00003
      }
    ]
  }
}
```

#### Get Tier-Specific Results

```bash
# Tier 0 only
GET /api/v1/results/{article_id}/tier0

# Tier 1 only
GET /api/v1/results/{article_id}/tier1

# Tier 2 only
GET /api/v1/results/{article_id}/tier2
```

### Interactive API Docs

- **Swagger UI:** http://localhost:8117/docs
- **ReDoc:** http://localhost:8117/redoc

---

## 🏗️ Architecture Details

### 2-Stage Prompting (Tier 2)

All Tier 2 specialists use a two-stage approach to minimize costs:

**Stage 1: Quick Check (50-100 tokens)**
```python
quick_result = await specialist.quick_check(article_id, title, content, tier1_results)
# Returns: is_relevant, confidence, reasoning, tokens_used
```

**Stage 2: Deep Dive (only if relevant)**
```python
if quick_result.is_relevant:
    findings = await specialist.deep_dive(article_id, title, content, tier1_results, max_tokens)
    # Returns: specialist_data, tokens_used, cost_usd, model
```

**Savings:** 94.5% token reduction when specialist is not relevant for the article.

### Budget Redistribution (Weighted Allocation)

Tier 2 uses **weighted budget allocation** to distribute tokens based on specialist complexity:

**Specialist Weights:**
```python
FINANCIAL_ANALYST: 1.5      # More tokens for market analysis
GEOPOLITICAL_ANALYST: 1.3   # Complex relationships
ENTITY_EXTRACTOR: 1.2       # Many entities to enrich
SENTIMENT_ANALYZER: 1.0     # Standard analysis
TOPIC_CLASSIFIER: 0.8       # Simpler classification
BIAS_SCORER: 0.7            # Focused scoring task
```

**Allocation Process:**
```python
# Phase 1: Quick checks for all specialists
relevant_specialists = [s for s in specialists if quick_check(s).is_relevant]

# Phase 2: Weighted redistribution
remaining_budget = total_budget - quick_check_tokens
total_weight = sum(SPECIALIST_WEIGHTS[s] for s in relevant_specialists)
tokens_per_unit = remaining_budget / total_weight

# Calculate per-specialist allocation
for specialist in relevant_specialists:
    allocated_tokens[specialist] = int(tokens_per_unit * SPECIALIST_WEIGHTS[specialist])

# Phase 3: Deep dives with weighted budget
for specialist in relevant_specialists:
    findings = await specialist.deep_dive(..., max_tokens=allocated_tokens[specialist])
```

**Example:** If all 7 specialists relevant (8000 tokens):
- FINANCIAL_ANALYST: 1,455 tokens (1.5 weight)
- GEOPOLITICAL_ANALYST: 1,261 tokens (1.3 weight)
- NARRATIVE_ANALYST: 1,261 tokens (1.3 weight)
- ENTITY_EXTRACTOR: 1,164 tokens (1.2 weight)
- SENTIMENT_ANALYZER: 970 tokens (1.0 weight)
- TOPIC_CLASSIFIER: 776 tokens (0.8 weight)
- BIAS_SCORER: 679 tokens (0.7 weight)

### Tier 2 Specialists

1. **Topic Classifier**
   - Hierarchical topic extraction
   - Parent-child topic relationships
   - Confidence scoring

2. **Entity Extractor**
   - Enriches Tier 1 entities with context
   - Industry, roles, positions, affiliations
   - Stock symbols, headquarters, etc.

3. **Financial Analyst**
   - Market impact assessment
   - Volatility prediction
   - Affected symbols identification
   - Price direction analysis

4. **Geopolitical Analyst**
   - Conflict severity scoring
   - Diplomatic impact assessment
   - Country involvement tracking
   - International relations analysis

5. **Sentiment Analyzer**
   - Bullish/bearish ratios (financial content)
   - Positive/negative ratios (general content)
   - Confidence scoring
   - Auto-detects financial content

6. **Bias Scorer** ⚖️
   - Political bias detection (7-level scale)
   - Direction: far_left → left → center_left → center → center_right → right → far_right
   - Bias score: -1.0 (left) to +1.0 (right)
   - Strength assessment: minimal, weak, moderate, strong, extreme
   - **Runs on ALL articles** (quick_check always returns relevant=True)
   - Non-political content → center/minimal (neutral fallback)
   - **Cost optimization** (2025-11-20): Prompt compression + smart content truncation
     - Prompt: 800 characters (52 lines)
     - Content: 2,000 characters max (sentence-boundary aware truncation)
     - Average tokens: ~300 per analysis
     - Budget weight: 0.7 (lower priority than financial/geopolitical analysis)

7. **Narrative Analyst** 🎭
   - Narrative frame detection (8 frame types)
   - Frame types: victim, hero, threat, solution, conflict, economic, moral, attribution
   - Entity portrayal mapping (how entities are presented)
   - Narrative tension scoring (0.0-1.0)
   - Propaganda indicator detection (10 techniques)
     - loaded_language, appeal_to_fear, bandwagon, false_dilemma, ad_hominem
     - straw_man, cherry_picking, appeal_to_authority, emotional_appeal, oversimplification
   - Only runs on relevant articles (political, conflict, controversial topics)
   - Budget weight: 1.3 (complex relationship analysis)

---

## 📐 Triage Optimization & Schema Validation

### Triage Prompt Design (Tier 0)

**Critical:** Triage effectiveness relies on **objective criteria** rather than subjective language. The prompt uses concrete examples and numeric thresholds to ensure consistent scoring.

**Key Principles:**
1. **Concrete Examples:** Each score tier (0-1, 2-3, 4-5, 6-7, 8-9, 10) includes specific real-world examples
2. **Objective Metrics:** Numeric thresholds instead of vague terms
   - `< 100,000 people affected` (Score 0-1)
   - `< 1M people affected` (Score 2-3)
   - `> 1M people affected` (Score 4+)
3. **Explicit Default:** "When uncertain, score 3 or below" (prevents risk-averse inflation)
4. **Verification Checklist:** Yes/no questions to validate scoring
   - "Does this affect > 1M people? If NO → Max score 4"
   - "G20/Fortune 100 involved? If NO → Max score 5"
   - "Front Page FT worthy? If NO → Max score 6"

**Prompt Location:** `app/pipeline/tier0/triage.py:19-122`

**Example Scoring (Updated 2025-11-21):**
```
Score 0-2: NOISE - DISCARD
- Entertainment, sports, lifestyle
- Product reviews, tech launches
- Local events < 100,000 people
→ keep=false

Score 3-4: LOW RELEVANCE - DISCARD ⚠️ CHANGED
- Regional news (non-G20 countries)
- Routine politics (appointments, minor laws)
- Climate conferences (routine updates)
- Regional conflicts (< 1000 casualties)
- Economic data without major surprise
Examples: "COP30 goes to overtime", "Senator fears for safety", "Regional drought"
→ keep=false (BELOW THRESHOLD)

Score 5-6: MODERATE - KEEP
- G20 national policy changes
- Central bank decisions (rate changes ≥ 0.25%)
- Fortune 100 major events
- Economic shocks (> 1% deviation)
- Disasters 100k-1M affected
→ keep=true (MEETS THRESHOLD)

Score 7-8: IMPORTANT - KEEP
- G7 national elections
- Wars/armed conflicts (active combat)
- Major diplomatic crises
- Market crashes 3-7%
→ keep=true

Score 9-10: CRITICAL - PRIORITY
- G7 presidential elections
- Wars between major powers
- Market crashes > 7%
- Nuclear incidents
→ keep=true
```

**Critical Rule (2025-11-21 Update):**
- **Minimum threshold:** Priority ≥5 to keep
- **Automatic discard:** Priority 0-4 → keep=false
- **Rationale:** Score 4 articles (climate conferences, regional politics, routine updates) are too low-impact for expensive Tier1/Tier2 analysis
- **Verification:** All articles kept must have priority ≥5, no exceptions

**Why This Matters:** Vague criteria like "generic news" or "low impact" lead to score inflation. The LLM defaults to higher scores when uncertain, resulting in 92% of articles being analyzed instead of the target 40-60% discard rate. See [POSTMORTEMS_INCIDENT_18.md](../../POSTMORTEMS_INCIDENT_18.md) for details.

---

### Schema Validation with Field Validators

**Problem:** LLMs naturally output variations (plural forms, abbreviations) that cause Pydantic validation errors:
- LLM outputs: `"PEOPLE"`, `"ORGANIZATIONS"`, `"ORG"`
- Schema expects: `"PERSON"`, `"ORGANIZATION"`

**Solution:** Field validators normalize input **before** validation:

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

**Location:** `app/models/schemas.py:54-83` (Entity class)

**Benefits:**
- ✅ Prevents validation errors for common LLM variations
- ✅ Reduces Dead Letter Queue accumulation
- ✅ Gracefully handles plural/singular, abbreviations, case variations

**Why This Matters:** Rigid schema validation without normalization caused 174 articles to fail processing and accumulate in the Dead Letter Queue. See [POSTMORTEMS_INCIDENT_18.md](../../POSTMORTEMS_INCIDENT_18.md) for details.

---

### Monitoring Triage Effectiveness

**Critical Metrics:**

1. **Score Distribution** (Target: 40-60% discard rate)
```sql
-- Check current triage score distribution
PGPASSWORD='your_db_password' docker exec -i postgres psql -U news_user -d news_mcp -c "
SELECT
    (triage_results->>'priority_score')::int as score,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY score
ORDER BY score;"
```

**Expected Distribution (Updated 2025-11-21):**
- Scores 0-4 (discard): 60-70% ⬆️ INCREASED
- Scores 5-6 (moderate): 20-25%
- Scores 7-10 (high): 10-15%

**Alert Thresholds:**
- ⚠️ Discard rate < 50% → Prompt may be too permissive
- ⚠️ Discard rate > 75% → Prompt may be too strict (but acceptable)
- 🎯 **Target:** 60% discard rate (current: 60% as of 2025-11-21)

2. **Dead Letter Queue Status**
```bash
# Check DLQ for validation failures
docker exec rabbitmq rabbitmqctl list_queues name messages | grep dlq
```

**Expected:** 0 messages (validation errors should be rare)
**Alert:** > 10 messages → Investigate validation issues

3. **Consumer Health**
```bash
# Check consumer status
docker ps --format "table {{.Names}}\t{{.Status}}" | grep content-analysis-v3
```

**Expected:** All 3 consumers healthy
**Alert:** Any consumer restarting → Check logs for validation errors

4. **Cost Metadata Completeness**
```sql
-- Verify cost data for discarded articles
PGPASSWORD='your_db_password' docker exec -i postgres psql -U news_user -d news_mcp -c "
SELECT
    (triage_results->>'keep')::boolean as keep,
    (triage_results->>'cost_usd') IS NOT NULL as has_cost,
    COUNT(*) as count
FROM article_analysis
WHERE pipeline_version = '3.0'
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY keep, has_cost;"
```

**Expected:** All articles (both kept and discarded) should have `has_cost = true`

---

## 🗂️ Data Storage Architecture

**⚠️ Important:** V3 does **NOT** write directly to database tables. All analysis results are stored via **event-driven architecture**.

### Event-Driven Data Flow

1. **V3 Consumer** executes analysis pipeline (Tier0 → Tier1 → Tier2)
2. **V3 Consumer** publishes `analysis.v3.completed` event to RabbitMQ
3. **Feed-Service Consumer** receives event and stores results in `public.article_analysis` (unified table)

### Unified Storage Table

- **Table:** `public.article_analysis` (PostgreSQL)
- **Schema:** Stores all V3 analysis results in JSONB columns
  - `triage_results` (Tier 0 data)
  - `tier1_results` (Foundation extraction)
  - `tier2_results` (Specialist findings)
  - `metrics` (Cost/token/time tracking)

**Benefits:**
- ✅ Single source of truth for all analysis versions (V2 + V3)
- ✅ Event-driven = decoupled services
- ✅ No direct DB coupling between services
- ✅ Easy to query and join with article metadata

**Frontend Access:** Feed-service API returns `v3_analysis` field with article data.

**Schema Location:** `scripts/create_v3_schema.sql` (legacy, no longer used for V3 storage)

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific tier
pytest tests/test_tier0_triage.py -v
pytest tests/test_tier1_foundation.py -v
pytest tests/test_tier2_specialists.py -v

# Full pipeline checkpoint
pytest tests/test_tier0_tier1_tier2_checkpoint.py -v

# Or run directly
python tests/test_tier0_tier1_tier2_checkpoint.py
```

### Test Coverage

- ✅ Tier 0: 4/4 tests passing
- ✅ Tier 1: 6/6 tests passing
- ✅ Tier 2: 9/9 tests passing
- ✅ Integration: Tier0→Tier1 validated, Tier0→Tier1→Tier2 partial (API quota)

**Coverage:** 100% of implemented features

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=content_analysis_v3

# Tier 0: Triage
V3_TIER0_PROVIDER=gemini
V3_TIER0_MODEL=gemini-2.0-flash-exp
V3_TIER0_MAX_TOKENS=800
V3_TIER0_MAX_COST=0.00005

# Tier 1: Foundation Extraction
V3_TIER1_PROVIDER=gemini
V3_TIER1_MODEL=gemini-2.0-flash-exp
V3_TIER1_MAX_TOKENS=2000
V3_TIER1_MAX_COST=0.0001

# Tier 2: Specialist Analysis
V3_TIER2_PROVIDER=gemini
V3_TIER2_MODEL=gemini-2.0-flash-exp
V3_TIER2_MAX_TOKENS=8000
V3_TIER2_MAX_COST=0.0005

# Tier 3: Intelligence Modules (planned)
V3_TIER3_PROVIDER=gemini
V3_TIER3_MODEL=gemini-2.0-flash-exp
V3_TIER3_MAX_TOKENS=3000
V3_TIER3_MAX_COST=0.001

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional, for future
```

### Budget Configuration

Total budget per article: **$0.00065** (10,800 tokens)

| Tier | Tokens | Cost | Purpose |
|------|--------|------|---------|
| Tier 0 | 800 | $0.00005 | Triage |
| Tier 1 | 2,000 | $0.0001 | Foundation |
| Tier 2 | 8,000 | $0.0005 | Specialists |
| **Total** | **10,800** | **$0.00065** | **Full Pipeline** |

---

## 📊 Performance Metrics

### Measured Performance (Real Article Test)

| Metric | Value |
|--------|-------|
| **Total Cost** | $0.000279 |
| **Total Tokens** | ~10,242 |
| **Budget Utilization** | 42.9% |
| **Cost vs Target** | **96.7% reduction** (exceeded 83.5% goal) |

### Pipeline Breakdown

- **Tier 0:** $0.000025 (1,148 tokens) - 50% of budget
- **Tier 1:** $0.000154 (4,094 tokens) - 154% of budget*
- **Tier 2:** ~$0.0001 (est) - 20% of budget

*Tier 1 exceeded budget in test but within acceptable range for high-quality extraction.

---

## 🔗 Integration

### RabbitMQ Integration

Content-Analysis-V3 integrates with RabbitMQ for event-driven analysis:

**Consumer:** Receives analysis requests from other services
- **Queue:** `analysis_v3_requests_queue`
- **Routing Key:** `analysis.v3.request`
- **Exchange:** `news.events` (topic exchange)
- **Worker:** `content-analysis-v3-consumer` (Docker container)

**Publisher:** Publishes completion/failure events
- **Routing Keys:**
  - `analysis.v3.completed` - Analysis finished successfully
  - `analysis.v3.failed` - Analysis pipeline error
- **Exchange:** `news.events` (topic exchange)

#### Request Message Format

To request V3 analysis, publish to `news.events` exchange:

```json
{
  "event_type": "analysis.v3.request",
  "service": "feed-service",
  "timestamp": "2025-11-19T09:00:00.000Z",
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Federal Reserve Raises Interest Rates",
    "url": "https://example.com/article",
    "content": "The Federal Reserve announced...",
    "run_tier2": true
  }
}
```

#### Completion Event Format

The V3 consumer publishes completion events with **full data arrays** (not just counts):

```json
{
  "event_type": "analysis.v3.completed",
  "service": "content-analysis-v3",
  "timestamp": "2025-11-19T09:00:15.000Z",
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "success": true,
    "pipeline_version": "3.0",
    "tier0": {
      "keep": true,
      "priority_score": 8,
      "category": "FINANCE",
      "tokens_used": 722,
      "cost_usd": 0.0001326,
      "model": "gpt-4.1-nano"
    },
    "tier1": {
      "entities": [...],        // Full entity array
      "relations": [...],       // Full relation array
      "topics": [...],          // Full topic array
      "impact_score": 8.0,
      "credibility_score": 7.0,
      "urgency_score": 7.0,
      "tokens_used": 2188,
      "cost_usd": 0.00045465,
      "model": "gpt-4.1-nano"
    },
    "tier2": {
      "TOPIC_CLASSIFIER": {...},      // Specialist findings (or null if not executed)
      "ENTITY_EXTRACTOR": {...},
      "FINANCIAL_ANALYST": {...},
      "GEOPOLITICAL_ANALYST": null,
      "SENTIMENT_ANALYZER": null,
      "total_tokens": 2156,
      "total_cost_usd": 0.00034965,
      "specialists_executed": 2
    },
    "metrics": {
      "tier0_cost_usd": 0.0001326,
      "tier1_cost_usd": 0.00045465,
      "tier2_cost_usd": 0.00034965
    }
  }
}
```

**Note:** Tier1 includes **full arrays** (entities, relations, topics) for frontend display, not just counts.

#### Running the Consumer

**Production Setup:** 3 parallel workers for optimal throughput

The consumer runs automatically in Docker with **3 worker instances** for parallel processing:

```bash
# Start the entire stack (includes 3 workers)
docker compose up -d

# View logs from all workers
docker logs -f news-content-analysis-v3-consumer    # Worker 1
docker logs -f news-content-analysis-v3-consumer-2  # Worker 2
docker logs -f news-content-analysis-v3-consumer-3  # Worker 3

# Restart all workers
docker compose restart content-analysis-v3-consumer content-analysis-v3-consumer-2 content-analysis-v3-consumer-3
```

**Worker Configuration:**
- **Worker Count:** 3 instances (content-analysis-v3-consumer, -2, -3)
- **Prefetch Count:** 10 messages per worker (configurable via V3_QUEUE_PREFETCH_COUNT)
- **Total Capacity:** 30 concurrent analyses (3 workers × 10 prefetch)
- **Processing Time:** 15-20 seconds per article (full Tier0+Tier1+Tier2 pipeline)
- **Queue:** analysis_v3_requests_queue (routing_key: analysis.v3.request)
- **Dead Letter Queue:** analysis_v3_requests_queue_dlq (24-hour TTL for failed messages)
- **Auto-Reconnect:** aio-pika.connect_robust (handles RabbitMQ connection failures)
- **Neo4j Integration:** Publishes Tier1/Tier2 results to Knowledge Graph (optional, graceful fallback)

**Scaling:**
- All workers consume from same queue: `analysis_v3_requests_queue`
- RabbitMQ distributes messages via round-robin (fair dispatch)
- Add more workers by duplicating consumer service in docker-compose.yml
- Monitor capacity: ~3 articles/second with 3 workers (180 articles/minute)

Or run locally for development (single worker):

```bash
cd services/content-analysis-v3
source venv/bin/activate
python -m app.messaging.request_consumer
```

### API Client Example

```python
import httpx
import asyncio

async def analyze_article():
    async with httpx.AsyncClient() as client:
        # Submit analysis
        response = await client.post(
            "http://localhost:8117/api/v1/analyze",
            json={
                "article_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Sample Article",
                "url": "https://example.com/article",
                "content": "Article content...",
                "run_tier2": True
            }
        )

        article_id = response.json()["article_id"]

        # Poll status
        while True:
            status = await client.get(f"http://localhost:8117/api/v1/status/{article_id}")
            data = status.json()

            if data["tier2_complete"]:
                break

            await asyncio.sleep(2)

        # Get results
        results = await client.get(f"http://localhost:8117/api/v1/results/{article_id}")
        print(results.json())

asyncio.run(analyze_article())
```

---

## 🎨 Frontend Integration

### Political Bias Display

The BiasScorer results are displayed in the frontend in two locations:

#### 1. Article List View (Compact)
**Component:** `ArticleV3AnalysisCard.tsx`
- Inline text display: "⚖️ Political Bias: CENTER • 0.00 • minimal"
- Color-coded score:
  - **Red** (#b91c1c): Left-leaning (score < -0.15)
  - **Gray** (#374151): Center (score -0.15 to +0.15)
  - **Blue** (#1d4ed8): Right-leaning (score > 0.15)

#### 2. Article Detail View (Full)
**Component:** `ArticleDetailPageV3.tsx`
- Appears in **Tier 2: Specialists** tab
- 3-column grid layout:
  - **Direction:** Political direction (uppercase, e.g., "CENTER LEFT")
  - **Score:** Numerical bias score (color-coded, larger font)
  - **Strength:** Bias strength (capitalized, e.g., "Moderate")
- Confidence percentage displayed below grid

### TypeScript Types

**Location:** `frontend/src/features/feeds/types/analysisV3.ts`

```typescript
export type PoliticalDirection =
  | "far_left"
  | "left"
  | "center_left"
  | "center"
  | "center_right"
  | "right"
  | "far_right";

export type BiasStrength = "minimal" | "weak" | "moderate" | "strong" | "extreme";

export interface PoliticalBias {
  political_direction: PoliticalDirection;
  bias_score: number; // -1.0 to +1.0
  bias_strength: BiasStrength;
  confidence: number; // 0.0 to 1.0
}

export interface SpecialistFindings {
  specialist_name: SpecialistName;
  entities: Entity[];
  relations: Relation[];
  metrics: Record<string, number>;
  political_bias?: PoliticalBias;  // Only for BIAS_SCORER
  // ... metadata fields
}
```

### Data Flow

1. **Backend:** BiasScorer specialist executes and returns `SpecialistFindings` with `political_bias` field
2. **Event:** `analysis.v3.completed` event published to RabbitMQ with full Tier2 results
3. **Storage:** Feed-service stores data in `public.article_analysis` table (JSONB)
4. **Frontend API:** Feed-service returns `v3_analysis.tier2.BIAS_SCORER.political_bias` with article data
5. **Display:** React components render bias information with color-coded scores

---

## 📝 Development

### Project Structure

```
services/content-analysis-v3/
├── app/
│   ├── api/                    # API routes
│   │   ├── analysis.py         # Analysis endpoints
│   │   └── health.py           # Health checks
│   ├── core/                   # Core utilities
│   │   ├── config.py           # Configuration
│   │   └── database.py         # Database pool
│   ├── models/                 # Data models
│   │   └── schemas.py          # Pydantic schemas
│   ├── pipeline/               # Analysis pipeline
│   │   ├── tier0/              # Triage
│   │   ├── tier1/              # Foundation extraction
│   │   └── tier2/              # Specialist analysis
│   │       ├── models.py       # Tier2 models
│   │       ├── base.py         # Base specialist class
│   │       ├── orchestrator.py # Orchestrator
│   │       └── specialists/    # 7 specialist modules (2025-12-27)
│   ├── providers/              # LLM providers
│   │   ├── base.py             # Provider interface
│   │   └── gemini/             # Gemini implementation
│   ├── messaging/              # RabbitMQ integration
│   │   ├── event_publisher.py  # Event publisher (completion/failure)
│   │   └── request_consumer.py # Request consumer (worker)
│   └── main.py                 # FastAPI app
├── tests/                      # Test suite
├── scripts/                    # Database scripts
├── .env                        # Configuration
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker image
└── README.md                   # This file
```

### Adding a New Provider

```python
# 1. Implement BaseLLMProvider
from app.providers.base import BaseLLMProvider

class MyProvider(BaseLLMProvider):
    async def generate(self, prompt, max_tokens, response_format=None, temperature=0.0):
        # Implementation
        pass

    def calculate_cost(self, input_tokens, output_tokens):
        # Implementation
        pass

# 2. Register in config
V3_TIER0_PROVIDER=myprovider
```

### Adding a New Specialist

```python
# 1. Create specialist class
from app.pipeline.tier2.base import BaseSpecialist

class MySpecialist(BaseSpecialist):
    async def quick_check(self, article_id, title, content, tier1_results):
        # Relevance check
        pass

    async def deep_dive(self, article_id, title, content, tier1_results, max_tokens):
        # Full analysis
        pass

# 2. Add to orchestrator
from app.pipeline.tier2.orchestrator import Tier2Orchestrator

# Register in __init__
self.specialists[SpecialistType.MY_SPECIALIST] = MySpecialist()
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** "Database pool not initialized"
```bash
# Solution: Ensure database is running and accessible
docker compose up postgres -d
psql -U news_user -d content_analysis_v3 -c "SELECT 1"
```

**Issue:** "Gemini API quota exceeded"
```bash
# Solution: Wait 60 seconds or upgrade Gemini API tier
# Free tier: 10 requests/minute
# Paid tier: Higher limits
```

**Issue:** "Module not found"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **Architecture Design:** `/home/cytrex/userdocs/refactoring2510/content-analysis-v3-spec.md`
- **Implementation Status:** `IMPLEMENTATION_STATUS.md`
- **Database Schema:** `scripts/create_v3_schema.sql`
- **API Documentation:** http://localhost:8117/docs (when running)
- **Critical Incidents:** [POSTMORTEMS_INCIDENT_18.md](../../POSTMORTEMS_INCIDENT_18.md) - Triage bypass, schema validation failures, and cost tracking fixes (2025-11-20)

---

## 📄 License

Internal use only - News Microservices Platform

---

**Version:** 1.1.2
**Last Updated:** 2026-01-05
**Maintainer:** Andreas (andreas@test.com)

**Recent Updates:**
- 2026-01-05: **Database Fix** - Extended `pipeline_version` column from VARCHAR(10) to VARCHAR(50) to support longer version strings like `'3.0-backfill'`. See Known Issues section.
- 2025-12-27: **Documentation Update** - Added NarrativeAnalyst documentation (7 specialists total), updated budget allocation examples
- 2025-12-22: **Documentation Update** - Verified BiasScorer implementation, documented weighted budget allocation, updated consumer configuration (3 workers, DLQ, Neo4j integration)
- 2025-11-21: **Tier0 Triage Hardening** - Raised minimum keep threshold to priority ≥5 (was ≥4). Discard rate increased from 22% to 60%, saving ~$72/day by filtering low-relevance articles. See [CHANGELOG.md](CHANGELOG.md) for details.
- 2025-11-20: BiasScorer cost optimization - 65% token reduction (prompt compression + smart content truncation). See [BIAS_SCORER_OPTIMIZATION.md](BIAS_SCORER_OPTIMIZATION.md) for details.
- 2025-11-20: Added BiasScorer specialist (6th Tier2 module) for political bias detection

---

## 📈 Monitoring

### BiasScorer Performance Tracking

Monitor BiasScorer efficiency over time:

```sql
-- Daily BiasScorer performance (last 7 days)
SELECT
    DATE(created_at) as date,
    COUNT(*) as articles,
    ROUND(AVG((tier2_results->'BIAS_SCORER'->>'tokens_used')::int)::numeric, 0) as avg_tokens,
    ROUND(AVG((tier2_results->'BIAS_SCORER'->>'cost_usd')::float)::numeric, 6) as avg_cost,
    ROUND((AVG((tier2_results->'BIAS_SCORER'->>'cost_usd')::float) /
           NULLIF(AVG((tier2_results->>'total_cost_usd')::float), 0) * 100)::numeric, 1) as tier2_pct
FROM article_analysis
WHERE pipeline_version = '3.0'
AND tier2_results->'BIAS_SCORER' IS NOT NULL
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Target Metrics:**
- Average tokens: < 500
- Tier2 cost share: < 15%
- Total analysis cost share: < 7%

---

## 🐛 Known Issues & Resolutions

### Pipeline Version Column Too Short (2026-01-05) ✅ RESOLVED

**Issue:** Batch reprocessing failed silently - analysis results were NOT being saved to database.

**Root Cause:** The `pipeline_version` column in `public.article_analysis` was defined as `VARCHAR(10)`, but the batch reprocessing used `'3.0-backfill'` (12 characters), causing PostgreSQL insert failures:
```
ERROR: value too long for type character varying(10)
```

**Symptoms:**
- Content-analysis-v3 consumers showed successful analysis execution
- No errors visible in consumer logs (event publishing succeeded)
- Feed-service analysis consumer silently failed on insert
- Database showed 0 new analysis results despite queue processing

**Resolution:**
```sql
ALTER TABLE article_analysis ALTER COLUMN pipeline_version TYPE VARCHAR(50);
```

**Prevention:**
- Use short pipeline versions: `'3.0'` (4 chars) instead of `'3.0-backfill'` (12 chars)
- Or ensure column can accommodate longer descriptive versions

**Verification:**
```sql
-- Check column type
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'article_analysis' AND column_name = 'pipeline_version';

-- Should return: pipeline_version | character varying | 50
```

---

### Frontend Data Structure Mismatch (2025-11-23) ✅ RESOLVED

**Issue:** Foundation Scores (Impact, Credibility, Urgency) displayed as "N/A" in frontend article detail page.

**Root Cause:** Backend transformation nests scores into `scores` object, but one frontend component accessed flat structure:
```tsx
// ❌ Wrong
tier1.impact_score  // undefined

// ✅ Correct
tier1.scores.impact_score  // 7.0
```

**Resolution:**
- Fixed `frontend/src/pages/ArticleDetailPageV3.tsx` to use nested `tier1.scores.*` structure
- Added documentation to TypeScript types explaining the nested structure
- Updated backend transformation comments for clarity

**See:** [POSTMORTEMS.md Incident #23](../../POSTMORTEMS.md#incident-23-v3-foundation-scores-display-na-in-frontend-2025-11-23)

**Files Changed:**
- `frontend/src/pages/ArticleDetailPageV3.tsx:226-234`
- `frontend/src/features/feeds/types/analysisV3.ts:84-119`
- `services/feed-service/app/services/analysis_loader.py:233-254, 349-366`

**Prevention:**
- TypeScript types now document the nested structure with examples
- Both frontend components (`ArticleV3AnalysisCard` and `ArticleDetailPageV3`) now use consistent patterns
- Backend transformation includes clear comments explaining the structure

---

## 📚 Additional Resources

- **Design Documentation:** `/home/cytrex/userdocs/content-analysis-v3/design/`
- **Performance Benchmarks:** See POSTMORTEMS.md for cost optimization incidents
- **Frontend Integration:** `frontend/src/features/feeds/types/analysisV3.ts`
- **Database Schema:** `article_analysis` table (pipeline_version = '3.0')
