#!/bin/bash
# Authenticated API Call Helper
# Usage: ./scripts/api_call.sh <METHOD> <ENDPOINT> [DATA]
#
# Examples:
#   ./scripts/api_call.sh POST /api/v1/admin/reindex
#   ./scripts/api_call.sh GET /api/v1/feeds
#   ./scripts/api_call.sh POST /api/v1/feeds '{"url":"https://example.com/feed"}'

set -e

# Configuration
AUTH_SERVICE="http://localhost:8100"
USERNAME="andreas"
PASSWORD="Aug2012#"

# Arguments
METHOD="${1:-GET}"
ENDPOINT="$2"
DATA="${3:-}"

if [ -z "$ENDPOINT" ]; then
    echo "Error: Endpoint required"
    echo "Usage: $0 <METHOD> <ENDPOINT> [DATA]"
    exit 1
fi

# Get token
echo "🔐 Authenticating..." >&2
TOKEN=$(curl -s -X POST "${AUTH_SERVICE}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Authentication failed" >&2
    exit 1
fi

echo "✅ Authenticated" >&2

# Detect service from endpoint
if [[ "$ENDPOINT" =~ ^/api/v1/admin ]]; then
    SERVICE="http://localhost:8106"  # Search service
elif [[ "$ENDPOINT" =~ ^/api/v1/feeds ]]; then
    SERVICE="http://localhost:8101"  # Feed service
elif [[ "$ENDPOINT" =~ ^/api/v1/articles ]]; then
    SERVICE="http://localhost:8102"  # Content Analysis
elif [[ "$ENDPOINT" =~ ^/api/v1/research ]]; then
    SERVICE="http://localhost:8103"  # Research service
elif [[ "$ENDPOINT" =~ ^/api/v1/osint ]]; then
    SERVICE="http://localhost:8104"  # OSINT service
elif [[ "$ENDPOINT" =~ ^/api/v1/notifications ]]; then
    SERVICE="http://localhost:8105"  # Notification service
elif [[ "$ENDPOINT" =~ ^/api/v1/analytics ]]; then
    SERVICE="http://localhost:8107"  # Analytics service
else
    SERVICE="http://localhost:8100"  # Default to auth service
fi

# Make API call
echo "📡 Calling ${METHOD} ${SERVICE}${ENDPOINT}" >&2

if [ -n "$DATA" ]; then
    curl -s -X "$METHOD" "${SERVICE}${ENDPOINT}" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$DATA"
else
    curl -s -X "$METHOD" "${SERVICE}${ENDPOINT}" \
        -H "Authorization: Bearer $TOKEN"
fi
