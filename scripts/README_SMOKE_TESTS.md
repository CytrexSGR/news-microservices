# Smoke Test Suite - Usage Guide

Automated smoke tests for all **18 microservices** + infrastructure.

## Quick Start

```bash
# Fast health check (all 18 services) - RECOMMENDED
./scripts/quick_smoke_test.sh

# E2E flow test (Auth → Feed → V3 → Search → Analytics → KG)
./scripts/test_e2e_flow.sh

# Infrastructure check (PostgreSQL, Redis, RabbitMQ, Neo4j)
./scripts/infrastructure_test.sh

# Individual service tests
./scripts/test_auth_service.sh
./scripts/test_feed_service.sh
./scripts/test_content_analysis_v3.sh
./scripts/test_fmp_service.sh
./scripts/test_search_service.sh
./scripts/test_analytics_service.sh
```

---

## Test Scripts

### 1. Main Suite Scripts

#### `quick_smoke_test.sh` ⚡ RECOMMENDED
**Purpose:** Fast parallel health checks
**Runtime:** ~5 seconds
**Tests:** All 18 services (Tier 1-3)
**Usage:**
```bash
./scripts/quick_smoke_test.sh
```
**Output:**
```
=== Quick Smoke Test - All 18 Services ===
✅ auth-service (port 8100) - PASS
✅ feed-service (port 8101) - PASS
✅ content-analysis-v3 (port 8117) - PASS
...
Success Rate: 94.4%
```

#### `test_e2e_flow.sh` 🔗 NEW
**Purpose:** End-to-end pipeline validation
**Runtime:** ~10 seconds
**Tests:** Auth → Feed → V3 → Search → Analytics → Knowledge Graph
**Usage:**
```bash
./scripts/test_e2e_flow.sh
```
**Output:**
```
=== E2E Flow Test - Article Pipeline ===
Step 1/6: Authentication... PASS
Step 2/6: Feed Service... PASS (60 feeds)
Step 3/6: Content-Analysis-V3... PASS
Step 4/6: Search Service... PASS
Step 5/6: Analytics Service... PASS
Step 6/6: Knowledge Graph... PASS
✅ E2E Flow Test: ALL SYSTEMS OPERATIONAL
```

#### `infrastructure_test.sh`
**Purpose:** Test infrastructure components
**Runtime:** ~3 seconds
**Tests:** PostgreSQL, Redis, RabbitMQ, Neo4j
**Usage:**
```bash
./scripts/infrastructure_test.sh
```

#### `smoke_test_suite.sh` (Comprehensive)
**Purpose:** Full end-to-end testing with detailed reports
**Runtime:** ~30 seconds
**Tests:** Services + critical flows + database
**Usage:**
```bash
./scripts/smoke_test_suite.sh
```

---

### 2. Individual Service Tests

#### Tier 1: Mission-Critical

| Script | Port | Tests |
|--------|------|-------|
| `test_auth_service.sh` | 8100 | Health, Login, Token validation |
| `test_feed_service.sh` | 8101 | Health, Feed list, Celery workers |
| `test_content_analysis_v3.sh` | 8117 | Health, Analysis, Neo4j |
| `test_fmp_service.sh` | 8113 | Health, Quotes, Market status |

#### Tier 2: Important

| Script | Port | Tests |
|--------|------|-------|
| `test_search_service.sh` | 8106 | Health, Search, Pagination |
| `test_analytics_service.sh` | 8107 | Health, Metrics, Dashboard |

---

## Test Results

### Current Status (2025-11-25)

**Services:** 17/18 PASS (94.4%)

| Tier | Service | Port | Status |
|------|---------|------|--------|
| 1 | auth-service | 8100 | ✅ PASS |
| 1 | feed-service | 8101 | ✅ PASS |
| 1 | content-analysis-v3 | 8117 | ✅ PASS |
| 1 | fmp-service | 8113 | ✅ PASS |
| 1 | scraping-service | 8009 | ✅ PASS |
| 2 | search-service | 8106 | ✅ PASS |
| 2 | analytics-service | 8107 | ✅ PASS |
| 2 | notification-service | 8105 | ✅ PASS |
| 2 | scheduler-service | 8108 | ✅ PASS |
| 2 | prediction-service | 8116 | ✅ PASS |
| 2 | narrative-service | 8119 | ✅ PASS |
| 2 | entity-canonicalization | 8112 | ✅ PASS |
| 3 | research-service | 8103 | ❌ FAIL (external API) |
| 3 | osint-service | 8104 | ✅ PASS |
| 3 | intelligence-service | 8118 | ✅ PASS |
| 3 | knowledge-graph | 8111 | ✅ PASS |
| 3 | oss-service | 8110 | ✅ PASS |
| 3 | ontology-service | 8109 | ✅ PASS |

**Infrastructure:** 4/4 PASS (100%)
- ✅ PostgreSQL
- ✅ Redis
- ✅ RabbitMQ
- ✅ Neo4j

**E2E Flow:** 6/6 PASS (100%)

---

## Known Issues

### 🟡 P2: Research Service Degraded
**Issue:** External Perplexity API unreachable
**Cause:** API endpoint changed or key invalid
**Impact:** Service returns 200 but status "degraded"
**Workaround:** Service functional for cached results

---

## CI/CD Integration

### GitHub Actions

A workflow file is available at `.github/workflows/smoketest.yml`:

```yaml
# Runs on push to main/develop and PRs
# Supports manual trigger with test level selection

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      test_level:
        type: choice
        options: [quick, full, e2e]
```

**Features:**
- Automatic service startup
- Quick smoke test (default)
- E2E flow test (on demand)
- Log collection on failure
- Test result artifacts

---

## Exit Codes

All test scripts return standard exit codes:

- **0** = All tests passed
- **1** = One or more tests failed

**Example usage:**
```bash
./scripts/quick_smoke_test.sh && ./scripts/test_e2e_flow.sh
if [ $? -eq 0 ]; then
    echo "All tests passed - proceed with deployment"
else
    echo "Tests failed - block deployment"
    exit 1
fi
```

---

## Adding New Tests

### Template for New Service Test

```bash
#!/bin/bash
# Service Name Smoke Test - Port XXXX
set +e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
echo "=== Service Name Smoke Test ==="
PASSED=0; FAILED=0; WARNINGS=0

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"andreas@test.com","password":"Aug2012#"}' | jq -r '.access_token')

# Test 1: Health Check (Critical)
echo -n "1. Health Check... "
[ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:XXXX/health)" == "200" ] && \
    echo -e "${GREEN}PASS${NC}" && ((PASSED++)) || \
    echo -e "${RED}FAIL${NC}" && ((FAILED++))

# Add more tests...

echo -e "\nPassed: ${GREEN}$PASSED${NC} | Failed: ${RED}$FAILED${NC}"
[ $FAILED -eq 0 ] && exit 0 || exit 1
```

---

## Troubleshooting

### Service not responding
```bash
# Check logs
docker logs news-<service-name> --tail 50

# Restart service
docker restart news-<service-name>

# Check health
curl http://localhost:<port>/health
```

### Database query fails
```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U news_user -d news_mcp

# Run query manually
SELECT COUNT(*) FROM <table>;
```

### Redis not responding
```bash
# Check Redis
docker exec -it redis redis-cli -a redis_secret_2024 PING
# Should return: PONG
```

---

## Reports

Test results are saved to:
```
reports/testing/
├── SMOKE_TEST_RESULTS_WEEK4.md              (Comprehensive report)
├── SMOKE_TEST_EXECUTION_SUMMARY.md          (Quick summary)
└── smoke_test_errors_*.log                  (Error logs)
```

---

## Maintenance

### Update test scripts when:
1. New service added → Add to `quick_smoke_test.sh` SERVICES array
2. Port changed → Update all relevant scripts
3. Health endpoint changed → Update test expectations
4. New critical flow → Add to `test_e2e_flow.sh`

### Documentation sync:
- Keep in sync with `/home/cytrex/userdocs/doku-update241125/SMOKETEST_CHECKLIST.md`

---

**Last Updated:** 2025-11-25
**Services Covered:** 18 (was 13)
**Maintained by:** Development Team
**CI/CD:** `.github/workflows/smoketest.yml`
