#!/bin/bash
#
# RabbitMQ Setup Script for DIA System
#
# Creates:
# - verification_exchange (topic exchange)
# - verification_queue (durable queue)
# - verification_dlq (dead letter queue)
# - Bindings
#
# Related: ADR-018 (DIA-Planner & Verifier)

set -e

RABBITMQ_CONTAINER="rabbitmq"
RABBITMQ_USER="${RABBITMQ_USER:-guest}"
RABBITMQ_PASS="${RABBITMQ_PASS:-guest}"

echo "=========================================="
echo "RabbitMQ Setup for DIA System"
echo "=========================================="

# Wait for RabbitMQ to be ready
echo "[1/5] Waiting for RabbitMQ to be ready..."
until docker exec $RABBITMQ_CONTAINER rabbitmq-diagnostics -q ping; do
  echo "  Waiting for RabbitMQ..."
  sleep 2
done
echo "  ✓ RabbitMQ is ready"

# Create verification exchange
echo "[2/5] Creating verification_exchange..."
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare exchange \
  name=verification_exchange \
  type=topic \
  durable=true || echo "  (already exists)"
echo "  ✓ verification_exchange created"

# Create dead letter exchange
echo "[3/5] Creating verification_dlx (dead letter exchange)..."
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare exchange \
  name=verification_dlx \
  type=topic \
  durable=true || echo "  (already exists)"
echo "  ✓ verification_dlx created"

# Create verification queue
echo "[4/5] Creating verification_queue..."
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare queue \
  name=verification_queue \
  durable=true \
  arguments='{"x-dead-letter-exchange":"verification_dlx","x-message-ttl":86400000}' || echo "  (already exists)"
echo "  ✓ verification_queue created"

# Create dead letter queue
echo "[5/5] Creating verification_dlq (dead letter queue)..."
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare queue \
  name=verification_dlq \
  durable=true || echo "  (already exists)"
echo "  ✓ verification_dlq created"

# Bind queue to exchange
echo "[6/6] Binding verification_queue to verification_exchange..."
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare binding \
  source=verification_exchange \
  destination=verification_queue \
  routing_key="verification.required.*" || echo "  (already exists)"
echo "  ✓ Binding created"

# Bind DLQ to DLX
docker exec $RABBITMQ_CONTAINER rabbitmqadmin \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  declare binding \
  source=verification_dlx \
  destination=verification_dlq \
  routing_key="#" || echo "  (already exists)"
echo "  ✓ DLQ binding created"

echo ""
echo "=========================================="
echo "✓ RabbitMQ Setup Complete!"
echo "=========================================="
echo ""
echo "Verification Infrastructure:"
echo "  - Exchange: verification_exchange (topic)"
echo "  - Queue: verification_queue"
echo "  - Routing Key: verification.required.*"
echo "  - Dead Letter Queue: verification_dlq"
echo ""
echo "Management UI: http://localhost:15672"
echo "  Username: $RABBITMQ_USER"
echo "  Password: [configured]"
echo ""
