#!/bin/bash
# Context Cache - Simulates RAG caching for frequently accessed patterns
# Usage: ./context_cache.sh [action] [key] [value]

CACHE_DIR="/tmp/claude_context_cache"
mkdir -p "$CACHE_DIR"

ACTION="${1:-list}"
KEY="$2"
VALUE="$3"

case "$ACTION" in
  "store")
    if [ -z "$KEY" ] || [ -z "$VALUE" ]; then
      echo "❌ Usage: $0 store <key> <value>"
      exit 1
    fi

    CACHE_FILE="$CACHE_DIR/$(echo "$KEY" | tr ' ' '_').cache"
    echo "$VALUE" > "$CACHE_FILE"
    echo "$(date)" >> "$CACHE_FILE"

    echo "✅ Cached: $KEY"
    echo "📁 Location: $CACHE_FILE"
    ;;

  "get")
    if [ -z "$KEY" ]; then
      echo "❌ Usage: $0 get <key>"
      exit 1
    fi

    CACHE_FILE="$CACHE_DIR/$(echo "$KEY" | tr ' ' '_').cache"

    if [ -f "$CACHE_FILE" ]; then
      echo "✅ Cache hit: $KEY"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      head -n -1 "$CACHE_FILE"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "📅 Cached: $(tail -n 1 "$CACHE_FILE")"
    else
      echo "❌ Cache miss: $KEY"
      echo "💡 No cached data found for this query"
    fi
    ;;

  "list")
    echo "📋 Cached Context Items:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -d "$CACHE_DIR" ] && [ -n "$(ls -A "$CACHE_DIR" 2>/dev/null)" ]; then
      ls -lt "$CACHE_DIR"/*.cache 2>/dev/null | \
      while read -r line; do
        file=$(echo "$line" | awk '{print $NF}')
        key=$(basename "$file" .cache | tr '_' ' ')
        date=$(tail -n 1 "$file")
        echo "  📦 $key"
        echo "     └─ Cached: $date"
        echo ""
      done
    else
      echo "  (empty)"
    fi
    ;;

  "clear")
    rm -rf "$CACHE_DIR"/*.cache 2>/dev/null
    echo "✅ Cache cleared"
    ;;

  "stats")
    echo "📊 Cache Statistics:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    TOTAL=$(ls -1 "$CACHE_DIR"/*.cache 2>/dev/null | wc -l)
    SIZE=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)

    echo "  📦 Total items: $TOTAL"
    echo "  💾 Cache size: $SIZE"
    echo "  📁 Location: $CACHE_DIR"
    ;;

  *)
    echo "❌ Unknown action: $ACTION"
    echo ""
    echo "Available actions:"
    echo "  store <key> <value> : Store context in cache"
    echo "  get <key>           : Retrieve cached context"
    echo "  list                : List all cached items"
    echo "  clear               : Clear all cache"
    echo "  stats               : Show cache statistics"
    ;;
esac
