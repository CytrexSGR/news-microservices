# n8n Workflow Automation Service

**Service Type**: External Tool (Docker Container)
**Container**: `news-n8n`
**Version**: 1.117.2
**Purpose**: Event-driven workflow automation and orchestration
**Status**: ✅ Production-ready

---

## Overview

n8n is a workflow automation platform integrated into the News Microservices stack for:
- **Event Processing**: RabbitMQ message monitoring and handling
- **Authentication Automation**: JWT token auto-refresh
- **API Orchestration**: Multi-service workflow coordination
- **Scheduled Tasks**: Cron-based automation

**Why n8n is NOT in `/services/`**: n8n is a third-party Docker container, not a custom Python microservice. Our custom Python services (auth, feed, content-analysis, etc.) are in `/services/`. n8n configuration and workflows are in `/home/cytrex/userdocs/n8n/`.

---

## Quick Access

- **UI**: http://localhost:5678
- **API**: http://localhost:5678/api/v1
- **Container**: `news-n8n`
- **Documentation**: `/home/cytrex/userdocs/n8n/`
- **Workflow Backups**: `/home/cytrex/userdocs/n8n/workflows/`

---

## API Authentication

n8n Public API uses API Key authentication:

```bash
# API Key (stored in /home/cytrex/userdocs/.env)
API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmMTNiY2NiNS1kZjUyLTQwOTYtOWYyMy02Zjg5OTg1OWU0OTUiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYxNTk2ODgyfQ.zxj8z9rywKJO-ZQnQ5sZit_YuoUbyI7MXzTXjA2c5Ek"

# Usage
curl -s "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $API_KEY"
```

---

## Active Workflows

### 1. RabbitMQ Event Monitor
- **ID**: `OlZdwPiDc59H3FKu`
- **Status**: Active ✅
- **Success Rate**: 100% (6/6 executions)
- **Purpose**: Logs all RabbitMQ events from `content_analysis_v2_queue`
- **Backup**: `/home/cytrex/userdocs/n8n/workflows/rabbitmq-event-monitor.json`

**Architecture**:
```
RabbitMQ Trigger → Log Event (Code Node)
```

**Why minimal?**: Complex workflows with IF-Nodes caused crashes (see Lessons Learned). Keep workflows simple and reliable.

### 2. JWT Token Auto-Refresh v3 (Smart)
- **ID**: `XoeCiwedaDmVCMsf`
- **Status**: Active ✅
- **Trigger**: Every 25 minutes
- **Purpose**: Auto-refresh JWT tokens and update n8n credentials
- **Impact**: Eliminates manual token management

---

## Common Operations

### Check Workflow Status
```bash
curl -s "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $API_KEY" | \
  jq '.data[] | {id, name, active}'
```

### View Recent Executions
```bash
curl -s "http://localhost:5678/api/v1/executions?limit=10" \
  -H "X-N8N-API-KEY: $API_KEY" | \
  jq '.data[] | {id, status, startedAt}'
```

### Create New Workflow
```bash
curl -s -X POST "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @workflow.json
```

### Activate Workflow
```bash
curl -s -X POST "http://localhost:5678/api/v1/workflows/{id}/activate" \
  -H "X-N8N-API-KEY: $API_KEY"
```

---

## Testing Patterns

### Test RabbitMQ Workflow
```bash
# 1. Stop content-analysis workers (for isolated testing)
docker compose stop content-analysis-v2

# 2. Publish test message
docker exec rabbitmq rabbitmqadmin publish \
  routing_key="content_analysis_v2_queue" \
  payload='{"event_type":"test","article_id":"123"}' \
  properties='{"content_type":"application/json"}'

# 3. Check execution
curl -s "http://localhost:5678/api/v1/executions?limit=1" \
  -H "X-N8N-API-KEY: $API_KEY" | jq '.data[0].status'
# Expected: "success"

# 4. Restart workers
docker compose up -d content-analysis-v2
```

---

## Monitoring

### Execution Success Rate
```bash
# Last 100 executions grouped by status
curl -s "http://localhost:5678/api/v1/executions?limit=100" \
  -H "X-N8N-API-KEY: $API_KEY" | \
  jq '[.data | group_by(.status) | .[] | {status: .[0].status, count: length}]'
```

**Target**: >95% success rate

### RabbitMQ Consumer Count
```bash
curl -s "http://localhost:15672/api/queues/%2F/content_analysis_v2_queue" \
  -u guest:guest | jq '{consumers, messages}'
```

**Expected**:
- 4 consumers (3x content-analysis-v2 workers + 1x n8n)
- 0 messages (all consumed quickly)

### Container Logs
```bash
docker logs news-n8n --tail 50 | grep -i error
```

**Red flags**:
- `compareOperationFunctions` errors → IF-Node issues
- `Code doesn't return items properly` → Return format error
- RabbitMQ connection errors

---

## Best Practices

### 1. Minimal Workflows
✅ **DO**: Keep workflows simple
```
RabbitMQ Trigger → Code Node
```

❌ **DON'T**: Add unnecessary complexity
```
RabbitMQ Trigger → IF Node → Success Branch → Error Handler → Retry Logic
```

**Why**: Simpler workflows are more reliable. Add complexity only when required.

### 2. Code Node Pattern
```javascript
// ✅ CORRECT - Always return array
const eventData = {
  timestamp: new Date().toISOString(),
  event_type: $input.item.json.event_type || 'unknown',
  article_id: $input.item.json.article_id
};

console.log('Event:', JSON.stringify(eventData, null, 2));

return [{ json: eventData }];  // Array!
```

**Critical**: Code Nodes (typeVersion 2) MUST return arrays, not objects.

### 3. Workflow Lifecycle
- **Create**: POST `/api/v1/workflows` (not PUT for existing)
- **Activate**: POST `/api/v1/workflows/{id}/activate`
- **Archive**: Don't try to fix broken workflows - create fresh

### 4. Service Names
Use full Docker Compose service names:
- ✅ `http://news-auth-service:8100`
- ✅ `http://news-feed-service:8101`
- ❌ `http://auth-service:8100` (wrong)

---

## Troubleshooting

### Workflow Shows Active But Not Listening
**Symptom**: No executions created despite messages in queue

**Check**:
```bash
# 1. Verify workflow is truly active
curl -s "http://localhost:5678/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: $API_KEY" | jq '.active'
# Expected: true

# 2. Check n8n logs
docker logs news-n8n --tail 100 | grep "Activated workflow"
```

**Solution**: Deactivate and reactivate workflow.

### Round-Robin Message Distribution
**Symptom**: Test messages not reaching n8n

**Cause**: Multiple consumers (workers + n8n) on same queue

**Solution**: Stop workers temporarily for isolated testing
```bash
docker compose stop content-analysis-v2
# Now n8n is the only consumer
```

### IF-Node Crashes
**Symptom**: `compareOperationFunctions[compareData.operation] is not a function`

**Solution**: Remove IF-Node entirely. Use Code Node for conditional logic if needed.

---

## Integration Points

### RabbitMQ
- **Queue**: `content_analysis_v2_queue`
- **Exchange**: Default (`amq.default`)
- **Credential**: "News Microservices RabbitMQ"
- **Consumer Behavior**: Round-robin with content-analysis workers

### Auth Service
- **Endpoint**: `http://news-auth-service:8100/api/v1/auth/login`
- **Credential**: "Feed Service API" (contains JWT tokens)
- **Auto-Refresh**: JWT Token Auto-Refresh workflow handles token rotation

### Feed Service
- **Endpoint**: `http://news-feed-service:8101/api/v1/feeds`
- **Credential**: "Feed Service API"
- **Use Case**: API testing and monitoring

---

## Documentation

**Comprehensive Guides**: `/home/cytrex/userdocs/n8n/`
- `README.md` - Quick reference
- `INTEGRATION_GUIDE.md` - API reference and setup
- `LESSONS_LEARNED.md` - Debugging stories and best practices
- `n8n-public-api.json` - OpenAPI specification
- `workflows/` - Production workflow backups

**Project Docs**: `/home/cytrex/news-microservices/docs/n8n/`
- Workflow guides (per workflow)
- Implementation status
- Next steps

---

## Performance Metrics

### Before Fix (2025-10-28)
- Total Executions: 8,632
- Failed: 8,630
- Success: 2
- **Failure Rate: 99.98%**

### After Fix (2025-10-28)
- New Workflow Executions: 6
- Failed: 0
- Success: 6
- **Success Rate: 100%**

**Execution Time**: ~10-50ms per event

---

## Future Improvements

1. **Prometheus Metrics**: Export execution count/status to Prometheus
2. **Retry Logic**: Implement error workflows with retry mechanism
3. **Separate Queues**: Dedicated `n8n_events` queue for monitoring
4. **Structured Logging**: Send logs to Loki/Elasticsearch

---

## Key Takeaways

1. ✅ Always return arrays from Code Nodes: `return [{ json: ... }];`
2. ✅ Keep workflows minimal - don't add complexity without reason
3. ✅ Test in isolation - stop other consumers during debugging
4. ✅ Use API for management - UI doesn't show all details
5. ✅ Archive broken workflows - don't try to fix in-place, rebuild clean
6. ✅ Check logs first - n8n logs reveal issues faster than API debugging
7. ✅ Verify service names - use `docker ps` to confirm hostnames

**Most Important**: When in doubt, **start fresh**. Rebuilding a workflow takes 5 minutes. Debugging a broken one can take hours.

---

**Last Updated**: 2025-10-28
**Status**: ✅ Production-ready, 100% success rate
**Related**: [CLAUDE.md](/home/cytrex/CLAUDE.md), [LESSONS_LEARNED.md](/home/cytrex/userdocs/n8n/LESSONS_LEARNED.md)
