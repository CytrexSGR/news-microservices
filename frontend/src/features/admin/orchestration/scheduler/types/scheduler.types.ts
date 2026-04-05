/**
 * Scheduler Service Types
 *
 * TypeScript type definitions for the Scheduler Service MCP tools.
 * Based on: mcp-orchestration-server scheduler tools
 */

/**
 * Scheduler Status Response
 */
export interface SchedulerStatus {
  active_jobs: number;
  pending_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  worker_status: 'running' | 'stopped' | 'starting' | 'error';
  uptime_seconds: number;
  last_heartbeat: string;
  version: string;
}

/**
 * Scheduler Health Response
 */
export interface SchedulerHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    celery: ComponentHealth;
    redis: ComponentHealth;
    database: ComponentHealth;
  };
  last_check: string;
  details?: string;
}

export interface ComponentHealth {
  status: 'healthy' | 'unhealthy';
  latency_ms?: number;
  error?: string;
}

/**
 * Job Types
 */
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  name: string;
  task_name: string;
  status: JobStatus;
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  result?: unknown;
  retries: number;
  max_retries: number;
  eta?: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
}

export interface JobsListResponse {
  jobs: Job[];
  total: number;
  skip: number;
  limit: number;
}

export interface JobsListParams {
  status?: JobStatus;
  skip?: number;
  limit?: number;
  task_name?: string;
}

/**
 * Jobs Statistics
 */
export interface JobsStats {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  success_rate: number;
  avg_duration_seconds: number;
  jobs_per_hour: number;
  last_hour: {
    completed: number;
    failed: number;
  };
}

/**
 * Cron Job Types
 */
export interface CronJob {
  name: string;
  task: string;
  schedule: string; // cron expression
  enabled: boolean;
  last_run?: string;
  next_run: string;
  run_count: number;
  last_status?: 'success' | 'failed';
  description?: string;
}

export interface CronJobsListResponse {
  cron_jobs: CronJob[];
  total: number;
}

/**
 * Feed Schedule Types
 */
export interface FeedSchedule {
  feed_id: number;
  feed_name: string;
  url: string;
  interval_minutes: number;
  next_run: string;
  last_run?: string;
  last_status?: 'success' | 'failed';
  enabled: boolean;
  priority: 'low' | 'normal' | 'high';
}

/**
 * API Request/Response helpers
 */
export interface CancelJobResponse {
  success: boolean;
  job_id: string;
  message: string;
}

export interface RetryJobResponse {
  success: boolean;
  job_id: string;
  new_job_id?: string;
  message: string;
}
