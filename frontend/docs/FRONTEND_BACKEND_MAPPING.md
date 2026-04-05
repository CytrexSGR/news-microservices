# Frontend-Backend Service Mapping

**Generated:** 2025-12-28
**Purpose:** Complete mapping of frontend features to backend services

---

## Overview

| Metric | Count |
|--------|-------|
| Frontend Features | 17 directories |
| Backend Services Used | 17 services |
| Backend Services NOT Used | 2 services |
| Obsolete References | 0 (all cleaned up 2025-12-28) |

---

## Service Mapping Table

| Frontend Feature | API File | Backend Service | Port | Status |
|-----------------|----------|-----------------|------|--------|
| **auth** | `@/api/axios.ts` | auth-service | 8100 | OK |
| **admin/health** | `admin/health/api/healthApi.ts` | analytics-service | 8107 | OK |
| **admin/monitoring** | `admin/monitoring/api/monitoringApi.ts` | analytics-service | 8107 | OK |
| **admin/scheduler** | `admin/scheduler/api/schedulerApi.ts` | scheduler-service | 8108 | OK |
| **admin/feed-service** | `lib/api/feedServiceAdmin.ts` | feed-service | 8101 | OK |
| **admin/knowledge-graph** | `lib/api/knowledgeGraphAdmin.ts` | knowledge-graph-service | 8111 | OK |
| **feeds** | `@/api/axios.ts` (feedApi) | feed-service | 8101 | OK |
| **finance** | `finance/services/financeApi.ts` | fmp-service | 8113 | OK |
| **intelligence** | `intelligence/api/intelligenceApi.ts` | intelligence-service | 8118 | OK |
| **intelligence/analysis** | `intelligence/analysis/api/analysisApi.ts` | feed-service | 8101 | OK |
| **intelligence/entities** | `intelligence/entities/api/entitiesApi.ts` | entity-canonicalization | 8112 | OK |
| **intelligence/narrative** | `intelligence/narrative/api/narrativeApi.ts` | narrative-service | 8119 | OK |
| **ml-lab** | `ml-lab/api/mlLabApi.ts` | prediction-service | 8116 | OK |
| **monitoring** | `monitoring/api/useServiceMetrics.ts` | MCP Server | N/A | OK |
| **narrative** | `narrative/api/narrativeApi.ts` | narrative-service | 8119 | OK |
| **notifications** | `notifications/api/notificationApi.ts` | notification-service | 8105 | OK |
| **research** | `research/api/researchApi.ts` | research-service | 8103 | OK |
| **search** | `@/api/axios.ts` (searchApi) | search-service | 8106 | OK |
| **trading** | `trading/lib/api-client.ts` | prediction-service + fmp-service | 8116, 8113 | OK |

### Additional Services (Not in Original Mapping)

| Frontend Feature | API File | Backend Service | Port | Status |
|-----------------|----------|-----------------|------|--------|
| **admin/ontology-proposals** | `lib/api/ontologyProposals.ts` | ontology-proposals-service | 8109 | OK |
| **admin/orchestration/mediastack** | `orchestration/mediastack/api/*.ts` | mcp-orchestration-server | 9008 | **MCP** |
| **admin/orchestration/scraping** | `orchestration/scraping/api/*.ts` | mcp-orchestration-server | 9008 | **MCP** |
| **admin/orchestration/scheduler** | `orchestration/scheduler/api/*.ts` | mcp-orchestration-server | 9008 | **MCP** |
| **feeds** (V3 analysis) | `lib/api/contentAnalysisV3.ts` | content-analysis-v3-api | 8117 | OK |
| **monitoring** (all features) | `monitoring/api/*.ts` | mcp-orchestration-server | 9008 | **MCP** |

---

## Central API Clients (`src/api/axios.ts`)

```typescript
// All clients include auth interceptor with JWT token
authApi      → VITE_AUTH_API_URL       → auth-service (8100)
analyticsApi → VITE_ANALYTICS_API_URL  → analytics-service (8107)
feedApi      → VITE_FEED_API_URL       → feed-service (8101)
analysisApi  → VITE_ANALYSIS_API_URL   → feed-service (8101) /analysis
searchApi    → VITE_SEARCH_API_URL     → search-service (8106)
predictionApi→ VITE_PREDICTION_API_URL → prediction-service (8116)
strategyLabApi → VITE_PREDICTION_API_URL → prediction-service (8116)
```

---

## Backend Services NOT Used in Frontend

| Service | Port | Reason |
|---------|------|--------|
| **osint-service** | 8104 | Backend-only service for intelligence monitoring |
| **llm-orchestrator** | N/A | Backend-internal for LLM coordination |
| **scraping-service** | N/A | Backend-only for web scraping |

---

## Environment Variables

Required `.env` variables for frontend:

```bash
# Auth
VITE_AUTH_API_URL=http://localhost:8100/api/v1

# Core Services
VITE_FEED_API_URL=http://localhost:8101/api/v1
VITE_ANALYSIS_API_URL=http://localhost:8101/api/v1/analysis
VITE_RESEARCH_SERVICE_URL=http://localhost:8103
VITE_NOTIFICATION_API_URL=http://localhost:8105/api/v1
VITE_SEARCH_API_URL=http://localhost:8106/api/v1
VITE_ANALYTICS_API_URL=http://localhost:8107/api/v1
VITE_SCHEDULER_SERVICE_URL=http://localhost:8108

# Knowledge Services
VITE_KG_API_URL=http://localhost:8111
VITE_CANONICALIZATION_API_URL=http://localhost:8112

# Financial/Trading
VITE_FMP_API_URL=http://localhost:8113/api/v1
VITE_PREDICTION_API_URL=http://localhost:8116/api/v1

# Intelligence
VITE_INTELLIGENCE_API_URL=http://localhost:8118/api/v1/intelligence
VITE_NARRATIVE_API_URL=http://localhost:8119/api/v1/narrative
```

---

## Proxy Configuration

### Vite Dev Proxy (`vite.config.ts`)

```typescript
proxy: {
  '/api/auth':       → localhost:8100
  '/api/feed':       → localhost:8101
  '/api/analytics':  → localhost:8107
  '/api/search':     → localhost:8106
  '/api/kg':         → localhost:8111
  '/api/nlp':        → localhost:8115 (ARCHIVED)
  '/api/prediction': → localhost:8116
  '/api/v1':         → localhost:8113 (FMP)
  '/ws':             → localhost:8113 (WebSocket)
}
```

### Nginx Production Proxy (`nginx.conf`)

Same routes as above, using Docker service names instead of localhost.

---

## Archived/Removed Services

### execution-service (Port 8120) - ARCHIVED 2025-12-28

**What was removed:**
- `src/api/executionService.ts` - DELETED
- `executionApi` in `src/lib/api/trading.ts` - REMOVED
- `executionClient` in `src/lib/api-client.ts` - REMOVED
- Proxy config in `vite.config.ts` - REMOVED
- Proxy config in `nginx.conf` - REMOVED

**Affected pages (now show "Under Construction"):**
- `/trading` - TradingDashboard.tsx
- `/trading/analytics` - AnalyticsDashboard.tsx

**Migration path:** Features will be rebuilt in prediction-service

### content-analysis-v2 (Port 8114) - ARCHIVED 2025-11-24

**Dead code found:**
- `src/lib/api/contentAnalysisAdmin.ts` - **99 lines, NOT imported anywhere** → DELETE
  - Contains hardcoded API key (security concern)
  - References VITE_ANALYSIS_V2_API_URL which no longer exists

**Files with archive comments (OK):**
- `src/App.tsx` - Line 41: "AgentConfigurationPage removed" comment
- `src/features/feeds/api/useArticleV2.ts` - Archive notice comment

**Port 8114 reassigned to:** `narrative-intelligence-gateway` (new service)

### mcpClient.ts - WRONG PORT

**Current configuration:**
```typescript
// src/shared/api/mcpClient.ts line 53
constructor(baseURL: string = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8114/api/v1')
```

**Problem:** Port 8114 is now `narrative-intelligence-gateway`, NOT the MCP server!

**Correct MCP Server:** `mcp-orchestration-server` runs on **Port 9008**

**Fix required:**
```typescript
// Change default from 8114 to 9008
constructor(baseURL: string = import.meta.env.VITE_MCP_API_URL || 'http://localhost:9008/api/v1')
```

**Impact:** 93 files use mcpClient for MCP tool calls (scheduler, monitoring, etc.)

---

## Issues Found

### 0. Environment File (.env) - Obsolete Entries

The `.env` file contains obsolete entries that should be removed:

```bash
# OBSOLETE - Remove these:
VITE_ANALYSIS_V2_API_URL=http://localhost:8117  # Wrong! V2 was 8114 (archived), 8117 is V3
VITE_NLP_API_URL=http://localhost:8115          # nlp-extraction-service archived 2025-12-27
VITE_EXECUTION_API_URL=http://localhost:8120    # execution-service archived 2025-12-28

# ADD these (missing):
VITE_ANALYSIS_V3_API_URL=http://localhost:8117  # Content-Analysis V3
VITE_ONTOLOGY_PROPOSALS_API_URL=http://localhost:8109
VITE_MCP_API_URL=http://localhost:9008          # MCP Orchestration Server
```

### 1. Port Inconsistency in Documentation ✅ FIXED (2025-12-28)

**CLAUDE.md** updated to reflect correct ports:
- `fmp-service` → Port 8113
- `ontology-proposals-service` → Port 8109

### 2. Duplicate Narrative API ✅ FIXED (2025-12-28)

**Resolution:** Deleted unused duplicate file:
- `features/intelligence/narrative/api/narrativeApi.ts` → **DELETED** (was not imported anywhere)
- `features/narrative/api/narrativeApi.ts` → **KEPT** (imported by 3 files)

### 3. Inconsistent Auth Token Access

Different patterns used across API files:
- `useAuthStore.getState().accessToken` (most files)
- `localStorage.getItem('auth-storage')` parsing (research, scheduler, narrative)

**Recommendation:** Standardize on single pattern (preferably Zustand store).

---

## Feature Coverage Matrix

| Backend Capability | Frontend Implementation | Status |
|-------------------|------------------------|--------|
| JWT Authentication | authApi + authStore | Complete |
| Feed Management | feedServiceAdmin | Complete |
| Article Analysis | analysisApi | Complete |
| Entity Canonicalization | entitiesApi | Complete |
| Knowledge Graph | knowledgeGraphAdmin | Complete |
| Notifications | notificationApi | Complete |
| Research Tasks | researchApi | Complete |
| Search | searchApi | Complete |
| Analytics/Monitoring | monitoringApi, cacheApi, healthApi | Complete |
| Scheduler | schedulerApi | Complete |
| Market Data (FMP) | financeApi | Complete |
| ML Lab / Prediction | mlLabApi | Complete |
| Intelligence Events | intelligenceApi | Complete |
| Narrative Analysis | narrativeApi | Complete |
| Trading Execution | - | ARCHIVED |
| OSINT Monitoring | - | No Frontend |
| LLM Orchestration | - | Backend Only |

---

## Refactoring Recommendations

### Priority 1: Critical Fixes ✅ ALL COMPLETED (2025-12-28)

| Task | File | Status |
|------|------|--------|
| **Delete dead code** | `src/lib/api/contentAnalysisAdmin.ts` | ✅ DELETED |
| **Fix MCP port** | `src/shared/api/mcpClient.ts:53` | ✅ Changed 8114 → 9008 |
| **Fix .env** | `.env` | ✅ Removed obsolete, added missing vars |

### Priority 2: Short-term Cleanup ✅ ALL COMPLETED (2025-12-28)

| Task | Files | Status |
|------|-------|--------|
| **Fix CLAUDE.md** | `/CLAUDE.md` | ✅ Updated fmp port + ontology-proposals |
| **Consolidate narrative APIs** | `features/intelligence/narrative/api/narrativeApi.ts` | ✅ DELETED (unused duplicate) |
| **Remove proxy configs** | `nginx.conf` | ✅ Removed `/api/nlp` (vite.config.ts was already clean) |

### Priority 3: Medium-term Improvements

| Task | Description |
|------|-------------|
| **Add env validation** | Create schema to validate required VITE_* vars at startup |
| **Update types** | Remove archived service types from `@/types/` |

### ~~Standardize auth~~ - NOT RECOMMENDED

Both patterns (`useAuthStore` and `localStorage.getItem('auth-storage')`) access the same data (Zustand persists to localStorage). Refactoring would be high-risk with no functional benefit.

### Priority 4: Long-term (Depends on Backend)

| Task | Description |
|------|-------------|
| **Rebuild trading execution** | After prediction-service refactoring complete |
| **Add OSINT frontend** | If user-facing OSINT features needed |
| **MCP Server consolidation** | Consider unified MCP gateway |

---

## Complete Backend Service Port Map

For reference, all backend services with their ports:

| Service | Port | Frontend Integration |
|---------|------|---------------------|
| auth-service | 8100 | Direct API |
| feed-service | 8101 | Direct API |
| research-service | 8103 | Direct API |
| osint-service | 8104 | **No frontend** |
| notification-service | 8105 | Direct API |
| search-service | 8106 | Direct API |
| analytics-service | 8107 | Direct API |
| scheduler-service | 8108 | Direct API |
| ontology-proposals-service | 8109 | Direct API |
| oss-service | 8110 | **No frontend** |
| knowledge-graph-service | 8111 | Direct API |
| entity-canonicalization | 8112 | Direct API |
| fmp-service | 8113 | Direct API |
| narrative-intelligence-gateway | 8114 | **No frontend** (new) |
| prediction-service | 8116 | Direct API |
| content-analysis-v3-api | 8117 | Direct API |
| intelligence-service | 8118 | Direct API |
| narrative-service | 8119 | Direct API |
| mediastack-service | 8121 | Via MCP |
| mcp-orchestration-server | 9008 | MCP Client |

---

## Cleanup Summary (2025-12-28)

### Phase 1: Code Cleanup (Morning)

**Files Deleted:**
- `src/lib/api/contentAnalysisAdmin.ts` (99 lines dead code, security concern: hardcoded API key)
- `src/features/intelligence/narrative/api/narrativeApi.ts` (151 lines, unused duplicate)

**Files Modified:**
- `src/shared/api/mcpClient.ts` - Fixed wrong default port (8114 → 9008)
- `.env` - Removed 3 obsolete vars, added 3 missing vars
- `nginx.conf` - Removed archived NLP service proxy

### Phase 2: Feature Removal (Evening)

**Cache Monitor Feature Removed:**
- `src/pages/admin/CacheMonitorPage.tsx` → DELETED
- `src/features/admin/cache/` → DELETED (entire folder)
- `src/components/layout/MainLayout.tsx` → Removed from navigation
- `src/App.tsx` → Removed route

**Reason:** Page never worked - backend returns raw Redis INFO data, frontend expected structured CacheStats. Low value, raw data available via CLI.

### Phase 3: Backend JWT Secret Fix (Evening)

**Critical Issue Found:** 6 services had placeholder JWT secrets instead of the real key.

**Services Fixed:**
| Service | Before | After |
|---------|--------|-------|
| analytics-service | `your-super-secret-jwt-key...` | ✅ Real key |
| notification-service | `your-super-secret-jwt-key...` | ✅ Real key |
| osint-service | `your-super-secret-jwt-key...` | ✅ Real key |
| scheduler-service | `your-super-secret-jwt-key...` | ✅ Real key |
| search-service | `your-super-secret-jwt-key...` | ✅ Real key |
| fmp-service | `your-secret-key-min-32...` | ✅ Real key |

**Impact:** All API calls from frontend to these services were returning 401 "Invalid authentication credentials".

### Documentation Updated
- `/CLAUDE.md` - Fixed service ports (fmp: 8113, ontology-proposals: 8109)
- `docs/FRONTEND_BACKEND_MAPPING.md` - This file

---

**Last Updated:** 2025-12-28 20:35
**Analysis Complete:** Frontend-Backend mapping with 17 active services
**Cleanup Status:** All phases COMPLETED
