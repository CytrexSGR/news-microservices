-- Migration V003: Add category column to sitrep_reports
-- Enables category-based filtering for SITREP reports
-- Categories: politics, finance, conflict_security, technology, crypto
--
-- Author: Claude Code
-- Date: 2026-01-05

BEGIN;

-- ============================================================================
-- 1. Add category column to sitrep_reports
-- ============================================================================

ALTER TABLE sitrep_reports
    ADD COLUMN IF NOT EXISTS category VARCHAR(50);

-- ============================================================================
-- 2. Create index for category filtering
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_sitrep_reports_category
    ON sitrep_reports(category);

-- Create composite index for efficient category + date queries
CREATE INDEX IF NOT EXISTS ix_sitrep_reports_category_date
    ON sitrep_reports(category, report_date DESC);

-- ============================================================================
-- 3. Record migration
-- ============================================================================

INSERT INTO _migration_history (migration_name, applied_at)
VALUES ('V003__add_sitrep_category', NOW())
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
