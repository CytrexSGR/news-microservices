-- Add sentiment analysis fields to entity_relationships table
-- Date: 2025-10-25
-- Description: Support sentiment scoring for knowledge graph relationships

BEGIN;

-- Add sentiment columns
ALTER TABLE entity_relationships
    ADD COLUMN IF NOT EXISTS sentiment_score FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_category VARCHAR(20),
    ADD COLUMN IF NOT EXISTS sentiment_confidence FLOAT;

-- Add comments for documentation
COMMENT ON COLUMN entity_relationships.sentiment_score IS 'Sentiment polarity from -1.0 (very negative) to +1.0 (very positive)';
COMMENT ON COLUMN entity_relationships.sentiment_category IS 'Categorical sentiment: positive, negative, or neutral';
COMMENT ON COLUMN entity_relationships.sentiment_confidence IS 'Confidence in sentiment assessment from 0.0 to 1.0';

COMMIT;
