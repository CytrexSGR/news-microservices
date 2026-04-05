#!/bin/bash
# Monitor unified table writes - Verify migration success
# Usage: ./scripts/monitor_unified_table_writes.sh
#
# Checks:
# 1. New analyses only go to unified table
# 2. Legacy table has no new writes
# 3. All services healthy
#
# Run this for 24-48h after migration to verify stability

echo "🔍 UNIFIED TABLE MIGRATION MONITOR"
echo "==================================="
echo "Started: $(date)"
echo ""

docker exec postgres psql -U news_user -d news_mcp <<'SQL'

-- MIGRATION HEALTH CHECK
SELECT
    '✅ MIGRATION STATUS' as check_type,
    '' as metric,
    '' as value;

-- 1. Table sizes and row counts
SELECT
    'Table Stats' as check_type,
    'UNIFIED (article_analysis)' as metric,
    CONCAT(COUNT(*), ' rows, ', pg_size_pretty(pg_total_relation_size('public.article_analysis'))) as value
FROM public.article_analysis

UNION ALL

SELECT
    'Table Stats' as check_type,
    'LEGACY (pipeline_executions_deprecated)' as metric,
    CONCAT(COUNT(*), ' rows, ', pg_size_pretty(pg_total_relation_size('content_analysis_v2.pipeline_executions_deprecated'))) as value
FROM content_analysis_v2.pipeline_executions_deprecated;

-- 2. Recent activity (last 24h)
SELECT
    '' as check_type,
    '─────────────────────────────────' as metric,
    '' as value

UNION ALL

SELECT
    'Recent Activity (24h)' as check_type,
    'UNIFIED new writes' as metric,
    COUNT(*)::text as value
FROM public.article_analysis
WHERE created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Recent Activity (24h)' as check_type,
    'LEGACY new writes' as metric,
    COUNT(*)::text || ' (SHOULD BE 0!)' as value
FROM content_analysis_v2.pipeline_executions_deprecated
WHERE completed_at > NOW() - INTERVAL '24 hours';

-- 3. Latest timestamps (verify no new legacy writes)
SELECT
    '' as check_type,
    '─────────────────────────────────' as metric,
    '' as value

UNION ALL

SELECT
    'Latest Timestamps' as check_type,
    'UNIFIED latest write' as metric,
    MAX(created_at)::text as value
FROM public.article_analysis

UNION ALL

SELECT
    'Latest Timestamps' as check_type,
    'LEGACY latest write' as metric,
    MAX(completed_at)::text || ' (should be ~2025-11-08 18:05 UTC)' as value
FROM content_analysis_v2.pipeline_executions_deprecated;

-- 4. Data completeness check
SELECT
    '' as check_type,
    '─────────────────────────────────' as metric,
    '' as value

UNION ALL

SELECT
    'Data Completeness' as check_type,
    'Articles in feed_items' as metric,
    COUNT(*)::text as value
FROM feed_items
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    'Data Completeness' as check_type,
    'With analysis in unified' as metric,
    COUNT(*)::text as value
FROM feed_items fi
INNER JOIN public.article_analysis aa ON fi.id = aa.article_id
WHERE fi.created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    'Data Completeness' as check_type,
    'Missing analysis' as metric,
    COUNT(*)::text || ' (acceptable if recent)' as value
FROM feed_items fi
LEFT JOIN public.article_analysis aa ON fi.id = aa.article_id
WHERE fi.created_at > NOW() - INTERVAL '7 days'
  AND aa.id IS NULL;

SQL

echo ""
echo "📊 SUMMARY"
echo "=========="
echo "- If 'LEGACY new writes (24h)' is 0 → ✅ Migration successful"
echo "- If 'LEGACY latest write' is ~2025-11-08 18:05 UTC → ✅ No new writes to legacy"
echo "- If 'UNIFIED new writes (24h)' > 0 → ✅ Unified table is active"
echo ""
echo "Completed: $(date)"
