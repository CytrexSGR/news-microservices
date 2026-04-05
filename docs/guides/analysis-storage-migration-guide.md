# Analysis Storage Migration Guide

**Version:** 1.0
**Date:** 2025-10-31
**Status:** Ready for Implementation
**Decision Required:** Choose Option A, B, or C (see [ADR-032](../decisions/ADR-032-dual-table-analysis-architecture.md))

---

## Table of Contents

1. [Overview](#overview)
2. [Current State](#current-state)
3. [Migration Options](#migration-options)
4. [Option A: Complete Migration (Recommended)](#option-a-complete-migration-recommended)
5. [Option B: Rollback to Legacy Only](#option-b-rollback-to-legacy-only)
6. [Option C: Dual-Table with Boundaries](#option-c-dual-table-with-boundaries)
7. [Testing Checklist](#testing-checklist)
8. [Rollback Procedures](#rollback-procedures)
9. [Monitoring](#monitoring)

---

## Overview

### Problem Statement

The news-microservices platform currently has **two separate tables** storing analysis results:

- **Legacy Table:** `content_analysis_v2.pipeline_executions` (7,097 rows, ACTIVELY USED)
- **Unified Table:** `public.article_analysis` (3,364 rows, ORPHANED - written but never read)

This dual-table architecture causes:
- Data fragmentation (47% coverage in unified table)
- Developer confusion (which table to use?)
- Wasted resources (orphaned data, duplicate processing)
- Maintenance burden (two tables to manage)

### Goal

Choose and implement one of three resolution options to eliminate confusion and establish a single source of truth.

---

## Current State

### Data Volume (as of 2025-10-31)

```sql
-- Legacy table (ACTIVELY USED)
SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;
-- Result: 7,097 rows

-- Unified table (ORPHANED)
SELECT COUNT(*) FROM public.article_analysis;
-- Result: 3,364 rows

-- Missing in unified table
SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe
LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
WHERE aa.article_id IS NULL;
-- Result: 3,733 analyses (pre-Oct 31 data)
```

### Data Flow

**LEGACY PATH (ACTIVE):**
```
content-analysis-v2 workers
  ↓ (direct write)
content_analysis_v2.pipeline_executions ✅
  ↓ (read)
content-analysis-v2 API
  ↓ (proxy)
feed-service
  ↓
Frontend ✅
```

**UNIFIED PATH (ORPHANED):**
```
content-analysis-v2 workers
  ↓ (publish event)
RabbitMQ
  ↓ (consume)
feed-service analysis-consumer
  ↓ (write)
public.article_analysis ❌
  ↓ (NEVER READ)
Data orphaned 💀
```

---

## Migration Options

### Decision Matrix

| Criteria | Option A (Migration) | Option B (Rollback) | Option C (Dual-Table) |
|----------|---------------------|---------------------|----------------------|
| **Effort** | 4-8 hours | 2 hours | 1 hour |
| **Risk** | Medium | Low | Minimal |
| **Long-term value** | High | Medium | Low |
| **Recommendation** | ⭐ **RECOMMENDED** | 🔄 Pragmatic fallback | ❌ Not recommended |

---

## Option A: Complete Migration (Recommended)

**Goal:** Finish incomplete migration to `public.article_analysis` (unified table).

**Outcome:** Single source of truth, event-driven architecture complete.

### Prerequisites

- [ ] Team approval to proceed
- [ ] 4-8 hour maintenance window scheduled
- [ ] Database backup taken
- [ ] Staging environment tested
- [ ] Rollback plan reviewed
- [ ] Monitoring dashboards ready

### Step 1: Pre-Migration Verification (15 minutes)

#### 1.1 Check Current State

```bash
# Connect to database
docker exec -it postgres psql -U news_user -d news_mcp

# Verify counts
\x
SELECT 'Legacy Table' as table_name, COUNT(*) as row_count
FROM content_analysis_v2.pipeline_executions
UNION ALL
SELECT 'Unified Table' as table_name, COUNT(*) as row_count
FROM public.article_analysis;

# Expected output:
#   table_name   | row_count
# ---------------+-----------
#  Legacy Table  |      7097
#  Unified Table |      3364
```

#### 1.2 Verify Services Running

```bash
# Check all required services
docker compose ps | grep -E "(content-analysis-v2|feed-service|postgres)"

# Should show:
# - content-analysis-v2-api (running)
# - content-analysis-v2-worker-* (running, 3 workers)
# - feed-service-api (running)
# - feed-service-analysis-consumer (running) ← CRITICAL
# - postgres (running)
```

#### 1.3 Take Database Backup

```bash
# Full backup
docker exec postgres pg_dump -U news_user -d news_mcp \
  -Fc -f /tmp/news_mcp_pre_migration_$(date +%Y%m%d_%H%M%S).dump

# Copy backup to host
docker cp postgres:/tmp/news_mcp_pre_migration_*.dump ./backups/

# Verify backup
ls -lh ./backups/news_mcp_pre_migration_*.dump
# Should show backup file > 100MB
```

### Step 2: Backfill Unified Table (1-2 hours)

#### 2.1 Create Backfill SQL Script

Create `/tmp/backfill_unified_table.sql`:

```sql
-- ================================================================================
-- BACKFILL UNIFIED TABLE WITH LEGACY DATA
-- ================================================================================
-- Goal: Copy 3,733 missing analyses from legacy to unified table
-- Duration: ~2-5 minutes for 3,733 rows
-- ================================================================================

BEGIN;

-- Step 1: Verify counts BEFORE migration
DO $$
DECLARE
    legacy_count INTEGER;
    unified_count INTEGER;
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO legacy_count FROM content_analysis_v2.pipeline_executions;
    SELECT COUNT(*) INTO unified_count FROM public.article_analysis;

    SELECT COUNT(*) INTO missing_count
    FROM content_analysis_v2.pipeline_executions pe
    LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
    WHERE aa.article_id IS NULL;

    RAISE NOTICE 'BEFORE BACKFILL:';
    RAISE NOTICE '  Legacy table: % rows', legacy_count;
    RAISE NOTICE '  Unified table: % rows', unified_count;
    RAISE NOTICE '  Missing in unified: % rows', missing_count;
    RAISE NOTICE '';

    IF missing_count = 0 THEN
        RAISE EXCEPTION 'No data to backfill. Aborting.';
    END IF;
END $$;

-- Step 2: Backfill missing analyses
-- Transform legacy schema to unified schema
INSERT INTO public.article_analysis (
    article_id,
    pipeline_version,
    success,
    triage_results,
    tier1_results,
    tier2_results,
    tier3_results,
    relevance_score,
    score_breakdown,
    metrics,
    error_message,
    failed_agents,
    created_at,
    updated_at
)
SELECT
    pe.article_id,
    pe.pipeline_version,
    pe.success,

    -- Triage results (direct mapping)
    pe.triage_decision AS triage_results,

    -- Tier 1 results (combine 4 agent results)
    jsonb_build_object(
        'entity_results', pe.entity_results,
        'summary_results', pe.summary_results,
        'sentiment_results', pe.sentiment_results,
        'topic_results', pe.topic_results
    ) AS tier1_results,

    -- Tier 2 results (combine 4 agent results)
    jsonb_build_object(
        'financial_results', pe.financial_results,
        'geopolitical_results', pe.geopolitical_results,
        'conflict_results', pe.conflict_results,
        'bias_results', pe.bias_results
    ) AS tier2_results,

    -- Tier 3 results (direct mapping)
    pe.intelligence_results AS tier3_results,

    -- Relevance score (extract from triage_decision)
    CASE
        WHEN pe.triage_decision IS NOT NULL THEN
            (pe.triage_decision->>'relevance_score')::DECIMAL(5,2)
        ELSE NULL
    END AS relevance_score,

    -- Score breakdown (extract from triage_decision)
    CASE
        WHEN pe.triage_decision IS NOT NULL THEN
            pe.triage_decision->'score_breakdown'
        ELSE NULL
    END AS score_breakdown,

    -- Metrics (combine performance data)
    jsonb_build_object(
        'total_cost_usd', pe.total_cost_usd,
        'total_processing_time_ms', pe.total_processing_time_ms,
        'cache_hits', pe.cache_hits,
        'agents_executed', pe.agents_executed
    ) AS metrics,

    pe.error_message,
    pe.failed_agents,
    pe.created_at,
    pe.updated_at

FROM content_analysis_v2.pipeline_executions pe
WHERE NOT EXISTS (
    SELECT 1 FROM public.article_analysis aa
    WHERE aa.article_id = pe.article_id
)
ON CONFLICT (article_id) DO NOTHING;

-- Step 3: Verify counts AFTER migration
DO $$
DECLARE
    legacy_count INTEGER;
    unified_count INTEGER;
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO legacy_count FROM content_analysis_v2.pipeline_executions;
    SELECT COUNT(*) INTO unified_count FROM public.article_analysis;

    SELECT COUNT(*) INTO missing_count
    FROM content_analysis_v2.pipeline_executions pe
    LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
    WHERE aa.article_id IS NULL;

    RAISE NOTICE '';
    RAISE NOTICE 'AFTER BACKFILL:';
    RAISE NOTICE '  Legacy table: % rows', legacy_count;
    RAISE NOTICE '  Unified table: % rows', unified_count;
    RAISE NOTICE '  Missing in unified: % rows', missing_count;
    RAISE NOTICE '';

    IF unified_count != legacy_count THEN
        RAISE EXCEPTION 'Count mismatch! Legacy: %, Unified: %', legacy_count, unified_count;
    END IF;

    IF missing_count != 0 THEN
        RAISE EXCEPTION 'Still have % missing rows! Migration incomplete.', missing_count;
    END IF;

    RAISE NOTICE '✅ BACKFILL SUCCESSFUL! All % analyses now in unified table.', unified_count;
END $$;

COMMIT;

-- Step 4: Verify sample data
\x
SELECT
    'Verification Sample' as check_type,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE success = true) as successful,
    COUNT(*) FILTER (WHERE success = false) as failed,
    ROUND(AVG((metrics->>'total_cost_usd')::DECIMAL), 6) as avg_cost_usd,
    ROUND(AVG((metrics->>'total_processing_time_ms')::INTEGER)) as avg_time_ms
FROM public.article_analysis;
```

#### 2.2 Execute Backfill

```bash
# Copy SQL script to postgres container
docker cp /tmp/backfill_unified_table.sql postgres:/tmp/

# Execute backfill (DRY RUN first - comment out BEGIN/COMMIT)
docker exec -it postgres psql -U news_user -d news_mcp -f /tmp/backfill_unified_table.sql

# Expected output:
# NOTICE:  BEFORE BACKFILL:
# NOTICE:    Legacy table: 7097 rows
# NOTICE:    Unified table: 3364 rows
# NOTICE:    Missing in unified: 3733 rows
#
# INSERT 0 3733
#
# NOTICE:  AFTER BACKFILL:
# NOTICE:    Legacy table: 7097 rows
# NOTICE:    Unified table: 7097 rows
# NOTICE:    Missing in unified: 0 rows
# NOTICE:  ✅ BACKFILL SUCCESSFUL! All 7097 analyses now in unified table.
#
# COMMIT
```

#### 2.3 Verify Backfill

```sql
-- Verify counts match
SELECT
    (SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions) as legacy_count,
    (SELECT COUNT(*) FROM public.article_analysis) as unified_count;
-- Expected: Both should be 7097

-- Spot check random articles
SELECT pe.article_id, pe.success, aa.success
FROM content_analysis_v2.pipeline_executions pe
JOIN public.article_analysis aa ON pe.article_id = aa.article_id
ORDER BY RANDOM()
LIMIT 5;
-- All success values should match

-- Check for data quality issues
SELECT COUNT(*) as rows_with_null_triage
FROM public.article_analysis
WHERE triage_results IS NULL AND success = true;
-- Should be 0 (all successful analyses should have triage results)
```

### Step 3: Update Read Path (2-4 hours)

You have **two implementation options**:

#### Option 3A: Update Feed-Service Directly (RECOMMENDED)

**Goal:** Make feed-service read directly from unified table instead of proxying to API.

**Pros:**
- Removes API dependency (faster, more reliable)
- Simpler architecture (no proxy layer)
- Better performance (no network hop)

**Cons:**
- Feed-service now directly queries database (slight coupling)
- More code changes required

**Implementation:**

1. **Update analysis_loader.py:**

```python
# services/feed-service/app/services/analysis_loader.py

# BEFORE (proxy to content-analysis-v2 API)
import httpx
from typing import Dict, Any, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)
V2_API_URL = "http://content-analysis-v2-api:8114/api/v2"

async def load_analysis_data(db, item_id: UUID) -> Dict[str, Any]:
    """Load analysis data from content-analysis-v2 API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{V2_API_URL}/pipeline-executions/{item_id}"
            )
            if response.status_code == 404:
                return {"pipeline_execution": None}
            if response.status_code != 200:
                logger.warning(f"V2 API returned {response.status_code}")
                return {"pipeline_execution": None}
            return {"pipeline_execution": response.json()}
    except Exception as e:
        logger.error(f"Failed to load v2 analysis: {e}")
        return {"pipeline_execution": None}


# AFTER (read from unified table)
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def load_analysis_data(
    db: AsyncSession,
    item_id: UUID
) -> Dict[str, Any]:
    """
    Load analysis data from public.article_analysis (unified table).

    Returns structure compatible with v2 API for backward compatibility.
    """
    try:
        # Query unified table
        from app.models.article_analysis import ArticleAnalysis

        result = await db.execute(
            select(ArticleAnalysis).where(
                ArticleAnalysis.article_id == item_id
            )
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            return {"pipeline_execution": None}

        # Transform to API-compatible format
        return {
            "pipeline_execution": {
                "id": str(analysis.id),
                "article_id": str(analysis.article_id),
                "pipeline_version": analysis.pipeline_version,
                "success": analysis.success,
                "error_message": analysis.error_message,
                "failed_agents": analysis.failed_agents or [],
                "triage_results": analysis.triage_results,
                "tier1_results": analysis.tier1_results,
                "tier2_results": analysis.tier2_results,
                "tier3_results": analysis.tier3_results,
                "relevance_score": float(analysis.relevance_score) if analysis.relevance_score else None,
                "score_breakdown": analysis.score_breakdown,
                "metrics": analysis.metrics,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
            }
        }

    except Exception as e:
        logger.error(f"Failed to load analysis for {item_id}: {e}", exc_info=True)
        return {"pipeline_execution": None}


async def load_analysis_data_batch(
    db: AsyncSession,
    item_ids: List[UUID]
) -> Dict[UUID, Dict[str, Any]]:
    """
    Load analysis data for multiple items from unified table.

    Replaces batch API call with efficient IN query.
    """
    if not item_ids:
        return {}

    try:
        from app.models.article_analysis import ArticleAnalysis

        # Single query with IN clause (efficient)
        result = await db.execute(
            select(ArticleAnalysis).where(
                ArticleAnalysis.article_id.in_(item_ids)
            )
        )
        analyses = result.scalars().all()

        # Build results dict
        results = {}
        for analysis in analyses:
            results[analysis.article_id] = {
                "pipeline_execution": {
                    "id": str(analysis.id),
                    "article_id": str(analysis.article_id),
                    "pipeline_version": analysis.pipeline_version,
                    "success": analysis.success,
                    "error_message": analysis.error_message,
                    "failed_agents": analysis.failed_agents or [],
                    "triage_results": analysis.triage_results,
                    "tier1_results": analysis.tier1_results,
                    "tier2_results": analysis.tier2_results,
                    "tier3_results": analysis.tier3_results,
                    "relevance_score": float(analysis.relevance_score) if analysis.relevance_score else None,
                    "score_breakdown": analysis.score_breakdown,
                    "metrics": analysis.metrics,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
                }
            }

        # Fill in None for missing IDs
        for item_id in item_ids:
            if item_id not in results:
                results[item_id] = {"pipeline_execution": None}

        return results

    except Exception as e:
        logger.error(f"Failed to load batch analysis: {e}", exc_info=True)
        return {item_id: {"pipeline_execution": None} for item_id in item_ids}
```

2. **Create ArticleAnalysis model:**

```python
# services/feed-service/app/models/article_analysis.py

from sqlalchemy import Column, UUID, String, Boolean, Text, DECIMAL, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from app.db import Base
from datetime import datetime

class ArticleAnalysis(Base):
    """Unified analysis results table."""

    __tablename__ = "article_analysis"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    article_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    # Execution Metadata
    pipeline_version = Column(String(10), nullable=False)
    success = Column(Boolean, nullable=False, default=False, index=True)
    error_message = Column(Text)
    failed_agents = Column(ARRAY(Text), default=[])

    # Analysis Results
    triage_results = Column(JSONB)
    tier1_results = Column(JSONB)
    tier2_results = Column(JSONB)
    tier3_results = Column(JSONB)

    # Relevance Scoring
    relevance_score = Column(DECIMAL(5, 2), index=True)
    score_breakdown = Column(JSONB)

    # Performance Metrics
    metrics = Column(JSONB)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", onupdate=datetime.now)

    def __repr__(self):
        return f"<ArticleAnalysis(article_id={self.article_id}, success={self.success})>"
```

3. **Update requirements.txt (if needed):**

```bash
# No new dependencies needed - using existing SQLAlchemy
```

4. **Test locally:**

```bash
# Restart feed-service to load new code
docker compose restart feed-service

# Watch logs
docker logs -f news-microservices-feed-service-1

# Test single article endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds/items/[article-id]

# Test article list (batch endpoint)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds/items?limit=20
```

#### Option 3B: Update Content-Analysis-V2 API

**Goal:** Keep feed-service proxy working, but update content-analysis-v2 API to read from unified table.

**Pros:**
- Feed-service requires no code changes
- Maintains API abstraction layer
- Easier rollback (just revert API code)

**Cons:**
- Keeps API dependency (network hop overhead)
- API now reads from feed-service database (cross-service coupling)

**Implementation:**

1. **Update pipeline_executions endpoint:**

```python
# services/content-analysis-v2/app/api/v2/endpoints/pipeline_executions.py

# Add at top
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Create connection to main database (where article_analysis lives)
MAIN_DB_URL = "postgresql+asyncpg://news_user:news_pass@postgres:5432/news_mcp"
main_engine = create_async_engine(MAIN_DB_URL)
MainSessionLocal = sessionmaker(main_engine, class_=AsyncSession, expire_on_commit=False)

@router.get("/pipeline-executions/{article_id}")
async def get_pipeline_execution(
    article_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get pipeline execution for an article.

    NOW READS FROM: public.article_analysis (unified table)
    PREVIOUSLY READ FROM: content_analysis_v2.pipeline_executions (legacy table)
    """
    async with MainSessionLocal() as db:
        from app.models.article_analysis import ArticleAnalysis  # Import from main schema

        result = await db.execute(
            select(ArticleAnalysis).where(
                ArticleAnalysis.article_id == article_id
            )
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Transform unified schema to API response format
        return {
            "id": str(analysis.id),
            "article_id": str(analysis.article_id),
            "pipeline_version": analysis.pipeline_version,
            "success": analysis.success,
            "error_message": analysis.error_message,
            "failed_agents": analysis.failed_agents or [],
            "triage_results": analysis.triage_results,
            "tier1_results": analysis.tier1_results,
            "tier2_results": analysis.tier2_results,
            "tier3_results": analysis.tier3_results,
            "relevance_score": float(analysis.relevance_score) if analysis.relevance_score else None,
            "score_breakdown": analysis.score_breakdown,
            "metrics": analysis.metrics,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
        }
```

**Note:** This option is NOT recommended because it creates cross-database coupling (content-analysis-v2 API reading from main database).

### Step 4: Deployment & Verification (1 hour)

#### 4.1 Deploy Code Changes

```bash
# If using Option 3A (feed-service direct read):
docker compose restart feed-service

# If using Option 3B (content-analysis-v2 API update):
docker compose restart content-analysis-v2-api

# Wait for health checks to pass
docker logs -f news-microservices-feed-service-1 | grep "health"
# Should see: "Application startup complete"
```

#### 4.2 Verify Frontend Works

**Test Article List Page:**
```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r '.access_token')

# Test article list (uses batch endpoint)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=20" \
  | jq '.items[] | {id, title, pipeline_execution}'

# Should see pipeline_execution data for each article
```

**Test Article Detail Page:**
```bash
# Get first article ID
ARTICLE_ID=$(curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=1" \
  | jq -r '.items[0].id')

# Test single article endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items/$ARTICLE_ID" \
  | jq '.pipeline_execution'

# Should see full analysis data
```

**Check Frontend UI:**
```bash
# Open in browser
echo "http://localhost:3000"

# Verify:
# - Article list loads
# - Analysis badges appear (relevance scores, sentiment, etc.)
# - Article detail shows full analysis
# - No JavaScript errors in console
```

#### 4.3 Performance Verification

```bash
# Measure response time (should be < 100ms for single article)
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items/$ARTICLE_ID" > /dev/null

# Measure batch response time (should be < 500ms for 20 articles)
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=20" > /dev/null
```

#### 4.4 Verify New Analyses

```bash
# Trigger new analysis (republish an article)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/admin/republish-article/$ARTICLE_ID"

# Wait 30 seconds for analysis to complete
sleep 30

# Verify analysis appears in unified table
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT article_id, success, created_at
  FROM public.article_analysis
  WHERE article_id = '$ARTICLE_ID'::uuid
  ORDER BY created_at DESC
  LIMIT 1;
"

# Verify frontend shows updated analysis
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items/$ARTICLE_ID" \
  | jq '.pipeline_execution.created_at'
# Should show recent timestamp
```

### Step 5: Deprecate Legacy Table (1 hour + 30-day wait)

#### 5.1 Rename Legacy Table (DO NOT DROP YET!)

```sql
-- Wait 24-48 hours after migration before renaming
-- This allows monitoring for issues

BEGIN;

-- Rename legacy table
ALTER TABLE content_analysis_v2.pipeline_executions
RENAME TO pipeline_executions_deprecated;

-- Add deprecation notice
COMMENT ON TABLE content_analysis_v2.pipeline_executions_deprecated IS
'DEPRECATED 2025-10-31: Data migrated to public.article_analysis.
This table kept for 30 days as safety backup.
Safe to drop after 2025-11-30 if no issues reported.
DO NOT WRITE TO THIS TABLE.';

COMMIT;
```

#### 5.2 Monitor for References

```bash
# Search codebase for references to old table
grep -r "pipeline_executions" --include="*.py" services/

# Expected: Only deprecation comments, no active code

# Check logs for errors referencing old table
docker logs news-microservices-feed-service-1 2>&1 | grep -i "pipeline_executions"
# Should be empty (no errors)
```

#### 5.3 Drop Legacy Table (After 30 Days)

```sql
-- ONLY after 30 days of successful operation
-- AND team approval

BEGIN;

-- Final verification: confirm unified table is healthy
DO $$
DECLARE
    unified_count INTEGER;
    recent_analyses INTEGER;
BEGIN
    SELECT COUNT(*) INTO unified_count FROM public.article_analysis;
    SELECT COUNT(*) INTO recent_analyses
    FROM public.article_analysis
    WHERE created_at > NOW() - INTERVAL '7 days';

    RAISE NOTICE 'Unified table: % total rows', unified_count;
    RAISE NOTICE 'Recent analyses (7 days): % rows', recent_analyses;

    IF unified_count < 7000 THEN
        RAISE EXCEPTION 'Unified table has fewer than 7000 rows. Something is wrong!';
    END IF;

    IF recent_analyses < 100 THEN
        RAISE WARNING 'Few recent analyses (%). Is the system working?', recent_analyses;
    END IF;
END $$;

-- Drop deprecated table
DROP TABLE content_analysis_v2.pipeline_executions_deprecated;

-- Drop schema if empty
DROP SCHEMA IF EXISTS content_analysis_v2 CASCADE;

COMMIT;

-- Cleanup complete!
SELECT 'Legacy table successfully removed' as status;
```

### Step 6: Documentation Updates (1 hour)

- [ ] Update [ADR-032](../decisions/ADR-032-dual-table-analysis-architecture.md) status to "Implemented"
- [ ] Update [docs/api/content-analysis-v2-api.md](../api/content-analysis-v2-api.md) - remove dual-table warnings
- [ ] Update [docs/architecture/analysis-tables-schema.md](../architecture/analysis-tables-schema.md) - mark legacy table as removed
- [ ] Update [CLAUDE.md](../../CLAUDE.md) - remove warning, note resolution
- [ ] Update [scripts/reanalyze_all_missing.sh](../../scripts/reanalyze_all_missing.sh) - reference unified table only
- [ ] Update [scripts/monitor_reanalysis.sh](../../scripts/monitor_reanalysis.sh) - reference unified table only
- [ ] Create migration post-mortem: `docs/migrations/2025-10-31-analysis-table-consolidation.md`
- [ ] Announce completion to team

---

## Option B: Rollback to Legacy Only

**Goal:** Remove unified table artifacts, keep legacy table as official storage.

**Outcome:** Single source of truth (legacy table), simpler architecture.

### Step 1: Remove Analysis-Consumer (30 minutes)

#### 1.1 Update docker-compose.yml

```yaml
# Remove this service:
# feed-service-analysis-consumer:
#   build:
#     context: ./services/feed-service
#     dockerfile: Dockerfile.dev
#   container_name: news-feed-service-analysis-consumer
#   restart: unless-stopped
#   command: python -m app.workers.analysis_consumer
#   ...

# (Comment out or delete entire service definition)
```

#### 1.2 Stop Worker

```bash
docker compose stop feed-service-analysis-consumer
docker compose rm -f feed-service-analysis-consumer
```

### Step 2: Drop Unified Table (15 minutes)

```sql
-- Take backup first (just in case)
CREATE TABLE public.article_analysis_backup AS
SELECT * FROM public.article_analysis;

-- Drop unified table
DROP TABLE public.article_analysis;

-- Verify
\dt public.*
-- Should NOT see article_analysis
```

### Step 3: Document Legacy Table as Official (15 minutes)

#### 3.1 Update Schema Documentation

```sql
-- Add comment to legacy table
COMMENT ON TABLE content_analysis_v2.pipeline_executions IS
'Official analysis storage (as of 2025-10-31).
Read by: content-analysis-v2 API, feed-service proxy, frontend.
Written by: content-analysis-v2 workers (direct).';
```

#### 3.2 Update Code Comments

```python
# services/feed-service/app/services/analysis_loader.py

# Update file header:
"""
Analysis data loader for feed items - V2 PROXY VERSION.
Delegates to content-analysis-v2 API (port 8114) for analysis data.

DATA STORAGE (as of 2025-10-31):
- Official table: content_analysis_v2.pipeline_executions
- Unified table (public.article_analysis) was removed (incomplete migration)

See: ADR-032 for migration decision
"""
```

### Step 4: Update Scripts (15 minutes)

```bash
# Update reanalyze_all_missing.sh
# - Remove dual-table warning
# - Add comment that legacy table is official

# Update monitor_reanalysis.sh
# - Remove dual-table warning
# - Add comment that legacy table is official
```

### Step 5: Documentation Updates (45 minutes)

- [ ] Update [ADR-032](../decisions/ADR-032-dual-table-analysis-architecture.md) - mark as "Rollback Completed"
- [ ] Update [docs/api/content-analysis-v2-api.md](../api/content-analysis-v2-api.md) - remove warnings
- [ ] Update [docs/architecture/analysis-tables-schema.md](../architecture/analysis-tables-schema.md) - document legacy as official
- [ ] Update [CLAUDE.md](../../CLAUDE.md) - remove warning
- [ ] Update [POSTMORTEMS.md](../../POSTMORTEMS.md) - add resolution note to Incident #8

---

## Option C: Dual-Table with Boundaries

**Goal:** Keep both tables, document boundaries clearly.

**Outcome:** Ongoing confusion, but documented.

### Implementation (1 hour)

#### 1. Document Table Boundaries

Create `docs/architecture/dual-table-boundaries.md`:

```markdown
# Dual-Table Analysis Storage - Boundaries

**Status:** Accepted as temporary solution
**Review Date:** 2025-11-30 (3 months)

## Tables

| Table | Used For | Read By | Written By |
|-------|----------|---------|------------|
| content_analysis_v2.pipeline_executions | Frontend display | API, feed-service | Workers (direct) |
| public.article_analysis | Future use | NOBODY | analysis-consumer (events) |

## Rules

1. **Frontend queries:** Always use content_analysis_v2.pipeline_executions
2. **New code:** Use content_analysis_v2.pipeline_executions until migration decision
3. **Monitoring:** Check BOTH tables for drift
4. **Scripts:** Default to content_analysis_v2.pipeline_executions

## Monitoring

```sql
-- Weekly check for drift
SELECT
    'Legacy table' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_analysis
FROM content_analysis_v2.pipeline_executions
UNION ALL
SELECT
    'Unified table' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_analysis
FROM public.article_analysis;
```

## Review

- **Next Review:** 2025-11-30
- **Owner:** Backend Team
- **Decision:** Choose Option A or B
```

#### 2. Add Monitoring Alerts

```python
# Add to monitoring dashboard
def check_table_drift():
    """Alert if unified table falls behind legacy table."""
    legacy_count = db.execute("SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions")
    unified_count = db.execute("SELECT COUNT(*) FROM public.article_analysis")

    drift_percent = (legacy_count - unified_count) / legacy_count * 100

    if drift_percent > 10:
        send_alert(f"Table drift: {drift_percent:.1f}% (Legacy: {legacy_count}, Unified: {unified_count})")
```

#### 3. Set 3-Month Review

```bash
# Add calendar reminder
# Team meeting: 2025-11-30
# Agenda: Decide on Option A or B for analysis tables
```

---

## Testing Checklist

### Pre-Migration Tests

- [ ] Database backup completed
- [ ] Services health checks passing
- [ ] Staging environment tested
- [ ] Rollback procedure documented
- [ ] Monitoring dashboards ready

### Post-Migration Tests

#### Functional Tests

- [ ] Article list loads (batch endpoint)
- [ ] Article detail loads (single endpoint)
- [ ] Analysis badges appear on articles
- [ ] Sentiment/relevance scores display
- [ ] Full analysis data accessible
- [ ] No JavaScript errors in console

#### Data Integrity Tests

```sql
-- All analyses present
SELECT COUNT(*) FROM public.article_analysis;
-- Expected: 7,097+

-- No null triage results for successful analyses
SELECT COUNT(*) FROM public.article_analysis
WHERE success = true AND triage_results IS NULL;
-- Expected: 0

-- Recent analyses present (last 24 hours)
SELECT COUNT(*) FROM public.article_analysis
WHERE created_at > NOW() - INTERVAL '24 hours';
-- Expected: > 0

-- Spot check random articles
SELECT * FROM public.article_analysis
ORDER BY RANDOM() LIMIT 5;
-- Manually verify data looks correct
```

#### Performance Tests

- [ ] Single article response < 100ms
- [ ] Batch (20 articles) response < 500ms
- [ ] No N+1 query issues
- [ ] Database CPU < 50%
- [ ] Memory usage stable

#### Integration Tests

```bash
# Test new analysis flow
# 1. Create test article
# 2. Trigger analysis
# 3. Verify appears in unified table
# 4. Verify appears in frontend
```

---

## Rollback Procedures

### If Issues Detected Within 24 Hours

#### Rollback Option A (Migration):

```sql
-- 1. Restore legacy table (if renamed)
ALTER TABLE content_analysis_v2.pipeline_executions_deprecated
RENAME TO pipeline_executions;

-- 2. Verify it works
SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;
-- Expected: 7,097
```

```bash
# 3. Revert code changes (if using Option 3A)
cd services/feed-service
git revert <migration-commit>
docker compose restart feed-service

# 4. Verify frontend works
curl http://localhost:3000
# Should load article list correctly
```

#### Rollback Option B (Rollback):

```sql
-- 1. Restore unified table from backup
CREATE TABLE public.article_analysis AS
SELECT * FROM public.article_analysis_backup;

-- 2. Restart analysis-consumer
# Add service back to docker-compose.yml
docker compose up -d feed-service-analysis-consumer
```

### If Issues Detected After 30 Days

**This is harder** - legacy table may be dropped.

**Recovery:**
1. Stop all services
2. Restore from database backup (full restore required)
3. Revert all code changes
4. Restart services
5. Verify data integrity
6. Analyze what went wrong

---

## Monitoring

### Metrics to Track

```yaml
# Prometheus metrics
- analysis_reads_total
- analysis_read_duration_seconds (histogram)
- analysis_read_errors_total
- analysis_cache_hits_total
- article_list_page_load_time_seconds
- article_detail_page_load_time_seconds
```

### Alerts

```yaml
# Prometheus alerts
- alert: HighAnalysisReadLatency
  expr: histogram_quantile(0.95, analysis_read_duration_seconds) > 0.1
  for: 5m
  annotations:
    summary: Analysis reads are slow (p95 > 100ms)

- alert: AnalysisReadErrors
  expr: rate(analysis_read_errors_total[5m]) > 0.01
  for: 2m
  annotations:
    summary: Analysis read errors detected

- alert: ArticleListSlow
  expr: histogram_quantile(0.95, article_list_page_load_time_seconds) > 2
  for: 5m
  annotations:
    summary: Article list page is slow (p95 > 2s)
```

### Daily Checks

```bash
# Run daily health check script
./scripts/daily_health_check.sh

# Check for errors in logs
docker logs news-microservices-feed-service-1 --since 24h | grep ERROR

# Verify analysis coverage
docker exec postgres psql -U news_user -d news_mcp -c "
  SELECT
    (SELECT COUNT(*) FROM feed_items WHERE created_at > NOW() - INTERVAL '24 hours') as articles_created,
    (SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '24 hours') as analyses_created;
"
# analyses_created should be close to articles_created
```

---

## Success Criteria

### Option A (Migration) Success

- ✅ All 7,097+ analyses in unified table
- ✅ Frontend displays data from unified table
- ✅ New analyses written to unified table only
- ✅ Performance acceptable (< 100ms single, < 500ms batch)
- ✅ No errors in logs for 7 days
- ✅ Legacy table deprecated (renamed, scheduled for removal)
- ✅ Documentation updated
- ✅ Team trained on new architecture

### Option B (Rollback) Success

- ✅ Unified table removed
- ✅ Analysis-consumer worker removed
- ✅ Frontend displays data from legacy table
- ✅ Performance acceptable
- ✅ No errors in logs for 7 days
- ✅ Documentation updated (legacy table is official)
- ✅ Code comments updated

### Option C (Dual-Table) Success

- ✅ Both tables documented clearly
- ✅ Monitoring in place for drift
- ✅ 3-month review scheduled
- ✅ Team understands boundaries
- ✅ Scripts updated with comments

---

## Related Documentation

- **[ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)** - Decision record
- **[POSTMORTEMS.md - Incident #8](../../POSTMORTEMS.md#incident-8)** - How we discovered this
- **[docs/architecture/analysis-tables-schema.md](../architecture/analysis-tables-schema.md)** - Schema reference
- **[docs/api/content-analysis-v2-api.md](../api/content-analysis-v2-api.md)** - API documentation

---

**Last Updated:** 2025-10-31
**Next Review:** After option chosen and implemented
**Owner:** Backend Team, Database Team, DevOps
