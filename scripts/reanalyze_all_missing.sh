#!/bin/bash
#
# Re-analyze ALL articles missing analysis (any date)
#
# Usage:
#   ./scripts/reanalyze_all_missing.sh [--limit N] [--dry-run]
#
# ⚠️ DUAL-TABLE ARCHITECTURE WARNING ⚠️
# =====================================
# This script checks the LEGACY table: content_analysis_v2.pipeline_executions
# NOT the unified table: public.article_analysis
#
# WHY: Frontend reads from legacy table (via content-analysis-v2 API proxy).
# The unified table exists but is NEVER READ by any service (orphaned data).
#
# See: POSTMORTEMS.md - Incident #8 for full analysis
# Related: services/feed-service/app/services/analysis_loader.py (reads legacy)
#          services/feed-service/app/workers/analysis_consumer.py (writes unified)
#
# Last Updated: 2025-10-31

set -e

# Default values
LIMIT=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--limit N] [--dry-run]"
            exit 1
            ;;
    esac
done

echo "================================================================================"
echo "RE-ANALYZE ALL MISSING ARTICLES (ANY DATE)"
echo "================================================================================"
echo "Limit: ${LIMIT:-All articles}"
echo "Dry run: $DRY_RUN"
echo ""

# Count articles without analysis
echo "Step 1: Counting articles without analysis..."
MISSING_COUNT=$(docker exec postgres psql -U news_user -d news_mcp -t -A -c "
    SELECT COUNT(fi.id)
    FROM feed_items fi
    LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
    WHERE pe.id IS NULL;
")

echo "  ✓ Found $MISSING_COUNT articles without analysis"

if [ "$MISSING_COUNT" -eq 0 ]; then
    echo ""
    echo "✓ No articles need re-analysis. All done!"
    exit 0
fi

# Show breakdown by date
echo ""
echo "Breakdown by date:"
docker exec postgres psql -U news_user -d news_mcp -c "
    SELECT
        fi.created_at::date as date,
        COUNT(*) as missing_articles
    FROM feed_items fi
    LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
    WHERE pe.id IS NULL
    GROUP BY date
    ORDER BY date DESC
    LIMIT 10;
" | tail -n +3 | head -n 12

# Show sample
echo ""
echo "Sample articles (first 3):"
docker exec postgres psql -U news_user -d news_mcp -c "
    SELECT
        LEFT(fi.title, 60) as title,
        fi.created_at
    FROM feed_items fi
    LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
    WHERE pe.id IS NULL
    ORDER BY fi.created_at DESC
    LIMIT 3;
" | tail -n +3 | head -n 5

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "[DRY RUN] Would create $MISSING_COUNT events in outbox"
    echo "Run without --dry-run to create events"
    exit 0
fi

# Create outbox events
echo ""
echo "Step 2: Creating outbox events..."

LIMIT_CLAUSE=""
if [ -n "$LIMIT" ]; then
    LIMIT_CLAUSE="LIMIT $LIMIT"
fi

# Insert events using a single SQL statement
INSERTED=$(docker exec postgres psql -U news_user -d news_mcp -t -A -c "
WITH missing_articles AS (
    SELECT
        fi.id as article_id,
        fi.feed_id,
        fi.title,
        fi.link,
        fi.created_at as article_created_at
    FROM feed_items fi
    LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
    WHERE pe.id IS NULL
    ORDER BY fi.created_at DESC
    $LIMIT_CLAUSE
),
inserted_events AS (
    INSERT INTO event_outbox (
        id,
        event_type,
        payload,
        status,
        correlation_id,
        created_at
    )
    SELECT
        gen_random_uuid(),
        'article.created',
        jsonb_build_object(
            'item_id', article_id::text,
            'feed_id', feed_id::text,
            'title', title,
            'link', link,
            'has_content', true,
            'timestamp', article_created_at::text
        ),
        'pending',
        gen_random_uuid(),
        NOW()
    FROM missing_articles
    ON CONFLICT DO NOTHING
    RETURNING id
)
SELECT COUNT(*) FROM inserted_events;
")

echo "  ✓ Created $INSERTED events in outbox"

# Verification
echo ""
echo "Step 3: Verification..."
PENDING_COUNT=$(docker exec postgres psql -U news_user -d news_mcp -t -A -c "
    SELECT COUNT(*) FROM event_outbox WHERE status = 'pending';
")
echo "  ✓ Total pending events in outbox: $PENDING_COUNT"

echo ""
echo "================================================================================"
echo "✅ RE-ANALYSIS QUEUED SUCCESSFULLY"
echo "================================================================================"
echo ""
echo "$INSERTED articles queued for analysis"
echo "The outbox processor will publish them within 5 seconds"
echo "Content-analysis workers will then process them"
echo ""
echo "Estimated processing time: ~$((INSERTED / 60)) minutes (3 workers, ~1 article/second)"
echo ""
echo "Monitor progress:"
echo "  - ./scripts/monitor_reanalysis.sh"
echo "  - Watch: docker exec postgres psql -U news_user -d news_mcp -c \\\"SELECT COUNT(*) FROM feed_items fi LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id WHERE pe.id IS NULL\\\""
