-- Migration: Add Feed Scheduling Fields
-- Purpose: Enable intelligent feed scheduling to prevent thundering herd problem
-- Date: 2025-11-20
-- Author: Feed Optimization System

-- ============================================================================
-- Step 1: Add scheduling columns to feeds table
-- ============================================================================

ALTER TABLE feeds
ADD COLUMN IF NOT EXISTS next_fetch_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS schedule_offset_minutes INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS scheduling_priority INTEGER DEFAULT 5;

-- ============================================================================
-- Step 2: Add performance indices
-- ============================================================================

-- Index for efficient querying of feeds due for fetching
CREATE INDEX IF NOT EXISTS idx_feeds_next_fetch
ON feeds(next_fetch_at)
WHERE is_active = true;

-- Index for scheduling optimization queries
CREATE INDEX IF NOT EXISTS idx_feeds_scheduling
ON feeds(fetch_interval, schedule_offset_minutes)
WHERE is_active = true;

-- ============================================================================
-- Step 3: Initialize next_fetch_at for existing feeds
-- ============================================================================

-- For feeds that have been fetched before, calculate next fetch based on:
-- last_fetched_at + fetch_interval + staggered offset
UPDATE feeds
SET next_fetch_at = last_fetched_at + (fetch_interval || ' minutes')::INTERVAL
WHERE is_active = true
  AND last_fetched_at IS NOT NULL
  AND next_fetch_at IS NULL;

-- For feeds never fetched, set to NOW + small random offset to avoid initial clustering
UPDATE feeds
SET next_fetch_at = NOW() + (FLOOR(RANDOM() * fetch_interval) || ' minutes')::INTERVAL
WHERE is_active = true
  AND last_fetched_at IS NULL
  AND next_fetch_at IS NULL;

-- ============================================================================
-- Step 4: Add comments for documentation
-- ============================================================================

COMMENT ON COLUMN feeds.next_fetch_at IS
'Timestamp when this feed should be fetched next. Used for intelligent scheduling to prevent thundering herd.';

COMMENT ON COLUMN feeds.schedule_offset_minutes IS
'Offset in minutes from the base interval for staggering feeds with same fetch_interval.';

COMMENT ON COLUMN feeds.scheduling_priority IS
'Priority for scheduling (1-10). Higher priority feeds are scheduled more optimally. Default: 5.';

-- ============================================================================
-- Step 5: Verify migration
-- ============================================================================

DO $$
DECLARE
    feeds_with_next_fetch INTEGER;
    active_feeds INTEGER;
BEGIN
    -- Count feeds with next_fetch_at set
    SELECT COUNT(*) INTO feeds_with_next_fetch
    FROM feeds
    WHERE next_fetch_at IS NOT NULL AND is_active = true;

    -- Count total active feeds
    SELECT COUNT(*) INTO active_feeds
    FROM feeds
    WHERE is_active = true;

    -- Verify all active feeds have next_fetch_at
    IF feeds_with_next_fetch < active_feeds THEN
        RAISE WARNING 'Migration incomplete: % of % active feeds have next_fetch_at set',
            feeds_with_next_fetch, active_feeds;
    ELSE
        RAISE NOTICE 'Migration successful: All % active feeds have next_fetch_at set', active_feeds;
    END IF;

    -- Show distribution of next fetches
    RAISE NOTICE 'Next fetch distribution:';
    RAISE NOTICE '  - Next 1 hour: % feeds', (
        SELECT COUNT(*) FROM feeds
        WHERE is_active = true
        AND next_fetch_at <= NOW() + INTERVAL '1 hour'
    );
    RAISE NOTICE '  - Next 6 hours: % feeds', (
        SELECT COUNT(*) FROM feeds
        WHERE is_active = true
        AND next_fetch_at <= NOW() + INTERVAL '6 hours'
    );
END $$;
