-- ============================================================================
-- Backfill Script: feed_items.source_id
-- ============================================================================
-- Updates existing feed_items with source_id by joining through the
-- feeds table and mapping table created during source migration.
--
-- Run with: docker compose exec -T postgres psql -U news_user -d news_mcp -f /scripts/backfill_feed_items_source_id.sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Show current state
-- ============================================================================
SELECT
    'Before backfill' as status,
    COUNT(*) as total_feed_items,
    COUNT(source_id) as with_source_id,
    COUNT(*) - COUNT(source_id) as without_source_id
FROM feed_items;

-- ============================================================================
-- Step 2: Update feed_items with source_id via mapping table
-- ============================================================================
-- Uses the _feed_to_source_mapping table created during feeds→sources migration

UPDATE feed_items fi
SET source_id = m.source_id
FROM _feed_to_source_mapping m
WHERE fi.feed_id = m.feed_id
  AND fi.source_id IS NULL;

-- ============================================================================
-- Step 3: Verify results
-- ============================================================================
SELECT
    'After backfill' as status,
    COUNT(*) as total_feed_items,
    COUNT(source_id) as with_source_id,
    COUNT(*) - COUNT(source_id) as without_source_id
FROM feed_items;

-- Show distribution by source
SELECT
    s.domain,
    s.canonical_name,
    COUNT(fi.id) as article_count
FROM sources s
LEFT JOIN feed_items fi ON fi.source_id = s.id
GROUP BY s.id, s.domain, s.canonical_name
ORDER BY article_count DESC
LIMIT 20;

COMMIT;

-- ============================================================================
-- Summary
-- ============================================================================
SELECT
    'Backfill complete!' as status,
    (SELECT COUNT(*) FROM feed_items WHERE source_id IS NOT NULL) as items_with_source,
    (SELECT COUNT(*) FROM feed_items WHERE source_id IS NULL) as items_without_source,
    (SELECT COUNT(DISTINCT source_id) FROM feed_items WHERE source_id IS NOT NULL) as unique_sources;
