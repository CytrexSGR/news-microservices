-- Migration: 009_create_cluster_memberships_table.sql
-- Description: Create cluster_memberships table for tracking article-to-cluster relationships
-- Date: 2026-01-04
-- Epic: 1.1 Clustering Service

-- Create cluster_memberships table
CREATE TABLE IF NOT EXISTS public.cluster_memberships (
    cluster_id UUID NOT NULL,
    article_id UUID NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    similarity_score FLOAT,

    -- Composite primary key
    PRIMARY KEY (cluster_id, article_id),

    -- Foreign key to article_clusters
    FOREIGN KEY (cluster_id) REFERENCES public.article_clusters(id) ON DELETE CASCADE
);

-- Index for looking up all clusters an article belongs to
CREATE INDEX IF NOT EXISTS idx_cluster_memberships_article_id
    ON public.cluster_memberships(article_id);

-- Index for looking up all articles in a cluster
CREATE INDEX IF NOT EXISTS idx_cluster_memberships_cluster_id
    ON public.cluster_memberships(cluster_id);

-- Index for idempotency checks (check if article already processed)
CREATE INDEX IF NOT EXISTS idx_cluster_memberships_article_exists
    ON public.cluster_memberships(article_id) WHERE TRUE;

-- Comment
COMMENT ON TABLE public.cluster_memberships IS
    'Tracks which articles belong to which clusters. Used for idempotency checking and member lookups.';

-- Verification
SELECT 'cluster_memberships table created successfully' AS status;
