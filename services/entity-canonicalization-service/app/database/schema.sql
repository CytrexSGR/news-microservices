-- Entity Canonicalization Service - Database Schema
-- PostgreSQL Schema for alias storage and entity canonicalization

-- Canonical entities table
CREATE TABLE IF NOT EXISTS canonical_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    wikidata_id VARCHAR(50),
    type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

    CONSTRAINT unique_canonical_name_type UNIQUE(name, type)
);

CREATE INDEX IF NOT EXISTS idx_canonical_type ON canonical_entities(type);
CREATE INDEX IF NOT EXISTS idx_wikidata_id ON canonical_entities(wikidata_id);

-- Entity aliases table
CREATE TABLE IF NOT EXISTS entity_aliases (
    id SERIAL PRIMARY KEY,
    canonical_id INTEGER NOT NULL REFERENCES canonical_entities(id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    CONSTRAINT unique_alias UNIQUE(alias)
);

CREATE INDEX IF NOT EXISTS idx_alias ON entity_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_canonical_id ON entity_aliases(canonical_id);

-- Statistics table
CREATE TABLE IF NOT EXISTS canonicalization_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_entities INTEGER DEFAULT 0 NOT NULL,
    total_aliases INTEGER DEFAULT 0 NOT NULL,
    wikidata_linked INTEGER DEFAULT 0 NOT NULL,

    CONSTRAINT unique_stat_date UNIQUE(date)
);

CREATE INDEX IF NOT EXISTS idx_stat_date ON canonicalization_stats(date);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_canonical_entities_updated_at
    BEFORE UPDATE ON canonical_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
