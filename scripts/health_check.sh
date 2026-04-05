#!/bin/bash
#
# Health Check Tool - News Microservices
# Checks all services, databases, and infrastructure
#

set -e

OUTPUT_DIR="reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JSON_REPORT="$OUTPUT_DIR/health-check-$TIMESTAMP.json"
MD_REPORT="$OUTPUT_DIR/health-check-$TIMESTAMP.md"

mkdir -p "$OUTPUT_DIR"

echo "=== Health Check Starting ==="
echo "Timestamp: $(date)"
echo ""

# Initialize JSON structure
cat > "$JSON_REPORT" << 'JSON'
{
  "timestamp": "TIMESTAMP_PLACEHOLDER",
  "overall_status": "unknown",
  "services": {},
  "databases": {},
  "infrastructure": {}
}
JSON

sed -i "s/TIMESTAMP_PLACEHOLDER/$(date -Iseconds)/" "$JSON_REPORT"

# Function to check docker service health
check_docker_services() {
  echo "=== Checking Docker Services ==="

  local total=0
  local healthy=0
  local unhealthy=0
  local stopped=0

  while IFS= read -r line; do
    name=$(echo "$line" | awk '{print $1}')
    status=$(echo "$line" | awk '{print $2}')

    total=$((total + 1))

    if [[ "$status" == *"Up"* && "$status" != *"unhealthy"* ]]; then
      healthy=$((healthy + 1))
      echo "  ✅ $name: healthy"
    elif [[ "$status" == *"unhealthy"* ]]; then
      unhealthy=$((unhealthy + 1))
      echo "  ❌ $name: UNHEALTHY"
    else
      stopped=$((stopped + 1))
      echo "  ⚠️  $name: stopped"
    fi
  done < <(docker compose ps --format "table {{.Name}}\t{{.Status}}" | tail -n +2)

  echo ""
  echo "Total: $total | Healthy: $healthy | Unhealthy: $unhealthy | Stopped: $stopped"
  echo ""

  # Update JSON
  jq --arg total "$total" \
     --arg healthy "$healthy" \
     --arg unhealthy "$unhealthy" \
     '.services.total = ($total | tonumber) |
      .services.healthy = ($healthy | tonumber) |
      .services.unhealthy = ($unhealthy | tonumber)' \
     "$JSON_REPORT" > "$JSON_REPORT.tmp" && mv "$JSON_REPORT.tmp" "$JSON_REPORT"

  return $unhealthy
}

# Function to check databases
check_databases() {
  echo "=== Checking Databases ==="

  local db_healthy=0
  local db_failed=0

  # PostgreSQL
  if docker exec postgres psql -U news_user -d news_mcp -c "SELECT 1" > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL: healthy"
    db_healthy=$((db_healthy + 1))
  else
    echo "  ❌ PostgreSQL: FAILED"
    db_failed=$((db_failed + 1))
  fi

  # Redis
  if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis: healthy"
    db_healthy=$((db_healthy + 1))
  else
    echo "  ❌ Redis: FAILED"
    db_failed=$((db_failed + 1))
  fi

  # Neo4j (if running)
  if docker ps --format "{{.Names}}" | grep -q neo4j; then
    if docker exec neo4j cypher-shell "RETURN 1" -u neo4j -p news_neo4j_2024 > /dev/null 2>&1; then
      echo "  ✅ Neo4j: healthy"
      db_healthy=$((db_healthy + 1))
    else
      echo "  ❌ Neo4j: FAILED"
      db_failed=$((db_failed + 1))
    fi
  else
    echo "  ⚠️  Neo4j: not running"
  fi

  echo ""
  echo "Databases: $db_healthy healthy, $db_failed failed"
  echo ""

  # Update JSON
  jq --arg healthy "$db_healthy" \
     --arg failed "$db_failed" \
     '.databases.healthy = ($healthy | tonumber) |
      .databases.failed = ($failed | tonumber)' \
     "$JSON_REPORT" > "$JSON_REPORT.tmp" && mv "$JSON_REPORT.tmp" "$JSON_REPORT"

  return $db_failed
}

# Function to check infrastructure components
check_infrastructure() {
  echo "=== Checking Infrastructure ==="

  local infra_healthy=0
  local infra_failed=0

  # RabbitMQ
  if curl -s -u guest:guest http://localhost:15672/api/overview > /dev/null 2>&1; then
    echo "  ✅ RabbitMQ Management: healthy"

    # Check queue depths
    queue_count=$(curl -s -u guest:guest http://localhost:15672/api/queues | jq 'length')
    total_messages=$(curl -s -u guest:guest http://localhost:15672/api/queues | jq '[.[].messages] | add')
    echo "     Queues: $queue_count, Total Messages: $total_messages"

    infra_healthy=$((infra_healthy + 1))
  else
    echo "  ❌ RabbitMQ Management: FAILED"
    infra_failed=$((infra_failed + 1))
  fi

  # n8n
  if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "  ✅ n8n: healthy"
    infra_healthy=$((infra_healthy + 1))
  else
    echo "  ❌ n8n: FAILED"
    infra_failed=$((infra_failed + 1))
  fi

  # Frontend
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✅ Frontend: responding"
    infra_healthy=$((infra_healthy + 1))
  else
    echo "  ❌ Frontend: FAILED"
    infra_failed=$((infra_failed + 1))
  fi

  echo ""
  echo "Infrastructure: $infra_healthy healthy, $infra_failed failed"
  echo ""

  # Update JSON
  jq --arg healthy "$infra_healthy" \
     --arg failed "$infra_failed" \
     '.infrastructure.healthy = ($healthy | tonumber) |
      .infrastructure.failed = ($failed | tonumber)' \
     "$JSON_REPORT" > "$JSON_REPORT.tmp" && mv "$JSON_REPORT.tmp" "$JSON_REPORT"

  return $infra_failed
}

# Function to generate Markdown report
generate_markdown_report() {
  cat > "$MD_REPORT" << MDEOF
# Health Check Report

**Timestamp:** $(date)
**Overall Status:** $(jq -r '.overall_status' "$JSON_REPORT")

---

## Services

- **Total:** $(jq -r '.services.total' "$JSON_REPORT")
- **Healthy:** $(jq -r '.services.healthy' "$JSON_REPORT")
- **Unhealthy:** $(jq -r '.services.unhealthy' "$JSON_REPORT")

## Databases

- **Healthy:** $(jq -r '.databases.healthy' "$JSON_REPORT")
- **Failed:** $(jq -r '.databases.failed' "$JSON_REPORT")

## Infrastructure

- **Healthy:** $(jq -r '.infrastructure.healthy' "$JSON_REPORT")
- **Failed:** $(jq -r '.infrastructure.failed' "$JSON_REPORT")

---

**Generated:** $(date)
MDEOF
}

# Main execution
main() {
  local services_failed=0
  local db_failed=0
  local infra_failed=0

  check_docker_services || services_failed=$?
  check_databases || db_failed=$?
  check_infrastructure || infra_failed=$?

  # Calculate overall status
  local total_failed=$((services_failed + db_failed + infra_failed))

  if [ $total_failed -eq 0 ]; then
    overall_status="✅ ALL HEALTHY"
    jq '.overall_status = "healthy"' "$JSON_REPORT" > "$JSON_REPORT.tmp" && mv "$JSON_REPORT.tmp" "$JSON_REPORT"
  else
    overall_status="❌ ISSUES DETECTED: $total_failed problems"
    jq '.overall_status = "unhealthy"' "$JSON_REPORT" > "$JSON_REPORT.tmp" && mv "$JSON_REPORT.tmp" "$JSON_REPORT"
  fi

  echo "==================================="
  echo "OVERALL STATUS: $overall_status"
  echo "==================================="
  echo ""
  echo "Reports generated:"
  echo "  JSON: $JSON_REPORT"
  echo "  Markdown: $MD_REPORT"

  # Generate Markdown report
  generate_markdown_report

  # Exit with appropriate code
  if [ $total_failed -gt 0 ]; then
    exit 1
  else
    exit 0
  fi
}

# Run main
main
