/**
 * Scheduler Service Types
 *
 * Based on scheduler-service/app/api/scheduler_api.py
 * Port: 8108
 */

// ============================================================================
// Enums and Literals
// ============================================================================

export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export type JobType =
  | 'CONTENT_ANALYSIS'
  | 'KNOWLEDGE_GRAPH'
  | 'ENTITY_EXTRACTION'
  | 'FEED_REFRESH'
  | 'DEDUPLICATION';

// ============================================================================
// Scheduler Status Types
// ============================================================================

export interface FeedMonitorStatus {
  is_running: boolean;
  check_interval_seconds: number;
}

export interface JobProcessorStatus {
  is_running: boolean;
  process_interval_seconds: number;
  max_concurrent_jobs: number;
}

export interface CronSchedulerStatus {
  is_running: boolean;
  total_jobs: number;
  running_jobs: number;
}

export interface QueueStatus {
  pending_jobs: number;
  processing_jobs: number;
}

export interface SchedulerStatus {
  feed_monitor: FeedMonitorStatus;
  job_processor: JobProcessorStatus;
  cron_scheduler: CronSchedulerStatus;
  queue: QueueStatus;
}

// ============================================================================
// Job Types
// ============================================================================

export interface AnalysisJob {
  id: string;
  article_id: string;
  job_type: string;
  status: JobStatus;
  priority: number;
  retry_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobListResponse {
  total: number;
  limit: number;
  offset: number;
  jobs: AnalysisJob[];
}

export interface JobStats {
  total_pending: number;
  total_processing: number;
  total_completed: number;
  total_failed: number;
  by_type: Record<string, number>;
}

// ============================================================================
// Cron Job Types
// ============================================================================

export interface CronJob {
  id: string;
  name: string;
  next_run_time: string | null;
  trigger: string;
  pending: boolean;
}

export interface CronJobListResponse {
  total: number;
  jobs: CronJob[];
}

// ============================================================================
// API Response Types
// ============================================================================

export interface JobActionResponse {
  status: string;
  message: string;
  job?: {
    id: string;
    status: string;
  };
}

export interface FeedCheckResponse {
  status: string;
  feed_id: string;
  message: string;
}

export interface DeduplicationResult {
  dry_run: boolean;
  entities_before: number;
  entities_after?: number;
  duplicates_found: number;
  merges_performed?: number;
  details?: Array<{
    canonical_name: string;
    duplicate_names: string[];
    entity_type: string;
  }>;
}

export interface DeduplicationResponse {
  status: string;
  dry_run: boolean;
  result: DeduplicationResult;
}

// ============================================================================
// Query Parameters
// ============================================================================

export interface JobsQuery {
  status?: JobStatus;
  limit?: number;
  offset?: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Convert cron expression to human-readable string
 */
export function cronToHumanReadable(trigger: string): string {
  // Extract the core schedule from trigger string like "cron[minute='0', hour='*/6', ...]"
  if (trigger.includes('interval')) {
    const match = trigger.match(/interval\[([^\]]+)\]/);
    if (match) {
      return `Every ${match[1].replace(/,\s*/g, ' ')}`;
    }
    return 'Interval';
  }

  if (trigger.includes('cron')) {
    const minuteMatch = trigger.match(/minute='([^']+)'/);
    const hourMatch = trigger.match(/hour='([^']+)'/);
    const dayMatch = trigger.match(/day='([^']+)'/);

    const minute = minuteMatch?.[1] || '*';
    const hour = hourMatch?.[1] || '*';
    const day = dayMatch?.[1] || '*';

    // Common patterns
    if (minute === '0' && hour === '*' && day === '*') {
      return 'Every hour at minute 0';
    }
    if (minute === '0' && hour === '0' && day === '*') {
      return 'Daily at midnight';
    }
    if (minute === '0' && hour === '*/6') {
      return 'Every 6 hours';
    }
    if (minute === '*/5') {
      return 'Every 5 minutes';
    }
    if (minute === '*/15') {
      return 'Every 15 minutes';
    }
    if (minute === '*/30') {
      return 'Every 30 minutes';
    }

    return `Cron: ${minute} ${hour} ${day}`;
  }

  if (trigger.includes('date')) {
    return 'One-time scheduled';
  }

  return trigger;
}

/**
 * Get status badge color
 */
export function getJobStatusColor(status: JobStatus): string {
  switch (status) {
    case 'PENDING':
      return 'bg-yellow-500/10 text-yellow-500';
    case 'PROCESSING':
      return 'bg-blue-500/10 text-blue-500';
    case 'COMPLETED':
      return 'bg-green-500/10 text-green-500';
    case 'FAILED':
      return 'bg-red-500/10 text-red-500';
    default:
      return 'bg-gray-500/10 text-gray-500';
  }
}

/**
 * Format duration between two dates
 */
export function formatDuration(
  startedAt: string | null,
  completedAt: string | null
): string {
  if (!startedAt || !completedAt) {
    return '-';
  }

  const start = new Date(startedAt);
  const end = new Date(completedAt);
  const durationMs = end.getTime() - start.getTime();

  if (durationMs < 1000) {
    return `${durationMs}ms`;
  }
  if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(1)}s`;
  }
  if (durationMs < 3600000) {
    return `${(durationMs / 60000).toFixed(1)}m`;
  }
  return `${(durationMs / 3600000).toFixed(1)}h`;
}
