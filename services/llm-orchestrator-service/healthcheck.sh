#!/bin/sh
# Enhanced health check for FastAPI services
# Validates both imports and HTTP endpoint
# Uses PORT environment variable (defaults to 8000)

PORT=${PORT:-8000}

# Step 1: Validate critical imports
python3 -c "from app.main import app" 2>/dev/null || exit 1

# Step 2: Check HTTP endpoint
curl -f "http://localhost:${PORT}/health" || exit 1

exit 0
