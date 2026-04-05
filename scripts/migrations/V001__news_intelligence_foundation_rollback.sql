-- ============================================================
-- Rollback: News Intelligence Foundation
-- Version: V001
-- Date: 2026-01-04
-- WARNING: This will DROP tables and columns. Data will be LOST.
-- ============================================================
-- Reverses all changes from V001__news_intelligence_foundation.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. REMOVE FK CONSTRAINTS FROM FEED_ITEMS
-- ============================================================
-- Must drop FKs before dropping referenced tables/columns

ALTER TABLE feed_items DROP CONSTRAINT IF EXISTS fk_feed_items_cluster;
ALTER TABLE feed_items DROP CONSTRAINT IF EXISTS fk_feed_items_corrects;
ALTER TABLE feed_items DROP CONSTRAINT IF EXISTS chk_pub_status;

-- ============================================================
-- 2. DROP INDEXES ON FEED_ITEMS
-- ============================================================

DROP INDEX IF EXISTS idx_feed_items_simhash;
DROP INDEX IF EXISTS idx_feed_items_pub_status;
DROP INDEX IF EXISTS idx_feed_items_relevance;
DROP INDEX IF EXISTS idx_feed_items_correction;
DROP INDEX IF EXISTS idx_feed_items_cluster;

-- ============================================================
-- 3. REMOVE COLUMNS FROM FEED_ITEMS
-- ============================================================

-- NewsML-G2 Essential Fields
ALTER TABLE feed_items DROP COLUMN IF EXISTS version;
ALTER TABLE feed_items DROP COLUMN IF EXISTS version_created_at;
ALTER TABLE feed_items DROP COLUMN IF EXISTS pub_status;
ALTER TABLE feed_items DROP COLUMN IF EXISTS is_correction;
ALTER TABLE feed_items DROP COLUMN IF EXISTS corrects_article_id;

-- SimHash Deduplication
ALTER TABLE feed_items DROP COLUMN IF EXISTS simhash_fingerprint;

-- Clustering Support
ALTER TABLE feed_items DROP COLUMN IF EXISTS cluster_id;
ALTER TABLE feed_items DROP COLUMN IF EXISTS cluster_similarity;
ALTER TABLE feed_items DROP COLUMN IF EXISTS cluster_assigned_at;

-- Time-Decay Ranking
ALTER TABLE feed_items DROP COLUMN IF EXISTS relevance_score;
ALTER TABLE feed_items DROP COLUMN IF EXISTS relevance_calculated_at;

-- ============================================================
-- 4. DROP NEW TABLES (order matters due to FKs)
-- ============================================================

-- Drop tables with FKs to feed_items first
DROP TABLE IF EXISTS publication_review_queue CASCADE;
DROP TABLE IF EXISTS article_versions CASCADE;

-- Drop independent tables
DROP TABLE IF EXISTS sitrep_reports CASCADE;
DROP TABLE IF EXISTS article_clusters CASCADE;

-- ============================================================
-- 5. REMOVE ENTITY_ALIASES EXTENSIONS
-- ============================================================

-- Drop constraints first
ALTER TABLE entity_aliases DROP CONSTRAINT IF EXISTS chk_alias_type;
ALTER TABLE entity_aliases DROP CONSTRAINT IF EXISTS chk_alias_source;
ALTER TABLE entity_aliases DROP CONSTRAINT IF EXISTS chk_alias_confidence;

-- Drop indexes
DROP INDEX IF EXISTS idx_entity_aliases_normalized;
DROP INDEX IF EXISTS idx_entity_aliases_type;
DROP INDEX IF EXISTS idx_entity_aliases_source;

-- Drop columns
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS alias_normalized;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS alias_type;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS language;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS confidence;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS source;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS is_active;
ALTER TABLE entity_aliases DROP COLUMN IF EXISTS usage_count;

-- ============================================================
-- 6. REMOVE MIGRATION RECORD
-- ============================================================

DELETE FROM _migration_history WHERE migration_name = 'V001__news_intelligence_foundation';

-- Note: We do NOT drop _migration_history table as it may contain other migrations

COMMIT;

-- ============================================================
-- POST-ROLLBACK VERIFICATION
-- ============================================================
-- Run these queries to verify rollback success:
--
-- -- Verify feed_items columns removed
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'feed_items'
-- AND column_name = 'simhash_fingerprint';
-- -- Expected: 0 rows
--
-- -- Verify tables dropped
-- SELECT table_name FROM information_schema.tables
-- WHERE table_name = 'article_clusters';
-- -- Expected: 0 rows
--
-- -- Verify migration record removed
-- SELECT * FROM _migration_history WHERE migration_name = 'V001__news_intelligence_foundation';
-- -- Expected: 0 rows
