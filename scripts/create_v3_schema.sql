-- Content-Analysis-V3 Database Schema
-- Created: 2025-11-19
-- Based on: /home/cytrex/userdocs/content-analysis-v3/design/data-model.md

-- Connect to content_analysis_v3
\c content_analysis_v3;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TIER 0: TRIAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS triage_decisions (
    article_id UUID PRIMARY KEY,
    priority_score INT CHECK (priority_score BETWEEN 0 AND 10),
    category VARCHAR(20) NOT NULL CHECK (category IN ('CONFLICT', 'FINANCE', 'POLITICS', 'HUMANITARIAN', 'SECURITY', 'TECHNOLOGY', 'OTHER')),
    keep BOOLEAN NOT NULL,
    tokens_used INT,
    cost_usd DECIMAL(10, 6),
    model VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_triage_keep ON triage_decisions(keep);
CREATE INDEX idx_triage_category ON triage_decisions(category);
CREATE INDEX idx_triage_created ON triage_decisions(created_at DESC);

-- ============================================================================
-- TIER 1: FOUNDATION EXTRACTION
-- ============================================================================

-- Entities
CREATE TABLE IF NOT EXISTS tier1_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT')),
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    mentions INT CHECK (mentions >= 1),
    aliases JSONB,
    role VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tier1_entities_article ON tier1_entities(article_id);
CREATE INDEX idx_tier1_entities_type ON tier1_entities(type);
CREATE INDEX idx_tier1_entities_name ON tier1_entities(name);

-- Relations
CREATE TABLE IF NOT EXISTS tier1_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    subject VARCHAR(200) NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object VARCHAR(200) NOT NULL,
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tier1_relations_article ON tier1_relations(article_id);
CREATE INDEX idx_tier1_relations_subject ON tier1_relations(subject);
CREATE INDEX idx_tier1_relations_predicate ON tier1_relations(predicate);

-- Topics
CREATE TABLE IF NOT EXISTS tier1_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    keyword VARCHAR(50) NOT NULL,
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    parent_category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tier1_topics_article ON tier1_topics(article_id);
CREATE INDEX idx_tier1_topics_keyword ON tier1_topics(keyword);

-- Scores
CREATE TABLE IF NOT EXISTS tier1_scores (
    article_id UUID PRIMARY KEY,
    impact_score DECIMAL(4, 2) CHECK (impact_score BETWEEN 0 AND 10),
    credibility_score DECIMAL(4, 2) CHECK (credibility_score BETWEEN 0 AND 10),
    urgency_score DECIMAL(4, 2) CHECK (urgency_score BETWEEN 0 AND 10),
    tokens_used INT,
    cost_usd DECIMAL(10, 6),
    model VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tier1_scores_impact ON tier1_scores(impact_score DESC);
CREATE INDEX idx_tier1_scores_urgency ON tier1_scores(urgency_score DESC);

-- ============================================================================
-- TIER 2: SPECIALIST ANALYSIS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tier2_specialist_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    specialist_type VARCHAR(50) NOT NULL CHECK (specialist_type IN ('TOPIC_CLASSIFIER', 'ENTITY_EXTRACTOR', 'FINANCIAL_ANALYST', 'GEOPOLITICAL_ANALYST', 'SENTIMENT_ANALYZER')),

    -- Specialist-specific data stored as JSONB
    specialist_data JSONB NOT NULL,

    tokens_used INT NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    model VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one result per specialist per article
    UNIQUE(article_id, specialist_type)
);

CREATE INDEX idx_tier2_article ON tier2_specialist_results(article_id);
CREATE INDEX idx_tier2_specialist ON tier2_specialist_results(specialist_type);
CREATE INDEX idx_tier2_created ON tier2_specialist_results(created_at DESC);

-- ============================================================================
-- TIER 3: INTELLIGENCE MODULES
-- ============================================================================

-- Intelligence module metrics (numerical only)
CREATE TABLE IF NOT EXISTS intelligence_module_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    module_name VARCHAR(50) NOT NULL CHECK (module_name IN ('EVENT_INTELLIGENCE', 'SECURITY_INTELLIGENCE', 'HUMANITARIAN_INTELLIGENCE', 'GEOPOLITICAL_INTELLIGENCE', 'FINANCIAL_INTELLIGENCE', 'REGIONAL_INTELLIGENCE')),
    metrics JSONB NOT NULL,
    tokens_used INT,
    cost_usd DECIMAL(10, 6),
    model VARCHAR(50),
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_intelligence_module_article ON intelligence_module_metrics(article_id);
CREATE INDEX idx_intelligence_module_name ON intelligence_module_metrics(module_name);
CREATE INDEX idx_intelligence_created ON intelligence_module_metrics(created_at DESC);

-- Symbolic findings (for Neo4j ingestion)
CREATE TABLE IF NOT EXISTS symbolic_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    module_name VARCHAR(50) NOT NULL,
    finding_type VARCHAR(50) NOT NULL CHECK (finding_type IN ('ENTITY_CLUSTER', 'CAUSAL_CHAIN', 'TEMPORAL_SEQUENCE', 'CONFLICT_PATTERN', 'INFLUENCE_NETWORK')),

    -- Graph structure stored as JSONB
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,

    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Neo4j ingestion tracking
    ingested_to_neo4j BOOLEAN DEFAULT FALSE,
    ingestion_timestamp TIMESTAMPTZ
);

CREATE INDEX idx_symbolic_findings_article ON symbolic_findings(article_id);
CREATE INDEX idx_symbolic_findings_pending ON symbolic_findings(ingested_to_neo4j) WHERE NOT ingested_to_neo4j;
CREATE INDEX idx_symbolic_findings_type ON symbolic_findings(finding_type);

-- ============================================================================
-- MASTER TABLE: ARTICLE ANALYSIS V3
-- ============================================================================

CREATE TABLE IF NOT EXISTS article_analysis_v3 (
    article_id UUID PRIMARY KEY,
    version VARCHAR(10) DEFAULT 'v3',

    -- Status tracking
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Cost & performance
    total_cost_usd DECIMAL(10, 6),
    total_tokens INT,
    processing_time_ms INT,

    -- Provider breakdown (JSONB)
    providers_used JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Error tracking
    error_message TEXT,
    retry_count INT DEFAULT 0 CHECK (retry_count >= 0)
);

CREATE INDEX idx_analysis_v3_status ON article_analysis_v3(status);
CREATE INDEX idx_analysis_v3_created ON article_analysis_v3(created_at DESC);
CREATE INDEX idx_analysis_v3_completed ON article_analysis_v3(completed_at DESC);
CREATE INDEX idx_analysis_v3_cost ON article_analysis_v3(total_cost_usd);

-- ============================================================================
-- VIEWS FOR ANALYSIS
-- ============================================================================

-- Cost breakdown view
CREATE OR REPLACE VIEW v3_cost_breakdown AS
SELECT
    a.article_id,
    a.total_cost_usd,
    a.total_tokens,
    a.providers_used,

    -- Tier breakdown
    t0.cost_usd AS tier0_cost,
    t1.cost_usd AS tier1_cost,
    COALESCE(SUM(t2.cost_usd), 0) AS tier2_cost,
    COALESCE(SUM(t3.cost_usd), 0) AS tier3_cost
FROM article_analysis_v3 a
LEFT JOIN triage_decisions t0 ON a.article_id = t0.article_id
LEFT JOIN tier1_scores t1 ON a.article_id = t1.article_id
LEFT JOIN tier2_specialist_results t2 ON a.article_id = t2.article_id
LEFT JOIN intelligence_module_metrics t3 ON a.article_id = t3.article_id
GROUP BY a.article_id, a.total_cost_usd, a.total_tokens, a.providers_used, t0.cost_usd, t1.cost_usd;

-- ============================================================================
-- GRANTS
-- ============================================================================

-- Grant permissions to news_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO news_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO news_user;

-- ============================================================================
-- COMPLETION
-- ============================================================================

\echo 'Content-Analysis-V3 schema created successfully!'
\echo ''
\echo 'Tables created:'
\echo '  - triage_decisions'
\echo '  - tier1_entities'
\echo '  - tier1_relations'
\echo '  - tier1_topics'
\echo '  - tier1_scores'
\echo '  - tier2_specialist_results'
\echo '  - intelligence_module_metrics'
\echo '  - symbolic_findings'
\echo '  - article_analysis_v3'
\echo ''
\echo 'Views created:'
\echo '  - v3_cost_breakdown'
\echo ''
\echo 'Ready for V3 pipeline implementation!'
