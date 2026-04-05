#!/bin/bash
# Disk Usage Analysis Script

echo "=== DISK USAGE OVERVIEW ==="
df -h /

echo ""
echo "=== TOP 20 LARGEST DIRECTORIES IN ROOT ==="
sudo du -h --max-depth=1 / 2>/dev/null | sort -hr | head -20

echo ""
echo "=== TOP 15 LARGEST DIRECTORIES IN /VAR ==="
sudo du -h --max-depth=1 /var 2>/dev/null | sort -hr | head -15

echo ""
echo "=== TOP 10 LARGEST DIRECTORIES IN /HOME ==="
sudo du -h --max-depth=2 /home 2>/dev/null | sort -hr | head -10

echo ""
echo "=== DOCKER DISK USAGE ==="
docker system df

echo ""
echo "=== DOCKER VOLUMES ==="
docker volume ls -q | while read vol; do
  size=$(docker volume inspect "$vol" --format '{{.Mountpoint}}' | xargs sudo du -sh 2>/dev/null | awk '{print $1}')
  echo "$vol: $size"
done | sort -k2 -hr | head -15

echo ""
echo "=== LARGE FILES (>1GB) ==="
sudo find / -type f -size +1G -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' | head -20

echo ""
echo "=== POSTGRES DATABASE SIZES ==="
docker exec postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) as size FROM pg_database ORDER BY pg_database_size(datname) DESC;" 2>/dev/null || echo "Could not query PostgreSQL"

echo ""
echo "=== SYSTEMD JOURNAL SIZE ==="
sudo journalctl --disk-usage 2>/dev/null || echo "Could not query journal"
