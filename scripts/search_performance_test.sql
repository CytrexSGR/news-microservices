-- Search Service Performance Analysis
-- Week 4 Batch 3 - Relevance Tuning Report

\timing on
\echo '==================================================================================='
\echo 'Search Service Performance Analysis - Relevance Tuning'
\echo '==================================================================================='
\echo ''

-- 1. Database Statistics
\echo '[1/6] Database Statistics'
\echo '-------------------------'
SELECT
    pg_size_pretty(pg_total_relation_size('article_indexes')) as total_size,
    pg_size_pretty(pg_relation_size('article_indexes')) as table_size,
    pg_size_pretty(pg_indexes_size('article_indexes')) as indexes_size,
    (SELECT COUNT(*) FROM article_indexes) as article_count,
    (SELECT COUNT(DISTINCT source) FROM article_indexes) as unique_sources,
    (SELECT COUNT(DISTINCT sentiment) FROM article_indexes WHERE sentiment IS NOT NULL) as sentiments;

\echo ''

-- 2. Index Usage Statistics
\echo '[2/6] Index Usage Statistics'
\echo '----------------------------'
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'article_indexes'
ORDER BY idx_scan DESC;

\echo ''

-- 3. Cache Hit Ratios
\echo '[3/6] PostgreSQL Cache Hit Ratios'
\echo '----------------------------------'
SELECT
    'Heap Blocks' as metric,
    sum(heap_blks_hit) as hits,
    sum(heap_blks_read) as misses,
    ROUND(
        100.0 * sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0),
        2
    ) as hit_ratio_percent
FROM pg_statio_user_tables
WHERE schemaname = 'public' AND relname = 'article_indexes'
UNION ALL
SELECT
    'Index Blocks' as metric,
    sum(idx_blks_hit) as hits,
    sum(idx_blks_read) as misses,
    ROUND(
        100.0 * sum(idx_blks_hit) / NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0),
        2
    ) as hit_ratio_percent
FROM pg_statio_user_tables
WHERE schemaname = 'public' AND relname = 'article_indexes';

\echo ''

-- 4. Query Performance Test - Default Weights
\echo '[4/6] Query Performance Test (Default Weights)'
\echo '----------------------------------------------'
EXPLAIN ANALYZE
SELECT
    article_id,
    title,
    ts_rank(search_vector, to_tsquery('english', 'tesla & electric')) as rank
FROM article_indexes
WHERE search_vector @@ to_tsquery('english', 'tesla & electric')
ORDER BY rank DESC
LIMIT 20;

\echo ''

-- 5. Query Performance Test - Tuned Weights with Normalization
\echo '[5/6] Query Performance Test (Tuned Weights + Normalization)'
\echo '-------------------------------------------------------------'
EXPLAIN ANALYZE
SELECT
    article_id,
    title,
    ts_rank(
        search_vector,
        to_tsquery('english', 'tesla & electric'),
        32  -- normalization: divide by document length
    ) as rank
FROM article_indexes
WHERE search_vector @@ to_tsquery('english', 'tesla & electric')
ORDER BY rank DESC
LIMIT 20;

\echo ''

-- 6. Fuzzy Search Performance Test
\echo '[6/6] Fuzzy Search Performance (Threshold = 0.3)'
\echo '-------------------------------------------------'
EXPLAIN ANALYZE
SELECT
    article_id,
    title,
    similarity(title, 'renewable energy') as title_sim,
    similarity(content, 'renewable energy') as content_sim,
    GREATEST(similarity(title, 'renewable energy'), similarity(content, 'renewable energy')) as max_sim
FROM article_indexes
WHERE
    similarity(title, 'renewable energy') >= 0.3
    OR similarity(content, 'renewable energy') >= 0.3
ORDER BY max_sim DESC
LIMIT 20;

\echo ''
\echo '==================================================================================='
\echo 'Analysis Complete'
\echo '==================================================================================='
\echo ''
\echo 'Key Findings:'
\echo '  1. Check execution times for all query types'
\echo '  2. Verify GIN index is being used (Bitmap Index Scan)'
\echo '  3. Ensure cache hit ratios > 80% for good performance'
\echo '  4. Compare default vs tuned weight performance'
\echo ''
\echo 'Recommendations:'
\echo '  - Tuned weights (0.8, 0.6, 0.4, 0.2) prioritize title matches'
\echo '  - Normalization flag (32) adjusts for document length'
\echo '  - Fuzzy threshold 0.3 balances precision and recall'
\echo '  - Query caching (Redis, 5min TTL) for repeat searches'
\echo '==================================================================================='
