-- Watchlist tables for entity and country tracking
-- Run against: postgres database

-- 1. Watchlist items table
CREATE TABLE IF NOT EXISTS security_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- For multi-user support later
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('entity', 'country', 'keyword', 'region')),
    item_value VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    notes TEXT,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    notify_on_new BOOLEAN DEFAULT true,
    notify_threshold INTEGER DEFAULT 7,  -- Min priority to trigger alert
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, item_type, item_value)
);

-- 2. Alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID REFERENCES security_watchlist(id) ON DELETE CASCADE,
    article_id UUID NOT NULL,
    title TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    threat_level VARCHAR(20) NOT NULL,
    country_code VARCHAR(3),
    matched_value VARCHAR(255) NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_watchlist_user ON security_watchlist(user_id);
CREATE INDEX idx_watchlist_type ON security_watchlist(item_type);
CREATE INDEX idx_alerts_watchlist ON security_alerts(watchlist_id);
CREATE INDEX idx_alerts_read ON security_alerts(is_read);
CREATE INDEX idx_alerts_created ON security_alerts(created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_watchlist_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER watchlist_updated
    BEFORE UPDATE ON security_watchlist
    FOR EACH ROW
    EXECUTE FUNCTION update_watchlist_timestamp();
