-- ============================================================================
-- TRIAGE Quality Analysis: gemini-flash-latest vs gemini-flash-lite-latest
-- ============================================================================
-- This script compares the quality and behavior of TRIAGE agent across models
--
-- Usage:
--   docker exec postgres psql -U news_user -d news_mcp -f /scripts/analyze_triage_quality.sql
--
-- Or from host:
--   psql -U news_user -d news_mcp -f scripts/analyze_triage_quality.sql
-- ============================================================================

\echo '============================================================================'
\echo 'TRIAGE MODEL COMPARISON ANALYSIS'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- 1. MODEL USAGE DISTRIBUTION
-- ============================================================================
\echo '1. MODEL USAGE OVER TIME'
\echo '-------------------------------------------'

SELECT
    model_used,
    DATE(created_at) as date,
    COUNT(*) as executions,
    AVG(cost_usd)::numeric(10,8) as avg_cost,
    SUM(cost_usd)::numeric(10,6) as total_cost,
    AVG(processing_time_ms)::int as avg_time_ms
FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY model_used, DATE(created_at)
ORDER BY date DESC, model_used;

\echo ''

-- ============================================================================
-- 2. PRIORITY SCORE DISTRIBUTION
-- ============================================================================
\echo '2. PRIORITY SCORE DISTRIBUTION BY MODEL'
\echo '-------------------------------------------'

SELECT
    model_used,
    COUNT(*) as total_articles,

    -- Score Statistics
    AVG((result_data->>'PriorityScore')::int)::numeric(5,2) as avg_priority_score,
    STDDEV((result_data->>'PriorityScore')::int)::numeric(5,2) as stddev_priority,
    MIN((result_data->>'PriorityScore')::int) as min_score,
    MAX((result_data->>'PriorityScore')::int) as max_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (result_data->>'PriorityScore')::int) as median_score,

    -- Tier 2 Decision Impact
    COUNT(*) FILTER (WHERE (result_data->>'PriorityScore')::int >= 60) as tier2_triggered,
    COUNT(*) FILTER (WHERE (result_data->>'PriorityScore')::int < 60) as tier2_skipped,
    ROUND(100.0 * COUNT(*) FILTER (WHERE (result_data->>'PriorityScore')::int >= 60) / COUNT(*), 2) as tier2_trigger_rate_pct

FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
  AND result_data->>'PriorityScore' IS NOT NULL
GROUP BY model_used
ORDER BY model_used;

\echo ''

-- ============================================================================
-- 3. SCORE BREAKDOWN COMPARISON
-- ============================================================================
\echo '3. SCORING COMPONENT BREAKDOWN BY MODEL'
\echo '-------------------------------------------'

SELECT
    model_used,
    COUNT(*) as articles,

    -- Component Scores
    AVG((result_data->'scoring_justification'->>'ImpactScore')::int)::numeric(5,2) as avg_impact_score,
    AVG((result_data->'scoring_justification'->>'EntityScore')::int)::numeric(5,2) as avg_entity_score,
    AVG((result_data->'scoring_justification'->>'SourceScore')::int)::numeric(5,2) as avg_source_score,
    AVG((result_data->'scoring_justification'->>'UrgencyMultiplier')::float)::numeric(4,2) as avg_urgency_multiplier,
    AVG((result_data->'scoring_justification'->>'FinalScore')::float)::numeric(6,2) as avg_final_score

FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
  AND result_data->'scoring_justification' IS NOT NULL
GROUP BY model_used
ORDER BY model_used;

\echo ''

-- ============================================================================
-- 4. CATEGORY DISTRIBUTION
-- ============================================================================
\echo '4. ARTICLE CATEGORY DISTRIBUTION BY MODEL'
\echo '-------------------------------------------'

SELECT
    model_used,
    result_data->>'category' as category,
    COUNT(*) as articles,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model_used), 2) as percentage
FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
  AND result_data->>'category' IS NOT NULL
GROUP BY model_used, result_data->>'category'
ORDER BY model_used, articles DESC;

\echo ''

-- ============================================================================
-- 5. PERFORMANCE METRICS
-- ============================================================================
\echo '5. PERFORMANCE METRICS BY MODEL'
\echo '-------------------------------------------'

SELECT
    model_used,
    COUNT(*) as executions,

    -- Cost Metrics
    AVG(cost_usd)::numeric(10,8) as avg_cost_usd,
    SUM(cost_usd)::numeric(10,6) as total_cost_usd,
    MIN(cost_usd)::numeric(10,8) as min_cost,
    MAX(cost_usd)::numeric(10,8) as max_cost,

    -- Time Metrics
    AVG(processing_time_ms)::int as avg_time_ms,
    MIN(processing_time_ms) as min_time_ms,
    MAX(processing_time_ms) as max_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_time_ms

FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY model_used
ORDER BY model_used;

\echo ''

-- ============================================================================
-- 6. SCORE RANGE BUCKETS
-- ============================================================================
\echo '6. PRIORITY SCORE BUCKETS BY MODEL'
\echo '-------------------------------------------'

WITH score_buckets AS (
    SELECT
        model_used,
        article_id,
        (result_data->>'PriorityScore')::int as priority_score,
        CASE
            WHEN (result_data->>'PriorityScore')::int >= 85 THEN '85-100 (Critical)'
            WHEN (result_data->>'PriorityScore')::int >= 70 THEN '70-84 (High)'
            WHEN (result_data->>'PriorityScore')::int >= 60 THEN '60-69 (Medium-High)'
            WHEN (result_data->>'PriorityScore')::int >= 50 THEN '50-59 (Medium)'
            WHEN (result_data->>'PriorityScore')::int >= 40 THEN '40-49 (Low-Medium)'
            ELSE '0-39 (Low)'
        END as score_bucket
    FROM content_analysis_v2.agent_results
    WHERE agent_name = 'TRIAGE'
      AND created_at > NOW() - INTERVAL '7 days'
      AND result_data->>'PriorityScore' IS NOT NULL
)
SELECT
    model_used,
    score_bucket,
    COUNT(*) as articles,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model_used), 2) as percentage
FROM score_buckets
GROUP BY model_used, score_bucket
ORDER BY model_used,
    CASE score_bucket
        WHEN '85-100 (Critical)' THEN 1
        WHEN '70-84 (High)' THEN 2
        WHEN '60-69 (Medium-High)' THEN 3
        WHEN '50-59 (Medium)' THEN 4
        WHEN '40-49 (Low-Medium)' THEN 5
        ELSE 6
    END;

\echo ''

-- ============================================================================
-- 7. TOP SCORED ARTICLES COMPARISON
-- ============================================================================
\echo '7. TOP 10 SCORED ARTICLES PER MODEL (for manual review)'
\echo '-------------------------------------------'

WITH ranked_articles AS (
    SELECT
        model_used,
        article_id,
        (result_data->>'PriorityScore')::int as priority_score,
        result_data->>'category' as category,
        result_data->'primary_topics' as topics,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY model_used ORDER BY (result_data->>'PriorityScore')::int DESC) as rn
    FROM content_analysis_v2.agent_results
    WHERE agent_name = 'TRIAGE'
      AND created_at > NOW() - INTERVAL '3 days'
      AND result_data->>'PriorityScore' IS NOT NULL
)
SELECT
    model_used,
    article_id::text,
    priority_score,
    category,
    topics::text as primary_topics,
    created_at
FROM ranked_articles
WHERE rn <= 10
ORDER BY model_used, priority_score DESC;

\echo ''

-- ============================================================================
-- 8. FAILURE RATE COMPARISON
-- ============================================================================
\echo '8. ERROR/FAILURE RATE BY MODEL'
\echo '-------------------------------------------'

SELECT
    model_used,
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE status = 'completed') as successful,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE error_message IS NOT NULL) as with_errors,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'failed') / COUNT(*), 2) as failure_rate_pct
FROM content_analysis_v2.agent_results
WHERE agent_name = 'TRIAGE'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY model_used
ORDER BY model_used;

\echo ''
\echo '============================================================================'
\echo 'ANALYSIS COMPLETE'
\echo '============================================================================'
\echo ''
\echo 'KEY QUESTIONS TO ANSWER:'
\echo '  1. Are average PriorityScores similar between models?'
\echo '  2. Is the Tier 2 trigger rate (>=60) comparable?'
\echo '  3. Are score components (Impact/Entity/Source) consistent?'
\echo '  4. Are categories distributed similarly?'
\echo '  5. Is gemini-flash-lite-latest fast enough for production?'
\echo ''
\echo 'RECOMMENDED THRESHOLDS FOR QUALITY:'
\echo '  - Score difference: < 5 points average acceptable'
\echo '  - Tier 2 trigger rate difference: < 10% acceptable'
\echo '  - Processing time: flash-lite should be 3-5x faster'
\echo '  - Cost savings: flash-lite should be ~90% cheaper'
\echo ''
