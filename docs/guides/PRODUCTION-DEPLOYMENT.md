# Production Deployment Guide

**Created:** 2025-10-18
**Status:** Frontend Production-Ready, Backend in Progress

---

## Quick Start

### Development (Current Default)

```bash
cd /home/cytrex/news-microservices
docker compose up -d
```

**What this does:**
- ✅ Starts all infrastructure (postgres, redis, rabbitmq)
- ✅ Starts all backend services with hot-reload
- ✅ Starts frontend with Vite dev server
- ✅ Code changes auto-reload (< 1 second)

### Production (When Ready)

```bash
cd /home/cytrex/news-microservices
docker compose -f docker-compose.prod.yml up -d
```

**What this does:**
- ✅ Builds optimized production images
- ✅ Frontend: Nginx serving static build (~59 MB)
- ⚠️ Backend: Still uses dev images (TODO)

---

## Production Files

### Frontend Production Stack ✅

**1. Production Dockerfile**
- **File:** `frontend/Dockerfile`
- **Size:** 59.1 MB (multi-stage: Node → Nginx)
- **Contents:**
  - Stage 1: Node 20 alpine, npm install, Vite build
  - Stage 2: Nginx alpine, copy dist/, serve static files

**2. Nginx Configuration**
- **File:** `frontend/nginx.conf`
- **Features:**
  - Gzip compression
  - Security headers
  - API proxy to all 8 backend services
  - Static file caching (1 year)
  - SPA fallback routing
  - Health check endpoint: `/health`

**3. Production Compose**
- **File:** `docker-compose.prod.yml`
- **Status:** Frontend complete, backend in progress
- **Includes:**
  - Infrastructure with production settings
  - Frontend with production Dockerfile
  - Backend services (currently using dev Dockerfiles)

---

## Build & Deploy

### Build Production Frontend

```bash
cd /home/cytrex/news-microservices/frontend
docker build -t news-frontend-prod:latest .
```

**Verification:**
```bash
# Check image size (should be ~59 MB)
docker images news-frontend-prod:latest --format "{{.Size}}"

# Inspect layers
docker history news-frontend-prod:latest
```

### Deploy Full Stack (Production)

```bash
cd /home/cytrex/news-microservices
docker compose -f docker-compose.prod.yml up -d --build
```

**Access:**
- Frontend: http://localhost (port 80)
- Backend APIs: http://localhost:8100-8108

---

## Architecture Differences

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| **Frontend** | Vite dev server (port 3000) | Nginx static serve (port 80) |
| **Hot-reload** | ✅ Volume mounts | ❌ Optimized build |
| **Source maps** | ✅ Full debugging | ⚠️ Limited (build config) |
| **API Proxy** | Vite proxy | Nginx proxy |
| **Image size** | Not optimized | 59 MB (optimized) |
| **Dependencies** | All (dev + prod) | Production only |

### Network Flow

**Development:**
```
Browser → localhost:3000 → Vite Dev Server
                          ↓ Proxy
                    Backend Services (8100-8108)
```

**Production:**
```
Browser → localhost:80 → Nginx
                       ↓ Static Files (/)
                       ↓ Proxy (/api/v1/*)
                    Backend Services (8100-8108)
```

---

## Frontend Production Features

### Optimizations

1. **Multi-stage Build**
   - Stage 1 (builder): 600+ MB with build tools
   - Stage 2 (runtime): 59 MB with only nginx + static files
   - ~90% size reduction

2. **Nginx Optimizations**
   - Gzip compression (6/10 level)
   - Static file caching (1 year expires)
   - Worker process auto-tuning
   - TCP optimizations (sendfile, tcp_nopush)

3. **Security Headers**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block
   - Referrer-Policy: no-referrer-when-downgrade

4. **API Proxying**
   - All `/api/v1/*` routes proxied to backend
   - WebSocket support (upgrade headers)
   - Real-IP forwarding (X-Forwarded-For)

### Health Check

**Endpoint:** `http://localhost/health`

**Response:** `healthy` (200 OK)

**Docker Health Check:**
```bash
docker inspect news-frontend-prod | grep -A10 Health
```

---

## Backend Production (TODO)

### Current Status

**⚠️ Using Development Dockerfiles in Production**

All backend services currently use `Dockerfile.dev`:
- Volume mounts included (not needed in production)
- Dev dependencies installed (pytest, black, mypy)
- Not optimized for size

### What's Needed

**1. Create Production Dockerfiles**

Each service needs `services/*/Dockerfile`:

```dockerfile
# Example: services/auth-service/Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Update docker-compose.prod.yml**

Replace `dockerfile: Dockerfile.dev` with `dockerfile: Dockerfile`:

```yaml
auth-service:
  build:
    context: ./services/auth-service
    dockerfile: Dockerfile  # Changed from Dockerfile.dev
```

**3. Optimize for Size**

Target sizes:
- Simple services (auth, feed, notification): < 400 MB
- Medium services (search, analytics): < 500 MB
- Complex services (content-analysis): < 600 MB

**See:** `docs/DOCKER-COMPOSE-WATCH-EXAMPLE.md` for optimization details

---

## Deployment Checklist

### Before Deploying to Production

- [ ] Environment variables configured
  - Database credentials
  - Redis password
  - RabbitMQ credentials
  - API secrets (OpenAI, etc.)

- [ ] Secrets management
  - Create `.env.prod` with production secrets
  - **NEVER commit .env.prod to git**
  - Use Docker secrets or Kubernetes secrets

- [ ] Database migrations
  - Run all migrations: `alembic upgrade head`
  - Verify schema version
  - Backup database before deploy

- [ ] Build all images
  ```bash
  docker compose -f docker-compose.prod.yml build
  ```

- [ ] Test locally
  ```bash
  docker compose -f docker-compose.prod.yml up -d
  # Verify all services healthy
  docker compose -f docker-compose.prod.yml ps
  ```

- [ ] SSL/TLS setup
  - Configure nginx for HTTPS
  - Obtain SSL certificates (Let's Encrypt)
  - Update nginx.conf with SSL config

---

## CI/CD Pipeline (Future)

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build frontend
        run: |
          cd frontend
          docker build -t news-frontend-prod:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push news-frontend-prod:${{ github.sha }}
```

### Image Registry Options

1. **Docker Hub** - Public/private repositories
2. **GitHub Container Registry (GHCR)** - Free for public repos
3. **AWS ECR** - If deploying to AWS
4. **Google GCR** - If deploying to GCP

---

## Monitoring & Logging

### Health Checks

**Check all services:**
```bash
docker compose -f docker-compose.prod.yml ps
```

**Individual service logs:**
```bash
docker compose -f docker-compose.prod.yml logs <service> -f
```

### Nginx Access Logs

```bash
docker exec news-frontend-prod tail -f /var/log/nginx/access.log
```

### Application Metrics

**TODO: Add monitoring**
- Prometheus for metrics
- Grafana for dashboards
- Loki for log aggregation

---

## Rollback Strategy

### Quick Rollback

```bash
# Stop current deployment
docker compose -f docker-compose.prod.yml down

# Start previous version
docker compose -f docker-compose.prod.yml up -d
```

### Version Tagging

```bash
# Tag current build
docker tag news-frontend-prod:latest news-frontend-prod:v1.0.0

# Rollback to specific version
docker tag news-frontend-prod:v1.0.0 news-frontend-prod:latest
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Frontend Not Accessible

**1. Check container status:**
```bash
docker compose -f docker-compose.prod.yml ps frontend
```

**2. Check nginx logs:**
```bash
docker compose -f docker-compose.prod.yml logs frontend
```

**3. Common issues:**
- Port 80 already in use → Change in docker-compose.prod.yml
- Backend services not found → Ensure services in same network
- Nginx config syntax error → Validate with `nginx -t`

### Backend Connection Issues

**1. Check network:**
```bash
docker network inspect news-microservices_news_network
```

**2. Test connectivity from frontend container:**
```bash
docker exec news-frontend-prod wget -O- http://news-auth-service:8000/health
```

**3. Verify proxy config:**
```bash
docker exec news-frontend-prod cat /etc/nginx/nginx.conf | grep upstream
```

---

## Performance Tuning

### Nginx Worker Processes

Auto-tuned by default, but can be set manually:

```nginx
# nginx.conf
worker_processes 4;  # Number of CPU cores
```

### Gzip Compression

Already enabled for:
- text/plain, text/css, text/xml
- application/json, application/javascript
- font files, SVG

### Static File Caching

Currently set to 1 year for versioned assets:

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## Cost Estimation

### Development Environment

**Resources:**
- CPU: ~4 cores
- RAM: ~8 GB
- Disk: ~20 GB

**Cost:** $0 (local development)

### Production Environment (Example)

**Small deployment (1000 users):**
- VM: 4 CPU, 8 GB RAM → ~$40/month
- Database: Managed PostgreSQL → ~$30/month
- Total: ~$70/month

**Medium deployment (10,000 users):**
- VMs: 2x (8 CPU, 16 GB RAM) → ~$160/month
- Database: Managed PostgreSQL (HA) → ~$100/month
- Load Balancer → ~$20/month
- Total: ~$280/month

---

## Next Steps

### Immediate (Before Production Deploy)

1. ✅ Create backend production Dockerfiles
2. ✅ Update docker-compose.prod.yml with production images
3. ✅ Set up environment variable management
4. ✅ Configure SSL/TLS for HTTPS

### Soon

1. ⚠️ Set up monitoring (Prometheus + Grafana)
2. ⚠️ Implement CI/CD pipeline
3. ⚠️ Database backup strategy
4. ⚠️ Log aggregation (ELK or Loki)

### Later

1. ⏳ Kubernetes migration (if scaling beyond single server)
2. ⏳ CDN for static assets
3. ⏳ Multi-region deployment
4. ⏳ Advanced caching strategies

---

**Last Updated:** 2025-10-18
**Status:** Frontend Production-Ready ✅
**Next Review:** When backend production Dockerfiles are created
