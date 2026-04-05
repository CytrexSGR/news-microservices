-- ============================================================
-- Migration: News Intelligence Foundation
-- Version: V001
-- Date: 2026-01-04
-- Description: Adds tables and columns for News Intelligence features
--              (Clustering, SITREP, Time-Decay, HITL, NewsML-G2)
-- ============================================================
-- IDEMPOTENT: Uses IF NOT EXISTS patterns - safe to run multiple times
-- ROLLBACK: See V001__news_intelligence_foundation_rollback.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. FEED_ITEMS TABLE EXTENSIONS
-- ============================================================
-- Adds NewsML-G2 fields, clustering support, SimHash, time-decay

-- NewsML-G2 Essential Fields
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS version_created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS pub_status VARCHAR(20) DEFAULT 'usable' NOT NULL;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS is_correction BOOLEAN DEFAULT FALSE;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS corrects_article_id UUID;

-- SimHash Deduplication
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS simhash_fingerprint BIGINT;

-- Clustering Support (FK added after article_clusters table exists)
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS cluster_id UUID;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS cluster_similarity FLOAT;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS cluster_assigned_at TIMESTAMP WITH TIME ZONE;

-- Time-Decay Ranking
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS relevance_score FLOAT;
ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS relevance_calculated_at TIMESTAMP WITH TIME ZONE;

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_feed_items_simhash
    ON feed_items(simhash_fingerprint)
    WHERE simhash_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_feed_items_pub_status
    ON feed_items(pub_status);

CREATE INDEX IF NOT EXISTS idx_feed_items_relevance
    ON feed_items(relevance_score DESC NULLS LAST)
    WHERE relevance_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_feed_items_correction
    ON feed_items(corrects_article_id)
    WHERE corrects_article_id IS NOT NULL;

-- Constraint for pub_status values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_pub_status'
    ) THEN
        ALTER TABLE feed_items ADD CONSTRAINT chk_pub_status
            CHECK (pub_status IN ('usable', 'withheld', 'canceled'));
    END IF;
END $$;

-- Self-referencing FK for corrections
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_feed_items_corrects'
    ) THEN
        ALTER TABLE feed_items ADD CONSTRAINT fk_feed_items_corrects
            FOREIGN KEY (corrects_article_id)
            REFERENCES feed_items(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================
-- 2. ARTICLE_CLUSTERS TABLE (NEW)
-- ============================================================
-- Stores story clusters for stream clustering

CREATE TABLE IF NOT EXISTS article_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cluster metadata
    title VARCHAR(500) NOT NULL,
    summary TEXT,

    -- Cluster state
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Cluster metrics
    article_count INTEGER DEFAULT 1,
    first_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_updated_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Centroid vector (stored as JSON array)
    centroid_vector JSONB,

    -- Story importance
    tension_score FLOAT,
    is_breaking BOOLEAN DEFAULT FALSE,
    burst_detected_at TIMESTAMP WITH TIME ZONE,

    -- Primary entities (top 5)
    primary_entities JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_cluster_status CHECK (status IN ('active', 'archived', 'merged'))
);

-- Indexes for article_clusters
CREATE INDEX IF NOT EXISTS idx_clusters_active_updated
    ON article_clusters(status, last_updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_clusters_breaking
    ON article_clusters(is_breaking, burst_detected_at DESC)
    WHERE is_breaking = TRUE;

CREATE INDEX IF NOT EXISTS idx_clusters_tension
    ON article_clusters(tension_score DESC NULLS LAST)
    WHERE status = 'active';

-- Now add FK from feed_items to article_clusters
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_feed_items_cluster'
    ) THEN
        ALTER TABLE feed_items ADD CONSTRAINT fk_feed_items_cluster
            FOREIGN KEY (cluster_id)
            REFERENCES article_clusters(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_feed_items_cluster
    ON feed_items(cluster_id)
    WHERE cluster_id IS NOT NULL;

-- ============================================================
-- 3. ARTICLE_VERSIONS TABLE (NEW)
-- ============================================================
-- NewsML-G2 version history tracking

CREATE TABLE IF NOT EXISTS article_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to current article
    article_id UUID NOT NULL,
    version INTEGER NOT NULL,
    pub_status VARCHAR(20) NOT NULL,

    -- Snapshot of content at this version
    title VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,

    -- Change metadata
    change_type VARCHAR(20) NOT NULL,
    change_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_version_change_type
        CHECK (change_type IN ('update', 'correction', 'withdrawal')),
    CONSTRAINT fk_version_article
        FOREIGN KEY (article_id)
        REFERENCES feed_items(id)
        ON DELETE CASCADE
);

-- Indexes for article_versions
CREATE INDEX IF NOT EXISTS idx_versions_article_version
    ON article_versions(article_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_versions_change_type
    ON article_versions(change_type, created_at DESC);

-- ============================================================
-- 4. PUBLICATION_REVIEW_QUEUE TABLE (NEW)
-- ============================================================
-- HITL workflow for content publication

CREATE TABLE IF NOT EXISTS publication_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content reference
    article_id UUID NOT NULL,
    target VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,

    -- Risk assessment
    risk_score FLOAT NOT NULL,
    risk_factors JSONB,

    -- Review status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Review metadata
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewer_notes TEXT,
    edited_content TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT chk_review_status
        CHECK (status IN ('pending', 'approved', 'rejected', 'edited', 'auto_approved', 'blocked')),
    CONSTRAINT fk_review_article
        FOREIGN KEY (article_id)
        REFERENCES feed_items(id)
        ON DELETE CASCADE
);

-- Indexes for publication_review_queue
CREATE INDEX IF NOT EXISTS idx_review_queue_pending
    ON publication_review_queue(status, created_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_review_queue_target
    ON publication_review_queue(target, status);

CREATE INDEX IF NOT EXISTS idx_review_queue_risk
    ON publication_review_queue(risk_score DESC)
    WHERE status = 'pending';

-- ============================================================
-- 5. SITREP_REPORTS TABLE (NEW)
-- ============================================================
-- Intelligence briefing storage

CREATE TABLE IF NOT EXISTS sitrep_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Report metadata
    report_date DATE NOT NULL,
    report_type VARCHAR(50) DEFAULT 'daily',

    -- Content
    title VARCHAR(200) NOT NULL,
    content_markdown TEXT NOT NULL,
    content_html TEXT,

    -- Structured data
    top_stories JSONB NOT NULL,
    key_entities JSONB NOT NULL,
    sentiment_summary JSONB NOT NULL,
    emerging_signals JSONB,

    -- Generation metadata
    generation_model VARCHAR(100) NOT NULL,
    generation_time_ms INTEGER NOT NULL,
    articles_analyzed INTEGER NOT NULL,

    -- Quality
    confidence_score FLOAT,
    human_reviewed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for sitrep_reports
CREATE INDEX IF NOT EXISTS idx_sitrep_date_type
    ON sitrep_reports(report_date DESC, report_type);

CREATE INDEX IF NOT EXISTS idx_sitrep_reviewed
    ON sitrep_reports(human_reviewed, created_at DESC);

-- ============================================================
-- 6. ENTITY_ALIASES TABLE EXTENSIONS
-- ============================================================
-- Extend existing table for fuzzy matching support
-- NOTE: entity_aliases already exists with INTEGER FK to canonical_entities

-- Add new columns for fuzzy matching
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS alias_normalized VARCHAR(255);
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS alias_type VARCHAR(50) DEFAULT 'name';
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 1.0;
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE entity_aliases ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;

-- Backfill alias_normalized from existing alias column
UPDATE entity_aliases
SET alias_normalized = LOWER(TRIM(alias))
WHERE alias_normalized IS NULL;

-- Add constraints for new columns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_alias_type'
    ) THEN
        ALTER TABLE entity_aliases ADD CONSTRAINT chk_alias_type
            CHECK (alias_type IN ('name', 'ticker', 'abbreviation', 'nickname'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_alias_source'
    ) THEN
        ALTER TABLE entity_aliases ADD CONSTRAINT chk_alias_source
            CHECK (source IN ('manual', 'discovered', 'wikidata'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_alias_confidence'
    ) THEN
        ALTER TABLE entity_aliases ADD CONSTRAINT chk_alias_confidence
            CHECK (confidence >= 0 AND confidence <= 1);
    END IF;
END $$;

-- Indexes for fuzzy matching (using CONCURRENTLY for production safety)
-- Note: CONCURRENTLY cannot be used inside a transaction, so we use regular CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_entity_aliases_normalized
    ON entity_aliases(alias_normalized)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_entity_aliases_type
    ON entity_aliases(alias_type)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_entity_aliases_source
    ON entity_aliases(source);

-- ============================================================
-- 7. MIGRATION METADATA
-- ============================================================
-- Track migration execution

CREATE TABLE IF NOT EXISTS _migration_history (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64)
);

INSERT INTO _migration_history (migration_name, checksum)
VALUES ('V001__news_intelligence_foundation', md5('v1.0-2026-01-04'))
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;

-- ============================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================
-- Run these queries to verify migration success:
--
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'feed_items'
-- AND column_name IN ('version', 'pub_status', 'simhash_fingerprint', 'cluster_id', 'relevance_score');
--
-- SELECT table_name FROM information_schema.tables
-- WHERE table_name IN ('article_clusters', 'article_versions', 'publication_review_queue', 'sitrep_reports');
--
-- SELECT * FROM _migration_history WHERE migration_name = 'V001__news_intelligence_foundation';
