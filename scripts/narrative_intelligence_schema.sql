-- Narrative Intelligence Database Schema
-- Created: 2025-12-26
-- Purpose: Support n8n workflows for narrative analysis automation

-- =========================================
-- #4 Entity Reputation Monitor
-- =========================================

-- Monitored entities watchlist
CREATE TABLE IF NOT EXISTS ni_monitored_entities (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) DEFAULT 'unknown',  -- PERSON, ORG, GPE, etc.
    priority INTEGER DEFAULT 5,  -- 1-10, higher = more important
    alert_threshold DECIMAL(3,2) DEFAULT 0.3,  -- Tension change threshold
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Entity tension history for trend analysis
CREATE TABLE IF NOT EXISTS ni_entity_tension_history (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    checked_at TIMESTAMP DEFAULT NOW(),
    avg_tension DECIMAL(4,3),
    max_tension DECIMAL(4,3),
    narrative_count INTEGER,
    dominant_frame VARCHAR(100),
    frame_distribution JSONB,
    tension_delta DECIMAL(4,3),  -- Change since last check
    alert_triggered BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_entity_tension_entity
ON ni_entity_tension_history(entity_name);

CREATE INDEX IF NOT EXISTS idx_entity_tension_checked
ON ni_entity_tension_history(checked_at DESC);

-- =========================================
-- #5 Narrative Shift Detector
-- =========================================

-- Daily frame snapshots for shift detection
CREATE TABLE IF NOT EXISTS ni_frame_history (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    snapshot_date DATE NOT NULL,
    dominant_frame VARCHAR(100),
    frame_distribution JSONB,  -- {frame_type: count, ...}
    avg_tension DECIMAL(4,3),
    narrative_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_name, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_frame_history_entity
ON ni_frame_history(entity_name, snapshot_date DESC);

-- Detected narrative shifts
CREATE TABLE IF NOT EXISTS ni_narrative_shifts (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW(),
    shift_type VARCHAR(50),  -- 'frame_change', 'tension_spike', 'new_frame'
    previous_frame VARCHAR(100),
    new_frame VARCHAR(100),
    tension_before DECIMAL(4,3),
    tension_after DECIMAL(4,3),
    severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    details JSONB,
    alert_sent BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_shifts_entity
ON ni_narrative_shifts(entity_name);

CREATE INDEX IF NOT EXISTS idx_shifts_detected
ON ni_narrative_shifts(detected_at DESC);

-- =========================================
-- #6 Co-occurrence Pattern Alerts
-- =========================================

-- Watch patterns for entity pairs
CREATE TABLE IF NOT EXISTS ni_watch_patterns (
    id SERIAL PRIMARY KEY,
    entity_a VARCHAR(255) NOT NULL,
    entity_b VARCHAR(255) NOT NULL,
    pattern_name VARCHAR(255),  -- e.g., "Russia-Election", "China-Cyber"
    alert_priority INTEGER DEFAULT 5,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_a, entity_b)
);

-- Co-occurrence history
CREATE TABLE IF NOT EXISTS ni_cooccurrence_history (
    id SERIAL PRIMARY KEY,
    entity_a VARCHAR(255) NOT NULL,
    entity_b VARCHAR(255) NOT NULL,
    checked_at TIMESTAMP DEFAULT NOW(),
    shared_narratives INTEGER,
    shared_frames JSONB,
    avg_combined_tension DECIMAL(4,3),
    is_new_pair BOOLEAN DEFAULT false,
    alert_triggered BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_cooccurrence_entities
ON ni_cooccurrence_history(entity_a, entity_b);

CREATE INDEX IF NOT EXISTS idx_cooccurrence_checked
ON ni_cooccurrence_history(checked_at DESC);

-- =========================================
-- #7 ATLAS Reports Metadata
-- =========================================

CREATE TABLE IF NOT EXISTS ni_atlas_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    report_type VARCHAR(50) DEFAULT 'daily',
    total_narratives INTEGER,
    high_tension_count INTEGER,
    entity_count INTEGER,
    top_frames JSONB,
    top_entities JSONB,
    key_insights JSONB,
    pdf_path TEXT,
    html_content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =========================================
-- #15 Webhook Subscriptions
-- =========================================

CREATE TABLE IF NOT EXISTS ni_webhook_subscriptions (
    id SERIAL PRIMARY KEY,
    endpoint_url TEXT NOT NULL,
    secret_key VARCHAR(255),
    event_types TEXT[],  -- ['high_tension', 'narrative_shift', 'new_pair']
    filters JSONB,  -- {min_tension: 0.8, entities: ['Trump', 'Putin']}
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_triggered_at TIMESTAMP
);

-- Webhook delivery log
CREATE TABLE IF NOT EXISTS ni_webhook_log (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES ni_webhook_subscriptions(id),
    event_type VARCHAR(50),
    payload JSONB,
    status_code INTEGER,
    response TEXT,
    delivered_at TIMESTAMP DEFAULT NOW()
);

-- =========================================
-- Insert sample monitored entities
-- =========================================

INSERT INTO ni_monitored_entities (entity_name, entity_type, priority, alert_threshold) VALUES
('Trump', 'PERSON', 10, 0.25),
('Biden', 'PERSON', 10, 0.25),
('Putin', 'PERSON', 9, 0.3),
('Zelenskyy', 'PERSON', 9, 0.3),
('Russia', 'GPE', 9, 0.3),
('Ukraine', 'GPE', 9, 0.3),
('China', 'GPE', 8, 0.3),
('European Union', 'ORG', 7, 0.35),
('NATO', 'ORG', 8, 0.3),
('Federal Reserve', 'ORG', 7, 0.35)
ON CONFLICT (entity_name) DO NOTHING;

-- Insert sample watch patterns
INSERT INTO ni_watch_patterns (entity_a, entity_b, pattern_name, alert_priority) VALUES
('Russia', 'Election', 'Foreign Interference', 10),
('China', 'Cyber', 'Cyber Threats', 9),
('Trump', 'Indictment', 'Legal Proceedings', 8),
('Fed', 'Rates', 'Monetary Policy', 7),
('Ukraine', 'NATO', 'Security Alliance', 8)
ON CONFLICT (entity_a, entity_b) DO NOTHING;

-- Grant access if needed
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO news_user;

COMMENT ON TABLE ni_monitored_entities IS 'Watchlist for entity reputation monitoring (Workflow #4)';
COMMENT ON TABLE ni_entity_tension_history IS 'Historical tension data per entity for trend analysis';
COMMENT ON TABLE ni_frame_history IS 'Daily frame snapshots for narrative shift detection (Workflow #5)';
COMMENT ON TABLE ni_narrative_shifts IS 'Detected narrative frame shifts with alerts';
COMMENT ON TABLE ni_watch_patterns IS 'Entity pair patterns to monitor for co-occurrence (Workflow #6)';
COMMENT ON TABLE ni_cooccurrence_history IS 'History of entity co-occurrences in narratives';
COMMENT ON TABLE ni_atlas_reports IS 'Metadata for generated ATLAS reports (Component #7)';
COMMENT ON TABLE ni_webhook_subscriptions IS 'External webhook subscriptions for alerts (Component #15)';
