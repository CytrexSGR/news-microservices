# Deployment Guides

**Created:** 2025-11-09 (Phase 1 Consolidation)
**Purpose:** Deployment procedures, production setup, and operational guides

---

## 📄 Guides Index

| File | Environment | Description |
|------|-------------|-------------|
| PRODUCTION_SETUP.md | Production | Production environment setup and configuration |

---

## 🚀 Deployment Environments

### Development
**Location:** `docker-compose.yml`
- Hot-reload enabled
- Volume mounts for code changes
- Debug logging
- Development credentials

**Quick Start:**
```bash
docker compose up -d
```

### Production
**Location:** `docker-compose.prod.yml`
- Optimized builds
- No volume mounts
- Production logging
- Secure credentials

**Setup:**
See `PRODUCTION_SETUP.md` for full instructions.

---

## 📊 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] Secrets management setup
- [ ] Backup strategy verified

### Deployment
- [ ] Stop services gracefully
- [ ] Run database migrations
- [ ] Build production images
- [ ] Start services
- [ ] Health check verification

### Post-Deployment
- [ ] Smoke tests passed
- [ ] Monitoring alerts configured
- [ ] Performance baselines verified
- [ ] Rollback plan ready

---

## 🔧 Deployment Strategies

### Blue-Green Deployment
- Two identical environments
- Zero-downtime deployment
- Instant rollback capability

### Rolling Deployment
- Gradual service updates
- Minimal downtime
- Progressive validation

### Canary Deployment
- Small subset first
- Monitor metrics
- Gradual rollout

---

## 📈 Monitoring & Health Checks

### Health Endpoints
Every service exposes `/health`:
```bash
curl http://localhost:8100/health  # auth-service
curl http://localhost:8101/health  # feed-service
# ... (all services)
```

### Monitoring Stack
- **Prometheus:** Metrics collection
- **Grafana:** Visualization
- **RabbitMQ UI:** Message queue monitoring
- **Application Logs:** Docker logs

### Alert Configuration
See `/docs/guides/monitoring-guide.md` for alert setup.

---

## 🔒 Security

### Secrets Management
- **Development:** `.env` files (git-ignored)
- **Production:** Environment variables or secrets manager
- **Never commit:** API keys, passwords, tokens

### SSL/TLS
- **Development:** Not required
- **Production:** Required for all external endpoints
- **Certificate Management:** Let's Encrypt or corporate CA

---

## 🔄 Rollback Procedures

### Quick Rollback (< 5 minutes)
```bash
# Revert to previous image tag
docker compose down
git checkout <previous-commit>
docker compose up -d
```

### Database Rollback
```bash
# Revert migration
alembic downgrade -1
```

**IMPORTANT:** Always test rollback procedures in staging first!

---

## 📚 Related Documentation

- **Production Setup:** `PRODUCTION_SETUP.md` (this directory)
- **Docker Guide:** [/docs/guides/docker-guide.md](/docs/guides/docker-guide.md)
- **Database Migrations:** [/docs/guides/migration-protocol.md](/docs/guides/migration-protocol.md)
- **Monitoring:** [/docs/guides/monitoring-guide.md](/docs/guides/monitoring-guide.md)
- **Architecture:** [/ARCHITECTURE.md](/ARCHITECTURE.md)

---

## 🆘 Troubleshooting

### Common Issues

**Services won't start:**
- Check Docker logs: `docker compose logs <service>`
- Verify environment variables
- Check port conflicts

**Database connection errors:**
- Verify PostgreSQL is running
- Check connection string
- Validate credentials

**Performance degradation:**
- Check resource utilization (CPU, memory)
- Review application logs for errors
- Verify database query performance

**For detailed troubleshooting:**
See [/docs/guides/troubleshooting-guide.md](/docs/guides/troubleshooting-guide.md)

---

*For development deployment, see main [README.md](/README.md). For production, see PRODUCTION_SETUP.md in this directory.*
