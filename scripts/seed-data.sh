#!/bin/bash
set -euo pipefail

# ============================================================================
# Database Seed Data Script
# ============================================================================
# Populates initial data for fresh database deployment
# Author: DevOps Engineer (Claude Flow Swarm)
# ============================================================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $*"
}

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-news_db}"
DB_USER="${DB_USER:-postgres}"

log "Seeding initial data..."

# Sample RSS feeds
docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" <<-EOSQL
    -- Sample feeds (if feeds table exists)
    INSERT INTO feeds (url, name, active, created_at)
    VALUES
        ('https://www.derstandard.at/rss', 'Der Standard', true, NOW()),
        ('https://orf.at/rss', 'ORF.at', true, NOW())
    ON CONFLICT (url) DO NOTHING;

    -- Sample categories (if categories table exists)
    INSERT INTO categories (name, slug, created_at)
    VALUES
        ('News', 'news', NOW()),
        ('Technology', 'tech', NOW()),
        ('Politics', 'politics', NOW())
    ON CONFLICT (slug) DO NOTHING;
EOSQL

log_success "Initial data seeded"
