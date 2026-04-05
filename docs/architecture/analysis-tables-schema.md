# Analysis Tables Schema Documentation

**Last Updated:** 2025-11-24
**Status:** ✅ **RESOLVED - SINGLE-TABLE ARCHITECTURE** (V2 Service Archived)

---

## ✅ RESOLUTION UPDATE (2025-11-24): Single-Table Architecture

**The dual-table issue has been RESOLVED.** The platform now uses a single unified table.

### Migration Completed

- **Legacy Service:** `content-analysis-v2` → **ARCHIVED** to `services/_archived/content-analysis-v2-20251124`
- **Legacy Table:** `content_analysis_v2.pipeline_executions` → Renamed to `_deprecated` (30-day retention)
- **Active Table:** `public.article_analysis` → **SINGLE SOURCE OF TRUTH** (22,021+ rows)
- **Backfill:** 304 missing articles restored from legacy table

### For Developers

✅ **Always use `public.article_analysis`** for analysis data
✅ `feed-service/app/services/analysis_loader.py` reads from unified table (30-40x faster)
✅ `feed-service/app/workers/analysis_consumer.py` writes to unified table
⚠️ Legacy table will be **DROPPED** after 2025-12-08 (30 days)

**See:** [POSTMORTEMS.md - Incident #8](../../POSTMORTEMS.md#incident-8) for full migration details

---

## Historical Context: Previous Dual-Table Situation

The news-microservices platform previously had **TWO separate tables** storing analysis results:

### Table Comparison

| Aspect | Legacy Table | Unified Table |
|--------|-------------|---------------|
| **Name** | `content_analysis_v2.pipeline_executions` | `public.article_analysis` |
| **Status** | ✅ **ACTIVELY USED** | ❌ **ORPHANED** (written but never read) |
| **Rows** | 7,097 (100% coverage) | 3,364 (47% coverage, only since Oct 31) |
| **Columns** | 22 | 15 |
| **Written By** | content-analysis-v2 workers (direct) | feed-service analysis-consumer (events) |
| **Read By** | content-analysis-v2 API → feed-service proxy | **NOBODY** (orphaned) |
| **Frontend** | ✅ Displays this data | ❌ Never sees this data |

### Impact

**Data Fragmentation:**
- 3,733 analyses exist ONLY in legacy table (pre-Oct 31)
- Unified table is missing 53% of historical data
- Data written to unified table is **NEVER displayed to users**

**Resource Waste:**
- Duplicate storage: ~4MB wasted
- Event processing: RabbitMQ messages for orphaned writes
- Worker CPU/memory: analysis-consumer running for no benefit

**Developer Confusion:**
- Which table should I query?
- Why are counts different?
- Where is the source of truth?

### Resolution Required

**Decision Status:** See [ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)

**Three Options:**
1. **Option A:** Complete migration to unified table (4-8h, recommended)
2. **Option B:** Rollback to legacy table only (2h, pragmatic)
3. **Option C:** Dual-table with clear boundaries (ongoing maintenance)

**Related Documentation:**
- [POSTMORTEMS.md - Incident #8](../../POSTMORTEMS.md#incident-8) - Full incident analysis
- [ADR-032](../decisions/ADR-032-dual-table-analysis-architecture.md) - Architecture decision
- [Analysis Storage Migration Guide](../guides/analysis-storage-migration-guide.md) - Implementation guide

---

## Table 1: Legacy Table (ACTIVELY USED) ✅

### Schema: `content_analysis_v2.pipeline_executions`

**Purpose:** Stores results from content-analysis-v2 AI pipeline executions.

**Status:** **ACTIVELY USED** - This is what the frontend displays.

**Access Pattern:**
```
1. content-analysis-v2 workers → Write directly to this table
2. content-analysis-v2 API → Read from this table
3. feed-service analysis_loader.py → Proxies to API
4. Frontend → Displays data from this table ✅
```

### Schema Definition

```sql
CREATE TABLE content_analysis_v2.pipeline_executions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL UNIQUE,  -- Foreign key to feed_items

    -- Execution Metadata
    pipeline_version VARCHAR(10) NOT NULL,  -- e.g., "2.0"
    success BOOLEAN NOT NULL DEFAULT false,
    agents_executed TEXT[] DEFAULT '{}',  -- List of agents that ran
    failed_agents TEXT[] DEFAULT '{}',    -- List of agents that failed
    error_message TEXT,

    -- Performance Metrics
    total_processing_time_ms INTEGER,
    total_cost_usd DECIMAL(10, 6),
    cache_hits INTEGER DEFAULT 0,

    -- Triage Results (Tier 0)
    triage_decision JSONB,  -- {relevance_score, reasoning, priority}

    -- Tier 1 Results
    tier1_summary JSONB,  -- {entities, summary, sentiment, topics}

    -- Tier 2 Results
    tier2_summary JSONB,  -- {financial, geopolitical, conflict, bias}

    -- Tier 3 Results
    tier3_summary JSONB,  -- {intelligence_synthesis}

    -- Individual Agent Results (Detailed)
    entity_results JSONB,
    summary_results JSONB,
    sentiment_results JSONB,
    topic_results JSONB,
    financial_results JSONB,
    geopolitical_results JSONB,
    conflict_results JSONB,
    bias_results JSONB,
    intelligence_results JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_pipeline_executions_article_id ON content_analysis_v2.pipeline_executions(article_id);
CREATE INDEX idx_pipeline_executions_success ON content_analysis_v2.pipeline_executions(success);
CREATE INDEX idx_pipeline_executions_created_at ON content_analysis_v2.pipeline_executions(created_at DESC);
```

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `article_id` | UUID | Foreign key to feed_items (unique) |
| `pipeline_version` | VARCHAR(10) | Pipeline version (e.g., "2.0") |
| `success` | BOOLEAN | Whether analysis succeeded |
| `agents_executed` | TEXT[] | List of agents that executed |
| `failed_agents` | TEXT[] | List of agents that failed |
| `error_message` | TEXT | Error message if failed |
| `total_processing_time_ms` | INTEGER | Total processing time in milliseconds |
| `total_cost_usd` | DECIMAL | Total cost in USD |
| `cache_hits` | INTEGER | Number of cache hits during processing |
| `triage_decision` | JSONB | Triage agent results (relevance, priority) |
| `tier1_summary` | JSONB | Tier 1 summary (entities, summary, sentiment, topics) |
| `tier2_summary` | JSONB | Tier 2 summary (financial, geopolitical, conflict, bias) |
| `tier3_summary` | JSONB | Tier 3 summary (intelligence synthesis) |
| `entity_results` | JSONB | Detailed entity extraction results |
| `summary_results` | JSONB | Detailed summary generation results |
| `sentiment_results` | JSONB | Detailed sentiment analysis results |
| `topic_results` | JSONB | Detailed topic classification results |
| `financial_results` | JSONB | Detailed financial analysis results |
| `geopolitical_results` | JSONB | Detailed geopolitical analysis results |
| `conflict_results` | JSONB | Detailed conflict event analysis results |
| `bias_results` | JSONB | Detailed bias detection results |
| `intelligence_results` | JSONB | Detailed intelligence synthesis results |
| `created_at` | TIMESTAMP | When execution was created |
| `updated_at` | TIMESTAMP | When execution was last updated |
| `completed_at` | TIMESTAMP | When execution completed |

### Sample Query

```sql
-- Get latest analysis for an article
SELECT * FROM content_analysis_v2.pipeline_executions
WHERE article_id = '123e4567-e89b-12d3-a456-426614174000';

-- Get all successful analyses from last 24 hours
SELECT article_id, pipeline_version, total_cost_usd, total_processing_time_ms
FROM content_analysis_v2.pipeline_executions
WHERE success = true
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Get failed analyses with errors
SELECT article_id, failed_agents, error_message, created_at
FROM content_analysis_v2.pipeline_executions
WHERE success = false
ORDER BY created_at DESC
LIMIT 10;
```

### Data Volume

```sql
-- Current row count (as of 2025-10-31)
SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;
-- Result: 7,097 rows (100% coverage since deployment)

-- Success rate
SELECT
    COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*) as success_rate_percent
FROM content_analysis_v2.pipeline_executions;
-- Result: ~97.0%

-- Average cost and processing time
SELECT
    AVG(total_cost_usd) as avg_cost_usd,
    AVG(total_processing_time_ms) as avg_processing_time_ms
FROM content_analysis_v2.pipeline_executions
WHERE success = true;
-- Result: ~$0.00239 per article, ~31,290ms processing time
```

---

## Table 2: Unified Table (ORPHANED) ❌

### Schema: `public.article_analysis`

**Purpose:** Intended to store analysis results in unified schema (part of incomplete migration).

**Status:** **ORPHANED** - Written to but never read by any service.

**Access Pattern:**
```
1. content-analysis-v2 workers → Publish analysis.completed event
2. RabbitMQ → Routes event to analysis_results_queue
3. feed-service analysis-consumer → Writes to this table
4. ❌ NOBODY READS FROM THIS TABLE ❌
```

**Problem:** This data is **NEVER displayed to users**. The frontend reads from the legacy table via API proxy.

### Schema Definition

```sql
CREATE TABLE public.article_analysis (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL UNIQUE,  -- Foreign key to feed_items

    -- Execution Metadata
    pipeline_version VARCHAR(10) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT false,
    error_message TEXT,
    failed_agents TEXT[] DEFAULT '{}',

    -- Analysis Results (Simplified Structure)
    triage_results JSONB,    -- Triage decision and reasoning
    tier1_results JSONB,     -- Combined Tier 1 results
    tier2_results JSONB,     -- Combined Tier 2 results
    tier3_results JSONB,     -- Combined Tier 3 results

    -- Relevance Scoring
    relevance_score DECIMAL(5, 2),  -- Overall relevance score (0-100)
    score_breakdown JSONB,          -- Detailed score breakdown

    -- Performance Metrics
    metrics JSONB,  -- {total_cost_usd, total_processing_time_ms, cache_hits}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_article_analysis_article_id ON public.article_analysis(article_id);
CREATE INDEX idx_article_analysis_success ON public.article_analysis(success);
CREATE INDEX idx_article_analysis_created_at ON public.article_analysis(created_at DESC);
CREATE INDEX idx_article_analysis_relevance_score ON public.article_analysis(relevance_score DESC);
```

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `article_id` | UUID | Foreign key to feed_items (unique) |
| `pipeline_version` | VARCHAR(10) | Pipeline version |
| `success` | BOOLEAN | Whether analysis succeeded |
| `error_message` | TEXT | Error message if failed |
| `failed_agents` | TEXT[] | List of agents that failed |
| `triage_results` | JSONB | Triage decision and reasoning |
| `tier1_results` | JSONB | Combined Tier 1 results |
| `tier2_results` | JSONB | Combined Tier 2 results |
| `tier3_results` | JSONB | Combined Tier 3 results |
| `relevance_score` | DECIMAL | Overall relevance score (0-100) |
| `score_breakdown` | JSONB | Detailed score breakdown |
| `metrics` | JSONB | Performance metrics (cost, time, cache hits) |
| `created_at` | TIMESTAMP | When analysis was created |
| `updated_at` | TIMESTAMP | When analysis was last updated |

### ⚠️ Current State

```sql
-- Current row count (as of 2025-10-31)
SELECT COUNT(*) FROM public.article_analysis;
-- Result: 3,364 rows (47% coverage, only since Oct 31)

-- Missing data (compared to legacy table)
SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe
LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
WHERE aa.article_id IS NULL;
-- Result: 3,733 analyses exist ONLY in legacy table (pre-Oct 31)
```

### Sample Query (If It Were Used)

```sql
-- Get latest analysis for an article
SELECT * FROM public.article_analysis
WHERE article_id = '123e4567-e89b-12d3-a456-426614174000';

-- Get high-relevance analyses
SELECT article_id, relevance_score, tier1_results->'summary' as summary
FROM public.article_analysis
WHERE success = true
  AND relevance_score > 80
ORDER BY relevance_score DESC
LIMIT 10;
```

---

## Schema Differences

### Column Count

- **Legacy Table:** 22 columns (granular, per-agent results)
- **Unified Table:** 15 columns (simplified, combined results)

### Detailed Comparison

| Feature | Legacy Table | Unified Table |
|---------|-------------|---------------|
| **Agent-Specific Results** | ✅ 9 separate JSONB columns | ❌ Combined in tier results |
| **Detailed Metadata** | ✅ agents_executed, cache_hits | ❌ Simplified to failed_agents only |
| **Relevance Scoring** | ❌ Embedded in triage_decision | ✅ Dedicated relevance_score column |
| **Performance Metrics** | ✅ Separate columns | ❌ Combined in metrics JSONB |
| **Completed Timestamp** | ✅ completed_at column | ❌ No completed_at |

### Incompatibility

**The schemas are NOT compatible for direct migration:**
- Legacy table has more granular data (9 agent-specific result columns)
- Unified table has simplified structure (combined tier results)
- Data transformation required for migration
- Some legacy fields have no unified equivalent

---

## Service Access Patterns

### Who Writes Where?

| Service | Legacy Table | Unified Table |
|---------|-------------|---------------|
| **content-analysis-v2 workers** | ✅ Direct writes | ❌ Indirect (via events) |
| **feed-service analysis-consumer** | ❌ No access | ✅ Event-driven writes |

### Who Reads Where?

| Service | Legacy Table | Unified Table |
|---------|-------------|---------------|
| **content-analysis-v2 API** | ✅ Direct reads | ❌ No access |
| **feed-service analysis_loader.py** | ✅ Via API proxy | ❌ No access |
| **Frontend** | ✅ Via feed-service | ❌ Never sees data |
| **Scripts (reanalyze, monitor)** | ✅ Direct queries | ❌ No queries |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     LEGACY PATH (ACTIVE)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  content-analysis-v2 workers                                    │
│           │                                                     │
│           │ (direct write)                                      │
│           ↓                                                     │
│  content_analysis_v2.pipeline_executions ✅                     │
│           │                                                     │
│           │ (read)                                              │
│           ↓                                                     │
│  content-analysis-v2 API                                        │
│           │                                                     │
│           │ (HTTP proxy)                                        │
│           ↓                                                     │
│  feed-service analysis_loader.py                                │
│           │                                                     │
│           │ (return)                                            │
│           ↓                                                     │
│  Frontend displays data ✅                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   UNIFIED PATH (ORPHANED)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  content-analysis-v2 workers                                    │
│           │                                                     │
│           │ (publish event: analysis.completed)                 │
│           ↓                                                     │
│  RabbitMQ (news.events exchange)                                │
│           │                                                     │
│           │ (routing_key: analysis.completed)                   │
│           ↓                                                     │
│  feed-service analysis-consumer                                 │
│           │                                                     │
│           │ (event-driven write)                                │
│           ↓                                                     │
│  public.article_analysis ❌                                     │
│           │                                                     │
│           │ (NEVER READ)                                        │
│           ↓                                                     │
│  Data orphaned 💀                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Considerations

### Data Transformation Required

**Legacy → Unified mapping is NOT 1:1:**

```python
# Example transformation (simplified)
def transform_legacy_to_unified(legacy_row):
    return {
        "article_id": legacy_row.article_id,
        "pipeline_version": legacy_row.pipeline_version,
        "success": legacy_row.success,
        "triage_results": legacy_row.triage_decision,  # Direct mapping
        "tier1_results": {  # Combine 4 agent results
            "entities": legacy_row.entity_results,
            "summary": legacy_row.summary_results,
            "sentiment": legacy_row.sentiment_results,
            "topics": legacy_row.topic_results,
        },
        "tier2_results": {  # Combine 4 agent results
            "financial": legacy_row.financial_results,
            "geopolitical": legacy_row.geopolitical_results,
            "conflict": legacy_row.conflict_results,
            "bias": legacy_row.bias_results,
        },
        "tier3_results": legacy_row.intelligence_results,  # Direct mapping
        "relevance_score": extract_relevance_score(legacy_row.triage_decision),
        "score_breakdown": extract_score_breakdown(legacy_row.triage_decision),
        "metrics": {
            "total_cost_usd": legacy_row.total_cost_usd,
            "total_processing_time_ms": legacy_row.total_processing_time_ms,
            "cache_hits": legacy_row.cache_hits,
        },
        "error_message": legacy_row.error_message,
        "failed_agents": legacy_row.failed_agents,
    }
```

### Challenges

1. **Schema Incompatibility:** Different structures require transformation logic
2. **Data Volume:** 7,097 rows to transform and migrate
3. **Downtime Risk:** Need to coordinate service restarts
4. **Verification:** Must verify all data paths work after migration
5. **Rollback Complexity:** Cannot easily rollback after migration

---

## Recommendations

### Primary Recommendation: Complete Migration (Option A)

**Why:**
- Finishes incomplete work (don't leave half-done migrations)
- Event-driven architecture is more scalable
- Unified table has cleaner, simpler schema
- One-time investment vs ongoing confusion

**Implementation Guide:** See [ADR-032](../decisions/ADR-032-dual-table-analysis-architecture.md) - Implementation Guide section

### Alternative: Rollback to Legacy Only (Option B)

**When to choose:**
- Migration complexity is too high
- Team lacks time for 4-8 hour migration
- Want to minimize risk

**Trade-off:** Keep legacy table name, direct database writes

---

## Related Documentation

- **[ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)** - Full decision record
- **[POSTMORTEMS.md - Incident #8](../../POSTMORTEMS.md#incident-8)** - How we discovered this issue
- **[Analysis Storage Migration Guide](../guides/analysis-storage-migration-guide.md)** - Step-by-step migration
- **[Content-Analysis-V2 API Documentation](../api/content-analysis-v2-api.md)** - API endpoints

---

**Last Updated:** 2025-10-31
**Next Review:** After migration decision (by 2025-11-08)
**Owner:** Backend Team, Database Team
