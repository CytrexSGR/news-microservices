#!/bin/bash
# Auto-update DATABASE_ARCHITECTURE.md with latest stats
# Usage: ./scripts/update-database-docs.sh

set -e

DOCS_FILE="./docs/DATABASE_ARCHITECTURE.md"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "🔄 Updating DATABASE_ARCHITECTURE.md..."

# Check if database is running
if ! docker exec news-postgres psql -U news_user -d postgres -c "SELECT 1" &>/dev/null; then
    echo "❌ Error: PostgreSQL container not running or not accessible"
    exit 1
fi

# Get current statistics
echo "📊 Fetching current statistics..."

FEEDS=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feeds;" | xargs)
ACTIVE_FEEDS=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feeds WHERE is_active = true;" | xargs)
ARTICLES=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feed_items;" | xargs)
ARTICLES_24H=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feed_items WHERE published_at >= NOW() - INTERVAL '24 hours';" | xargs)
ANALYZED=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(DISTINCT article_id) FROM analysis_results;" | xargs)

DB_SIZE=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT pg_size_pretty(pg_database_size('news_mcp'));" | xargs)
TOTAL_SIZE=$(docker exec news-postgres du -sh /var/lib/postgresql/data 2>/dev/null | cut -f1)

# Update the documentation
echo "✍️  Updating documentation..."

# Update header stats
sed -i "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" "$DOCS_FILE"
sed -i "s/\*\*Database Size:\*\*.*/\*\*Database Size:\*\* $TOTAL_SIZE/" "$DOCS_FILE"
sed -i "s/\*\*Active Articles:\*\*.*/\*\*Active Articles:\*\* $ARTICLES/" "$DOCS_FILE"
sed -i "s/\*\*Active Feeds:\*\*.*/\*\*Active Feeds:\*\* $ACTIVE_FEEDS/" "$DOCS_FILE"

# Update the data distribution table
sed -i "s/\*\*Size:\*\* [0-9.]* MB/\*\*Size:\*\* $DB_SIZE/" "$DOCS_FILE"
sed -i "s/\*\*Total Size:\*\* [0-9.]* MB/\*\*Total Size:\*\* $TOTAL_SIZE/" "$DOCS_FILE"

# Update key statistics
sed -i "s/- Total Feeds: [0-9]*/- Total Feeds: $FEEDS/" "$DOCS_FILE"
sed -i "s/- Total Articles: [0-9]*/- Total Articles: $ARTICLES/" "$DOCS_FILE"
sed -i "s/- Last 24h: [0-9]* articles/- Last 24h: $ARTICLES_24H articles/" "$DOCS_FILE"
sed -i "s/- Analyzed: [0-9]* articles/- Analyzed: $ANALYZED articles/" "$DOCS_FILE"

echo ""
echo "✅ Documentation updated successfully!"
echo ""
echo "📈 Current Statistics:"
echo "   Feeds:        $FEEDS (Active: $ACTIVE_FEEDS)"
echo "   Articles:     $ARTICLES"
echo "   Last 24h:     $ARTICLES_24H"
echo "   Analyzed:     $ANALYZED"
echo "   news_mcp:     $DB_SIZE"
echo "   Total:        $TOTAL_SIZE"
echo ""
echo "📝 File: $DOCS_FILE"
echo "🕐 Updated: $TIMESTAMP"

# Store update in memory for Claude Flow
if command -v npx &> /dev/null; then
    npx claude-flow@alpha hooks post-edit \
        --file "$DOCS_FILE" \
        --memory-key "news-microservices/docs/database-architecture-updated" \
        2>/dev/null || true
fi
