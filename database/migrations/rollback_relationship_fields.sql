-- Rollback: Remove relationship extraction fields
-- Created: 2025-10-23
-- Service: content-analysis-service
-- Purpose: Rollback relationship triplet storage changes

BEGIN;

-- Drop indexes
DROP INDEX IF EXISTS idx_analysis_has_relationships;
DROP INDEX IF EXISTS idx_analysis_relationships_gin;
DROP INDEX IF EXISTS idx_entity_relationship_confidence;

-- Drop columns
ALTER TABLE analysis_results DROP COLUMN IF EXISTS extracted_relationships;
ALTER TABLE analysis_results DROP COLUMN IF EXISTS relationship_metadata;

COMMIT;

-- NOTE: Cannot remove enum values without recreating the type
-- If enum values need to be removed, manual intervention required:
--
-- 1. Create new enum type without the values:
--    CREATE TYPE relationshiptype_new AS ENUM (
--        'works_for', 'located_in', 'owns', 'related_to',
--        'member_of', 'partner_of', 'not_applicable'
--    );
--
-- 2. Update all tables using the enum:
--    ALTER TABLE entity_relationships
--    ALTER COLUMN relationship_type TYPE relationshiptype_new
--    USING relationship_type::text::relationshiptype_new;
--
-- 3. Drop old enum and rename new one:
--    DROP TYPE relationshiptype;
--    ALTER TYPE relationshiptype_new RENAME TO relationshiptype;
