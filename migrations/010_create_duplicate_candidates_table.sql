-- migrations/010_create_duplicate_candidates_table.sql
-- Migration: Create duplicate_candidates table for HITL near-duplicate review
-- Date: 2026-01-04
-- Epic: 1.2 Deduplication Pipeline

CREATE TABLE IF NOT EXISTS public.duplicate_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The new article being ingested
    new_article_id UUID NOT NULL,

    -- The existing article it's similar to
    existing_article_id UUID NOT NULL,

    -- Similarity metrics
    hamming_distance INTEGER NOT NULL,
    simhash_new BIGINT NOT NULL,
    simhash_existing BIGINT NOT NULL,

    -- Review state
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_decision VARCHAR(20), -- 'keep_both', 'reject_new', 'merge'
    review_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT chk_duplicate_status CHECK (status IN ('pending', 'reviewed', 'auto_resolved')),
    CONSTRAINT chk_review_decision CHECK (
        review_decision IS NULL OR
        review_decision IN ('keep_both', 'reject_new', 'merge')
    ),

    -- Foreign keys (soft - articles may be deleted)
    CONSTRAINT fk_new_article FOREIGN KEY (new_article_id)
        REFERENCES feed_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_existing_article FOREIGN KEY (existing_article_id)
        REFERENCES feed_items(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_status
    ON duplicate_candidates(status) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_new_article
    ON duplicate_candidates(new_article_id);

CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_existing_article
    ON duplicate_candidates(existing_article_id);

-- Comment
COMMENT ON TABLE duplicate_candidates IS
    'Near-duplicate articles flagged for human review. Hamming distance 4-7.';

SELECT 'duplicate_candidates table created' AS status;
