#!/bin/bash
set -e

# Backfill Script for Unprocessed Articles
# Creates article.created events for articles that haven't been analyzed

DAYS=${1:-7}
BATCH_SIZE=${2:-100}
MODE=${3:-dry-run}

echo "================================"
echo "Backfill Unprocessed Articles"
echo "================================"
echo "Days to look back: $DAYS"
echo "Batch size: $BATCH_SIZE"
echo "Mode: $MODE"
echo ""

# Get statistics
echo "Getting statistics..."
docker exec -i postgres psql -U news_user -d news_mcp << EOF
SELECT
    COUNT(*) as total,
    COUNT(pe.id) as processed,
    COUNT(*) - COUNT(pe.id) as unprocessed,
    ROUND((COUNT(pe.id)::numeric / COUNT(*) * 100), 1) as coverage_pct
FROM feed_items fi
LEFT JOIN content_analysis_v2.pipeline_executions pe
    ON fi.id = pe.article_id AND pe.success = true
WHERE fi.created_at >= NOW() - INTERVAL '$DAYS days'
  AND fi.content IS NOT NULL
  AND LENGTH(fi.content) >= 10;
EOF

echo ""
echo "Getting sample of unprocessed articles..."
docker exec -i postgres psql -U news_user -d news_mcp << EOF
SELECT
    fi.id,
    LEFT(fi.title, 60) as title,
    fi.created_at::date as date,
    LENGTH(fi.content) as content_len
FROM feed_items fi
LEFT JOIN content_analysis_v2.pipeline_executions pe
    ON fi.id = pe.article_id AND pe.success = true
WHERE fi.created_at >= NOW() - INTERVAL '$DAYS days'
  AND pe.id IS NULL
  AND fi.content IS NOT NULL
  AND LENGTH(fi.content) >= 10
ORDER BY fi.created_at ASC
LIMIT 5;
EOF

if [ "$MODE" = "dry-run" ]; then
    echo ""
    echo "================================"
    echo "DRY RUN MODE - No changes made"
    echo "================================"

    # Count what would be inserted
    COUNT=$(docker exec -i postgres psql -U news_user -d news_mcp -t << EOF | xargs
SELECT COUNT(*)
FROM feed_items fi
LEFT JOIN content_analysis_v2.pipeline_executions pe
    ON fi.id = pe.article_id AND pe.success = true
WHERE fi.created_at >= NOW() - INTERVAL '$DAYS days'
  AND pe.id IS NULL
  AND fi.content IS NOT NULL
  AND LENGTH(fi.content) >= 10
LIMIT $BATCH_SIZE;
EOF
)

    echo "Would create $COUNT article.created events in outbox"
    echo ""
    echo "To execute, run:"
    echo "  $0 $DAYS $BATCH_SIZE execute"

elif [ "$MODE" = "execute" ]; then
    echo ""
    echo "================================"
    echo "EXECUTING BACKFILL"
    echo "================================"

    read -p "Create events in outbox? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Backfill cancelled"
        exit 0
    fi

    echo "Creating events..."

    # Insert events into outbox
    RESULT=$(docker exec -i postgres psql -U news_user -d news_mcp << EOF
WITH unprocessed AS (
    SELECT
        fi.id,
        fi.feed_id,
        fi.title,
        fi.link
    FROM feed_items fi
    LEFT JOIN content_analysis_v2.pipeline_executions pe
        ON fi.id = pe.article_id AND pe.success = true
    WHERE fi.created_at >= NOW() - INTERVAL '$DAYS days'
      AND pe.id IS NULL
      AND fi.content IS NOT NULL
      AND LENGTH(fi.content) >= 10
    ORDER BY fi.created_at ASC
    LIMIT $BATCH_SIZE
),
inserted AS (
    INSERT INTO event_outbox (event_type, payload, status, created_at)
    SELECT
        'article.created',
        jsonb_build_object(
            'item_id', id::text,
            'feed_id', feed_id::text,
            'title', title,
            'link', link,
            'has_content', true,
            'backfill', true
        ),
        'pending',
        NOW()
    FROM unprocessed
    RETURNING id
)
SELECT COUNT(*) FROM inserted;
EOF
)

    EVENTS_CREATED=$(echo "$RESULT" | tail -2 | head -1 | xargs)

    echo ""
    echo "✓ Backfill complete!"
    echo "  Events created: $EVENTS_CREATED"
    echo "  Processing will begin within ~5 seconds (next outbox run)"

    # Show outbox status
    echo ""
    echo "Current outbox status:"
    docker exec -i postgres psql -U news_user -d news_mcp << EOF
SELECT
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM event_outbox
WHERE event_type = 'article.created'
  AND created_at >= NOW() - INTERVAL '1 hour'
GROUP BY status
ORDER BY status;
EOF

else
    echo "Invalid mode: $MODE"
    echo "Use 'dry-run' or 'execute'"
    exit 1
fi
