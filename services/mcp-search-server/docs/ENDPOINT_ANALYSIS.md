# MCP Intelligence Server - Endpoint Analysis

**Date:** 2025-12-04
**Purpose:** Comprehensive analysis of backend service endpoints to identify MCP tool opportunities
**Current Progress:** 28/40-50 tools (56-70%)

---

## 📊 Summary

**Current Status:**
- Analyzed 5 backend services (analysis, entity-canonicalization, osint, intelligence, narrative)
- Identified 18 additional endpoint candidates
- Prioritized 4 high-value analytics endpoints for immediate implementation
- Target: Reach 32 tools (64-80% of Phase 1 goal)

---

## 🔍 Detailed Endpoint Analysis

### 1. intelligence-service (Port 8110)

**Already Implemented (6 tools):**
- ✅ GET /api/v1/intelligence/overview → `get_intelligence_overview`
- ✅ GET /api/v1/intelligence/clusters → `get_event_clusters`
- ✅ GET /api/v1/intelligence/clusters/{cluster_id} → `get_cluster_details`
- ✅ GET /api/v1/intelligence/events/latest → `get_latest_events`

**New Endpoints Discovered:**

**High-Value Analytics:**
1. **GET /api/v1/intelligence/clusters/{cluster_id}/events** ⭐ **Priority 1**
   - **Purpose:** Get paginated events for specific cluster
   - **Value:** Essential for drilling down into cluster details
   - **Returns:** Events with title, source, entities, keywords, sentiment, bias
   - **Pagination:** Yes (page, per_page)
   - **MCP Tool:** `get_cluster_events`

2. **GET /api/v1/intelligence/subcategories** ⭐ **Priority 2**
   - **Purpose:** Get top 2 sub-topics per category (geo, finance, tech)
   - **Value:** Dynamic sub-category discovery from current news
   - **Returns:** Top keywords/topics with risk scores and event counts
   - **Example:** Geo → Ukraine, Israel | Finance → USD, Bitcoin
   - **MCP Tool:** `get_subcategories`

3. **GET /api/v1/intelligence/risk-history** ⭐ **Priority 3**
   - **Purpose:** Historical risk scores for trend visualization
   - **Value:** Track risk evolution over time
   - **Returns:** Daily risk history (global, geo, finance)
   - **Parameters:** days (1-30, default: 7)
   - **MCP Tool:** `get_risk_history`

**Operational/Admin Endpoints:**
4. POST /api/v1/intelligence/clustering/trigger (admin)
   - Manual clustering with custom parameters
   - Requires admin role
   - Priority: Low (admin-only operation)

5. GET /api/v1/intelligence/clustering/status
   - Clustering configuration and status
   - Priority: Low (monitoring/operational)

6. GET /api/v1/intelligence/clustering/task/{task_id}
   - Celery task status tracking
   - Priority: Low (operational)

---

### 2. narrative-service (Port 8115)

**Already Implemented (4 tools):**
- ✅ GET /api/v1/narrative/overview → `get_narrative_overview`
- ✅ GET /api/v1/narrative/frames → `get_narrative_frames`
- ✅ GET /api/v1/narrative/bias → `get_bias_analysis`
- ✅ POST /api/v1/narrative/analyze/text → `analyze_text_narrative`

**New Endpoints Discovered:**

**High-Value Analytics:**
1. **GET /api/v1/narrative/clusters** ⭐ **Priority 4**
   - **Purpose:** List narrative clusters
   - **Value:** Group similar narrative frames by type and entity overlap
   - **Returns:** Clusters with frame counts, dominant frame type, keywords
   - **Filters:** active_only, min_frame_count, limit
   - **MCP Tool:** `list_narrative_clusters`

**Operational/Admin Endpoints:**
2. POST /api/v1/narrative/frames
   - Create narrative frame (internal service use)
   - Priority: N/A (not for MCP)

3. POST /api/v1/narrative/clusters/update
   - Update clusters from recent frames (admin)
   - Priority: Low (periodic task)

4. GET /api/v1/narrative/cache/stats
   - Cache performance statistics
   - Priority: Low (monitoring)

5. POST /api/v1/narrative/cache/clear
   - Clear cache entries (admin)
   - Priority: Low (admin maintenance)

---

### 3. entity-canonicalization-service (Port 8112)

**Already Implemented (7 tools):**
- ✅ POST /api/v1/canonicalization/canonicalize → `canonicalize_entity`
- ✅ GET /api/v1/canonicalization/clusters → `get_entity_clusters`
- ✅ POST /api/v1/canonicalization/canonicalize/batch → `batch_canonicalize_entities`
- ✅ GET /api/v1/canonicalization/stats → `get_canonicalization_stats`
- ✅ GET /api/v1/canonicalization/jobs/{job_id}/status → `get_async_job_status`
- ✅ GET /api/v1/canonicalization/jobs/{job_id}/result → `get_async_job_result`
- ✅ GET /api/v1/canonicalization/aliases/{canonical_name} → `get_entity_aliases`

**New Endpoints Discovered:**

**Analytics Endpoints:**
1. GET /api/v1/canonicalization/stats/detailed
   - Extended statistics with cache performance
   - Priority: Medium (detailed monitoring)

2. GET /api/v1/canonicalization/trends/entity-types
   - Entity type distribution trends
   - Priority: Medium (analytics)

3. GET /api/v1/canonicalization/history/merges
   - Merge operation history
   - Priority: Medium (analytics)

**Admin/Operational Endpoints:**
4. POST /api/v1/canonicalization/canonicalize/batch/async
   - Async batch canonicalization (already have sync version)
   - Priority: Low (operational alternative)

5. POST /api/v1/canonicalization/reprocess/start
   - Start reprocessing all entities (admin)
   - Priority: Low (maintenance)

6. GET /api/v1/canonicalization/reprocess/status
   - Reprocess job status
   - Priority: Low (admin monitoring)

7. POST /api/v1/canonicalization/reprocess/stop
   - Stop reprocessing (admin)
   - Priority: Low (admin control)

8. GET /api/v1/canonicalization/reprocess/celery-status/{task_id}
   - Celery task status
   - Priority: Low (operational)

9. POST /api/v1/canonicalization/admin/cleanup-memory
   - Clear in-memory caches (admin)
   - Priority: Low (admin maintenance)

10. GET /api/v1/canonicalization/health
    - Health check (already covered by service health)
    - Priority: N/A (redundant)

---

### 4. osint-service (Port 8104)

**Already Implemented (10 tools):**
- ✅ GET /api/v1/patterns/detect → `detect_intelligence_patterns`
- ✅ GET /api/v1/graph/quality → `analyze_graph_quality`
- ✅ GET /api/v1/templates/ → `list_osint_templates`
- ✅ GET /api/v1/templates/{template_name} → `get_osint_template`
- ✅ POST /api/v1/instances/{instance_id}/execute → `execute_osint_instance`
- ✅ GET /api/v1/executions/{execution_id} → `get_osint_execution`
- ✅ GET /api/v1/instances/ → `list_osint_instances`
- ✅ POST /api/v1/instances/ → `create_osint_instance`
- ✅ GET /api/v1/alerts/ → `list_osint_alerts`
- ✅ GET /api/v1/alerts/stats → `get_osint_alert_stats`

**New Endpoints Discovered:**

**Template Management:**
1. GET /api/v1/templates/categories
   - List template categories
   - Priority: Medium (template discovery)

2. POST /api/v1/templates/reload
   - Reload templates from disk (admin)
   - Priority: Low (admin operation)

3. POST /api/v1/templates/validate
   - Validate template configuration
   - Priority: Low (development/admin)

**Instance Management:**
4. GET /api/v1/instances/{instance_id}
   - Get single instance details
   - Priority: Medium (useful with list)

5. PUT /api/v1/instances/{instance_id}
   - Update instance configuration
   - Priority: Medium (management)

6. DELETE /api/v1/instances/{instance_id}
   - Delete instance
   - Priority: Medium (management)

7. POST /api/v1/instances/{instance_id}/pause
   - Pause monitoring
   - Priority: Medium (management)

8. POST /api/v1/instances/{instance_id}/resume
   - Resume monitoring
   - Priority: Medium (management)

**Alert Management:**
9. GET /api/v1/alerts/{alert_id}
   - Get single alert details
   - Priority: Medium (useful with list)

10. POST /api/v1/alerts/{alert_id}/acknowledge
    - Acknowledge alert
    - Priority: Medium (alert workflow)

**Execution Tracking:**
11. GET /api/v1/executions/
    - List executions with filtering
    - Priority: Medium (operational)

---

### 5. analysis-service (Port 8102)

**Already Implemented (3 tools):**
- ✅ POST /api/v1/analyze → `analyze_article`
- ✅ POST /api/v1/extract → `extract_entities`
- ✅ GET /api/v1/analysis/{analysis_id} → `get_analysis_status`

**Status:** Core endpoints covered. Additional analysis endpoints would be in content-analysis-v3-service.

---

## 🎯 Implementation Priority

### Phase 1: High-Value Analytics (4 tools) ⭐ **IMPLEMENT NOW**

**Goal:** Reach 32 tools (64-80% of Phase 1 target)

1. **get_cluster_events** (intelligence-service)
   - Essential drill-down capability
   - Complements existing cluster tools
   - High user value

2. **get_subcategories** (intelligence-service)
   - Dynamic topic discovery
   - Unique insight into current news
   - High analytical value

3. **get_risk_history** (intelligence-service)
   - Trend visualization
   - Historical context
   - High dashboard value

4. **list_narrative_clusters** (narrative-service)
   - Narrative pattern discovery
   - Complements frame analysis
   - High analytical value

**Implementation Effort:** ~1-2 hours
**Expected Result:** 32 total tools (64-80% of 40-50 target)

---

### Phase 2: Management & Operations (8-10 tools)

**Implement if needed to reach 40-50 target**

**OSINT Management (6 tools):**
- get_osint_instance
- update_osint_instance
- delete_osint_instance
- pause_osint_instance
- resume_osint_instance
- acknowledge_osint_alert

**Entity Management (3 tools):**
- get_entity_trends
- get_merge_history
- get_detailed_canonicalization_stats

**Intelligence Admin (3 tools):**
- trigger_manual_clustering
- get_clustering_status
- get_clustering_task_status

**Implementation Effort:** ~2-3 hours
**Expected Result:** 40-42 total tools (80-105% of target)

---

## 📈 Projected Progress

**Current:** 28 tools (56-70% of 40-50 target)

**After Phase 1 (High-Value Analytics):**
- Total: 32 tools
- Progress: 64-80% of target
- Status: Strong foundation with essential analytics
- Decision: Evaluate if Phase 2 needed

**After Phase 2 (Management & Operations):**
- Total: 40-42 tools
- Progress: 80-105% of target
- Status: Comprehensive coverage with management capabilities
- Decision: Phase 1 Server 1 complete

---

## 🎓 Lessons & Observations

### Service API Patterns

1. **intelligence-service:**
   - Rich analytics capabilities
   - Good pagination support
   - Normalized risk scores (0-100 scale)
   - Trend analysis built-in

2. **narrative-service:**
   - Excellent caching layer
   - Parallel query execution
   - Well-structured responses
   - Cache statistics available

3. **entity-canonicalization-service:**
   - Comprehensive async job tracking
   - Good monitoring capabilities
   - Admin operations well-separated
   - Vector-based similarity matching

4. **osint-service:**
   - Template-based architecture
   - Instance lifecycle management
   - Alert workflow support
   - 50+ pre-built templates

### MCP Tool Design Insights

1. **Prioritize analytics over operations**
   - Users need insights, not admin tasks
   - Management tools can be Phase 2

2. **Cluster-related tools are highly valuable**
   - Event clustering is core intelligence feature
   - Users want to drill down into clusters
   - Historical trends enhance understanding

3. **Pagination is essential**
   - Large result sets need pagination
   - Consistent pagination pattern across tools

4. **Cache awareness**
   - Services use intelligent caching
   - MCP tools benefit from backend caching
   - No need to implement MCP-level caching

---

## 📚 References

### Source Files Analyzed

**intelligence-service:**
- `/services/intelligence-service/app/routers/intelligence.py` (727 lines)
- `/services/intelligence-service/app/api/clustering_admin.py` (132 lines)

**narrative-service:**
- `/services/narrative-service/app/routers/narrative.py` (498 lines)

**entity-canonicalization-service:**
- `/services/entity-canonicalization-service/app/api/routes/canonicalization.py` (analyzed previously)

**osint-service:**
- `/services/osint-service/app/api/templates.py` (analyzed previously)
- `/services/osint-service/app/api/instances.py` (analyzed previously)
- `/services/osint-service/app/api/executions.py` (analyzed previously)
- `/services/osint-service/app/api/alerts.py` (analyzed previously)

---

**Last Updated:** 2025-12-04 18:30 UTC
**Next Action:** Implement Phase 1 high-value analytics tools (4 tools)
**Estimated Time:** 1-2 hours
