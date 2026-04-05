#!/bin/bash
# Publish scraping events for all articles in a feed

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

  # Create JSON payload
  PAYLOAD=$(cat <<EOF
{
  "routing_key": "article.created",
  "payload": "{\"event_type\":\"article.created\",\"payload\":{\"feed_id\":\"$FEED_ID\",\"item_id\":\"$ITEM_ID\",\"url\":\"$URL\",\"scrape_method\":\"auto\"},\"correlation_id\":\"$ITEM_ID\"}",
  "properties": {}
}
EOF
)

  # Publish via RabbitMQ Management API
  curl -s -u guest:guest -X POST "http://localhost:15672/api/exchanges/%2F/news.events/publish" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" > /dev/null

  COUNT=$((COUNT + 1))
  echo "[$COUNT/$TOTAL] Published event for article $ITEM_ID"
  sleep 0.1

done <<< "$ARTICLES"

echo ""
echo "✅ Published $COUNT scraping events"
