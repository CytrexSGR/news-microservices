-- Create centralized article_analysis table in postgres (shared) database
-- This table stores analysis results from both V2 and V3 pipelines
CREATE TABLE IF NOT EXISTS public.article_analysis (
    article_id UUID PRIMARY KEY,
    pipeline_version VARCHAR(10) NOT NULL DEFAULT '2.0', -- '2.0' or '3.0'
    success BOOLEAN NOT NULL,
    
    -- V2/V3 Triage (Tier0)
    triage_results JSONB,
    
    -- Tier 1 Foundation
    tier1_results JSONB,
    
    -- Tier 2 Specialists
    tier2_results JSONB,
    
    -- Tier 3 Intelligence (V2 only)
    tier3_results JSONB,
    
    -- V2 Relevance Scoring (deprecated in V3)
    relevance_score NUMERIC(5, 2),
    score_breakdown JSONB,
    
    -- Metrics
    metrics JSONB,
    
    -- Error handling
    error_message TEXT,
    failed_agents TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_article_analysis_created ON public.article_analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_article_analysis_pipeline ON public.article_analysis(pipeline_version);
CREATE INDEX IF NOT EXISTS idx_article_analysis_success ON public.article_analysis(success);

-- Comment
COMMENT ON TABLE public.article_analysis IS 'Centralized analysis results from V2 and V3 pipelines';
COMMENT ON COLUMN public.article_analysis.pipeline_version IS '2.0 for V2 pipeline, 3.0 for V3 pipeline';
COMMENT ON COLUMN public.article_analysis.triage_results IS 'V2: triage decision, V3: tier0 triage';
COMMENT ON COLUMN public.article_analysis.tier3_results IS 'V2 only - V3 does not have Tier3';
COMMENT ON COLUMN public.article_analysis.relevance_score IS 'V2 only - V3 does not use relevance scoring';
