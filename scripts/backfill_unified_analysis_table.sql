-- Backfill unified analysis table with missing data from legacy table
-- Date: 2025-11-08
-- Reason: Complete migration from dual-table to single-table architecture
-- Missing: 316 rows (12 from Oct 26, 308 from Nov 3)

-- STEP 1: Verify missing count
SELECT
    COUNT(*) as missing_rows,
    '(Expected: 316)' as note
FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
);

-- STEP 2: Backfill missing rows
-- Transform legacy schema → unified schema
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
    gen_random_uuid() as id,  -- Generate new UUID for unified table
    pe.article_id,
    pe.pipeline_version,
    pe.success,

    -- Transform legacy field names to unified names
    pe.triage_decision as triage_results,
    pe.tier1_summary as tier1_results,
    pe.tier2_summary as tier2_results,
    pe.tier3_summary as tier3_results,

    pe.overall_relevance_score as relevance_score,
    pe.score_breakdown,

    -- Build metrics object from legacy fields
    jsonb_build_object(
        'total_processing_time_ms', pe.total_processing_time_ms,
        'total_cost_usd', pe.total_cost_usd,
        'cache_hits', pe.cache_hits,
        'agents_executed', pe.agents_executed,
        'agents_skipped', pe.agents_skipped,
        'token_usage', pe.token_usage
    ) as metrics,

    pe.error_message,
    pe.agents_skipped as failed_agents,  -- Map skipped agents to failed_agents

    pe.completed_at as created_at,
    pe.completed_at as updated_at

FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true  -- Only backfill successful analyses
ORDER BY pe.completed_at;

-- STEP 3: Verify backfill success
SELECT
    'Backfill complete!' as status,
    COUNT(*) as total_unified_rows,
    COUNT(*) - 21704 as newly_added_rows,
    '(Expected: ~316)' as note
FROM public.article_analysis;

-- STEP 4: Final verification - should be 0 or very few
SELECT
    COUNT(*) as remaining_missing,
    '(Expected: 0 or very few failed analyses)' as note
FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = true;

-- STEP 5: Show what's NOT backfilled (failed analyses)
SELECT
    COUNT(*) as failed_analyses_not_backfilled,
    '(Expected: ~0, only failed analyses should remain)' as note
FROM content_analysis_v2.pipeline_executions pe
WHERE pe.article_id NOT IN (
    SELECT article_id FROM public.article_analysis
)
AND pe.success = false;
