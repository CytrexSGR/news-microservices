# Research Service API Endpoints

## Summary
Total Endpoints: **20** (Target: 14 ✅)

## Endpoint Breakdown

### Research Task Endpoints (7 endpoints)
**Prefix**: `/research`

1. **POST** `/research/` - Create a new research task
   - Request: `ResearchTaskCreate` (query, model_name, depth, feed_id, article_id)
   - Response: `ResearchTaskResponse`
   - Status: 201 Created

2. **GET** `/research/{task_id}` - Get a specific research task
   - Response: `ResearchTaskResponse`

3. **GET** `/research/` - List research tasks with pagination
   - Query params: status, feed_id, page, page_size
   - Response: `ResearchTaskList`

4. **POST** `/research/batch` - Create multiple research tasks
   - Request: `ResearchTaskBatchCreate` (queries list, model_name, depth, feed_id)
   - Response: `list[ResearchTaskResponse]`

5. **GET** `/research/feed/{feed_id}` - Get research tasks for a specific feed
   - Query params: limit
   - Response: `list[ResearchTaskResponse]`

6. **GET** `/research/history` - Get research history
   - Query params: days, page, page_size
   - Response: `ResearchTaskList`

7. **GET** `/research/stats` - Get usage statistics
   - Query params: days
   - Response: `UsageStats` (total_requests, total_tokens, total_cost, breakdown by model)

### Template Endpoints (7 endpoints)
**Prefix**: `/templates`

8. **POST** `/templates/` - Create a new research template
   - Request: `TemplateCreate` (name, description, query_template, parameters, default_model, default_depth)
   - Response: `TemplateResponse`
   - Status: 201 Created

9. **GET** `/templates/` - List available templates
   - Query params: include_public
   - Response: `list[TemplateResponse]`

10. **GET** `/templates/{template_id}` - Get a specific template
    - Response: `TemplateResponse`

11. **PUT** `/templates/{template_id}` - Update a template
    - Request: `TemplateUpdate` (name, description, query_template, parameters, etc.)
    - Response: `TemplateResponse`

12. **DELETE** `/templates/{template_id}` - Delete a template (soft delete)
    - Status: 204 No Content

13. **POST** `/templates/{template_id}/preview` - Preview rendered template with variables
    - Request: `TemplateApply` (variables, model_name, depth, feed_id, article_id)
    - Response: `TemplatePreview` (rendered_query, estimated_cost)

14. **POST** `/templates/{template_id}/apply` - Apply template and create research task
    - Request: `TemplateApply`
    - Response: `ResearchTaskResponse`

### Research Run Endpoints (6 endpoints) 🆕
**Prefix**: `/runs`

15. **POST** `/runs/` - Create a new research run from a template
    - Request: `ResearchRunCreate` (template_id, parameters, model_name, depth, scheduled_at, is_recurring)
    - Response: `ResearchRunResponse`
    - Status: 201 Created

16. **GET** `/runs/{run_id}` - Get a specific research run
    - Response: `ResearchRunResponse`

17. **GET** `/runs/{run_id}/status` - Get the current status of a research run
    - Response: `ResearchRunStatus` (status, progress, tasks_created, tasks_completed, tasks_failed)

18. **GET** `/runs/` - List research runs with pagination
    - Query params: status, template_id, page, page_size
    - Response: `ResearchRunList`

19. **POST** `/runs/{run_id}/cancel` - Cancel a pending or running research run
    - Status: 204 No Content

20. **GET** `/runs/template/{template_id}` - Get research runs for a specific template
    - Query params: limit
    - Response: `list[ResearchRunResponse]`

## Authentication
All endpoints require JWT authentication via `get_current_user` dependency.

## Error Handling
- **400 Bad Request**: Invalid input, cost limits exceeded
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: Insufficient permissions (e.g., updating another user's template)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Unexpected server errors

## Key Features

### Research Tasks
- Single and batch task creation
- Status tracking (pending, processing, completed, failed)
- Cost tracking and usage statistics
- Result caching with Redis
- Feed and article association

### Templates
- Parameterized query templates
- Public and private templates
- Template preview with cost estimation
- Direct template application
- Usage statistics tracking

### Research Runs (NEW!)
- Automated research execution from templates
- Scheduled and recurring runs
- Real-time progress tracking
- Cancellation support
- Comprehensive run statistics
- Task linkage and aggregation
- Cost tracking per run

## Implementation Details

### Files Created/Modified
1. `/app/api/runs.py` - New run endpoints (6 endpoints)
2. `/app/services/run_service.py` - ResearchRunService implementation
3. `/app/schemas/research.py` - Added ResearchRun schemas (ResearchRunCreate, ResearchRunResponse, ResearchRunList, ResearchRunStatus)
4. `/app/models/research.py` - ResearchRun model (already exists, linked to ResearchTask and CostTracking)
5. `/app/api/__init__.py` - Updated to include runs router

### Service Architecture
- **ResearchService**: Core research task execution
- **TemplateService**: Template management and application
- **ResearchRunService**: Batch/scheduled research orchestration

### Database Models
- **ResearchTask**: Individual research queries
- **ResearchTemplate**: Reusable query templates
- **ResearchRun**: Batch execution records
- **ResearchCache**: Result caching
- **CostTracking**: Cost monitoring and limits

## Status
✅ **Complete** - 20/14 endpoints implemented (143% of target)
