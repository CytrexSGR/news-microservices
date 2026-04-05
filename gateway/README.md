# Traefik API Gateway

## Overview

This is the API Gateway configuration for the News-MCP microservices architecture using Traefik v2.10. It provides centralized routing, authentication, rate limiting, and monitoring for all microservices.

## Features

- **Dynamic Routing**: Route requests to appropriate microservices
- **JWT Authentication**: Validate tokens via Auth Service
- **Rate Limiting**: Protect services from abuse (100 req/min default)
- **CORS Handling**: Support cross-origin requests
- **SSL/TLS Termination**: HTTPS with Let's Encrypt
- **Load Balancing**: Distribute traffic across service instances
- **Canary Deployments**: Gradual rollout with traffic splitting
- **Health Checks**: Monitor service availability
- **Metrics & Tracing**: Prometheus metrics and Jaeger tracing
- **WebSocket Support**: Handle real-time connections
- **Circuit Breaker**: Protect services from cascading failures

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for convenience commands)
- Valid domain name (for production SSL)

### Development Setup

1. **Clone and navigate to gateway directory:**
   ```bash
   cd /home/cytrex/news-microservices/gateway
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the gateway:**
   ```bash
   make up
   # OR without make:
   docker compose up -d
   ```

4. **Verify health:**
   ```bash
   make health
   # OR:
   ./scripts/health-check.sh
   ```

5. **Test routes:**
   ```bash
   make test
   # OR:
   ./scripts/test-routes.sh
   ```

## Architecture

```
Internet
    |
    v
[Traefik Gateway]
    |
    +---> Auth Service (port 8000)
    |
    +---> Feed Service (port 8001)
    |
    +---> Content Analysis Service (port 8002) [Phase 2]
    |
    +---> Research Service (port 8003) [Phase 2]
    |
    +---> OSINT Service (port 8004) [Phase 2]
```

## Configuration

### Routes

All routes are defined in `config/routes.yml`:

| Route Pattern | Service | Authentication | Description |
|--------------|---------|---------------|-------------|
| `/api/v1/auth/*` | auth-service:8000 | No | Authentication endpoints |
| `/api/v1/users/*` | auth-service:8000 | Yes (JWT) | User management |
| `/api/v1/feeds/*` | feed-service:8001 | Yes (JWT) | Feed management |
| `/health` | health-service | No | Gateway health check |
| `/api/docs` | api-docs-service | Basic Auth | API documentation |
| `/ws/feeds` | feed-service-ws | Yes (JWT) | WebSocket for feeds |

### Middlewares

Configured middlewares in `config/middlewares.yml`:

| Middleware | Purpose | Configuration |
|-----------|---------|---------------|
| `secure-headers` | Security headers | HSTS, CSP, X-Frame-Options |
| `cors` | CORS handling | Allow localhost:3000/3001 |
| `rate-limit` | Rate limiting | 100 req/min per IP |
| `jwt-auth` | JWT validation | Forward auth to auth-service |
| `request-id` | Request tracking | Add X-Request-Id header |
| `compress` | Response compression | gzip for > 1KB |

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# JWT Configuration
JWT_SECRET=your-jwt-secret-key
SERVICE_JWT_SECRET=service-jwt-secret

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
FEED_SERVICE_URL=http://feed-service:8001

# Rate Limiting
RATE_LIMIT_AVERAGE=100
RATE_LIMIT_BURST=200

# SSL
SSL_EMAIL=admin@news-mcp.local
DOMAIN=news-mcp.local
```

## Usage

### Management Commands

```bash
# Start/stop gateway
make up
make down
make restart

# View logs
make logs
docker compose logs -f traefik

# Health checks
make health
./scripts/health-check.sh

# Test all routes
make test
./scripts/test-routes.sh --verbose

# Deploy to Kubernetes
make deploy

# Start canary deployment
make canary SERVICE=auth-service VERSION=v2

# View metrics
make metrics
curl http://localhost:8082/metrics

# Access dashboard
make dashboard
# Browse to http://localhost:8080
# Login: admin / SecurePass123!
```

### Canary Deployments

Deploy new versions gradually:

```bash
# Start canary deployment (10% → 25% → 50% → 75% → 100%)
./scripts/canary-rollout.sh auth-service v2

# Monitor progress
docker logs -f news-gateway

# Rollback if needed
./scripts/canary-rollout.sh --rollback auth-service
```

### Adding New Services

1. **Update routes configuration** (`config/routes.yml`):
   ```yaml
   http:
     routers:
       new-service-api:
         rule: "PathPrefix(`/api/v1/new-service`)"
         service: new-service
         middlewares:
           - secure-headers
           - cors
           - rate-limit
           - jwt-auth

     services:
       new-service:
         loadBalancer:
           servers:
             - url: "http://new-service:8005"
           healthCheck:
             path: /health
   ```

2. **Reload configuration:**
   ```bash
   make reload
   ```

### Custom Middleware

Add custom middleware in `config/middlewares.yml`:

```yaml
http:
  middlewares:
    custom-auth:
      forwardAuth:
        address: "http://custom-auth:8000/validate"
        authResponseHeaders:
          - X-User-Id
          - X-Permissions
```

## Monitoring

### Prometheus Metrics

Metrics available at `http://localhost:8082/metrics`:

- Request count by service
- Response time percentiles
- Error rates
- Active connections

### Distributed Tracing

Jaeger UI available at `http://localhost:16686`:

- Request flow visualization
- Latency breakdown
- Error tracking

### Access Logs

JSON-formatted logs in `logs/access.json`:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "method": "GET",
  "path": "/api/v1/feeds",
  "status": 200,
  "duration": 45,
  "client_ip": "192.168.1.100"
}
```

## Security

### JWT Validation

All protected endpoints require JWT tokens:

```bash
# Get token
TOKEN=$(curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r .token)

# Use token
curl http://localhost/api/v1/feeds \
  -H "Authorization: Bearer $TOKEN"
```

### Rate Limiting

Default limits:
- 100 requests/minute per IP
- Burst of 200 requests allowed
- Configurable per route

### Security Headers

Automatically added to all responses:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy`

## Kubernetes Deployment

### Deploy to K8s

```bash
# Create namespace
kubectl create namespace news-microservices

# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n news-microservices
kubectl get svc -n news-microservices

# View logs
kubectl logs -n news-microservices -l app=traefik
```

### Scaling

```bash
# Scale replicas
kubectl scale deployment traefik-gateway \
  -n news-microservices --replicas=3

# Autoscaling
kubectl autoscale deployment traefik-gateway \
  -n news-microservices --min=2 --max=10 --cpu-percent=70
```

## Troubleshooting

### Common Issues

1. **Gateway not accessible:**
   ```bash
   # Check container status
   docker ps | grep traefik

   # Check logs
   docker logs news-gateway

   # Test connectivity
   curl http://localhost/health
   ```

2. **Service not reachable:**
   ```bash
   # Check network
   docker exec news-gateway ping auth-service

   # Check DNS
   docker exec news-gateway nslookup auth-service

   # Check service health
   curl http://auth-service:8000/health
   ```

3. **JWT validation failing:**
   ```bash
   # Test auth endpoint directly
   curl http://auth-service:8000/api/v1/auth/validate \
     -H "Authorization: Bearer $TOKEN"

   # Check middleware config
   grep jwt-auth config/middlewares.yml
   ```

4. **Rate limiting issues:**
   ```bash
   # Check current limits
   grep rate-limit config/middlewares.yml

   # Test rate limiting
   for i in {1..150}; do
     curl http://localhost/health
   done
   ```

5. **SSL certificate problems:**
   ```bash
   # Check certificate
   openssl s_client -connect localhost:443 \
     -servername api.news-mcp.local

   # Generate new dev certs
   make certs
   ```

### Debug Mode

Enable debug logging:

```bash
# Enable debug
make debug

# View debug logs
docker logs -f news-gateway | grep DEBUG

# Disable debug
docker exec news-gateway sh -c \
  'sed -i "s/level: DEBUG/level: INFO/" /etc/traefik/traefik.yml'
make reload
```

## Performance Tuning

### Optimization Tips

1. **Connection pooling:**
   ```yaml
   serversTransport:
     maxIdleConnsPerHost: 200
   ```

2. **Compression:**
   ```yaml
   compress:
     minResponseBodyBytes: 1024
   ```

3. **Caching headers:**
   ```yaml
   headers:
     customResponseHeaders:
       Cache-Control: "public, max-age=3600"
   ```

4. **Circuit breaker:**
   ```yaml
   circuitBreaker:
     expression: "NetworkErrorRatio() > 0.5"
   ```

## Development

### Local Testing

```bash
# Start in development mode
make dev-up

# Watch logs
make dev-logs

# Run tests
make test

# Performance test
make perf
```

### Adding Features

1. Create feature branch
2. Update configuration files
3. Test locally
4. Update documentation
5. Submit PR

## License

MIT

## Support

For issues or questions:
- Check logs: `docker logs news-gateway`
- Run health check: `make health`
- Review configuration: `make config`

## Maintenance

### Backup

```bash
# Backup configuration
make backup

# Restore from backup
make restore BACKUP_FILE=backups/traefik-config-20240101-120000.tar.gz
```

### Updates

```bash
# Update Traefik version
docker pull traefik:v2.10
make restart
```

## References

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [JWT RFC](https://tools.ietf.org/html/rfc7519)
- [CORS Specification](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)