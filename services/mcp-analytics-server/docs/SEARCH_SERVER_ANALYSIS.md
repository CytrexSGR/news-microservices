# MCP Search Server - Endpoint Analysis

**Date:** 2025-12-04
**Purpose:** Analyze search-service, feed-service, and research-service APIs for Phase 1 Server 2
**Target:** 20-25 MCP tools for mcp-search-server
**Services:** 3 backend services (search, feed, research)
**Total Endpoints:** ~57 endpoints across all services

---

## 📊 Summary

**Services Analyzed:**
- search-service (Port 8106) - 19 endpoints
- feed-service (Port 8101) - 19+ endpoints
- research-service (Port 8103) - 19 endpoints

**Goal:** Select 20-25 most valuable endpoints for MCP tool implementation

**Strategy:** Focus on user-facing functionality, exclude admin/stats endpoints

---

## 🔍 Detailed Endpoint Analysis

### 1. search-service (Port 8106)

#### Core Search Endpoints (6) ⭐ **HIGH PRIORITY**

1. **GET /api/v1/search**
   - **Purpose:** Basic article search with PostgreSQL full-text search
   - **Parameters:** query, page, page_size, source, sentiment, date_from, date_to
   - **Value:** Essential search functionality
   - **MCP Tool:** `search_articles`

2. **POST /api/v1/search/advanced**
   - **Purpose:** Advanced search with fuzzy matching, highlighting, facets
   - **Features:** AND/OR operators, phrase search, field search, exclusion
   - **Value:** Power user search capabilities
   - **MCP Tool:** `advanced_search`

3. **GET /api/v1/search/suggest**
   - **Purpose:** Search query suggestions/autocomplete
   - **Value:** Improves search UX
   - **MCP Tool:** `get_search_suggestions`

4. **GET /api/v1/search/facets**
   - **Purpose:** Get available facets for search filtering
   - **Value:** Discover filter options
   - **MCP Tool:** `get_search_facets`

5. **GET /api/v1/search/popular**
   - **Purpose:** Get popular/trending searches
   - **Value:** Discover what others are searching
   - **MCP Tool:** `get_popular_searches`

6. **GET /api/v1/search/related**
   - **Purpose:** Get related searches based on query
   - **Value:** Search exploration
   - **MCP Tool:** `get_related_searches`

#### Saved Searches (5) ⭐ **MEDIUM PRIORITY**

7. **GET /api/v1/saved-searches**
   - **Purpose:** List user's saved searches
   - **Value:** Personal search management
   - **MCP Tool:** `list_saved_searches`

8. **POST /api/v1/saved-searches**
   - **Purpose:** Create/save a search query
   - **Value:** Reusable searches
   - **MCP Tool:** `create_saved_search`

9. **GET /api/v1/saved-searches/{search_id}**
   - **Purpose:** Get specific saved search
   - **Value:** Retrieve saved search details
   - **MCP Tool:** `get_saved_search`

10. **PUT /api/v1/saved-searches/{search_id}**
    - **Purpose:** Update saved search
    - **Value:** Modify saved searches
    - **MCP Tool:** `update_saved_search`

11. **DELETE /api/v1/saved-searches/{search_id}**
    - **Purpose:** Delete saved search
    - **Value:** Search management
    - **MCP Tool:** `delete_saved_search`

#### Search History (2) 🔸 **LOW PRIORITY**

12. GET /api/v1/history - Get search history
13. DELETE /api/v1/history - Clear search history

#### Admin Endpoints (7) ⏸️ **SKIP (Admin-only)**

- GET /admin/stats/* - Statistics endpoints (5)
- POST /admin/reindex - Reindex operation
- POST /admin/sync - Sync operation

**Selected for MCP:** 11 tools (Core + Saved Searches)

---

### 2. feed-service (Port 8101)

#### Core Feed Management (8) ⭐ **HIGH PRIORITY**

*Note: Need to read feeds.py in detail to get exact endpoints*

1. **GET /api/v1/feeds**
   - **Purpose:** List all feeds
   - **Value:** Feed discovery
   - **MCP Tool:** `list_feeds`

2. **POST /api/v1/feeds**
   - **Purpose:** Create new feed
   - **Value:** Feed management
   - **MCP Tool:** `create_feed`

3. **GET /api/v1/feeds/{feed_id}**
   - **Purpose:** Get specific feed details
   - **Value:** Feed information
   - **MCP Tool:** `get_feed`

4. **PUT /api/v1/feeds/{feed_id}**
   - **Purpose:** Update feed
   - **Value:** Feed configuration
   - **MCP Tool:** `update_feed`

5. **DELETE /api/v1/feeds/{feed_id}**
   - **Purpose:** Delete feed
   - **Value:** Feed cleanup
   - **MCP Tool:** `delete_feed`

6. **GET /api/v1/feeds/{feed_id}/items**
   - **Purpose:** Get feed items/articles
   - **Value:** Browse feed content
   - **MCP Tool:** `get_feed_items`

7. **POST /api/v1/feeds/{feed_id}/fetch**
   - **Purpose:** Manual feed fetch
   - **Value:** Immediate update
   - **MCP Tool:** `fetch_feed`

8. **GET /api/v1/feeds/{feed_id}/health**
   - **Purpose:** Feed health status
   - **Value:** Monitor feed quality
   - **MCP Tool:** `get_feed_health`

#### Feed Assessment (3) ⭐ **MEDIUM PRIORITY**

9. **POST /api/v1/feeds/{feed_id}/assess**
   - **Purpose:** Assess feed credibility with Perplexity
   - **Value:** Automated feed vetting
   - **MCP Tool:** `assess_feed`

10. **GET /api/v1/feeds/{feed_id}/assessment-history**
    - **Purpose:** Feed assessment history
    - **Value:** Track assessment changes
    - **MCP Tool:** `get_assessment_history`

11. **POST /api/v1/feeds/pre-assess**
    - **Purpose:** Pre-assess feed before adding
    - **Value:** Preview feed quality
    - **MCP Tool:** `pre_assess_feed`

#### Scheduling (6) 🔸 **LOW PRIORITY**

12. GET /scheduling/timeline - Schedule timeline
13. GET /scheduling/distribution - Schedule distribution
14. POST /scheduling/optimize - Optimize schedule
15. GET /scheduling/conflicts - Schedule conflicts
16. GET /scheduling/stats - Scheduling statistics
17. PUT /scheduling/feeds/{feed_id}/schedule - Update feed schedule

#### Admiralty Codes (10) ⏸️ **SKIP (Admin configuration)**

- GET/PUT /admiralty-codes/thresholds/* - Threshold management (4)
- GET/PUT /admiralty-codes/weights/* - Weight management (5)
- GET /admiralty-codes/status - Configuration status

**Selected for MCP:** 11 tools (Core + Assessment)

---

### 3. research-service (Port 8103)

#### Research Tasks (7) ⭐ **HIGH PRIORITY**

1. **POST /api/v1/research**
   - **Purpose:** Create Perplexity research task
   - **Value:** AI-powered research
   - **MCP Tool:** `create_research_task`

2. **POST /api/v1/research/batch**
   - **Purpose:** Create multiple research tasks
   - **Value:** Batch research operations
   - **MCP Tool:** `create_batch_research`

3. **GET /api/v1/research**
   - **Purpose:** List research tasks
   - **Value:** Task management
   - **MCP Tool:** `list_research_tasks`

4. **GET /api/v1/research/{task_id}**
   - **Purpose:** Get research task details
   - **Value:** Task results
   - **MCP Tool:** `get_research_task`

5. **GET /api/v1/research/history**
   - **Purpose:** Research task history
   - **Value:** Historical research data
   - **MCP Tool:** `get_research_history`

6. **GET /api/v1/research/stats**
   - **Purpose:** Usage statistics
   - **Value:** Monitor API usage
   - **MCP Tool:** `get_research_stats`

7. **GET /api/v1/research/feed/{feed_id}**
   - **Purpose:** Get research tasks for specific feed
   - **Value:** Feed-specific research
   - **MCP Tool:** `get_feed_research_tasks`

#### Research Templates (4) ⭐ **MEDIUM PRIORITY**

8. **GET /api/v1/templates**
   - **Purpose:** List research templates
   - **Value:** Reusable research workflows
   - **MCP Tool:** `list_research_templates`

9. **GET /api/v1/templates/{template_id}**
   - **Purpose:** Get template details
   - **Value:** Template information
   - **MCP Tool:** `get_research_template`

10. **POST /api/v1/templates/{template_id}/apply**
    - **Purpose:** Apply template to create task
    - **Value:** Quick research from template
    - **MCP Tool:** `apply_research_template`

11. **GET /api/v1/templates/functions**
    - **Purpose:** List available research functions
    - **Value:** Discover research capabilities
    - **MCP Tool:** `list_research_functions`

#### Template Management (3) 🔸 **LOW PRIORITY**

12. POST /templates - Create template
13. PUT /templates/{id} - Update template
14. DELETE /templates/{id} - Delete template

#### Research Runs (5) 🔸 **LOW PRIORITY**

15. GET /runs - List runs
16. POST /runs - Create run
17. GET /runs/{id} - Get run details
18. GET /runs/{id}/status - Get run status
19. POST /runs/{id}/cancel - Cancel run

**Selected for MCP:** 11 tools (Tasks + Core Templates)

---

## 🎯 Implementation Priority

### Phase 1: Core Functionality (11 tools) ⭐ **IMPLEMENT FIRST**

**search-service (4 tools):**
1. search_articles - Basic search
2. advanced_search - Advanced search
3. get_search_suggestions - Autocomplete
4. get_search_facets - Filter discovery

**feed-service (4 tools):**
5. list_feeds - Browse feeds
6. get_feed - Feed details
7. get_feed_items - Feed content
8. assess_feed - Feed credibility

**research-service (3 tools):**
9. create_research_task - AI research
10. get_research_task - Task results
11. list_research_tasks - Task management

**Total:** 11 tools (44% of 25 target)

---

### Phase 2: Extended Features (11 tools) ⭐ **IMPLEMENT NEXT**

**search-service (5 tools):**
12. get_popular_searches - Trending searches
13. get_related_searches - Search exploration
14. list_saved_searches - Saved search management
15. create_saved_search - Save search
16. delete_saved_search - Remove saved search

**feed-service (3 tools):**
17. create_feed - Add new feed
18. get_feed_health - Monitor feed quality
19. pre_assess_feed - Preview feed quality

**research-service (3 tools):**
20. get_research_history - Historical research
21. list_research_templates - Template discovery
22. apply_research_template - Quick research

**Total:** 22 tools (88% of 25 target)

---

### Phase 3: Advanced Features (3 tools) 🔸 **OPTIONAL**

**search-service (1 tool):**
23. update_saved_search - Modify saved search

**feed-service (1 tool):**
24. fetch_feed - Manual feed update

**research-service (1 tool):**
25. create_batch_research - Batch research operations

**Total:** 25 tools (100% of target)

---

## 📈 Projected Progress

### After Phase 1 (11 tools)
- **Progress:** 44% of 25 target
- **Coverage:** Core search, feed, and research functionality
- **User Value:** Essential operations covered

### After Phase 2 (22 tools)
- **Progress:** 88% of 25 target
- **Coverage:** Extended features including saved searches, templates
- **User Value:** Comprehensive functionality

### After Phase 3 (25 tools)
- **Progress:** 100% of 25 target
- **Coverage:** Advanced features for power users
- **User Value:** Complete Phase 1 Server 2

---

## 🎓 Key Insights

### 1. Service Coverage Balance

Each service contributes evenly to the 25-tool target:
- **search-service:** 8-10 tools (32-40%)
- **feed-service:** 7-9 tools (28-36%)
- **research-service:** 7-8 tools (28-32%)

### 2. Admin Endpoints Excluded

~24 admin/stats endpoints excluded:
- search-service: 7 admin endpoints
- feed-service: 16 admin/config endpoints
- research-service: 1 admin endpoint

**Rationale:** Focus on user-facing functionality

### 3. Template vs. Direct Operations

Research service has template-based and direct operations:
- **Direct:** create_research_task (flexible)
- **Template:** apply_research_template (quick)
- **Both valuable** for different use cases

### 4. Feed Assessment Integration

Feed assessment is Perplexity-powered:
- Automated credibility scoring
- Historical tracking
- Pre-assessment for new feeds

**High value** for news source vetting

---

## 📚 Next Steps

### 1. Create mcp-search-server Structure
- Copy mcp-intelligence-server as template
- Adapt config for search/feed/research services
- Update port configuration

### 2. Implement Client Methods
- SearchClient with circuit breaker
- FeedClient with circuit breaker
- ResearchClient with circuit breaker

### 3. Add MCP Tool Registrations
- Phase 1: 11 core tools
- Phase 2: 11 extended tools
- Phase 3: 3 advanced tools

### 4. Configure Docker Compose
- Add mcp-search-server service
- Port mapping (e.g., 9002)
- Environment variables

### 5. Test & Verify
- Restart services
- Verify 20-25 tools loaded
- Test in Claude Desktop

---

## 📊 Resource Requirements

**Development Time:**
- Phase 1 (11 tools): ~2 hours
- Phase 2 (11 tools): ~2 hours
- Phase 3 (3 tools): ~30 minutes
- **Total:** ~4.5 hours

**Infrastructure:**
- New Docker service (mcp-search-server)
- Port 9002 (similar to 9001 for intelligence)
- ~100-150 MB Docker image
- Shared PostgreSQL connection

---

**Last Updated:** 2025-12-04 18:45 UTC
**Next Action:** Create mcp-search-server project structure
**Estimated Completion:** Phase 1 complete in ~2 hours
