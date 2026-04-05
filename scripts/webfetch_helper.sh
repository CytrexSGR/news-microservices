#!/bin/bash
# WebFetch Helper - Automated external documentation fetching
# Usage: ./webfetch_helper.sh "topic" [category]

TOPIC="$1"
CATEGORY="${2:-general}"

echo "🌐 WebFetch Helper: Fetching documentation for '$TOPIC'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# URL mapping for common topics
declare -A DOCS_URLS

# Docker Documentation
DOCS_URLS["docker networking"]="https://docs.docker.com/network/bridge/"
DOCS_URLS["docker compose"]="https://docs.docker.com/compose/compose-file/"
DOCS_URLS["docker troubleshooting"]="https://docs.docker.com/config/daemon/"
DOCS_URLS["docker iptables"]="https://docs.docker.com/network/packet-filtering-firewalls/"

# Python/SQLAlchemy
DOCS_URLS["sqlalchemy connection"]="https://docs.sqlalchemy.org/en/20/core/pooling.html"
DOCS_URLS["sqlalchemy timeout"]="https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls"
DOCS_URLS["fastapi"]="https://fastapi.tiangolo.com/tutorial/sql-databases/"
DOCS_URLS["psycopg2 timeout"]="https://www.psycopg.org/docs/module.html#psycopg2.connect"

# PostgreSQL
DOCS_URLS["postgresql connection"]="https://www.postgresql.org/docs/current/libpq-connect.html"
DOCS_URLS["postgresql timeout"]="https://www.postgresql.org/docs/current/runtime-config-client.html"

# Redis
DOCS_URLS["redis connection"]="https://redis.io/docs/connect/clients/python/"
DOCS_URLS["redis timeout"]="https://redis-py.readthedocs.io/en/stable/connections.html"

# RabbitMQ
DOCS_URLS["rabbitmq"]="https://www.rabbitmq.com/docs/networking"

# Search for matching URL
FOUND=0
for key in "${!DOCS_URLS[@]}"; do
  if [[ "$TOPIC" == *"$key"* ]] || [[ "$key" == *"$TOPIC"* ]]; then
    URL="${DOCS_URLS[$key]}"
    echo "✅ Found documentation: $key"
    echo "🔗 URL: $URL"
    echo ""
    echo "💡 Claude Code can fetch this using:"
    echo "   WebFetch(\"$URL\", \"Explain ${TOPIC} configuration and troubleshooting\")"
    echo ""
    FOUND=1
    break
  fi
done

if [ $FOUND -eq 0 ]; then
  # Fallback: Generate search URLs
  echo "🔍 No direct match found. Suggested search resources:"
  echo ""

  # GitHub Issues search
  GITHUB_QUERY=$(echo "$TOPIC" | sed 's/ /+/g')
  echo "  📦 GitHub Issues (Docker):"
  echo "     https://github.com/moby/moby/issues?q=$GITHUB_QUERY"
  echo ""

  echo "  📚 Stack Overflow:"
  echo "     https://stackoverflow.com/search?q=$GITHUB_QUERY"
  echo ""

  echo "  📖 Official Docs Search:"
  echo "     https://docs.docker.com/search/?q=$GITHUB_QUERY"
  echo ""
fi

# Suggest Claude Code integration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Integration with Claude Code:"
echo ""
echo "   1. Copy the URL above"
echo "   2. In chat, mention: 'Fetch and analyze [URL]'"
echo "   3. Claude will use WebFetch tool automatically"
echo ""

# Cache common URLs
CACHE_FILE="/tmp/webfetch_cache.txt"
echo "$TOPIC|$URL|$(date)" >> "$CACHE_FILE"

echo "💾 URL cached for quick access"
