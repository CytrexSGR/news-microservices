#!/bin/bash
# Download Natural Earth country boundaries

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"

mkdir -p "$DATA_DIR"

echo "=========================================="
echo "Downloading Natural Earth country boundaries..."
echo "=========================================="

# Primary source: datasets/geo-countries (public domain)
curl -L -o "$DATA_DIR/countries.geojson" \
  "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

echo ""
echo "Download complete!"
echo "  File: $DATA_DIR/countries.geojson"
echo "  Size: $(ls -lh "$DATA_DIR/countries.geojson" | awk '{print $5}')"
echo ""

# Validate JSON
if python3 -c "import json; json.load(open('$DATA_DIR/countries.geojson'))" 2>/dev/null; then
    echo "  JSON validation: OK"
    FEATURE_COUNT=$(python3 -c "import json; print(len(json.load(open('$DATA_DIR/countries.geojson'))['features']))")
    echo "  Features: $FEATURE_COUNT countries"
else
    echo "  JSON validation: FAILED"
    exit 1
fi
