-- Migration: Add GIN indexes for Intelligence Features
-- Date: 2026-01-03
-- Purpose: Optimize entity and sentiment queries for burst detection, momentum, etc.

-- GIN index for entity queries (performance critical for burst detection)
CREATE INDEX IF NOT EXISTS idx_article_analysis_entities
ON article_analysis USING GIN ((tier1_data->'entities'));

-- Index for sentiment momentum queries
CREATE INDEX IF NOT EXISTS idx_article_analysis_sentiment_date
ON article_analysis (created_at, ((tier2_data->'SENTIMENT_ANALYZER'->>'sentiment_score')::float));

-- B-tree index on created_at for time-range queries
CREATE INDEX IF NOT EXISTS idx_article_analysis_created_at
ON article_analysis (created_at DESC);

-- Verify indexes were created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'article_analysis'
  AND indexname LIKE 'idx_article_analysis_%'
ORDER BY indexname;
