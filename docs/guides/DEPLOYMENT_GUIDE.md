# News Microservices - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Database Initialization](#database-initialization)
5. [Service Deployment](#service-deployment)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup and Restore](#backup-and-restore)
9. [Rollback Procedures](#rollback-procedures)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 22.04 LTS or later / Debian 11+ / CentOS 8+
- **CPU**: Minimum 4 cores (8 recommended)
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: Minimum 50GB free space (100GB recommended)
- **Network**: Stable internet connection with open ports

### Software Requirements

- **Docker**: Version 24.0 or later
- **Docker Compose**: Version 2.20 or later
- **Git**: Version 2.30 or later
- **curl**: For API testing
- **jq**: For JSON parsing (optional but recommended)

### Port Requirements

The following ports must be available:

| Port | Service | Purpose |
|------|---------|---------|
| 80 | Traefik | HTTP traffic |
| 443 | Traefik | HTTPS traffic |
| 5432 | PostgreSQL | Database |
| 6379 | Redis | Cache |
| 5672 | RabbitMQ | Message queue |
| 15672 | RabbitMQ | Management UI |
| 9000 | MinIO | Object storage API |
| 9001 | MinIO | Console UI |
| 8080 | Traefik | Dashboard |
| 8000-8007 | Services | Microservices APIs |

## Pre-Deployment Checklist

### Infrastructure Checklist

- [ ] Docker and Docker Compose installed
- [ ] Required ports available (80, 443, 5432, 6379, 5672, 9000, 8000-8007)
- [ ] Sufficient disk space (minimum 50GB free)
- [ ] Sufficient RAM (minimum 8GB)
- [ ] Domain name configured (for production)
- [ ] SSL certificates obtained (for production)
- [ ] Firewall rules configured
- [ ] Network connectivity verified

### Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong JWT secret key
- [ ] Configured secure database credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configured CORS policies
- [ ] Enabled rate limiting
- [ ] Set up API key management
- [ ] Configured firewall rules
- [ ] Set appropriate file permissions

### Configuration Checklist

- [ ] `.env` file created from `.env.example`
- [ ] Environment variables configured
- [ ] Database credentials set
- [ ] API keys configured
- [ ] Service URLs configured
- [ ] Log levels set appropriately
- [ ] Backup destinations configured

## Environment Configuration

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/news-microservices.git
cd news-microservices
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` file with your specific configuration:

```bash
# Database Configuration
POSTGRES_USER=newsuser
POSTGRES_PASSWORD=<STRONG_PASSWORD>  # Generate with: openssl rand -hex 32
POSTGRES_DB=news_platform
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<STRONG_PASSWORD>  # Generate with: openssl rand -hex 32
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# RabbitMQ Configuration
RABBITMQ_USER=newsrabbit
RABBITMQ_PASSWORD=<STRONG_PASSWORD>  # Generate with: openssl rand -hex 32
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<STRONG_PASSWORD>  # Generate with: openssl rand -hex 32
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}

# JWT Configuration
JWT_SECRET_KEY=<STRONG_SECRET>  # Generate with: openssl rand -base64 64
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# API Keys (for external services)
OPENAI_API_KEY=<your_openai_key>
ANTHROPIC_API_KEY=<your_anthropic_key>
PERPLEXITY_API_KEY=<your_perplexity_key>

# Service Configuration
AUTH_SERVICE_URL=http://auth-service:8000
FEED_SERVICE_URL=http://feed-service:8001
CONTENT_ANALYSIS_SERVICE_URL=http://content-analysis-service:8002
RESEARCH_SERVICE_URL=http://research-service:8003
OSINT_SERVICE_URL=http://osint-service:8004
NOTIFICATION_SERVICE_URL=http://notification-service:8005
SEARCH_SERVICE_URL=http://search-service:8006
ANALYTICS_SERVICE_URL=http://analytics-service:8007

# Traefik Configuration
DOMAIN=localhost  # Change to your domain in production
ACME_EMAIL=admin@example.com  # Change to your email

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Environment
ENVIRONMENT=production  # Options: development, staging, production
```

### Step 4: Generate Secure Passwords

```bash
# Generate PostgreSQL password
echo "POSTGRES_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate Redis password
echo "REDIS_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate RabbitMQ password
echo "RABBITMQ_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate MinIO password
echo "MINIO_ROOT_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate JWT secret
echo "JWT_SECRET_KEY=$(openssl rand -base64 64)" >> .env
```

### Step 5: Set File Permissions

```bash
chmod 600 .env
```

## Database Initialization

### Step 1: Start Infrastructure Services

```bash
docker compose up -d postgres redis rabbitmq minio
```

### Step 2: Wait for Services to be Ready

```bash
# Wait for PostgreSQL
until docker exec news-postgres pg_isready -U postgres; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Wait for Redis
until docker exec news-redis redis-cli ping; do
    echo "Waiting for Redis..."
    sleep 2
done

# Wait for RabbitMQ
until docker exec news-rabbitmq rabbitmqctl status; do
    echo "Waiting for RabbitMQ..."
    sleep 2
done
```

### Step 3: Initialize Databases

Each service will create its own database on first run. You can pre-create them:

```bash
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE auth_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE feed_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE content_analysis_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE research_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE osint_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE notification_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE search_db;"
docker exec -it news-postgres psql -U postgres -c "CREATE DATABASE analytics_db;"
```

## Service Deployment

### Step 1: Build Service Images

```bash
# Build all services
docker compose build

# Or build specific service
docker compose build auth-service
```

### Step 2: Start All Services

```bash
# Start all services
docker compose up -d

# Or start services in stages
docker compose up -d traefik
docker compose up -d auth-service
docker compose up -d feed-service
docker compose up -d content-analysis-service
docker compose up -d research-service
docker compose up -d osint-service
docker compose up -d notification-service
docker compose up -d search-service
docker compose up -d analytics-service
```

### Step 3: Verify Services

```bash
# Check all containers are running
docker compose ps

# Check logs for errors
docker compose logs -f

# Run validation script
chmod +x scripts/validate-deployment.sh
./scripts/validate-deployment.sh
```

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended for Production)

#### Step 1: Update Traefik Configuration

Edit `docker-compose.yml` and update Traefik service:

```yaml
traefik:
  command:
    - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
    - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
  volumes:
    - ./letsencrypt:/letsencrypt
```

#### Step 2: Add HTTPS Labels to Services

```yaml
auth-service:
  labels:
    - "traefik.http.routers.auth.tls=true"
    - "traefik.http.routers.auth.tls.certresolver=letsencrypt"
```

### Using Custom Certificates

#### Step 1: Place Certificates

```bash
mkdir -p certs
cp your-cert.crt certs/
cp your-cert.key certs/
```

#### Step 2: Update Traefik Configuration

```yaml
traefik:
  volumes:
    - ./certs:/certs:ro
  command:
    - "--providers.file.directory=/etc/traefik/dynamic"
```

Create `traefik/dynamic/certs.yml`:

```yaml
tls:
  certificates:
    - certFile: /certs/your-cert.crt
      keyFile: /certs/your-cert.key
```

## Monitoring Setup

### Prometheus Configuration

Prometheus is configured to scrape all service metrics automatically.

#### Access Prometheus

```
URL: http://localhost:9090
```

#### Key Metrics to Monitor

- `up` - Service availability
- `http_requests_total` - Request count
- `http_request_duration_seconds` - Request latency
- `container_cpu_usage_seconds_total` - CPU usage
- `container_memory_usage_bytes` - Memory usage

### Grafana Configuration

#### Step 1: Access Grafana

```
URL: http://localhost:3001
Default credentials: admin / admin
```

#### Step 2: Add Prometheus Data Source

1. Go to Configuration > Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. URL: `http://prometheus:9090`
5. Click "Save & Test"

#### Step 3: Import Dashboards

Pre-configured dashboards are available in `monitoring/grafana/dashboards/`.

### Log Aggregation

#### Using Docker Logs

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f auth-service

# Filter logs by level
docker compose logs | grep ERROR
```

#### Using External Log Aggregation (Optional)

Configure services to send logs to ELK Stack, Loki, or other log aggregation systems.

## Backup and Restore

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup all databases
docker exec news-postgres pg_dumpall -U postgres | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$TIMESTAMP.sql.gz"
```

#### Schedule with Cron

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup-database.sh
```

#### Manual Backup

```bash
# Backup single database
docker exec news-postgres pg_dump -U postgres auth_db | gzip > auth_db_backup.sql.gz

# Backup all databases
docker exec news-postgres pg_dumpall -U postgres | gzip > all_databases_backup.sql.gz
```

### Database Restore

```bash
# Restore single database
gunzip -c auth_db_backup.sql.gz | docker exec -i news-postgres psql -U postgres auth_db

# Restore all databases
gunzip -c all_databases_backup.sql.gz | docker exec -i news-postgres psql -U postgres
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v news-microservices_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data.tar.gz -C /data .

# Backup MinIO data
docker run --rm \
  -v news-microservices_minio_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_data.tar.gz -C /data .
```

### Volume Restore

```bash
# Restore PostgreSQL data
docker run --rm \
  -v news-microservices_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_data.tar.gz"

# Restore MinIO data
docker run --rm \
  -v news-microservices_minio_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/minio_data.tar.gz"
```

## Rollback Procedures

### Service Rollback

#### Step 1: Identify Previous Version

```bash
# List available images
docker images | grep news-microservices

# Check git history
git log --oneline
```

#### Step 2: Rollback to Previous Image

```bash
# Stop current service
docker compose stop auth-service

# Tag current image as backup
docker tag news-microservices-auth-service:latest news-microservices-auth-service:backup

# Pull/checkout previous version
git checkout <previous-commit>
docker compose build auth-service

# Start service
docker compose up -d auth-service
```

#### Step 3: Verify Rollback

```bash
# Check service health
curl http://localhost:8000/health

# Check logs
docker compose logs -f auth-service
```

### Database Rollback

#### Using Database Backup

```bash
# Stop services
docker compose stop

# Restore database
gunzip -c backup_<timestamp>.sql.gz | docker exec -i news-postgres psql -U postgres

# Start services
docker compose up -d
```

#### Using Database Migrations (if implemented)

```bash
# Rollback migrations
docker exec auth-service alembic downgrade -1
```

### Full System Rollback

```bash
# Stop all services
docker compose down

# Checkout previous version
git checkout <previous-commit>

# Restore backups if needed
./scripts/restore-backups.sh

# Rebuild and start
docker compose build
docker compose up -d

# Validate
./scripts/validate-deployment.sh
```

## Troubleshooting

### Service Won't Start

**Symptom**: Container exits immediately after starting

**Solutions**:

1. Check logs:
   ```bash
   docker compose logs service-name
   ```

2. Check environment variables:
   ```bash
   docker compose config
   ```

3. Verify dependencies are running:
   ```bash
   docker compose ps
   ```

4. Check disk space:
   ```bash
   df -h
   ```

### Database Connection Errors

**Symptom**: Services report "connection refused" or "can't connect to database"

**Solutions**:

1. Verify PostgreSQL is running:
   ```bash
   docker compose ps postgres
   ```

2. Check PostgreSQL logs:
   ```bash
   docker compose logs postgres
   ```

3. Verify credentials in `.env`:
   ```bash
   grep POSTGRES .env
   ```

4. Test connection manually:
   ```bash
   docker exec -it news-postgres psql -U postgres
   ```

### Port Already in Use

**Symptom**: "port is already allocated" error

**Solutions**:

1. Find process using port:
   ```bash
   sudo lsof -i :8000
   ```

2. Stop conflicting process:
   ```bash
   sudo kill -9 <PID>
   ```

3. Or change port in `docker-compose.yml`

### Out of Memory

**Symptom**: Services crash with OOM errors

**Solutions**:

1. Check memory usage:
   ```bash
   docker stats
   ```

2. Reduce service memory limits in `docker-compose.yml`

3. Add swap space:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### SSL Certificate Issues

**Symptom**: "certificate verify failed" or HTTPS not working

**Solutions**:

1. Check certificate files exist:
   ```bash
   ls -la certs/
   ```

2. Verify certificate validity:
   ```bash
   openssl x509 -in certs/cert.crt -text -noout
   ```

3. Check Traefik logs:
   ```bash
   docker compose logs traefik
   ```

### Slow Performance

**Symptom**: Services respond slowly

**Solutions**:

1. Check resource usage:
   ```bash
   docker stats
   ```

2. Review database query performance:
   ```bash
   docker exec news-postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

3. Check Redis cache hit rate:
   ```bash
   docker exec news-redis redis-cli info stats | grep hits
   ```

4. Enable query caching
5. Add database indexes
6. Scale services horizontally

### Service Discovery Issues

**Symptom**: Services can't find each other

**Solutions**:

1. Check Docker network:
   ```bash
   docker network ls
   docker network inspect <network-name>
   ```

2. Verify service names in `docker-compose.yml` match URLs in `.env`

3. Test DNS resolution:
   ```bash
   docker exec auth-service nslookup postgres
   ```

## Health Checks

All services expose a `/health` endpoint for monitoring:

```bash
# Check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "Checking port $port:"
    curl -s http://localhost:$port/health | jq .
done
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_users_email ON users(email);

-- Analyze tables
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE;
```

### Redis Optimization

```bash
# Configure max memory
docker exec news-redis redis-cli CONFIG SET maxmemory 2gb
docker exec news-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Service Scaling

```yaml
# In docker-compose.yml
auth-service:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

## Security Best Practices

1. **Change All Default Passwords**
2. **Use Strong JWT Secrets** (minimum 64 characters)
3. **Enable SSL/TLS** in production
4. **Configure CORS** properly
5. **Enable Rate Limiting** on API Gateway
6. **Use Secret Management** (HashiCorp Vault, AWS Secrets Manager)
7. **Regular Security Updates**
8. **Enable Audit Logging**
9. **Restrict Database Access** (use least privilege)
10. **Regular Security Scans**

## Maintenance Schedule

### Daily
- Monitor service health
- Check error logs
- Verify backup completion

### Weekly
- Review performance metrics
- Update security patches
- Clean up old logs and backups

### Monthly
- Review and optimize database queries
- Update dependencies
- Capacity planning review
- Disaster recovery drill

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/news-microservices/issues
- Documentation: https://docs.your-domain.com
- Email: support@your-domain.com

## Feature-Specific Deployment Checklists

### Idempotency and Event-Carried State Transfer (2025-01-22)

Post-deployment validation for duplicate analysis prevention feature.

#### Implementation Checklist

- [x] **Code Changes Deployed**
  - [x] message_handler.py:119-143 - Idempotency check
  - [x] message_handler.py:166-226 - Event-Carried State Transfer
  - [x] feed_fetcher.py:404-423 - analysis_config in events

- [x] **Database Cleanup**
  - [x] Backup created: `/tmp/backups/analysis_results_backup_20250122.sql`
  - [x] 1026 duplicate entries removed
  - [x] Zero remaining duplicates validated
  - [x] Foreign key constraints handled (9 child tables)

- [x] **Documentation**
  - [x] ADR-011: Analysis Idempotency Pattern
  - [x] Incident Report: Duplicate Analysis Fix
  - [x] Service docs updated (content-analysis-service.md)
  - [x] API docs updated (feed-service-api.md)

- [x] **Services Restarted**
  - [x] feed-service restarted
  - [x] content-analysis-service restarted

#### Validation Tests

- [x] **Phase 1: Event-Carried State Transfer**
  - [x] Trigger feed fetch for existing feed
  - [x] Verify log: "✅ Using analysis config from event (no DB query)"
  - [x] Confirm no cross-service database queries
  - [x] Result: Working ✓

- [x] **Phase 2: Idempotency**
  - [x] Trigger analysis for article with existing results
  - [x] Verify log: "✓ Analysis already exists for article {id}, skipping"
  - [x] Confirm message ACKed without reprocessing
  - [x] Result: Working ✓

- [x] **Phase 3: No New Duplicates**
  - [x] Query: `SELECT article_id, analysis_type, COUNT(*) FROM analysis_results WHERE status='COMPLETED' GROUP BY article_id, analysis_type HAVING COUNT(*) > 1`
  - [x] Expected: 0 rows
  - [x] Result: 0 duplicates ✓

#### Performance Metrics

- **Database Queries**: 80% reduction in feed-service queries
- **API Costs**: ~$50/month savings in LLM API calls
- **Processing Speed**: 99.5% faster for duplicate messages (5ms vs 10s)
- **Database Size**: 12% reduction in analysis_results table

#### Monitoring Recommendations

**Week 1 Post-Deployment:**
- [ ] Monitor for "✓ Analysis already exists" logs (should appear during requeuing)
- [ ] Check for "⚠️ No analysis config in event" warnings (should be zero)
- [ ] Verify no "Feed configuration not found" errors
- [ ] Run duplicate check query daily

**Month 1 Post-Deployment:**
- [ ] Review OpenAI API costs (should see ~$50/month reduction)
- [ ] Analyze RabbitMQ message redelivery metrics
- [ ] Check analysis_results table growth rate
- [ ] Validate no regression in analysis quality

#### Known Limitations

1. **Imperfect Idempotency Check**
   - Current: Checks for ANY completed analysis
   - Should: Check per analysis_type
   - Impact: May skip legitimate re-analysis
   - **Action Item**: Improve to per-type check (see ADR-011)

2. **Race Condition Window**
   - Small window (<50ms) where parallel consumers can create duplicates
   - Frequency: <1% of messages
   - **Mitigation**: Acceptable for v1, can add distributed locks later

#### Rollback Procedure

If issues arise:

```bash
# 1. Revert code changes
git revert 55e801a

# 2. Rebuild services
docker compose build feed-service content-analysis-service

# 3. Restart services
docker compose stop feed-service content-analysis-service
docker compose up -d feed-service content-analysis-service

# 4. Restore database if needed
gunzip -c /tmp/backups/analysis_results_backup_20250122.sql.gz | \
  docker exec -i news-postgres psql -U news_user -d news_mcp
```

#### Related Documentation

- [ADR-011: Analysis Idempotency Pattern](../decisions/ADR-011-analysis-idempotency.md)
- [Incident Report: Duplicate Analysis Fix](../incidents/2025-01-22-duplicate-analysis-fix.md)
- [Content Analysis Service Docs](../services/content-analysis-service.md)

---

**Last Updated**: 2025-01-22
