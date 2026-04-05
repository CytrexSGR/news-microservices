# Production Deployment Guide - News Microservices

**Last Updated:** 2025-12-04
**Target:** Fresh server installation for production deployment

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Installation](#application-installation)
4. [Configuration](#configuration)
5. [Deployment](#deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Backup & Restore](#backup--restore)
9. [Rollback Strategy](#rollback-strategy)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum (Development/Testing):**
- CPU: 4 cores
- RAM: 16 GB
- Disk: 50 GB SSD
- Network: 100 Mbps

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 32 GB
- Disk: 200 GB SSD (or separate volumes for Docker, databases)
- Network: 1 Gbps
- Backup storage: 500 GB (offsite)

### Software Requirements

- **OS:** Ubuntu 22.04 LTS or newer (recommended)
- **Docker:** 24.0+ with Docker Compose V2
- **Git:** 2.40+
- **Python:** 3.11+ (for tooling/scripts)
- **Node.js:** 18+ (for frontend builds)

### Access Requirements

- Root/sudo access
- Firewall ports open:
  - 80, 443 (HTTPS/TLS)
  - 22 (SSH)
  - 15672 (RabbitMQ Management - internal only)
  - 7474 (Neo4j Browser - internal only)

---

## Server Setup

### 1. System Updates

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y curl wget git vim htop net-tools

# Set timezone
sudo timedatectl set-timezone Europe/Berlin
```

### 2. Docker Installation

```bash
# Remove old Docker versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install Docker from official repository
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker compose version
```

**Expected output:**
```
Docker version 24.0.x
Docker Compose version v2.x.x
```

### 3. System Tuning (Production)

```bash
# Increase file descriptor limits (for RabbitMQ, databases)
sudo tee -a /etc/security/limits.conf <<EOF
* soft nofile 65536
* hard nofile 65536
EOF

# Increase max map count (for Elasticsearch-based services, if used)
sudo sysctl -w vm.max_map_count=262144
sudo tee -a /etc/sysctl.conf <<EOF
vm.max_map_count=262144
EOF

# Apply changes
sudo sysctl -p

# Reboot to apply all changes
sudo reboot
```

---

## Application Installation

### 1. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/news-microservices
sudo chown $USER:$USER /opt/news-microservices
cd /opt/news-microservices

# Clone repository
git clone <YOUR_REPO_URL> .

# Checkout production branch (if different from main)
git checkout main  # or production branch
```

### 2. Directory Structure Verification

```bash
# Verify critical directories exist
ls -la services/
ls -la frontend/
ls -la scripts/

# Expected: 16 service directories, frontend/, scripts/
```

---

## Configuration

### 1. Environment Variables

#### Main .env File

```bash
cd /opt/news-microservices

# Copy template
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Critical variables to configure:**

```bash
# ============================================
# SECURITY (MUST CHANGE!)
# ============================================
JWT_SECRET_KEY=<GENERATE_STRONG_SECRET_MIN_32_CHARS>
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql+asyncpg://news_user:<POSTGRES_PASSWORD>@postgres:5432/news_mcp

# ============================================
# REDIS
# ============================================
REDIS_URL=redis://:<REDIS_PASSWORD>@redis:6379/0

# ============================================
# RABBITMQ
# ============================================
RABBITMQ_URL=amqp://admin:<RABBITMQ_PASSWORD>@rabbitmq:5672/news_mcp
RABBITMQ_USER=admin
RABBITMQ_PASS=<RABBITMQ_PASSWORD>

# ============================================
# NEO4J
# ============================================
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<NEO4J_PASSWORD>

# ============================================
# EXTERNAL APIS (Optional but recommended)
# ============================================
OPENAI_API_KEY=<YOUR_OPENAI_KEY>
OPENAI_MODEL=gpt-4o-mini
PERPLEXITY_API_KEY=<YOUR_PERPLEXITY_KEY>
FMP_API_KEY=<YOUR_FMP_KEY>

# ============================================
# EMAIL (Notification Service)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<YOUR_EMAIL>
SMTP_PASSWORD=<YOUR_APP_PASSWORD>

# ============================================
# PRODUCTION SETTINGS
# ============================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# ============================================
# FRONTEND CORS (CRITICAL!)
# ============================================
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]
```

**Generate secure secrets:**

```bash
# JWT Secret (32+ characters)
openssl rand -base64 32

# Database passwords
openssl rand -base64 24

# API keys: Obtain from respective services
```

#### Service-Specific Configs

Some services may need additional configuration:

```bash
# Example: FMP Service
cp services/fmp-service/.env.example services/fmp-service/.env.production

# Example: Research Service
cp services/research-service/.env.example services/research-service/.env.production
```

### 2. SSL/TLS Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt install -y certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificates will be in: /etc/letsencrypt/live/your-domain.com/
```

**Option B: Self-Signed (Development only)**

```bash
# Generate self-signed certificate
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes
```

### 3. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verify rules
sudo ufw status
```

---

## Deployment

### Option 1: Production Deployment (Recommended)

```bash
cd /opt/news-microservices

# 1. Pull latest code
git pull origin main

# 2. Build images
docker compose -f docker-compose.prod.yml build

# 3. Start services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# 4. Wait for startup (30-60 seconds)
sleep 30

# 5. Verify services are healthy
docker compose -f docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                STATUS              PORTS
postgres            Up (healthy)
redis               Up (healthy)
rabbitmq            Up (healthy)        0.0.0.0:15672->15672/tcp
neo4j               Up (healthy)
frontend            Up (healthy)        0.0.0.0:80->80/tcp
auth-service        Up (healthy)
feed-service        Up (healthy)
...
```

### Option 2: Using Makefile (Development-style)

```bash
# Start production environment
make prod-d

# Check health
make health
```

### Initial Data Setup

```bash
# 1. Run database migrations
./scripts/init-migrations.sh

# 2. Create admin user
docker exec -it news-auth-service python -c "
from app.services.user_service import UserService
import asyncio

async def create_admin():
    user_service = UserService()
    await user_service.create_user(
        username='andreas',
        email='andreas@test.com',
        password='Aug2012#',
        roles=['admin', 'user']
    )
    print('Admin user created!')

asyncio.run(create_admin())
"

# 3. Seed initial data (optional)
./scripts/seed-data.sh
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Check all service health endpoints
./scripts/health_check.sh

# Or manually:
curl http://localhost/health  # Frontend
curl http://localhost:8100/health  # Auth
curl http://localhost:8101/health  # Feed
curl http://localhost:8106/health  # Search
# ... etc
```

**Expected response (all services):**
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0",
  "timestamp": "2025-12-04T10:00:00Z"
}
```

### 2. API Smoke Tests

```bash
# Run comprehensive smoke tests
./scripts/quick_smoke_test.sh

# Individual service tests
./scripts/test_auth_service.sh
./scripts/test_feed_service.sh
./scripts/test_search_service.sh
./scripts/test_analytics_service.sh
./scripts/test_fmp_service.sh
```

### 3. End-to-End Test

```bash
# Full workflow test
./scripts/test_e2e_flow.sh
```

This tests:
- User authentication (JWT)
- Feed creation/ingestion
- Content analysis pipeline
- Search indexing
- Analytics tracking

### 4. Monitor Startup Logs

```bash
# Watch all service logs
docker compose -f docker-compose.prod.yml logs -f

# Watch specific service
docker logs -f news-feed-service

# Check for errors
docker compose -f docker-compose.prod.yml logs | grep -i error
docker compose -f docker-compose.prod.yml logs | grep -i exception
```

---

## Monitoring & Maintenance

### 1. Resource Monitoring

```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Service-specific memory
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" --no-stream
```

### 2. Log Management

```bash
# View logs with timestamps
docker compose -f docker-compose.prod.yml logs -t

# Follow logs for specific service
docker compose -f docker-compose.prod.yml logs -f feed-service

# Save logs to file
docker compose -f docker-compose.prod.yml logs > deployment-logs-$(date +%Y%m%d).log
```

### 3. Database Maintenance

```bash
# PostgreSQL vacuum (weekly)
docker exec postgres psql -U news_user -d news_mcp -c "VACUUM ANALYZE;"

# Check database size
docker exec postgres psql -U news_user -d news_mcp -c "
SELECT
  pg_size_pretty(pg_database_size('news_mcp')) as db_size;
"

# Redis memory stats
docker exec redis redis-cli -a redis_secret_2024 INFO memory
```

### 4. RabbitMQ Monitoring

```bash
# Queue stats
docker exec rabbitmq rabbitmqctl list_queues name messages consumers

# Check for stuck messages
docker exec rabbitmq rabbitmqctl list_queues | grep -v " 0 "
```

---

## Backup & Restore

### 1. Database Backup

```bash
# Create backup directory
mkdir -p /backups/postgres

# PostgreSQL backup
docker exec postgres pg_dump -U news_user news_mcp > \
  /backups/postgres/news_mcp_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip /backups/postgres/news_mcp_*.sql

# Neo4j backup (requires Neo4j Enterprise for hot backup)
docker exec neo4j neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j_$(date +%Y%m%d_%H%M%S).dump
```

### 2. Automated Backup (Cron)

```bash
# Create backup script
sudo nano /usr/local/bin/backup-news-microservices.sh

# Add content:
#!/bin/bash
BACKUP_DIR="/backups/news-microservices"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR/postgres"

# PostgreSQL backup
docker exec postgres pg_dump -U news_user news_mcp | \
  gzip > "$BACKUP_DIR/postgres/news_mcp_$DATE.sql.gz"

# Remove backups older than 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete

# Make executable
sudo chmod +x /usr/local/bin/backup-news-microservices.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /usr/local/bin/backup-news-microservices.sh
```

### 3. Restore from Backup

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore PostgreSQL
gunzip -c /backups/postgres/news_mcp_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i postgres psql -U news_user news_mcp

# Restore Neo4j
docker exec neo4j neo4j-admin database load neo4j \
  --from-path=/backups/neo4j_YYYYMMDD_HHMMSS.dump --overwrite-destination=true

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

---

## Rollback Strategy

### 1. Docker Image Rollback

```bash
# List available image versions
docker images | grep news-

# Stop current deployment
docker compose -f docker-compose.prod.yml down

# Tag previous working version as 'latest'
docker tag news-feed-service:previous news-feed-service:latest

# Restart with previous version
docker compose -f docker-compose.prod.yml up -d
```

### 2. Git-based Rollback

```bash
# Find last working commit
git log --oneline

# Rollback to specific commit
git checkout <COMMIT_HASH>

# Rebuild and deploy
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 3. Database Rollback

```bash
# Restore from backup (see Backup & Restore section)

# Or run specific migration rollback
docker exec news-feed-service alembic downgrade -1
```

---

## Troubleshooting

### Problem: Services not starting

**Symptoms:** Containers crash or restart loop

**Diagnosis:**
```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Check resource usage
docker stats
```

**Solutions:**
- Increase RAM/CPU if resources are exhausted
- Check `.env.production` for configuration errors
- Verify database connections: `docker exec postgres pg_isready -U news_user`
- Restart individual service: `docker compose -f docker-compose.prod.yml restart <service-name>`

### Problem: Database connection errors

**Symptoms:** `Connection refused` or `Authentication failed`

**Diagnosis:**
```bash
# Test PostgreSQL connection
docker exec postgres psql -U news_user -d news_mcp -c "SELECT 1;"

# Check Redis connection
docker exec redis redis-cli -a redis_secret_2024 PING

# Check RabbitMQ
docker exec rabbitmq rabbitmqctl status
```

**Solutions:**
- Verify credentials in `.env.production`
- Wait for infrastructure services to fully start (30-60s)
- Check Docker network: `docker network inspect news-microservices_news_network`

### Problem: High memory usage

**Symptoms:** Server becomes slow, OOM errors

**Diagnosis:**
```bash
# Check memory usage per container
docker stats --no-stream

# Check for memory leaks
./scripts/quick_memory_check.sh
```

**Solutions:**
- Known issue: entity-canonicalization service had memory leak (fixed in commit 788a6ce)
- Restart problematic service: `docker restart <container-name>`
- Scale down services if not needed
- Increase server RAM

### Problem: RabbitMQ queue backlog

**Symptoms:** Messages accumulating, slow processing

**Diagnosis:**
```bash
# Check queue depths
docker exec rabbitmq rabbitmqctl list_queues name messages

# Check consumer count
docker exec rabbitmq rabbitmqctl list_queues name consumers
```

**Solutions:**
- Scale up consumer services (feed-service, content-analysis)
- Check for dead-letter queues: `rabbitmqctl list_queues | grep dlq`
- Increase worker concurrency in Celery configuration

### Problem: Frontend not accessible

**Symptoms:** HTTP 502/503 errors

**Diagnosis:**
```bash
# Check frontend container
docker logs news-frontend-production

# Test Nginx config
docker exec news-frontend-production nginx -t

# Check backend connectivity
curl http://localhost:8100/health
```

**Solutions:**
- Verify CORS_ORIGINS in `.env.production`
- Check Nginx configuration in `frontend/nginx.conf`
- Restart frontend: `docker compose restart frontend`

---

## Additional Resources

- **Architecture Overview:** [/docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- **Backend Development:** [/CLAUDE.backend.md](../../CLAUDE.backend.md)
- **Frontend Development:** [/CLAUDE.frontend.md](../../CLAUDE.frontend.md)
- **Service Documentation:** `/docs/services/<service-name>.md`
- **Critical Incidents:** [/POSTMORTEMS.md](../../POSTMORTEMS.md)

---

## Security Checklist

Before going live, verify:

- [ ] All default passwords changed (PostgreSQL, Redis, RabbitMQ, Neo4j)
- [ ] JWT_SECRET_KEY is strong and unique (32+ characters)
- [ ] CORS_ORIGINS set to production domains only
- [ ] SSL/TLS certificates installed and valid
- [ ] Firewall configured (only 80, 443, 22 open externally)
- [ ] RabbitMQ Management UI not exposed externally (port 15672 internal only)
- [ ] Neo4j Browser not exposed externally (port 7474 internal only)
- [ ] DEBUG=false in production
- [ ] LOG_LEVEL=WARNING or ERROR in production
- [ ] Regular backups configured (daily minimum)
- [ ] Monitoring/alerting configured
- [ ] API rate limiting enabled
- [ ] .env.production files gitignored and not committed

---

**Deployment completed?** Run the full verification suite:

```bash
./scripts/quick_smoke_test.sh
./scripts/test_e2e_flow.sh
./scripts/health_check.sh
```

**Questions or issues?** Check [POSTMORTEMS.md](../../POSTMORTEMS.md) for common problems and solutions.
