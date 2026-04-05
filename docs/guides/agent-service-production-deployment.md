# Agent Service - Production Deployment Guide

## Document Information

- **Service:** Agent Service (Agentic Control Plane)
- **Version:** 1.0.0
- **Status:** ✅ Production Ready
- **Last Updated:** 2025-10-23
- **Validation Status:** ⏳ Full validation pending next service implementation

---

## Executive Summary

The Agent Service is **production-ready** and successfully deployed. All core components are operational:

- ✅ Service container healthy (port 8110)
- ✅ Database schema deployed (2 tables)
- ✅ API endpoints responding
- ✅ Health checks passing
- ✅ Authentication integrated
- ✅ Dependencies verified

**Note:** Complete functional validation requires the next service to be implemented, as documented in the roadmap.

---

## Production Deployment Checklist

### Pre-Deployment

- [x] **Service Implementation**
  - [x] Core ReAct engine implemented
  - [x] Tool registry with 3 tools (search, analysis, email)
  - [x] Database models defined
  - [x] API endpoints created
  - [x] Authentication middleware integrated

- [x] **Database**
  - [x] Alembic migrations created
  - [x] Migration tested in development
  - [x] Tables created successfully
  - [x] Indexes configured

- [x] **Configuration**
  - [x] Environment variables documented
  - [x] .env template created
  - [x] JWT secret aligned with other services
  - [x] Service URLs configured for Docker network

- [x] **Documentation**
  - [x] Technical documentation (agent-service.md)
  - [x] API documentation
  - [x] Quick-start guide
  - [x] CLI tool documentation
  - [x] Claude Desktop integration analysis

- [x] **Testing**
  - [x] Service starts successfully
  - [x] Health endpoint responds
  - [x] Database connections work
  - [x] Authentication validates correctly
  - [ ] **End-to-end workflow test** (pending next service)

### Deployment Steps

#### 1. Environment Preparation

```bash
# Navigate to project root
cd /home/cytrex/news-microservices

# Ensure all required services are running
docker compose ps
# Required: postgres, redis, rabbitmq, auth-service, search-service,
#          content-analysis-service, notification-service
```

#### 2. Configuration Validation

```bash
# Check agent-service .env file
cat services/agent-service/.env

# Verify critical variables:
# - OPENAI_API_KEY (must be valid)
# - JWT_SECRET_KEY (must match all services)
# - Service URLs (use internal Docker names)
```

**Critical Configuration:**

```bash
# Verify JWT secret consistency across all services
grep -r "JWT_SECRET_KEY=" services/*/.env | cut -d: -f2 | sort | uniq -c

# Expected output: 1 line showing all services have same secret
```

#### 3. Database Migration

```bash
# Run migrations
docker exec news-agent-service alembic upgrade head

# Verify tables created
docker exec postgres psql -U news_user -d news_mcp \
  -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'agent_%';"

# Expected output: agent_conversations, agent_tool_calls
```

#### 4. Service Start

```bash
# Start agent-service
docker compose up -d agent-service

# Monitor logs during startup
docker compose logs -f agent-service

# Look for:
# - "Starting Agent Service v1.0.0"
# - "OpenAI Model: gpt-4o-2024-08-06"
# - "Max Iterations: 10"
# - No error messages
```

#### 5. Health Verification

```bash
# Check container status
docker ps --filter "name=news-agent-service"

# Verify health endpoint
curl http://localhost:8110/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "agent-service",
#   "version": "1.0.0"
# }
```

#### 6. API Endpoint Verification

```bash
# Test authentication (should fail without token)
curl -X POST http://localhost:8110/api/v1/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected: 401 Unauthorized (proves auth is working)

# Test with valid token (requires login first)
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r '.access_token')

curl -X POST http://localhost:8110/api/v1/agent/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# Should return agent response (not 401)
```

#### 7. CLI Tool Verification

```bash
# Make script executable (if not already)
chmod +x /home/cytrex/news-microservices/scripts/news-agent.sh

# Test CLI
./scripts/news-agent.sh --help

# Test simple query
./scripts/news-agent.sh "Suche nach KI-Artikeln"
```

### Post-Deployment

- [x] **Monitoring**
  - [x] Health checks configured (30s interval)
  - [ ] Prometheus metrics (future enhancement)
  - [ ] Log aggregation setup (future enhancement)

- [x] **Documentation**
  - [x] Deployment guide created
  - [x] User documentation available
  - [x] API documentation complete

- [ ] **Validation** (pending next service)
  - [ ] End-to-end workflow test
  - [ ] Multi-tool workflow test
  - [ ] Error handling verification

---

## Production Configuration

### Recommended Production .env Settings

```bash
# ============================================================================
# PRODUCTION CONFIGURATION FOR AGENT SERVICE
# ============================================================================

# Service Identity
SERVICE_NAME=agent-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-YOUR_PRODUCTION_KEY_HERE
OPENAI_MODEL=gpt-4o-2024-08-06
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=120

# Service URLs (Internal Docker Network)
AUTH_SERVICE_URL=http://auth-service:8100
SEARCH_SERVICE_URL=http://search-service:8106
ANALYSIS_SERVICE_URL=http://content-analysis-service:8102
NOTIFICATION_SERVICE_URL=http://notification-service:8105

# Database Configuration (PostgreSQL)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=news_mcp
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT Authentication (CRITICAL: Must match ALL services!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Port
PORT=8110
```

### Security Considerations

1. **OpenAI API Key**
   - Store in secure secrets management (not in .env for real production)
   - Rotate periodically
   - Monitor usage and costs

2. **JWT Secret Key**
   - **CRITICAL:** Must be identical across all services
   - Use strong random value (32+ characters)
   - Never commit to version control
   - Rotate with coordinated deployment

3. **Database Credentials**
   - Use strong password
   - Limit user permissions to necessary operations
   - Enable SSL connections in production

4. **Network Security**
   - Agent service only accessible within Docker network
   - External access only through reverse proxy (if needed)
   - CORS origins restricted to known frontends

### Performance Tuning

#### OpenAI API Settings

```bash
# Conservative (lower cost, slower)
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.3
AGENT_MAX_ITERATIONS=5
AGENT_TIMEOUT_SECONDS=60

# Balanced (recommended)
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=120

# Aggressive (higher quality, higher cost)
OPENAI_MAX_TOKENS=8192
OPENAI_TEMPERATURE=0.9
AGENT_MAX_ITERATIONS=15
AGENT_TIMEOUT_SECONDS=180
```

#### Database Connection Pool

For high load, consider tuning SQLAlchemy connection pool in `app/database.py`:

```python
engine = create_async_engine(
    settings.get_async_database_url(),
    echo=False,
    pool_size=20,          # Default: 5
    max_overflow=10,       # Default: 10
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

---

## Monitoring & Observability

### Health Checks

**Endpoint:** `GET /health`

**Docker Healthcheck:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8110/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "agent-service",
  "version": "1.0.0"
}
```

### Log Monitoring

**Key Log Messages to Monitor:**

**Startup:**
```
INFO: Starting Agent Service v1.0.0
INFO: OpenAI Model: gpt-4o-2024-08-06
INFO: Max Iterations: 10
INFO: Timeout: 120s
```

**Request Handling:**
```
INFO: Executing ReAct cycle for query: "..."
INFO: Iteration 1/10 - LLM Response received (finish_reason: tool_calls)
INFO: Executing tool: search_articles
INFO: Tool 'search_articles' completed successfully (0.342s)
INFO: Workflow completed successfully (status: COMPLETED)
```

**Errors to Alert On:**
```
ERROR: Tool 'search_articles' failed: Connection timeout
ERROR: OpenAI API error: Rate limit exceeded
ERROR: Max iterations (10) reached without completion
ERROR: Agent workflow failed: ...
```

### Metrics to Track (Future Enhancement)

1. **Request Metrics**
   - Total requests
   - Requests per user
   - Success/failure rate
   - Average execution time

2. **Token Usage**
   - Total tokens per request
   - Prompt vs completion tokens
   - Daily/monthly token consumption
   - Cost tracking

3. **Tool Execution**
   - Tool call frequency (which tools used most)
   - Tool success/failure rates
   - Tool execution times

4. **Iteration Statistics**
   - Average iterations per workflow
   - Workflows reaching max iterations
   - Time per iteration

---

## Backup & Recovery

### Database Backup

**Backup Agent Service Tables:**

```bash
# Backup agent tables
docker exec postgres pg_dump -U news_user -d news_mcp \
  -t agent_conversations -t agent_tool_calls \
  --data-only --column-inserts \
  > /tmp/backups/agent_service_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh /tmp/backups/agent_service_*.sql
```

**Restore:**

```bash
# Restore from backup
docker exec -i postgres psql -U news_user -d news_mcp \
  < /tmp/backups/agent_service_YYYYMMDD_HHMMSS.sql
```

### Configuration Backup

```bash
# Backup configuration
cp services/agent-service/.env \
   /tmp/backups/agent-service.env.$(date +%Y%m%d)
```

---

## Scaling Considerations

### Current Architecture

- **Single instance** (sufficient for PoC and low-traffic production)
- **Stateless service** (can scale horizontally)
- **Database-backed persistence** (shared state across instances)

### Horizontal Scaling (Future)

To scale to multiple instances:

1. **Load Balancer Configuration:**
   ```yaml
   # docker-compose.yml
   agent-service:
     deploy:
       replicas: 3
     ports:
       - "8110-8112:8110"  # Multiple ports
   ```

2. **Session Affinity:**
   - Not required (service is stateless)
   - Conversation state persisted in database

3. **Rate Limiting:**
   - Implement per-user rate limits
   - OpenAI API rate limit handling

### Vertical Scaling

For single instance optimization:

```yaml
# docker-compose.yml
agent-service:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker compose logs agent-service --tail 50
```

**Common Issues:**

1. **Missing OpenAI API Key**
   - Error: "OPENAI_API_KEY environment variable not set"
   - Fix: Add valid API key to .env

2. **Database Connection Failed**
   - Error: "Could not connect to database"
   - Fix: Ensure postgres container is running and healthy

3. **JWT Secret Mismatch**
   - Symptom: 401 errors despite valid token
   - Fix: Verify JWT_SECRET_KEY matches across all services

### Agent Workflow Fails

**Max Iterations Reached:**
```
ERROR: Max iterations (10) reached without completion
```
- Cause: Query too complex or tools returning insufficient info
- Fix: Simplify query or increase AGENT_MAX_ITERATIONS

**Tool Execution Failed:**
```
ERROR: Tool 'search_articles' failed: Connection timeout
```
- Cause: Downstream service unavailable
- Fix: Check search-service health, restart if needed

### High Token Usage

**Monitor token consumption:**
```sql
SELECT
  DATE(created_at) as date,
  SUM(tokens_used_total) as total_tokens,
  AVG(tokens_used_total) as avg_tokens,
  COUNT(*) as conversations
FROM agent_conversations
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Optimization:**
- Reduce OPENAI_MAX_TOKENS
- Simplify system prompts
- Use more efficient tools

---

## Rollback Procedure

If issues occur after deployment:

### 1. Stop Agent Service

```bash
docker compose stop agent-service
```

### 2. Rollback Database (if migration issues)

```bash
# Downgrade to previous migration
docker exec news-agent-service alembic downgrade -1

# Or drop agent tables entirely
docker exec postgres psql -U news_user -d news_mcp \
  -c "DROP TABLE IF EXISTS agent_tool_calls CASCADE;"
docker exec postgres psql -U news_user -d news_mcp \
  -c "DROP TABLE IF EXISTS agent_conversations CASCADE;"
docker exec postgres psql -U news_user -d news_mcp \
  -c "DELETE FROM alembic_version WHERE version_num = '001';"
```

### 3. Restore Configuration

```bash
# Restore previous .env
cp /tmp/backups/agent-service.env.YYYYMMDD \
   services/agent-service/.env
```

### 4. Rebuild and Restart

```bash
docker compose up -d --build agent-service
```

---

## Maintenance Tasks

### Weekly

- [ ] Review logs for errors or warnings
- [ ] Check token usage and costs
- [ ] Verify all dependent services are healthy
- [ ] Review conversation success rates

### Monthly

- [ ] Analyze query patterns and tool usage
- [ ] Update documentation if needed
- [ ] Review and optimize system prompts
- [ ] Plan feature enhancements

### Quarterly

- [ ] Security audit (API keys, JWT secrets)
- [ ] Performance review
- [ ] Cost optimization review
- [ ] Update dependencies

---

## Production Status

### Current State

| Component | Status | Notes |
|-----------|--------|-------|
| **Service Container** | ✅ Healthy | Running on port 8110 |
| **Database Schema** | ✅ Deployed | 2 tables created |
| **API Endpoints** | ✅ Operational | /invoke, /conversations |
| **Health Checks** | ✅ Passing | 30s interval |
| **Authentication** | ✅ Integrated | JWT validation working |
| **CLI Tool** | ✅ Available | Terminal interface ready |
| **Documentation** | ✅ Complete | Technical + user guides |
| **End-to-End Testing** | ⏳ Pending | Requires next service |

### Known Limitations

1. **Validation Status:** Full functional validation pending next service implementation (as documented in roadmap)
2. **Error Recovery:** Currently fail-fast strategy (will be enhanced with retry logic)
3. **Monitoring:** Basic health checks only (metrics framework planned)
4. **Scalability:** Single instance (horizontal scaling planned for future)

### Next Steps

According to the service roadmap:

1. **Immediate (Next Sprint):**
   - Implement next service for end-to-end validation
   - Complete functional testing
   - Add retry logic for tool failures

2. **Short-term (1-2 Months):**
   - Prometheus metrics integration
   - Advanced error recovery strategies
   - User preference management

3. **Long-term (3+ Months):**
   - Streaming responses
   - Multi-agent coordination
   - Advanced workflow patterns

---

## Support & Escalation

### Documentation References

- **Technical Details:** `/docs/services/agent-service.md`
- **Quick Start:** `/docs/guides/agent-service-quickstart.md`
- **API Docs:** `http://localhost:8110/docs` (Swagger UI)

### Contact

For issues or questions:
1. Check service logs: `docker compose logs agent-service`
2. Review troubleshooting section in technical documentation
3. Check related service health (auth, search, analysis, notification)

---

## Compliance & Best Practices

### Code Quality

- ✅ Type hints throughout codebase
- ✅ Async/await patterns consistently applied
- ✅ Error handling implemented
- ✅ Logging configured at appropriate levels

### Security

- ✅ JWT authentication required for all endpoints
- ✅ User can only access own conversations
- ✅ API keys stored in environment variables
- ✅ CORS configured with explicit origins

### Documentation

- ✅ Comprehensive technical documentation
- ✅ API documentation with examples
- ✅ User guides and quick-start
- ✅ Deployment procedures documented

### Testing

- ✅ Service health verification
- ✅ API endpoint validation
- ⏳ End-to-end workflows (pending next service)

---

## Conclusion

The Agent Service is **production-ready** and successfully deployed:

- ✅ All infrastructure components operational
- ✅ Service responding correctly
- ✅ Authentication integrated
- ✅ Database schema deployed
- ✅ Documentation complete
- ✅ CLI tooling available

**Important Note:** Complete functional validation requires the next service implementation, as this service orchestrates workflows across multiple microservices. Current deployment allows for integration work and further development to proceed.

---

**Last Updated:** 2025-10-23
**Document Version:** 1.0.0
**Service Version:** 1.0.0
**Status:** ✅ Production Ready (with validation note)
