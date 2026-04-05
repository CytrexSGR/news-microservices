# Production Deployment Checklist

**Quick reference for deploying News Microservices to a new server**

---

## Pre-Deployment (30-60 minutes)

### [ ] Server Preparation

```bash
# System updates
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim htop

# Docker installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# System tuning
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Reboot
sudo reboot
```

### [ ] Application Setup

```bash
# Clone repository
sudo mkdir -p /opt/news-microservices
sudo chown $USER:$USER /opt/news-microservices
cd /opt/news-microservices
git clone <REPO_URL> .
git checkout main
```

### [ ] Configuration

```bash
# Copy environment template
cp .env.example .env.production

# Generate secrets
echo "JWT_SECRET: $(openssl rand -base64 32)"
echo "DB_PASSWORD: $(openssl rand -base64 24)"
echo "REDIS_PASSWORD: $(openssl rand -base64 24)"
echo "RABBITMQ_PASSWORD: $(openssl rand -base64 24)"
```

**Edit `.env.production`:**
- [ ] `JWT_SECRET_KEY` (generated above)
- [ ] `POSTGRES_PASSWORD` (generated above)
- [ ] `REDIS_URL` (with password)
- [ ] `RABBITMQ_URL` (with password)
- [ ] `NEO4J_PASSWORD`
- [ ] `OPENAI_API_KEY` (if using)
- [ ] `PERPLEXITY_API_KEY` (if using)
- [ ] `FMP_API_KEY` (if using)
- [ ] `SMTP_*` credentials (email notifications)
- [ ] `CORS_ORIGINS` (production domains)
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=WARNING`

### [ ] SSL/TLS Certificates

```bash
# Let's Encrypt
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com
```

### [ ] Firewall

```bash
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw status
```

---

## Deployment (10-15 minutes)

### [ ] Build & Start

```bash
cd /opt/news-microservices

# Build images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Wait for startup
sleep 30
```

### [ ] Initialize Database

```bash
# Run migrations
./scripts/init-migrations.sh

# Create admin user (andreas / Aug2012#)
docker exec -it news-auth-service python scripts/create_admin.py
```

---

## Verification (10-15 minutes)

### [ ] Health Checks

```bash
# Quick health check
./scripts/quick_smoke_test.sh

# Detailed service health
./scripts/health_check.sh

# Individual service tests
./scripts/test_auth_service.sh
./scripts/test_feed_service.sh
./scripts/test_search_service.sh
./scripts/test_analytics_service.sh
./scripts/test_fmp_service.sh

# End-to-end test
./scripts/test_e2e_flow.sh
```

### [ ] Manual Health Checks

```bash
# Frontend
curl http://localhost/health

# Backend services
curl http://localhost:8100/health  # Auth
curl http://localhost:8101/health  # Feed
curl http://localhost:8106/health  # Search
curl http://localhost:8107/health  # Analytics
```

**Expected response:**
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### [ ] Infrastructure Checks

```bash
# PostgreSQL
docker exec postgres pg_isready -U news_user

# Redis
docker exec redis redis-cli -a redis_secret_2024 PING

# RabbitMQ
docker exec rabbitmq rabbitmqctl status

# Neo4j
docker exec neo4j cypher-shell -u neo4j -p neo4j_password_2024 "RETURN 1;"
```

### [ ] Resource Monitoring

```bash
# Container stats
docker stats --no-stream

# Check for errors in logs
docker compose -f docker-compose.prod.yml logs | grep -i error
docker compose -f docker-compose.prod.yml logs | grep -i exception
```

---

## Post-Deployment (15-30 minutes)

### [ ] Backup Configuration

```bash
# Create backup directory
sudo mkdir -p /backups/news-microservices/postgres

# Create backup script
sudo nano /usr/local/bin/backup-news-microservices.sh
```

**Backup script content:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/news-microservices"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR/postgres"

# PostgreSQL backup
docker exec postgres pg_dump -U news_user news_mcp | \
  gzip > "$BACKUP_DIR/postgres/news_mcp_$DATE.sql.gz"

# Remove backups older than 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-news-microservices.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line: 0 2 * * * /usr/local/bin/backup-news-microservices.sh
```

### [ ] Monitoring Setup

```bash
# Set up resource monitoring
./scripts/monitor-resources.sh &

# Check RabbitMQ queues
watch -n 5 'docker exec rabbitmq rabbitmqctl list_queues name messages'
```

### [ ] Documentation

- [ ] Document server IP address
- [ ] Document domain name(s)
- [ ] Document backup locations
- [ ] Document deployment date/version
- [ ] Update team wiki/documentation

---

## Security Final Checks

### [ ] Credentials

- [ ] All default passwords changed
- [ ] JWT_SECRET_KEY unique and strong (32+ chars)
- [ ] `.env.production` NOT committed to git
- [ ] API keys secured and documented separately

### [ ] Network Security

- [ ] Firewall active (only 80, 443, 22 open)
- [ ] RabbitMQ Management UI not exposed (15672 internal only)
- [ ] Neo4j Browser not exposed (7474 internal only)
- [ ] CORS_ORIGINS limited to production domains

### [ ] Application Security

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=WARNING` or `ERROR`
- [ ] Rate limiting enabled
- [ ] SSL/TLS certificates valid

---

## Rollback Plan

**If deployment fails:**

```bash
# Stop containers
docker compose -f docker-compose.prod.yml down

# Restore from backup
gunzip -c /backups/postgres/news_mcp_LATEST.sql.gz | \
  docker exec -i postgres psql -U news_user news_mcp

# Rollback to previous git commit
git checkout <PREVIOUS_COMMIT>

# Restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Success Criteria

✅ **Deployment is successful if:**

- [ ] All containers running and healthy (`docker ps`)
- [ ] All health endpoints return 200 OK
- [ ] Admin user can log in (andreas / Aug2012#)
- [ ] Smoke tests pass (`./scripts/quick_smoke_test.sh`)
- [ ] End-to-end test passes (`./scripts/test_e2e_flow.sh`)
- [ ] No errors in logs (past 5 minutes)
- [ ] Memory usage < 80% (`docker stats`)
- [ ] Disk usage < 80% (`df -h`)
- [ ] RabbitMQ queues processing (no stuck messages)
- [ ] Backup cron job configured
- [ ] Monitoring active

---

## Estimated Total Time

- **Server Preparation:** 30-60 minutes (including reboot)
- **Deployment:** 10-15 minutes
- **Verification:** 10-15 minutes
- **Post-Deployment:** 15-30 minutes

**Total:** 65-120 minutes (1-2 hours)

---

## Quick Commands Reference

```bash
# Start
docker compose -f docker-compose.prod.yml up -d

# Stop
docker compose -f docker-compose.prod.yml down

# Restart specific service
docker compose -f docker-compose.prod.yml restart feed-service

# View logs
docker compose -f docker-compose.prod.yml logs -f feed-service

# Health check
./scripts/health_check.sh

# Backup
docker exec postgres pg_dump -U news_user news_mcp > backup.sql

# Container stats
docker stats

# Cleanup old images
docker system prune -a
```

---

## Support Resources

- **Full Guide:** [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Architecture:** [/docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- **Troubleshooting:** [/POSTMORTEMS.md](../../POSTMORTEMS.md)
- **Backend Guide:** [/CLAUDE.backend.md](../../CLAUDE.backend.md)

---

**Deployment Date:** ______________
**Deployed By:** ______________
**Server IP:** ______________
**Domain:** ______________
**Notes:** ______________
