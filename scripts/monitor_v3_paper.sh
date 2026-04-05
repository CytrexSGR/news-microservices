#!/bin/bash
# V3 Paper Trading Monitor
# Usage: ./scripts/monitor_v3_paper.sh [interval_seconds]

INTERVAL=${1:-30}

TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "andreas", "password": "Aug2012#"}' | jq -r '.access_token')

echo "=========================================="
echo "  V3 Paper Trading Monitor"
echo "  Started: $(date)"
echo "  Refresh: ${INTERVAL}s"
echo "=========================================="

while true; do
    clear
    echo "=========================================="
    echo "  V3 Paper Trading Monitor - $(date '+%H:%M:%S')"
    echo "=========================================="

    echo ""
    echo "=== Kelly Mode ==="
    curl -s http://localhost:8116/api/v1/ml/live/kelly/status | jq -c '{mode, ultra_high: .current_sizes.ultra_high, low: .current_sizes.low}'

    echo ""
    echo "=== Sessions Status ==="
    curl -s http://localhost:8116/api/v1/paper-trading/sessions \
      -H "Authorization: Bearer $TOKEN" | jq -r '.sessions[] | "\(.symbol): PnL=\(.pnl_percent)% Trades=\(.trades) Position=\(.current_position // "none")"'

    echo ""
    echo "=== Latest Paper Trades (last 5) ==="
    curl -s "http://localhost:8116/api/v1/ml/paper-trades?limit=5" \
      -H "Authorization: Bearer $TOKEN" | jq -r '.trades[] | select(.reasoning | contains("V2-BASELINE") | not) | "\(.created_at | split("T")[1][:8]) \(.symbol) \(.action) \(.status) PnL=\(.pnl_pct // "open")%"'

    echo ""
    echo "=== Service Logs (V3 Features) ==="
    docker logs news-prediction-service --tail 10 2>&1 | grep -E "EMERGENCY|KELLY|TCA|NET_PROFIT|V3" | tail -5

    echo ""
    echo "Press Ctrl+C to exit..."
    sleep $INTERVAL
done
