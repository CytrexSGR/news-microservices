-- ============================================================================
-- Migration Script: feeds → sources + source_feeds
-- ============================================================================
-- This script migrates existing RSS feeds to the new unified source management
-- system. Each unique domain becomes a Source, and each Feed becomes a SourceFeed.
--
-- Run with: docker compose exec -T postgres psql -U news_user -d news_mcp -f /scripts/migrate_feeds_to_sources.sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create temporary function to extract domain from URL
-- ============================================================================
CREATE OR REPLACE FUNCTION extract_domain(url TEXT) RETURNS TEXT AS $$
BEGIN
    -- Remove protocol (http:// or https://)
    url := REGEXP_REPLACE(url, '^https?://', '');
    -- Remove www.
    url := REGEXP_REPLACE(url, '^www\.', '');
    -- Take only the domain part (before first /)
    url := SPLIT_PART(url, '/', 1);
    -- Remove port if present
    url := SPLIT_PART(url, ':', 1);
    -- Return lowercase
    RETURN LOWER(url);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Step 2: Create temporary table with domain info
-- ============================================================================
CREATE TEMP TABLE feed_domains AS
SELECT
    f.id as feed_id,
    extract_domain(f.url) as domain,
    f.name,
    f.url,
    f.category,
    f.scrape_method,
    f.assessment_status,
    f.assessment_date,
    f.credibility_tier,
    f.reputation_score,
    f.political_bias,
    f.founded_year,
    f.organization_type,
    f.editorial_standards,
    f.trust_ratings,
    f.assessment_summary,
    f.fetch_interval,
    f.is_active,
    f.enable_analysis_v2,
    f.enable_categorization,
    f.enable_summary,
    f.health_score,
    f.consecutive_failures,
    f.last_fetched_at,
    f.last_error_message,
    f.last_error_at,
    f.etag,
    f.last_modified,
    f.total_items,
    f.items_last_24h,
    f.created_at,
    f.updated_at,
    -- Rank feeds within domain by quality
    ROW_NUMBER() OVER (
        PARTITION BY extract_domain(f.url)
        ORDER BY
            CASE WHEN f.assessment_status = 'completed' THEN 0 ELSE 1 END,
            COALESCE(f.reputation_score, 0) DESC,
            LENGTH(f.name)
    ) as rank_in_domain
FROM feeds f
-- Exclude test feeds
WHERE f.id NOT IN (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid
);

-- ============================================================================
-- Step 3: Create Sources from unique domains (using best feed per domain)
-- ============================================================================

INSERT INTO sources (
    id,
    domain,
    canonical_name,
    organization_name,
    description,
    homepage_url,
    status,
    is_active,
    category,
    -- Scraping config
    scrape_method,
    scrape_status,
    rate_limit_per_minute,
    -- Assessment data (from best feed)
    assessment_status,
    assessment_date,
    credibility_tier,
    reputation_score,
    political_bias,
    founded_year,
    organization_type,
    editorial_standards,
    trust_ratings,
    assessment_summary,
    -- Timestamps
    created_at,
    updated_at
)
SELECT
    gen_random_uuid() as id,
    fd.domain,
    fd.name as canonical_name,
    NULL as organization_name,
    NULL as description,
    'https://' || fd.domain as homepage_url,
    'active' as status,
    true as is_active,
    fd.category,
    COALESCE(fd.scrape_method, 'newspaper4k') as scrape_method,
    'working' as scrape_status,
    10 as rate_limit_per_minute,
    fd.assessment_status,
    fd.assessment_date,
    fd.credibility_tier,
    fd.reputation_score,
    fd.political_bias,
    fd.founded_year,
    fd.organization_type,
    fd.editorial_standards,
    fd.trust_ratings,
    fd.assessment_summary,
    fd.created_at,
    fd.updated_at
FROM feed_domains fd
WHERE fd.rank_in_domain = 1;

-- ============================================================================
-- Step 4: Create SourceFeeds from existing Feeds
-- ============================================================================

INSERT INTO source_feeds (
    id,
    source_id,
    provider_type,
    provider_id,
    channel_name,
    feed_url,
    fetch_interval,
    is_active,
    enable_analysis,
    health_score,
    consecutive_failures,
    last_fetched_at,
    last_error,
    etag,
    last_modified,
    total_items,
    items_last_24h,
    discovered_at,
    created_at,
    updated_at
)
SELECT
    gen_random_uuid() as id,
    s.id as source_id,
    'rss' as provider_type,
    NULL as provider_id,
    -- Use feed name as channel_name if domain has multiple feeds
    CASE
        WHEN (SELECT COUNT(*) FROM feed_domains fd2 WHERE fd2.domain = fd.domain) > 1
        THEN fd.name
        ELSE NULL
    END as channel_name,
    fd.url as feed_url,
    fd.fetch_interval,
    fd.is_active,
    -- Enable analysis if any analysis feature was enabled
    (fd.enable_analysis_v2 OR fd.enable_categorization OR fd.enable_summary) as enable_analysis,
    fd.health_score,
    fd.consecutive_failures,
    fd.last_fetched_at,
    fd.last_error_message as last_error,
    fd.etag,
    fd.last_modified,
    fd.total_items,
    fd.items_last_24h,
    fd.created_at as discovered_at,
    fd.created_at,
    fd.updated_at
FROM feed_domains fd
JOIN sources s ON s.domain = fd.domain;

-- ============================================================================
-- Step 5: Migrate assessment history
-- ============================================================================

INSERT INTO source_assessment_history (
    id,
    source_id,
    assessment_status,
    assessment_date,
    credibility_tier,
    reputation_score,
    political_bias,
    founded_year,
    organization_type,
    editorial_standards,
    trust_ratings,
    assessment_summary,
    created_at
)
SELECT
    gen_random_uuid() as id,
    s.id as source_id,
    fah.assessment_status,
    fah.assessment_date,
    fah.credibility_tier,
    fah.reputation_score,
    fah.political_bias,
    fah.founded_year,
    fah.organization_type,
    fah.editorial_standards,
    fah.trust_ratings,
    fah.assessment_summary,
    fah.created_at
FROM feed_assessment_history fah
JOIN feed_domains fd ON fd.feed_id = fah.feed_id
JOIN sources s ON s.domain = fd.domain;

-- ============================================================================
-- Step 6: Update scrape metrics on sources (aggregate from feeds)
-- ============================================================================

UPDATE sources s SET
    scrape_success_rate = COALESCE(
        (
            SELECT AVG(
                CASE WHEN fd.total_items > 0
                THEN (fd.total_items::float - fd.consecutive_failures) / fd.total_items
                ELSE 1.0
                END
            )
            FROM feed_domains fd
            WHERE fd.domain = s.domain
        ),
        0.0
    ),
    scrape_total_attempts = (
        SELECT COALESCE(SUM(fd.total_items), 0)
        FROM feed_domains fd
        WHERE fd.domain = s.domain
    ),
    scrape_last_success = (
        SELECT MAX(fd.last_fetched_at)
        FROM feed_domains fd
        WHERE fd.domain = s.domain
        AND fd.consecutive_failures = 0
    ),
    scrape_last_failure = (
        SELECT MAX(fd.last_error_at)
        FROM feed_domains fd
        WHERE fd.domain = s.domain
        AND fd.last_error_at IS NOT NULL
    );

-- ============================================================================
-- Step 7: Create mapping table for reference (for debugging/rollback)
-- ============================================================================

DROP TABLE IF EXISTS _feed_to_source_mapping;
CREATE TABLE _feed_to_source_mapping (
    feed_id UUID PRIMARY KEY,
    source_id UUID NOT NULL,
    source_feed_id UUID NOT NULL,
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO _feed_to_source_mapping (feed_id, source_id, source_feed_id)
SELECT
    fd.feed_id,
    s.id as source_id,
    sf.id as source_feed_id
FROM feed_domains fd
JOIN sources s ON s.domain = fd.domain
JOIN source_feeds sf ON sf.source_id = s.id AND sf.feed_url = fd.url;

-- ============================================================================
-- Step 8: Cleanup
-- ============================================================================

DROP FUNCTION IF EXISTS extract_domain(TEXT);
DROP TABLE IF EXISTS feed_domains;

-- ============================================================================
-- Verification queries
-- ============================================================================

SELECT 'feeds (excl. test)' as table_name, COUNT(*) as count FROM feeds WHERE id NOT IN ('00000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000002'::uuid)
UNION ALL
SELECT 'sources' as table_name, COUNT(*) as count FROM sources
UNION ALL
SELECT 'source_feeds' as table_name, COUNT(*) as count FROM source_feeds
UNION ALL
SELECT 'mapping' as table_name, COUNT(*) as count FROM _feed_to_source_mapping;

COMMIT;

-- ============================================================================
-- Post-migration summary
-- ============================================================================
SELECT
    'Migration complete!' as status,
    (SELECT COUNT(*) FROM sources) as sources_created,
    (SELECT COUNT(*) FROM source_feeds) as source_feeds_created;
