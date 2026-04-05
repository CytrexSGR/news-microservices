/**
 * Scheduler Service API Client
 *
 * Handles communication with scheduler-service (port 8108)
 * Endpoints:
 * - GET /api/v1/scheduler/status - Scheduler status
 * - GET /api/v1/scheduler/jobs - List all analysis jobs
 * - GET /api/v1/scheduler/jobs/stats - Job queue statistics
 * - GET /api/v1/scheduler/cron/jobs - List cron jobs
 * - POST /api/v1/scheduler/jobs/:id/retry - Retry failed job
 * - POST /api/v1/scheduler/jobs/:id/cancel - Cancel pending job
 * - POST /api/v1/scheduler/feeds/:feed_id/check - Force feed check
 * - POST /api/v1/scheduler/neo4j/entities/deduplicate - Deduplicate entities
 */

import type {
  SchedulerStatus,
  JobListResponse,
  JobStats,
  CronJobListResponse,
  JobActionResponse,
  FeedCheckResponse,
  DeduplicationResponse,
  JobsQuery,
} from '../types';

const SCHEDULER_SERVICE_URL =
  import.meta.env.VITE_SCHEDULER_SERVICE_URL || 'http://localhost:8108';

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

    const response = await fetch(`${SCHEDULER_SERVICE_URL}${endpoint}`, {
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
// Scheduler Status API
// ============================================================================

/**
 * Get scheduler operational status
 */
export async function getSchedulerStatus(): Promise<
  ApiResponse<SchedulerStatus>
> {
  return fetchApi<SchedulerStatus>('/api/v1/scheduler/status');
}

// ============================================================================
// Job Queue API
// ============================================================================

/**
 * List analysis jobs with optional filtering
 */
export async function listJobs(
  params?: JobsQuery
): Promise<ApiResponse<JobListResponse>> {
  const searchParams = new URLSearchParams();

  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const queryString = searchParams.toString();
  return fetchApi<JobListResponse>(
    `/api/v1/scheduler/jobs${queryString ? `?${queryString}` : ''}`
  );
}

/**
 * Get job queue statistics
 */
export async function getJobStats(): Promise<ApiResponse<JobStats>> {
  return fetchApi<JobStats>('/api/v1/scheduler/jobs/stats');
}

/**
 * Retry a failed job
 */
export async function retryJob(
  jobId: string
): Promise<ApiResponse<JobActionResponse>> {
  return fetchApi<JobActionResponse>(`/api/v1/scheduler/jobs/${jobId}/retry`, {
    method: 'POST',
  });
}

/**
 * Cancel a pending or processing job
 */
export async function cancelJob(
  jobId: string
): Promise<ApiResponse<JobActionResponse>> {
  return fetchApi<JobActionResponse>(`/api/v1/scheduler/jobs/${jobId}/cancel`, {
    method: 'POST',
  });
}

// ============================================================================
// Cron Jobs API
// ============================================================================

/**
 * List all cron scheduled jobs
 */
export async function listCronJobs(): Promise<
  ApiResponse<CronJobListResponse>
> {
  return fetchApi<CronJobListResponse>('/api/v1/scheduler/cron/jobs');
}

// ============================================================================
// Feed Operations API
// ============================================================================

/**
 * Force immediate feed check and analysis
 */
export async function forceFeedCheck(
  feedId: string
): Promise<ApiResponse<FeedCheckResponse>> {
  return fetchApi<FeedCheckResponse>(
    `/api/v1/scheduler/feeds/${feedId}/check`,
    {
      method: 'POST',
    }
  );
}

// ============================================================================
// Entity Operations API
// ============================================================================

/**
 * Run entity deduplication on Neo4j Knowledge Graph
 */
export async function runDeduplication(
  dryRun = true
): Promise<ApiResponse<DeduplicationResponse>> {
  return fetchApi<DeduplicationResponse>(
    `/api/v1/scheduler/neo4j/entities/deduplicate?dry_run=${dryRun}`,
    {
      method: 'POST',
    }
  );
}
