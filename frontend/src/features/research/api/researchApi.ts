/**
 * Research Service API Client
 *
 * Handles communication with research-service (port 8103)
 * Endpoints:
 * - POST /api/v1/research - Create research task
 * - GET /api/v1/research - List research tasks
 * - GET /api/v1/research/{task_id} - Get task details
 * - GET /api/v1/research/history - Get research history
 * - POST /api/v1/research/batch - Create batch tasks
 * - GET /api/v1/templates - List templates
 * - POST /api/v1/templates/{id}/apply - Apply template
 * - GET /api/v1/templates/functions - List research functions
 */

import type {
  ResearchTaskCreate,
  ResearchTaskBatchCreate,
  ResearchTaskResponse,
  ResearchTaskList,
  ResearchTasksQuery,
  ResearchHistoryQuery,
  TemplateResponse,
  TemplateApply,
  UsageStats,
  ResearchFunctionInfo,
  ResearchSourcesResponse,
  ExportRequest,
  ExportResponse,
  CancelResponse,
  RetryResponse,
  ExportFormat,
} from '../types';

const RESEARCH_SERVICE_URL =
  import.meta.env.VITE_RESEARCH_SERVICE_URL || 'http://localhost:8103';

/**
 * API Response wrapper
 */
interface ApiResponse<T> {
  data?: T;
  error?: string;
}

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  try {
    const authStorage = localStorage.getItem('auth-storage');
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      return parsed.state?.token || null;
    }
  } catch {
    // Ignore parse errors
  }
  return null;
}

/**
 * Fetch helper with error handling and auth
 */
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${RESEARCH_SERVICE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorJson.message || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      return { error: errorMessage };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

// ============================================================================
// Research Tasks API
// ============================================================================

/**
 * Create a new research task
 */
export async function createResearchTask(
  taskData: ResearchTaskCreate
): Promise<ApiResponse<ResearchTaskResponse>> {
  return fetchApi<ResearchTaskResponse>('/api/v1/research/', {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
}

/**
 * Get a specific research task
 */
export async function getResearchTask(
  taskId: number
): Promise<ApiResponse<ResearchTaskResponse>> {
  return fetchApi<ResearchTaskResponse>(`/api/v1/research/${taskId}`);
}

/**
 * List research tasks with pagination and filters
 */
export async function listResearchTasks(
  params?: ResearchTasksQuery
): Promise<ApiResponse<ResearchTaskList>> {
  const searchParams = new URLSearchParams();

  if (params?.status) searchParams.set('status', params.status);
  if (params?.feed_id) searchParams.set('feed_id', params.feed_id);
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

  const queryString = searchParams.toString();
  return fetchApi<ResearchTaskList>(
    `/api/v1/research/${queryString ? `?${queryString}` : ''}`
  );
}

/**
 * Get research history
 */
export async function getResearchHistory(
  params?: ResearchHistoryQuery
): Promise<ApiResponse<ResearchTaskList>> {
  const searchParams = new URLSearchParams();

  if (params?.days) searchParams.set('days', params.days.toString());
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

  const queryString = searchParams.toString();
  return fetchApi<ResearchTaskList>(
    `/api/v1/research/history${queryString ? `?${queryString}` : ''}`
  );
}

/**
 * Create batch research tasks
 */
export async function createBatchTasks(
  batchData: ResearchTaskBatchCreate
): Promise<ApiResponse<ResearchTaskResponse[]>> {
  return fetchApi<ResearchTaskResponse[]>('/api/v1/research/batch', {
    method: 'POST',
    body: JSON.stringify(batchData),
  });
}

/**
 * Get research tasks for a specific feed
 */
export async function getFeedResearchTasks(
  feedId: string,
  limit = 10
): Promise<ApiResponse<ResearchTaskResponse[]>> {
  return fetchApi<ResearchTaskResponse[]>(
    `/api/v1/research/feed/${feedId}?limit=${limit}`
  );
}

/**
 * Get usage statistics
 */
export async function getUsageStats(
  days = 30
): Promise<ApiResponse<UsageStats>> {
  return fetchApi<UsageStats>(`/api/v1/research/stats?days=${days}`);
}

// ============================================================================
// Templates API
// ============================================================================

/**
 * List available templates
 */
export async function listTemplates(
  includePublic = true
): Promise<ApiResponse<TemplateResponse[]>> {
  return fetchApi<TemplateResponse[]>(
    `/api/v1/templates/?include_public=${includePublic}`
  );
}

/**
 * Get a specific template
 */
export async function getTemplate(
  templateId: number
): Promise<ApiResponse<TemplateResponse>> {
  return fetchApi<TemplateResponse>(`/api/v1/templates/${templateId}`);
}

/**
 * Apply a template to create a research task
 */
export async function applyTemplate(
  templateId: number,
  applyData: TemplateApply
): Promise<ApiResponse<ResearchTaskResponse>> {
  return fetchApi<ResearchTaskResponse>(`/api/v1/templates/${templateId}/apply`, {
    method: 'POST',
    body: JSON.stringify(applyData),
  });
}

/**
 * List available research functions
 */
export async function listResearchFunctions(): Promise<
  ApiResponse<{ functions: ResearchFunctionInfo[] }>
> {
  return fetchApi<{ functions: ResearchFunctionInfo[] }>(
    '/api/v1/templates/functions'
  );
}

// ============================================================================
// Cancel, Retry, Sources, Export API
// ============================================================================

/**
 * Cancel a pending or processing research task
 */
export async function cancelResearchTask(
  taskId: number
): Promise<ApiResponse<CancelResponse>> {
  return fetchApi<CancelResponse>(`/api/v1/research/${taskId}/cancel`, {
    method: 'POST',
  });
}

/**
 * Retry a failed research task
 */
export async function retryResearchTask(
  taskId: number
): Promise<ApiResponse<RetryResponse>> {
  return fetchApi<RetryResponse>(`/api/v1/research/${taskId}/retry`, {
    method: 'POST',
  });
}

/**
 * Get sources for a completed research task
 */
export async function getResearchSources(
  taskId: number
): Promise<ApiResponse<ResearchSourcesResponse>> {
  return fetchApi<ResearchSourcesResponse>(`/api/v1/research/${taskId}/sources`);
}

/**
 * Export research task to specified format
 */
export async function exportResearchTask(
  taskId: number,
  format: ExportFormat = 'markdown',
  options?: Omit<ExportRequest, 'format'>
): Promise<ApiResponse<ExportResponse>> {
  const params = new URLSearchParams({ format });
  if (options?.include_sources !== undefined) {
    params.set('include_sources', String(options.include_sources));
  }
  if (options?.include_metadata !== undefined) {
    params.set('include_metadata', String(options.include_metadata));
  }
  return fetchApi<ExportResponse>(
    `/api/v1/research/${taskId}/export?${params.toString()}`
  );
}
