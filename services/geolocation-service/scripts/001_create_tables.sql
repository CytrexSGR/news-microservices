-- Geolocation Service Database Migration
-- Creates tables for geographic news visualization
-- Note: Uses JSONB for geometry instead of PostGIS for compatibility

-- Countries table with Natural Earth boundaries (GeoJSON stored as JSONB)
CREATE TABLE IF NOT EXISTS countries (
    iso_code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_de VARCHAR(100),
    region VARCHAR(50),
    subregion VARCHAR(50),
    centroid_lon FLOAT,
    centroid_lat FLOAT,
    boundary JSONB,  -- GeoJSON MultiPolygon stored as JSONB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for country queries
CREATE INDEX IF NOT EXISTS idx_countries_region ON countries (region);
CREATE INDEX IF NOT EXISTS idx_countries_name ON countries (name);

-- Article-to-country mapping
CREATE TABLE IF NOT EXISTS article_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL,
    country_code VARCHAR(2) REFERENCES countries(iso_code),
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(20) DEFAULT 'entity_extraction',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for article lookups
CREATE INDEX IF NOT EXISTS idx_article_locations_article_id ON article_locations (article_id);
CREATE INDEX IF NOT EXISTS idx_article_locations_country_code ON article_locations (country_code);
CREATE INDEX IF NOT EXISTS idx_article_locations_created_at ON article_locations (created_at DESC);

-- Cached country statistics
CREATE TABLE IF NOT EXISTS country_stats (
    country_code VARCHAR(2) PRIMARY KEY REFERENCES countries(iso_code),
    article_count_24h INTEGER DEFAULT 0,
    article_count_7d INTEGER DEFAULT 0,
    article_count_30d INTEGER DEFAULT 0,
    avg_impact_score FLOAT,
    dominant_category VARCHAR(50),
    last_article_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comment on tables
COMMENT ON TABLE countries IS 'Country boundaries from Natural Earth (GeoJSON as JSONB)';
COMMENT ON TABLE article_locations IS 'Mapping of articles to countries based on entity extraction';
COMMENT ON TABLE country_stats IS 'Cached statistics per country for fast dashboard queries';

-- Success message
SELECT 'Geolocation tables created successfully' AS status;
