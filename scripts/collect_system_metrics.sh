#!/bin/bash
#
# System Health Metrics Collection
# Measures CPU, RAM, disk, Docker container resources
#

OUTPUT_DIR="reports/metrics/system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$OUTPUT_DIR/system-$TIMESTAMP.json"

mkdir -p "$OUTPUT_DIR"

echo "=== System Health Metrics ==="
echo "Timestamp: $(date)"
echo ""

# CPU Usage
echo "CPU Usage:"
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "  User: ${cpu_usage}%"

# Memory Usage
echo "Memory Usage:"
mem_total=$(free -m | awk 'NR==2{print $2}')
mem_used=$(free -m | awk 'NR==2{print $3}')
mem_percent=$(echo "scale=2; $mem_used / $mem_total * 100" | bc)
echo "  Used: ${mem_used}MB / ${mem_total}MB (${mem_percent}%)"

# Disk Usage
echo "Disk Usage:"
disk_usage=$(df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1)
disk_used=$(df -h / | awk 'NR==2{print $3}')
disk_total=$(df -h / | awk 'NR==2{print $2}')
echo "  Used: ${disk_used} / ${disk_total} (${disk_usage}%)"

# Docker Container Resources
echo ""
echo "Docker Container Resources:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -15

# Save to JSON
cat > "$RESULTS_FILE" << JSON
{
  "timestamp": "$(date -Iseconds)",
  "cpu": {
    "user_percent": $cpu_usage
  },
  "memory": {
    "total_mb": $mem_total,
    "used_mb": $mem_used,
    "percent": $mem_percent
  },
  "disk": {
    "used": "$disk_used",
    "total": "$disk_total",
    "percent": $disk_usage
  },
  "docker_containers": []
}
JSON

echo ""
echo "Results saved to: $RESULTS_FILE"
