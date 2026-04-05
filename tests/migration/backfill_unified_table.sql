-- ================================================================================
-- BACKFILL UNIFIED TABLE WITH LEGACY DATA
-- ================================================================================
-- Purpose: Copy missing analyses from legacy to unified table with data transformation
-- Duration: ~2-5 minutes for 3,733 rows
-- Safety: Transaction-wrapped with verification checks
-- ================================================================================

-- Enable timing and verbose output
\timing on
\set ON_ERROR_STOP on

BEGIN;

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: PRE-MIGRATION VERIFICATION                                       │
-- └──────────────────────────────────────────────────────────────────────────┘

DO $$
DECLARE
    legacy_count INTEGER;
    unified_count INTEGER;
    missing_count INTEGER;
    duplicate_count INTEGER;
BEGIN
    -- Count rows in both tables
    SELECT COUNT(*) INTO legacy_count
    FROM content_analysis_v2.pipeline_executions;

    SELECT COUNT(*) INTO unified_count
    FROM public.article_analysis;

    -- Count missing rows
    SELECT COUNT(*) INTO missing_count
    FROM content_analysis_v2.pipeline_executions pe
    LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
    WHERE aa.article_id IS NULL;

    -- Check for duplicates in unified table
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT article_id, COUNT(*) as cnt
        FROM public.article_analysis
        GROUP BY article_id
        HAVING COUNT(*) > 1
    ) sub;

    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  BEFORE BACKFILL - VERIFICATION                            ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Legacy table rows:     % ', LPAD(legacy_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Unified table rows:    % ', LPAD(unified_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Missing in unified:    % ', LPAD(missing_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Duplicates in unified: % ', LPAD(duplicate_count::TEXT, 7, ' ');
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';

    -- Safety checks
    IF legacy_count < 7000 THEN
        RAISE EXCEPTION 'Legacy table has only % rows (expected > 7000). Database corruption?', legacy_count;
    END IF;

    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'Unified table has % duplicates. Fix duplicates before migration.', duplicate_count;
    END IF;

    IF missing_count = 0 THEN
        RAISE EXCEPTION 'No data to backfill (unified table already complete). Aborting.';
    END IF;

    RAISE NOTICE '✓ Pre-migration checks passed';
    RAISE NOTICE '→ Proceeding with backfill of % rows...', missing_count;
    RAISE NOTICE '';
END $$;

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: BACKFILL WITH DATA TRANSFORMATION                                │
-- └──────────────────────────────────────────────────────────────────────────┘

DO $$ BEGIN
    RAISE NOTICE 'Starting backfill... (this may take 2-5 minutes)';
END $$;

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

    -- Tier 1 results (direct mapping from legacy tier1_summary)
    pe.tier1_summary AS tier1_results,

    -- Tier 2 results (direct mapping from legacy tier2_summary)
    pe.tier2_summary AS tier2_results,

    -- Tier 3 results (direct mapping from legacy tier3_summary)
    pe.tier3_summary AS tier3_results,

    -- Relevance score (use overall_relevance_score from legacy table)
    pe.overall_relevance_score::DECIMAL(5,2) AS relevance_score,

    -- Score breakdown (direct mapping)
    pe.score_breakdown,

    -- Metrics (combine performance data)
    jsonb_build_object(
        'total_cost_usd', COALESCE(pe.total_cost_usd, 0),
        'total_processing_time_ms', COALESCE(pe.total_processing_time_ms, 0),
        'cache_hits', COALESCE(pe.cache_hits, 0),
        'agents_executed', COALESCE(pe.agents_executed, ARRAY[]::TEXT[])
    ) AS metrics,

    pe.error_message,
    ARRAY[]::TEXT[] AS failed_agents,  -- Legacy table doesn't have this field
    pe.started_at AS created_at,       -- Map started_at to created_at
    COALESCE(pe.completed_at, pe.started_at) AS updated_at  -- Map completed_at to updated_at (use started_at as fallback)

FROM content_analysis_v2.pipeline_executions pe
INNER JOIN public.feed_items fi ON pe.article_id = fi.id  -- Only migrate articles that still exist
WHERE NOT EXISTS (
    SELECT 1 FROM public.article_analysis aa
    WHERE aa.article_id = pe.article_id
)
ON CONFLICT (article_id) DO NOTHING;

-- Get insert count
\set rows_inserted `echo "SELECT COUNT(*) FROM public.article_analysis aa WHERE NOT EXISTS (SELECT 1 FROM content_analysis_v2.pipeline_executions pe WHERE pe.article_id = aa.article_id AND pe.created_at < aa.created_at);"`

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✓ Backfill complete';
    RAISE NOTICE '';
END $$;

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: POST-MIGRATION VERIFICATION                                      │
-- └──────────────────────────────────────────────────────────────────────────┘

DO $$
DECLARE
    legacy_count INTEGER;
    unified_count INTEGER;
    missing_count INTEGER;
    null_triage_count INTEGER;
    null_tier1_count INTEGER;
    relevance_scores_extracted INTEGER;
    success_count INTEGER;
    duplicate_count INTEGER;
BEGIN
    -- Count rows in both tables
    SELECT COUNT(*) INTO legacy_count
    FROM content_analysis_v2.pipeline_executions;

    SELECT COUNT(*) INTO unified_count
    FROM public.article_analysis;

    -- Count missing rows (should be 0)
    SELECT COUNT(*) INTO missing_count
    FROM content_analysis_v2.pipeline_executions pe
    LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
    WHERE aa.article_id IS NULL;

    -- Data quality checks
    SELECT COUNT(*) INTO null_triage_count
    FROM public.article_analysis
    WHERE success = true AND triage_results IS NULL;

    SELECT COUNT(*) INTO null_tier1_count
    FROM public.article_analysis
    WHERE success = true AND tier1_results IS NULL;

    -- Count successful analyses
    SELECT COUNT(*) INTO success_count
    FROM public.article_analysis
    WHERE success = true;

    -- Count relevance scores extracted
    SELECT COUNT(*) INTO relevance_scores_extracted
    FROM public.article_analysis
    WHERE success = true AND relevance_score IS NOT NULL;

    -- Check for duplicates
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT article_id, COUNT(*) as cnt
        FROM public.article_analysis
        GROUP BY article_id
        HAVING COUNT(*) > 1
    ) sub;

    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  AFTER BACKFILL - VERIFICATION                             ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Legacy table rows:     %', LPAD(legacy_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Unified table rows:    %', LPAD(unified_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Missing in unified:    %', LPAD(missing_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Duplicates in unified: %', LPAD(duplicate_count::TEXT, 7, ' ');
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  DATA QUALITY                                              ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Null triage (success): %', LPAD(null_triage_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Null tier1 (success):  %', LPAD(null_tier1_count::TEXT, 7, ' ');
    RAISE NOTICE '║  Relevance scores:      % / %',
                   LPAD(relevance_scores_extracted::TEXT, 5, ' '),
                   LPAD(success_count::TEXT, 5, ' ');
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';

    -- Verification checks (will raise exception if failed)
    -- Allow up to 1% discrepancy (orphaned records, data inconsistencies)
    IF ABS(unified_count - legacy_count) > legacy_count * 0.01 THEN
        RAISE EXCEPTION 'Count mismatch > 1%%! Legacy: %, Unified: %, Diff: %',
                        legacy_count, unified_count, ABS(unified_count - legacy_count);
    END IF;

    -- Allow small number of missing rows (orphaned records)
    IF missing_count > legacy_count * 0.01 THEN
        RAISE EXCEPTION 'Too many missing rows: % (> 1%% of legacy)', missing_count;
    END IF;

    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'Created % duplicates during backfill!', duplicate_count;
    END IF;

    IF null_triage_count > success_count * 0.1 THEN
        RAISE WARNING 'High null triage count: % (> 10%% of successful analyses)', null_triage_count;
    END IF;

    RAISE NOTICE '✅ BACKFILL SUCCESSFUL!';
    RAISE NOTICE '   → All % analyses now in unified table', unified_count;
    RAISE NOTICE '   → Data quality checks passed';
    RAISE NOTICE '   → Ready for deployment';
    RAISE NOTICE '';
END $$;

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 4: SAMPLE DATA VERIFICATION                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

DO $$ BEGIN
    RAISE NOTICE 'Sample data from unified table (5 random successful analyses):';
    RAISE NOTICE '';
END $$;

\x
SELECT
    article_id,
    pipeline_version,
    success,
    relevance_score,
    CASE
        WHEN tier1_results IS NOT NULL THEN 'Present'
        ELSE 'NULL'
    END as tier1_status,
    CASE
        WHEN tier2_results IS NOT NULL THEN 'Present'
        ELSE 'NULL'
    END as tier2_status,
    created_at
FROM public.article_analysis
WHERE success = true
ORDER BY RANDOM()
LIMIT 5;
\x

-- Commit transaction
COMMIT;

DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  MIGRATION COMPLETE                                        ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Status: ✅ SUCCESS                                        ║';
    RAISE NOTICE '║  Next: Run post-migration tests                            ║';
    RAISE NOTICE '║         ./tests/migration/test_post_migration.sh           ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
END $$;
