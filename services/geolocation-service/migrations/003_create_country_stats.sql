-- Cached country statistics
CREATE TABLE IF NOT EXISTS country_stats (
    country_code VARCHAR(2) PRIMARY KEY REFERENCES countries(iso_code),
    article_count_24h INTEGER DEFAULT 0,
    article_count_7d INTEGER DEFAULT 0,
    article_count_30d INTEGER DEFAULT 0,
    avg_impact_score FLOAT,
    dominant_category VARCHAR(50),
    last_article_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_country_stats_updated ON country_stats(last_updated);
