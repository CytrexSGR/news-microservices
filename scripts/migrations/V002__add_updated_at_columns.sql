-- Migration V002: Add updated_at columns and missing index
-- Fixes P1 issues from code review:
-- 1. Missing updated_at columns on article_clusters, publication_review_queue, sitrep_reports
-- 2. Missing index on article_versions(pub_status, created_at DESC)
--
-- Author: Claude Code
-- Date: 2026-01-04

BEGIN;

-- ============================================================================
-- 1. Add updated_at columns to tables missing them
-- ============================================================================

ALTER TABLE article_clusters
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE publication_review_queue
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE sitrep_reports
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- ============================================================================
-- 2. Create trigger function for auto-updating updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. Add triggers to automatically update updated_at on row modification
-- ============================================================================

-- article_clusters trigger
DROP TRIGGER IF EXISTS trg_article_clusters_updated ON article_clusters;
CREATE TRIGGER trg_article_clusters_updated
    BEFORE UPDATE ON article_clusters
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- publication_review_queue trigger
DROP TRIGGER IF EXISTS trg_publication_review_queue_updated ON publication_review_queue;
CREATE TRIGGER trg_publication_review_queue_updated
    BEFORE UPDATE ON publication_review_queue
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- sitrep_reports trigger
DROP TRIGGER IF EXISTS trg_sitrep_reports_updated ON sitrep_reports;
CREATE TRIGGER trg_sitrep_reports_updated
    BEFORE UPDATE ON sitrep_reports
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ============================================================================
-- 4. Add missing index on article_versions for pub_status queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_versions_pub_status
    ON article_versions(pub_status, created_at DESC);

-- ============================================================================
-- 5. Verification queries (informational, run after commit)
-- ============================================================================

-- Verify columns exist
-- SELECT table_name, column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name IN ('article_clusters', 'publication_review_queue', 'sitrep_reports')
--   AND column_name = 'updated_at';

-- Verify triggers exist
-- SELECT trigger_name, event_object_table, action_timing, event_manipulation
-- FROM information_schema.triggers
-- WHERE trigger_name LIKE 'trg_%_updated';

-- Verify index exists
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE indexname = 'idx_versions_pub_status';

COMMIT;
