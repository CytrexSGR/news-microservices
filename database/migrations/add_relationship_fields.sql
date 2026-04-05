-- Migration: Add relationship extraction fields to analysis_results
-- Created: 2025-10-23
-- Service: content-analysis-service
-- Purpose: Enable structured relationship triplet storage for Knowledge Graph

BEGIN;

-- Add new enum values for RelationshipType (if not exists)
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ruled_against' AND enumtypid = 'relationshiptype'::regtype) THEN
        ALTER TYPE relationshiptype ADD VALUE 'ruled_against';
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'abused_monopoly_in' AND enumtypid = 'relationshiptype'::regtype) THEN
        ALTER TYPE relationshiptype ADD VALUE 'abused_monopoly_in';
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'announced' AND enumtypid = 'relationshiptype'::regtype) THEN
        ALTER TYPE relationshiptype ADD VALUE 'announced';
    END IF;
END $$;

-- Add JSONB columns for relationship storage
ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS extracted_relationships JSONB;

ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS relationship_metadata JSONB;

-- Add comments for documentation
COMMENT ON COLUMN analysis_results.extracted_relationships IS
'Structured relationship triplets in format [[entity1, relation, entity2], ...]. Example: [["Apple", "located_in", "California"], ["Tim Cook", "works_for", "Apple"]]';

COMMENT ON COLUMN analysis_results.relationship_metadata IS
'Confidence scores, evidence, validation metrics, and quality indicators for relationships. Includes acceptance_rate, avg_confidence, and validation stats.';

-- Create index for relationship existence queries
CREATE INDEX IF NOT EXISTS idx_analysis_has_relationships
ON analysis_results ((extracted_relationships IS NOT NULL))
WHERE analysis_type = 'entities';

-- Create GIN index for JSONB containment queries
-- This allows fast queries like: WHERE extracted_relationships @> '["Apple", "located_in", "California"]'
CREATE INDEX IF NOT EXISTS idx_analysis_relationships_gin
ON analysis_results USING gin (extracted_relationships)
WHERE analysis_type = 'entities';

-- Create index on entity_relationships for confidence-based filtering
CREATE INDEX IF NOT EXISTS idx_entity_relationship_confidence
ON entity_relationships(confidence)
WHERE confidence >= 0.7;

COMMIT;

-- Verification queries (run separately after migration)
-- 1. Check new columns exist:
-- \d+ analysis_results

-- 2. Check enum values:
-- SELECT enumlabel FROM pg_enum WHERE enumtypid = 'relationshiptype'::regtype ORDER BY enumlabel;

-- 3. Check indexes:
-- \di idx_analysis_has_relationships
-- \di idx_analysis_relationships_gin
-- \di idx_entity_relationship_confidence
