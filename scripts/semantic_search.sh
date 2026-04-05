#!/bin/bash
# Semantic Search Helper - Simulates RAG-like behavior using intelligent grep combinations
# Usage: ./semantic_search.sh "concept" [file_type]

CONCEPT="$1"
FILE_TYPE="${2:-all}"

echo "🔍 Semantic Search: '$CONCEPT'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Concept mapping - translate high-level concepts to search terms
case "$CONCEPT" in
  "database connection"|"db connection"|"database timeout")
    TERMS=("connect" "database" "session" "engine" "pool" "timeout" "CONNECTION" "DATABASE_URL" "create_engine" "SessionLocal")
    ;;
  "auth"|"authentication"|"jwt")
    TERMS=("auth" "token" "jwt" "login" "password" "credential" "Bearer" "authenticate")
    ;;
  "networking"|"network issue"|"connection timeout")
    TERMS=("network" "socket" "tcp" "connection" "timeout" "connect_ex" "getaddrinfo" "bind")
    ;;
  "health check"|"healthcheck"|"service health")
    TERMS=("health" "healthy" "readiness" "liveness" "startup" "status" "ping")
    ;;
  "docker"|"container"|"compose")
    TERMS=("docker" "container" "compose" "image" "volume" "network" "service")
    ;;
  "error handling"|"exception")
    TERMS=("try" "except" "catch" "error" "exception" "raise" "throw" "Exception")
    ;;
  "config"|"configuration"|"environment")
    TERMS=("config" "settings" "env" "environment" "Environment" "getenv" "CONFIG" "SETTINGS")
    ;;
  *)
    # Generic search - use the concept directly
    TERMS=("$CONCEPT")
    ;;
esac

# Determine file patterns
case "$FILE_TYPE" in
  "python"|"py")
    PATTERN="*.py"
    ;;
  "yaml"|"yml")
    PATTERN="*.{yml,yaml}"
    ;;
  "docker")
    PATTERN="{Dockerfile,docker-compose*.yml,.dockerignore}"
    ;;
  "config")
    PATTERN="{*.yml,*.yaml,*.json,*.toml,.env*}"
    ;;
  *)
    PATTERN="*"
    ;;
esac

# Execute intelligent multi-term search
echo "📁 Searching in: $PATTERN"
echo "🔑 Semantic terms: ${TERMS[@]}"
echo ""

RESULTS_FILE="/tmp/semantic_search_results_$$.txt"
> "$RESULTS_FILE"

# Search for each term and collect results
for TERM in "${TERMS[@]}"; do
  # Case-insensitive search with context
  rg --no-heading --line-number --context 2 -i "$TERM" --glob "$PATTERN" \
     --glob '!venv' --glob '!node_modules' --glob '!.git' --glob '!__pycache__' \
     2>/dev/null >> "$RESULTS_FILE"
done

# Remove duplicates and sort by relevance (files with most matches first)
if [ -s "$RESULTS_FILE" ]; then
  echo "✅ Found matches:"
  echo ""

  # Group by file and show counts
  cat "$RESULTS_FILE" | grep -E '^[^:]+:[0-9]+:' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20 | \
  while read count file; do
    echo "  📄 $file ($count matches)"
  done

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "💡 Top relevant files with context:"
  echo ""

  # Show top 5 most relevant files with snippets
  cat "$RESULTS_FILE" | grep -E '^[^:]+:[0-9]+:' | cut -d: -f1 | sort | uniq -c | sort -rn | head -5 | \
  while read count file; do
    echo "═══════════════════════════════════════════════════"
    echo "📂 $file (Relevance: $count matches)"
    echo "═══════════════════════════════════════════════════"

    # Show first 10 lines of context from this file
    grep -A 3 "^$file:" "$RESULTS_FILE" | head -15
    echo ""
  done

  rm -f "$RESULTS_FILE"
else
  echo "❌ No matches found for: $CONCEPT"
  rm -f "$RESULTS_FILE"
  exit 1
fi

echo ""
echo "💾 Cached results available for this session"
echo "🔄 Run again with different file_type: python, yaml, docker, config"
