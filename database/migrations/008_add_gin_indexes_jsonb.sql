-- Migration: Add GIN indexes for JSONB query performance
-- Created: 2025-11-25
-- Purpose: Improve query performance on JSONB columns in article_analysis table

-- GIN index for tier1_results (entities, relations, topics queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_tier1_gin
ON public.article_analysis USING GIN (tier1_results jsonb_path_ops);

-- GIN index for tier2_results (specialist analysis queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_tier2_gin
ON public.article_analysis USING GIN (tier2_results jsonb_path_ops);

-- GIN index for triage_results (filtering by decision/relevance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_triage_gin
ON public.article_analysis USING GIN (triage_results jsonb_path_ops);

-- GIN index for metrics (cost/token analysis)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_metrics_gin
ON public.article_analysis USING GIN (metrics jsonb_path_ops);

-- Note: jsonb_path_ops is more efficient than default GIN operator class
-- but only supports @> (containment) operator
-- Use this when queries are primarily containment checks like:
--   WHERE tier1_results @> '{"entities": [{"type": "PERSON"}]}'

COMMENT ON INDEX idx_article_analysis_tier1_gin IS 'GIN index for tier1 entity/relation/topic queries';
COMMENT ON INDEX idx_article_analysis_tier2_gin IS 'GIN index for tier2 specialist result queries';
COMMENT ON INDEX idx_article_analysis_triage_gin IS 'GIN index for triage decision filtering';
COMMENT ON INDEX idx_article_analysis_metrics_gin IS 'GIN index for cost/token analytics';
