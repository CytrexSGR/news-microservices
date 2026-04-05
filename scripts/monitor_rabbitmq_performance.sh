#!/bin/bash
# RabbitMQ Performance Monitoring Script
# Created: 2025-10-31
# Task: 405 - RabbitMQ Optimization
#
# Usage:
#   ./scripts/monitor_rabbitmq_performance.sh [interval]
#
# Arguments:
#   interval - Monitoring interval in seconds (default: 10)
#
# Example:
#   ./scripts/monitor_rabbitmq_performance.sh 5

INTERVAL=${1:-10}

echo "==================================================================="
echo "RabbitMQ Performance Monitor (Task 405)"
echo "==================================================================="
echo "Monitoring interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo ""

# Function to get timestamp
timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

# Function to get queue stats
get_queue_stats() {
  docker exec rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged consumers 2>/dev/null | \
    awk 'NR>1 && NR<(NF-1) {
      printf "%-35s | Messages: %4d | Ready: %4d | Unacked: %4d | Consumers: %2d\n", $1, $2, $3, $4, $5
    }'
}

# Function to get connection count
get_connection_count() {
  docker exec rabbitmq rabbitmqctl list_connections 2>/dev/null | wc -l
}

# Main monitoring loop
while true; do
  echo "==================================================================="
  echo "📊 Timestamp: $(timestamp)"
  echo "==================================================================="

  # Queue statistics
  echo ""
  echo "📋 Queue Statistics:"
  echo "-------------------------------------------------------------------"
  get_queue_stats

  # Connection count
  echo ""
  echo "🔌 Active Connections: $(get_connection_count)"

  # Critical metrics
  echo ""
  echo "🎯 Critical Metrics:"
  echo "-------------------------------------------------------------------"

  # Check for queue buildup (> 100 messages)
  BACKLOG=$(docker exec rabbitmq rabbitmqctl list_queues messages 2>/dev/null | \
    awk 'NR>1 && $2>100 {count++} END {print count+0}')

  if [ "$BACKLOG" -gt 0 ]; then
    echo "⚠️  WARNING: $BACKLOG queue(s) have > 100 messages (backlog detected)"
  else
    echo "✅ No queue backlogs (all queues < 100 messages)"
  fi

  # Check for queues with no consumers
  NO_CONSUMERS=$(docker exec rabbitmq rabbitmqctl list_queues name consumers 2>/dev/null | \
    awk 'NR>1 && $2==0 && $1!~/dlq/ {count++} END {print count+0}')

  if [ "$NO_CONSUMERS" -gt 0 ]; then
    echo "⚠️  WARNING: $NO_CONSUMERS queue(s) have no consumers"
  else
    echo "✅ All queues have active consumers"
  fi

  # Check Dead Letter Queue
  DLQ_MESSAGES=$(docker exec rabbitmq rabbitmqctl list_queues name messages 2>/dev/null | \
    awk '$1~/dlq/ {sum+=$2} END {print sum+0}')

  if [ "$DLQ_MESSAGES" -gt 0 ]; then
    echo "⚠️  WARNING: Dead Letter Queue has $DLQ_MESSAGES failed messages"
  else
    echo "✅ No messages in Dead Letter Queue"
  fi

  echo ""
  echo "-------------------------------------------------------------------"
  echo "Next update in ${INTERVAL}s..."
  echo ""

  sleep "$INTERVAL"
done
