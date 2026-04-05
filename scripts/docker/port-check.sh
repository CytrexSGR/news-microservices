#!/bin/bash
# Port availability checker
# Usage: ./scripts/docker/port-check.sh

set -e

echo "🔍 Checking port availability for news-microservices..."
echo ""

# Infrastructure ports
INFRA_PORTS=(5432 6379 5672 15672 9200)
INFRA_NAMES=("Postgres" "Redis" "RabbitMQ-AMQP" "RabbitMQ-Mgmt" "Elasticsearch")

# Service ports
SERVICE_PORTS=(8100 8101 8102 8103 8104 8105 8106 8107 8108 8109)
SERVICE_NAMES=("auth" "feed" "content-analysis" "research" "osint" "notification" "search" "analytics" "scheduler" "scraping")

# Gateway ports
GATEWAY_PORTS=(80 443 8180)
GATEWAY_NAMES=("HTTP" "HTTPS" "Traefik-Dashboard")

BLOCKED_COUNT=0

# Function to check single port
check_port() {
  local PORT=$1
  local NAME=$2

  if command -v lsof &> /dev/null; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
      echo "❌ Port $PORT ($NAME) is BLOCKED"
      PROCESS=$(lsof -ti:$PORT 2>/dev/null | head -1)
      if [ -n "$PROCESS" ]; then
        PROC_INFO=$(ps -p $PROCESS -o comm= 2>/dev/null || echo "unknown")
        echo "   Process: $PROC_INFO (PID: $PROCESS)"
        echo "   Kill with: sudo kill -9 $PROCESS"
      fi
      BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
      return 1
    else
      echo "✅ Port $PORT ($NAME) available"
      return 0
    fi
  elif command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":$PORT "; then
      echo "❌ Port $PORT ($NAME) is BLOCKED"
      BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
      return 1
    else
      echo "✅ Port $PORT ($NAME) available"
      return 0
    fi
  else
    echo "⚠️  Warning: Neither lsof nor netstat available, skipping port check"
    return 0
  fi
}

# Check infrastructure ports
echo "=== Infrastructure Ports ==="
for i in "${!INFRA_PORTS[@]}"; do
  check_port "${INFRA_PORTS[$i]}" "${INFRA_NAMES[$i]}"
done
echo ""

# Check service ports
echo "=== Service Ports (8100-8199) ==="
for i in "${!SERVICE_PORTS[@]}"; do
  check_port "${SERVICE_PORTS[$i]}" "${SERVICE_NAMES[$i]}"
done
echo ""

# Check gateway ports
echo "=== Gateway Ports ==="
for i in "${!GATEWAY_PORTS[@]}"; do
  check_port "${GATEWAY_PORTS[$i]}" "${GATEWAY_NAMES[$i]}"
done
echo ""

# Summary
echo "════════════════════════════════════════"
if [ $BLOCKED_COUNT -eq 0 ]; then
  echo "✅ SUCCESS: All ports available"
  echo "════════════════════════════════════════"
  echo ""
  echo "You can now start services:"
  echo "  docker-compose -f compose/base.yml -f compose/services.yml -f compose/dev.override.yml up -d"
  exit 0
else
  echo "❌ FAILED: $BLOCKED_COUNT port(s) blocked"
  echo "════════════════════════════════════════"
  echo ""
  echo "Fix blocked ports before starting Docker services."
  echo "See docs/docker/PORT_ALLOCATION.md for port table."
  exit 1
fi
