-- Backfill unified analysis table with missing data from legacy table
-- Date: 2025-11-08
-- Reason: Complete migration from dual-table to single-table architecture
-- Missing: 315 unique articles (320 rows including duplicates)
--
-- IMPORTANT: Takes only the LATEST analysis per article (handles re-analyses)

BEGIN;

-- STEP 1: Verify missing count
SELECT
    COUNT(DISTINCT pe.article_id) as missing_unique_articles,
    '(Expected: ~315)' as note
FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true;

-- STEP 2: Backfill missing articles (LATEST analysis only)
-- Uses DISTINCT ON to get the most recent analysis per article
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
    '(Expected: ~315)' as note
FROM public.article_analysis;

-- STEP 4: Final verification - should be 0
SELECT
    COUNT(DISTINCT pe.article_id) as remaining_missing_articles,
    '(Expected: 0)' as note
FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true;

-- STEP 5: Check for duplicate articles in legacy (informational)
SELECT
    COUNT(*) - COUNT(DISTINCT article_id) as duplicate_analyses_in_legacy,
    '(This is normal - re-analyses)' as note
FROM content_analysis_v2.pipeline_executions;

COMMIT;
