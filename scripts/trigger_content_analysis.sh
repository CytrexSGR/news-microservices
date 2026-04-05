#!/bin/bash
# Trigger content analysis for all articles with scraped content

FEED_ID="cceeea83-d487-406f-87d9-2758862aba45"

echo "Fetching articles with content from database..."
ARTICLES=$(PGPASSWORD=your_db_password psql -h localhost -U news_user -d news_mcp -t -A -F'|' -c "
  SELECT id, link
  FROM feed_items
  WHERE feed_id = '$FEED_ID'
    AND content IS NOT NULL
    AND LENGTH(content) > 100;
")

COUNT=0
TOTAL=$(echo "$ARTICLES" | wc -l)

echo "Found $TOTAL articles with content. Publishing article.updated events for analysis..."

while IFS='|' read -r ITEM_ID URL; do
  if [ -z "$ITEM_ID" ] || [ -z "$URL" ]; then
    continue
  fi

  # Create JSON payload for article.updated event
  PAYLOAD_JSON=$(cat <<EOF
{
  "routing_key": "article.updated",
  "payload": "{\"event_type\":\"article.updated\",\"payload\":{\"feed_id\":\"$FEED_ID\",\"item_id\":\"$ITEM_ID\",\"url\":\"$URL\",\"updated_fields\":[\"content\"]}}",
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
    echo "[$COUNT/$TOTAL] ✓ Triggered analysis for $ITEM_ID"
  else
    echo "[$COUNT/$TOTAL] ✗ Failed $ITEM_ID: $RESULT"
  fi

  sleep 0.3

done <<< "$ARTICLES"

echo ""
echo "✅ Triggered analysis for $COUNT/$TOTAL articles"
echo "Check progress: docker compose logs content-analysis-service --follow"
