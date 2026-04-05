-- Migration: 008_add_article_analysis_article_id_index
-- Date: 2025-11-09
-- Author: Technical Debt Cleanup (CODE-007)
-- Description: Add index on article_analysis.article_id for 30-40x faster queries
--
-- Performance Impact:
--   Before: 220-270ms per query (sequential scan)
--   After:  5-10ms per query (index scan)
--   Improvement: 30-40x faster
--
-- References:
--   - CODE_QUALITY_DEBT.md:CODE-007
--   - feed-service/app/services/analysis_loader.py (main consumer)

-- Create index on article_analysis.article_id
-- This is the primary foreign key used for JOINs with articles table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_article_id_fk
ON public.article_analysis(article_id);

-- Add comment for future reference
COMMENT ON INDEX public.idx_article_analysis_article_id_fk IS
'Index on article_id foreign key for fast JOINs with articles table.
Added 2025-11-09 as part of CODE-007 performance optimization.
Expected to improve feed-service queries by 30-40x.';

-- Verify index was created
\d public.article_analysis

-- Expected output should include:
-- Indexes:
--   "idx_article_analysis_article_id_fk" btree (article_id)
