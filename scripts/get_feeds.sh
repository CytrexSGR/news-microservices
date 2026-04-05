#!/bin/bash
# List all feeds
# Usage: ./scripts/get_feeds.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📰 Fetching feeds..."
"${SCRIPT_DIR}/api_call.sh" GET /api/v1/feeds | jq '.'
