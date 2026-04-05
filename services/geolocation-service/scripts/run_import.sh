#!/bin/bash
# Run the complete country data import

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_URL="${1:-postgresql://postgres:postgres@localhost:5432/news_intelligence}"

echo "=========================================="
echo "Geo News Map - Country Data Import"
echo "=========================================="
echo ""
echo "Database: $DB_URL"
echo ""

# Step 1: Download data if not exists
if [ ! -f "$SCRIPT_DIR/../data/countries.geojson" ]; then
    echo "Step 1: Downloading country data..."
    bash "$SCRIPT_DIR/download_data.sh"
else
    echo "Step 1: Country data already exists, skipping download"
    echo "  File: $SCRIPT_DIR/../data/countries.geojson"
fi
echo ""

# Step 2: Check PostGIS extension
echo "Step 2: Verifying PostGIS extension..."
POSTGIS_CHECK=$(psql "$DB_URL" -t -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');" 2>/dev/null || echo "false")
if [[ "$POSTGIS_CHECK" == *"t"* ]]; then
    echo "  PostGIS extension: OK"
else
    echo "  PostGIS extension: NOT FOUND"
    echo "  Run: CREATE EXTENSION IF NOT EXISTS postgis;"
    echo ""
fi
echo ""

# Step 3: Import countries
echo "Step 3: Importing countries..."
python3 "$SCRIPT_DIR/import_countries.py" "$DB_URL"
echo ""

# Step 4: Enrich German names
echo "Step 4: Enriching with German names..."
python3 "$SCRIPT_DIR/enrich_german_names.py" "$DB_URL"
echo ""

# Step 5: Initialize stats
echo "Step 5: Initializing country stats..."
psql "$DB_URL" -f "$SCRIPT_DIR/init_country_stats.sql"
echo ""

# Step 6: Summary
echo "=========================================="
echo "Import Summary"
echo "=========================================="
psql "$DB_URL" -c "
SELECT
    region,
    COUNT(*) as countries,
    COUNT(name_de) as with_german_name
FROM countries
GROUP BY region
ORDER BY region;
"

echo ""
echo "=========================================="
echo "Import complete!"
echo "=========================================="
