#!/bin/bash
# Publish scraping events for all articles - CORRECT FORMAT

FEED_ID="cceeea83-d487-406f-87d9-2758862aba45"

echo "Fetching articles from database..."
ARTICLES=$(PGPASSWORD=your_db_password psql -h localhost -U news_user -d news_mcp -t -A -F'|' -c "SELECT id, link FROM feed_items WHERE feed_id = '$FEED_ID';")

COUNT=0
TOTAL=$(echo "$ARTICLES" | wc -l)

echo "Found $TOTAL articles. Publishing events..."

while IFS='|' read -r ITEM_ID URL; do
  if [ -z "$ITEM_ID" ] || [ -z "$URL" ]; then
    continue
  fi

  # Create correctly escaped JSON payload
  PAYLOAD_JSON=$(cat <<EOF
{
  "routing_key": "article.created",
  "payload": "{\"event_type\":\"article.created\",\"payload\":{\"feed_id\":\"$FEED_ID\",\"item_id\":\"$ITEM_ID\",\"url\":\"$URL\",\"scrape_method\":\"auto\"}}",
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
    echo "[$COUNT/$TOTAL] ✓ Published $ITEM_ID"
  else
    echo "[$COUNT/$TOTAL] ✗ Failed $ITEM_ID: $RESULT"
  fi

  # Small delay to not overwhelm the system
  sleep 0.5

done <<< "$ARTICLES"

echo ""
echo "✅ Published $COUNT/$TOTAL events successfully"
echo "Events are being processed by scraping-service..."
echo "Check progress: docker compose logs scraping-service --follow"
