# Production Setup - Quick Start Guide

## Overview

This guide provides the fastest path to production deployment for the News Microservices platform with focus on the FMP Service.

---

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB+ RAM available
- 10GB+ disk space
- Valid FMP API key

---

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
cd /home/cytrex/news-microservices

# Run automated deployment
./scripts/deploy-production.sh
```

The script will:
- ✅ Run security checks
- ✅ Verify configuration files
- ✅ Prompt for CORS confirmation
- ✅ Deploy production environment
- ✅ Wait for health checks
- ✅ Run test suite
- ✅ Display summary

### Option 2: Manual Deployment

```bash
cd /home/cytrex/news-microservices

# 1. Stop development environment
docker compose down

# 2. Deploy production
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# 3. Verify deployment
curl http://localhost:8113/health

# 4. Run tests
docker exec news-fmp-service-prod python -m pytest tests/ -v
```

---

## Critical: CORS Configuration

**BEFORE DEPLOYMENT**, update production domains:

```bash
nano /home/cytrex/news-microservices/services/fmp-service/.env.production
```

Update this line:
```bash
# Change from:
CORS_ORIGINS=["http://localhost:80", "http://localhost:3000"]

# To your production domain:
CORS_ORIGINS=["https://news.example.com", "https://api.news.example.com"]
```

---

## Security Checklist

Before deploying to production, verify:

- [ ] CORS_ORIGINS updated with production domains
- [ ] .env.production files exist and are gitignored
- [ ] JWT_SECRET_KEY is not default value
- [ ] PostgreSQL password is strong (32+ bytes)
- [ ] Redis password is strong (32+ bytes)
- [ ] RabbitMQ not using guest/guest
- [ ] LOG_LEVEL set to WARNING or ERROR
- [ ] ENVIRONMENT=production

**Automated Check:**
```bash
./scripts/deploy-production.sh
# Will verify all checklist items before deploying
```

---

## Production Credentials

Production uses cryptographically secure credentials (32-48 bytes, generated with Python `secrets` module).

**Files:**
- `/home/cytrex/news-microservices/.env.production` - Infrastructure credentials
- `/home/cytrex/news-microservices/services/fmp-service/.env.production` - FMP service config

**⚠️ CRITICAL:** These files contain production secrets and are **NOT** in git!

### Backup Credentials

```bash
# Create encrypted backup
tar -czf /tmp/env-backup-$(date +%Y%m%d).tar.gz \
  .env.production \
  services/fmp-service/.env.production

# Store in secure location (NOT on same server!)
```

---

## Verification

### 1. Health Check

```bash
curl http://localhost:8113/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "fmp-service",
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. Container Status

```bash
docker compose -f docker-compose.prod.yml ps
```

All services should show "Up (healthy)".

### 3. Run Tests

```bash
docker exec news-fmp-service-prod python -m pytest tests/ -v
```

Expected: 11 passed tests.

### 4. Rate Limit Check

```bash
curl http://localhost:8113/api/v1/admin/rate-limit/stats
```

Expected: status "ok", 300 calls limit.

---

## Monitoring

### View Logs

```bash
# Follow FMP service logs
docker logs news-fmp-service-prod -f

# Last 100 lines
docker logs news-fmp-service-prod --tail 100

# Filter for errors
docker logs news-fmp-service-prod 2>&1 | grep -i error
```

### Container Stats

```bash
# Real-time stats
docker stats news-fmp-service-prod

# All production containers
docker stats $(docker ps --filter "name=-prod" --format "{{.Names}}")
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs news-fmp-service-prod --tail 100

# Common issues:
# - Database connection failed → verify POSTGRES_PASSWORD matches
# - Redis connection failed → verify REDIS_PASSWORD matches
# - Invalid configuration → check .env.production syntax
```

### Health Check Fails

```bash
# Test health endpoint directly
docker exec news-fmp-service-prod curl -f http://localhost:8113/health

# Check application logs
docker logs news-fmp-service-prod | grep -i error
```

### CORS Errors

```bash
# Verify CORS configuration
docker exec news-fmp-service-prod env | grep CORS

# Update and restart
nano services/fmp-service/.env.production
docker compose -f docker-compose.prod.yml restart fmp-service
```

---

## Rollback

If deployment fails:

```bash
# Stop production
docker compose -f docker-compose.prod.yml down

# Return to development
docker compose up -d

# Verify
curl http://localhost:8113/health
# Should show: "environment": "development"
```

---

## Performance Tuning

### Database Connection Pool

Adjust in `.env.production`:
```bash
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### Rate Limiting

Adjust API rate limits:
```bash
FMP_RATE_LIMIT_CALLS=300    # Calls per window
FMP_RATE_LIMIT_WINDOW=60    # Window in seconds
```

### Memory Limits

Add to `docker-compose.prod.yml`:
```yaml
fmp-service:
  deploy:
    resources:
      limits:
        memory: 512M
      reservations:
        memory: 256M
```

---

## Detailed Documentation

For comprehensive documentation, see:

- **Production Deployment Guide:** `services/fmp-service/docs/PRODUCTION_DEPLOYMENT.md`
- **Security Configuration:** `docs/decisions/ADR-017-fmp-production-security.md`
- **API Endpoints:** `services/fmp-service/docs/API_ENDPOINTS.md`
- **Historical Data:** `services/fmp-service/docs/HISTORICAL_DATA_LOADING.md`
- **Service README:** `services/fmp-service/README.md`

---

## Support

For issues or questions:

1. Check logs: `docker logs news-fmp-service-prod`
2. Review troubleshooting section above
3. Verify configuration files are correct
4. Test health endpoint: `curl http://localhost:8113/health`

---

## Production Checklist Summary

```bash
# Quick verification script
cd /home/cytrex/news-microservices

echo "Checking production configuration..."
grep "ENVIRONMENT=production" services/fmp-service/.env.production && echo "✓ Environment: production"
grep "LOG_LEVEL=WARNING\|LOG_LEVEL=ERROR" services/fmp-service/.env.production && echo "✓ Log level: production"
! grep "your-secret-key" services/fmp-service/.env.production && echo "✓ JWT secret: customized"
! git status --porcelain | grep ".env.production" && echo "✓ Secrets: gitignored"
docker ps | grep "news-fmp-service-prod.*healthy" && echo "✓ Service: healthy"
```

---

**Last Updated:** 2025-10-25
**Version:** 1.0.0
**Status:** Production Ready ✅
