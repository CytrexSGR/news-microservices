#!/bin/bash
# Docker cleanup script - removes dead/exited containers, dangling images, old volumes
# Usage: ./scripts/docker/cleanup-dead.sh
# Recommended: Run via cron every 30 minutes

set -e

echo "🧹 Docker Cleanup Starting..."
echo "$(date)"
echo ""

# Remove dead containers
echo "=== Removing Dead Containers ==="
DEAD=$(docker ps -a -f "status=dead" -q 2>/dev/null || true)
if [ -n "$DEAD" ]; then
  echo "Found dead containers: $DEAD"
  docker rm -f $DEAD
  echo "✅ Removed $(echo $DEAD | wc -w) dead container(s)"
else
  echo "✅ No dead containers found"
fi
echo ""

# Remove exited containers (older than 1 hour)
echo "=== Removing Old Exited Containers (>1h) ==="
EXITED=$(docker ps -a -f "status=exited" --filter "until=1h" -q 2>/dev/null || true)
if [ -n "$EXITED" ]; then
  echo "Found exited containers: $EXITED"
  docker rm $EXITED
  echo "✅ Removed $(echo $EXITED | wc -w) exited container(s)"
else
  echo "✅ No old exited containers found"
fi
echo ""

# Prune dangling images
echo "=== Pruning Dangling Images ==="
BEFORE_IMAGES=$(docker images -q | wc -l)
docker image prune -f > /dev/null 2>&1
AFTER_IMAGES=$(docker images -q | wc -l)
REMOVED_IMAGES=$((BEFORE_IMAGES - AFTER_IMAGES))
if [ $REMOVED_IMAGES -gt 0 ]; then
  echo "✅ Removed $REMOVED_IMAGES dangling image(s)"
else
  echo "✅ No dangling images found"
fi
echo ""

# Prune unused volumes (older than 24h)
echo "=== Pruning Old Volumes (>24h unused) ==="
VOLUMES_BEFORE=$(docker volume ls -q | wc -l)
docker volume prune -f --filter "until=24h" > /dev/null 2>&1
VOLUMES_AFTER=$(docker volume ls -q | wc -l)
REMOVED_VOLUMES=$((VOLUMES_BEFORE - VOLUMES_AFTER))
if [ $REMOVED_VOLUMES -gt 0 ]; then
  echo "✅ Removed $REMOVED_VOLUMES old volume(s)"
else
  echo "✅ No old volumes found"
fi
echo ""

# Prune unused networks
echo "=== Pruning Unused Networks ==="
docker network prune -f > /dev/null 2>&1
echo "✅ Unused networks removed"
echo ""

# Summary
echo "════════════════════════════════════════"
echo "✅ Cleanup Complete"
echo "════════════════════════════════════════"
echo "Removed:"
echo "  - Dead containers: $(echo $DEAD | wc -w)"
echo "  - Exited containers: $(echo $EXITED | wc -w)"
echo "  - Dangling images: $REMOVED_IMAGES"
echo "  - Old volumes: $REMOVED_VOLUMES"
echo ""

# Disk space saved
DISK_FREED=$(docker system df 2>/dev/null | grep "Reclaimable" | awk '{print $4}' || echo "Unknown")
echo "💾 Disk space status:"
docker system df
echo ""
echo "Next cleanup: Recommended in 30 minutes"
echo "Add to crontab: */30 * * * * /path/to/cleanup-dead.sh >> /var/log/docker-cleanup.log 2>&1"
