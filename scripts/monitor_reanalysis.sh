#!/bin/bash
#
# Monitor re-analysis progress in real-time
#
# Usage: ./scripts/monitor_reanalysis.sh [interval_seconds]
#
# ⚠️ DUAL-TABLE ARCHITECTURE WARNING ⚠️
# =====================================
# This script monitors the LEGACY table: content_analysis_v2.pipeline_executions
# NOT the unified table: public.article_analysis
#
# WHY: Frontend reads from legacy table (via content-analysis-v2 API proxy).
# The unified table exists but is NEVER READ by any service (orphaned data).
#
# See: POSTMORTEMS.md - Incident #8 for full analysis
# Related: services/feed-service/app/services/analysis_loader.py (reads legacy)
#          services/feed-service/app/workers/analysis_consumer.py (writes unified)
#
# Last Updated: 2025-10-31

INTERVAL=${1:-5}  # Default: refresh every 5 seconds

echo "=========================================="
echo "RE-ANALYSIS PROGRESS MONITOR"
echo "=========================================="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=========================================="
    echo "RE-ANALYSIS PROGRESS - $(date '+%H:%M:%S')"
    echo "=========================================="
    echo ""

    # Count new analyses (last 10 minutes)
    echo "📊 Analyses Completed (last 10 min):"
    docker exec postgres psql -U news_user -d news_mcp -t -A -c "
        SELECT COUNT(*)
        FROM article_analysis
        WHERE created_at > NOW() - INTERVAL '10 minutes'
    "
    echo ""

    # Still missing (ANY DATE)
    echo "📝 Articles Still Missing Analysis (ALL DATES):"
    docker exec postgres psql -U news_user -d news_mcp -t -A -c "
        SELECT COUNT(*)
        FROM feed_items fi
        LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
        WHERE pe.id IS NULL
    "
    echo ""

    # Breakdown by date
    echo "📅 Missing by Date:"
    docker exec postgres psql -U news_user -d news_mcp -c "
        SELECT
            fi.created_at::date as date,
            COUNT(*) as missing
        FROM feed_items fi
        LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
        WHERE pe.id IS NULL
        GROUP BY date
        ORDER BY date DESC
        LIMIT 5
    " | tail -n +3 | head -n 7
    echo ""

    # Outbox status
    echo "📬 Outbox Events:"
    docker exec postgres psql -U news_user -d news_mcp -c "
        SELECT status, COUNT(*)
        FROM event_outbox
        WHERE created_at > NOW() - INTERVAL '10 minutes'
        GROUP BY status
        ORDER BY status
    " | tail -n +3
    echo ""

    # Worker status (last 30 seconds)
    echo "⚙️  Content Analysis Workers (last 30s):"
    docker logs news-microservices-content-analysis-v2-1 2>&1 \
        | grep "Pipeline complete" \
        | tail -3 \
        | awk '{print "  - " $0}' 2>/dev/null || echo "  (checking...)"
    echo ""

    # Consumer status (last 30 seconds)
    echo "💾 Analysis Consumer (last 30s):"
    docker logs news-feed-service-analysis-consumer 2>&1 \
        | grep "Stored analysis" \
        | tail -3 \
        | awk '{print "  - " $0}' 2>/dev/null || echo "  (checking...)"
    echo ""

    echo "Refreshing in ${INTERVAL}s... (Ctrl+C to stop)"
    sleep "$INTERVAL"
done
