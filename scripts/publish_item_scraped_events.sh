#!/bin/bash
# Publish item_scraped events for content analysis

FEED_ID="cceeea83-d487-406f-87d9-2758862aba45"

echo "Fetching articles with content from database..."
ARTICLES=$(PGPASSWORD=your_db_password psql -h localhost -U news_user -d news_mcp -t -A -F'|' -c "
  SELECT id, link, LENGTH(content) as char_count
  FROM feed_items
  WHERE feed_id = '$FEED_ID'
    AND content IS NOT NULL
    AND LENGTH(content) > 100
  ORDER BY created_at DESC;
")

COUNT=0
TOTAL=$(echo "$ARTICLES" | wc -l)

echo "Found $TOTAL articles with content. Publishing item_scraped events..."

while IFS='|' read -r ITEM_ID URL CHAR_COUNT; do
  if [ -z "$ITEM_ID" ] || [ -z "$URL" ]; then
    continue
  fi

  # Estimate word count (roughly char_count / 5)
  WORD_COUNT=$((CHAR_COUNT / 5))

  # Create JSON payload
  PAYLOAD_JSON=$(cat <<EOF
{
  "routing_key": "item_scraped",
  "payload": "{\"event_type\":\"item_scraped\",\"payload\":{\"feed_id\":\"$FEED_ID\",\"item_id\":\"$ITEM_ID\",\"url\":\"$URL\",\"word_count\":$WORD_COUNT,\"scrape_method\":\"httpx\",\"status\":\"success\"}}",
  "properties": {"content_type":"application/json"},
  "payload_encoding": "string"
}
EOF
)

  # Publish event
  RESULT=$(curl -s -u guest:guest -X POST "http://localhost:15672/api/exchanges/%2F/news.events/publish" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_JSON")

  if echo "$RESULT" | grep -q '"routed":true'; then
    COUNT=$((COUNT + 1))
    echo "[$COUNT/$TOTAL] ✓ Published item_scraped for $ITEM_ID (~$WORD_COUNT words)"
  else
    echo "[$COUNT/$TOTAL] ✗ Failed $ITEM_ID: $RESULT"
  fi

  sleep 0.2

done <<< "$ARTICLES"

echo ""
echo "✅ Published $COUNT/$TOTAL item_scraped events"
echo "Content analysis should now process these articles..."
echo "Monitor: docker compose logs content-analysis-service --follow"
