-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Countries with boundaries
CREATE TABLE IF NOT EXISTS countries (
    iso_code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_de VARCHAR(100),
    region VARCHAR(50),
    subregion VARCHAR(50),
    centroid GEOMETRY(POINT, 4326),
    boundary GEOMETRY(MULTIPOLYGON, 4326),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_countries_region ON countries(region);
CREATE INDEX IF NOT EXISTS idx_countries_centroid ON countries USING GIST(centroid);
CREATE INDEX IF NOT EXISTS idx_countries_boundary ON countries USING GIST(boundary);
