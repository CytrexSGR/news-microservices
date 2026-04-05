#!/bin/bash
# Trigger search index rebuild
# Usage: ./scripts/reindex_search.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Triggering search reindex..."
"${SCRIPT_DIR}/api_call.sh" POST /api/v1/admin/reindex | jq '.'
