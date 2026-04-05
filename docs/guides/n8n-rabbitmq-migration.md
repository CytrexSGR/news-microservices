# n8n RabbitMQ Virtual Host Migration Guide

**Date:** 2025-11-01 (Updated: 2025-11-02)
**Status:** ⚠️ **OBSOLETE** - Workflows have been deleted

---

## ⚠️ IMPORTANT UPDATE (2025-11-02)

**This guide is NO LONGER NEEDED.**

The problematic "RabbitMQ Event Monitor" workflows have been **permanently deleted** because:
- They had no business value (only logged events via `console.log`)
- They were consuming from production queues (dangerous)
- Analysis showed they were test/experiment leftovers

**Current n8n status:**
- ✅ 2 active workflows (JWT Auto-Refresh, Entity-to-KG)
- ✅ 0 RabbitMQ consumers
- ✅ Production queues protected

**If you need RabbitMQ monitoring in the future:**
- See [ADR-033: RabbitMQ Consumer Monitoring](../decisions/ADR-033-rabbitmq-consumer-monitoring.md)
- Use RabbitMQ Management API (no consumer = no risk)
- Create isolated queues in `/n8n` vhost

---

## Historical Reference (Original Guide)

---

## Overview

n8n has been isolated to prevent message theft from production queues. All RabbitMQ-related workflows must be manually migrated to use the `/n8n` virtual host.

**What Changed:**
- ✅ RabbitMQ virtual host `/n8n` created
- ✅ User `n8n_user` created with access only to `/n8n`
- ✅ docker-compose.yml updated with RabbitMQ credentials
- ⚠️ **Workflows must be updated manually** (RabbitMQ connections are stored in workflow definitions)

---

## Affected Workflows

Based on startup logs, these workflows are active and may need updates:

1. **RabbitMQ Event Monitor** (ID: `OlZdwPiDc59H3FKu`)
   - ⚠️ **CRITICAL** - This workflow was consuming from production queue `content_analysis_v2_queue`
   - Must be updated to use `/n8n` vhost

2. **Entity-to-Knowledge-Graph-v2-Async** (ID: `5o3ZjyhLELti9its`)
   - May have RabbitMQ triggers/connections

3. **JWT Token Auto-Refresh v3 (Smart)** (ID: `XoeCiwedaDmVCMsf`)
   - Likely unaffected (JWT refresh, no RabbitMQ)

---

## Migration Steps

### Step 1: Access n8n UI

```bash
# Start n8n (currently stopped for safety)
docker start news-n8n

# Access UI
open http://localhost:5678
```

### Step 2: Identify RabbitMQ Nodes

For each workflow:

1. Open workflow in editor
2. Look for nodes of type:
   - **RabbitMQ Trigger** (consumes messages)
   - **RabbitMQ** (publishes messages)

### Step 3: Update RabbitMQ Connection

For each RabbitMQ node:

1. **Click on the RabbitMQ node**
2. **Find "Credential for RabbitMQ" dropdown**
3. **Create new credential:**
   - Name: `RabbitMQ - n8n vhost`
   - Hostname: `rabbitmq` (or use env var: `{{$env.RABBITMQ_HOST}}`)
   - Port: `5672` (or use env var: `{{$env.RABBITMQ_PORT}}`)
   - User: `n8n_user` (or use env var: `{{$env.RABBITMQ_USER}}`)
   - Password: `n8n_secret_2024` (or use env var: `{{$env.RABBITMQ_PASSWORD}}`)
   - **Virtual Host:** `n8n` (or use env var: `{{$env.RABBITMQ_VHOST}}`)
   - SSL: `false`

4. **Update Queue Names:**
   - ⚠️ **DO NOT use production queues!**
   - Old: `content_analysis_v2_queue` ❌
   - New: `n8n_test_queue` ✅ (example)
   - Create your own queue names in `/n8n` vhost

### Step 4: Test Workflow

1. **Save workflow**
2. **Activate workflow**
3. **Verify in RabbitMQ Management UI:**
   ```
   http://localhost:15672
   → Virtual Hosts → n8n → Queues
   ```
4. **Check that no consumers appear on production queues:**
   ```bash
   curl -s -u guest:guest http://localhost:15672/api/queues/%2F/content_analysis_v2_queue | jq '.consumers'
   # Expected: 3 (only content-analysis-v2 workers)
   ```

---

## Using Environment Variables (Recommended)

Instead of hardcoding credentials, use the env vars from `docker-compose.yml`:

**RabbitMQ Connection:**
- Hostname: `{{$env.RABBITMQ_HOST}}`
- Port: `{{$env.RABBITMQ_PORT}}`
- User: `{{$env.RABBITMQ_USER}}`
- Password: `{{$env.RABBITMQ_PASSWORD}}`
- Vhost: `{{$env.RABBITMQ_VHOST}}`

**Benefits:**
- No hardcoded secrets
- Easy to update
- Consistent across workflows

---

## RabbitMQ Virtual Host Architecture

```
RabbitMQ
├── / (default vhost)
│   ├── news.events (exchange)
│   ├── content_analysis_v2_queue
│   ├── Consumers: content-analysis-v2 workers ONLY ✅
│   └── Publishers: feed-service
│
└── /n8n (isolated vhost)
    ├── [Your custom queues/exchanges]
    └── Consumers: n8n workflows ONLY ✅
```

**Isolation Rules:**
- n8n_user can **ONLY** access `/n8n` vhost
- n8n **CANNOT** consume from production queues
- Production services **CANNOT** access `/n8n` vhost

---

## Verification Checklist

Before starting n8n permanently:

- [ ] All RabbitMQ Trigger nodes updated to use new credential
- [ ] New credential uses `n8n_user` and vhost `/n8n`
- [ ] Queue names are NOT production queues
- [ ] Workflows tested and working
- [ ] RabbitMQ Management UI shows:
  - [ ] No consumers from n8n on `/` vhost
  - [ ] n8n consumers only on `/n8n` vhost
  - [ ] Production queue has exactly 3 consumers

**Verify Isolation:**
```bash
# Should return 3 (not 4!)
curl -s -u guest:guest http://localhost:15672/api/queues/%2F/content_analysis_v2_queue | jq '.consumers'

# Should show n8n connections
curl -s -u guest:guest http://localhost:15672/api/connections | jq '.[] | select(.user=="n8n_user")'
```

---

## Troubleshooting

### Problem: Workflow can't connect to RabbitMQ

**Solution:** Check credential configuration:
- Verify vhost is `n8n` (not `/` or empty)
- Verify user is `n8n_user`
- Check RabbitMQ logs: `docker logs rabbitmq`

### Problem: Queue doesn't exist

**Solution:** RabbitMQ queues in `/n8n` vhost must be created first.

**Option A:** Let n8n create them automatically (if node supports it)
**Option B:** Create manually in RabbitMQ Management UI:
```
http://localhost:15672
→ Queues → Add a new queue
→ Virtual host: n8n
→ Name: your_queue_name
→ Durability: Durable
```

### Problem: n8n still consuming from production queue

**Solution:**
1. Stop n8n immediately: `docker stop news-n8n`
2. Check which workflow has old connection:
   ```bash
   docker logs news-n8n | grep "Activated workflow"
   ```
3. Fix workflow credential
4. Restart n8n

---

## Example: Converting RabbitMQ Event Monitor

**OLD Configuration (❌ DANGEROUS):**
```yaml
RabbitMQ Trigger Node:
  Credential: RabbitMQ (default)
    - Host: rabbitmq
    - Port: 5672
    - User: guest
    - Password: guest
    - Vhost: / (or empty)    # ❌ Production vhost!
  Queue: content_analysis_v2_queue  # ❌ Production queue!
```

**NEW Configuration (✅ SAFE):**
```yaml
RabbitMQ Trigger Node:
  Credential: RabbitMQ - n8n vhost
    - Host: {{$env.RABBITMQ_HOST}}
    - Port: {{$env.RABBITMQ_PORT}}
    - User: {{$env.RABBITMQ_USER}}
    - Password: {{$env.RABBITMQ_PASSWORD}}
    - Vhost: {{$env.RABBITMQ_VHOST}}  # ✅ Isolated vhost
  Queue: n8n_monitoring_queue         # ✅ Custom queue
```

---

## Related Documentation

- **Incident #9:** [POSTMORTEMS.md](../../POSTMORTEMS.md) - n8n message theft incident
- **ADR-033:** [RabbitMQ Consumer Monitoring](../decisions/ADR-033-rabbitmq-consumer-monitoring.md)
- **RabbitMQ Best Practices:** [rabbitmq-best-practices.md](./rabbitmq-best-practices.md)

---

## Next Steps

1. **Complete workflow migration** (this guide)
2. **Implement monitoring** (ADR-033 Week 1)
3. **Test n8n workflows** in isolated environment
4. **Start n8n permanently** once verified safe

---

**Last Updated:** 2025-11-01
**Status:** Workflows need manual migration before n8n can start
