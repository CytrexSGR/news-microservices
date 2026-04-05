-- Backfill unified analysis table with missing data from legacy table
-- Date: 2025-11-08
-- Reason: Complete migration from dual-table to single-table architecture
-- Missing: 304 unique articles (out of 315 total, 11 were deleted from feed_items)
--
-- IMPORTANT:
-- - Takes only the LATEST analysis per article (handles re-analyses)
-- - Only backfills articles that still exist in feed_items (FK constraint)

BEGIN;

-- STEP 1: Verify missing count and FK constraints
SELECT
    COUNT(DISTINCT pe.article_id) as total_missing,
    COUNT(DISTINCT CASE WHEN fi.id IS NOT NULL THEN pe.article_id END) as can_backfill,
    COUNT(DISTINCT CASE WHEN fi.id IS NULL THEN pe.article_id END) as deleted_articles,
    '(Expected: ~304 can backfill, ~11 deleted)' as note
FROM content_analysis_v2.pipeline_executions pe
LEFT JOIN feed_items fi ON pe.article_id = fi.id
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true;

-- STEP 2: Backfill missing articles (LATEST analysis only, FK-safe)
INSERT INTO public.article_analysis (
    id,
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
    gen_random_uuid() as id,
    article_id,
    pipeline_version,
    success,
    triage_decision as triage_results,
    tier1_summary as tier1_results,
    tier2_summary as tier2_results,
    tier3_summary as tier3_results,
    overall_relevance_score as relevance_score,
    score_breakdown,
    jsonb_build_object(
        'total_processing_time_ms', total_processing_time_ms,
        'total_cost_usd', total_cost_usd,
        'cache_hits', cache_hits,
        'agents_executed', agents_executed,
        'agents_skipped', agents_skipped,
        'token_usage', token_usage
    ) as metrics,
    error_message,
    agents_skipped as failed_agents,
    completed_at as created_at,
    completed_at as updated_at
FROM (
    SELECT DISTINCT ON (pe.article_id)
        pe.*
    FROM content_analysis_v2.pipeline_executions pe
    INNER JOIN feed_items fi ON pe.article_id = fi.id  -- FK constraint check
    WHERE pe.article_id NOT IN (
        SELECT article_id FROM public.article_analysis
    )
    AND pe.success = true
    ORDER BY pe.article_id, pe.completed_at DESC  -- Take latest per article
) latest_analyses
ORDER BY completed_at;

-- STEP 3: Verify backfill success
SELECT
    'Backfill complete!' as status,
    COUNT(*) as total_unified_rows,
    COUNT(*) - 21704 as newly_added_rows,
    '(Expected: ~304 new rows)' as note
FROM public.article_analysis;

-- STEP 4: Final verification - should be ~11 (deleted articles)
SELECT
    COUNT(DISTINCT pe.article_id) as remaining_missing_articles,
    '(Expected: ~11, only deleted articles)' as note
FROM content_analysis_v2.pipeline_executions pe
LEFT JOIN feed_items fi ON pe.article_id = fi.id
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true
AND fi.id IS NULL;  -- Only count deleted articles

-- STEP 5: Confirm zero missing for existing articles
SELECT
    COUNT(DISTINCT pe.article_id) as missing_existing_articles,
    '(Expected: 0, all existing articles backfilled)' as note
FROM content_analysis_v2.pipeline_executions pe
INNER JOIN feed_items fi ON pe.article_id = fi.id
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true;

COMMIT;

-- Summary report
SELECT
    'BACKFILL SUMMARY' as report_type,
    (SELECT COUNT(*) FROM public.article_analysis) as total_analyses,
    (SELECT COUNT(DISTINCT article_id) FROM content_analysis_v2.pipeline_executions WHERE success = true) as total_legacy_articles,
    (SELECT COUNT(*) - COUNT(DISTINCT article_id) FROM content_analysis_v2.pipeline_executions) as duplicate_analyses_in_legacy;
