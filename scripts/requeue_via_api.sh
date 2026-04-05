#!/bin/bash
# Re-queue old articles by triggering manual fetch for all active feeds

echo "============================================"
echo "Re-queuing old articles for scraping"
echo "============================================"
echo ""

# Get list of active feeds
FEEDS=$(docker exec news-postgres psql -U news_user -d news_mcp -t -c "
SELECT id FROM feeds WHERE is_active = true AND scrape_full_content = true LIMIT 20;
" | tr -d ' ')

COUNT=0
for feed_id in $FEEDS; do
    if [ ! -z "$feed_id" ]; then
        echo "Triggering fetch for feed: $feed_id"
        curl -s -X POST "http://localhost:8101/api/v1/feeds/$feed_id/fetch" > /dev/null 2>&1

        COUNT=$((COUNT + 1))

        # Rate limit: wait 2 seconds between requests
        sleep 2
    fi
done

echo ""
echo "============================================"
echo "✅ Triggered fetch for $COUNT feeds"
echo "============================================"
