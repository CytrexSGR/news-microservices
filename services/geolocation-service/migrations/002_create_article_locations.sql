-- Article-to-country mapping
CREATE TABLE IF NOT EXISTS article_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    country_code VARCHAR(2) REFERENCES countries(iso_code),
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(20) DEFAULT 'entity_extraction',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(article_id, country_code)
);

CREATE INDEX IF NOT EXISTS idx_article_locations_country ON article_locations(country_code);
CREATE INDEX IF NOT EXISTS idx_article_locations_article ON article_locations(article_id);
CREATE INDEX IF NOT EXISTS idx_article_locations_created ON article_locations(created_at);
