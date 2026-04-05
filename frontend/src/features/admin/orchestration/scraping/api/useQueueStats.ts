import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { QueueStats, QueueJob, PendingJobsResponse, QueueJobStatusResponse } from '../types/scraping.types';

/**
 * Query keys for queue
 */
export const queueStatsQueryKey = ['scraping', 'queue', 'stats'] as const;
export const pendingJobsQueryKey = ['scraping', 'queue', 'pending'] as const;
export const queueJobQueryKey = (jobId: string) => ['scraping', 'queue', 'job', jobId] as const;

/**
 * Fetch queue statistics
 */
async function fetchQueueStats(): Promise<QueueStats> {
  return mcpClient.callTool<QueueStats>('scraping_get_queue_stats');
}

/**
 * Fetch pending jobs
 */
async function fetchPendingJobs(params?: { limit?: number }): Promise<PendingJobsResponse> {
  return mcpClient.callTool<PendingJobsResponse>('scraping_get_pending_jobs', params || {});
}

/**
 * Fetch single queue job status
 */
async function fetchQueueJobStatus(jobId: string): Promise<QueueJobStatusResponse> {
  return mcpClient.callTool<QueueJobStatusResponse>('scraping_get_job_status', { job_id: jobId });
}

/**
 * Hook to fetch queue statistics
 *
 * @param options - React Query options
 * @returns Query result with queue stats
 *
 * @example
 * ```tsx
 * const { data } = useQueueStats();
 * console.log(`${data?.pending_jobs} jobs pending`);
 * ```
 */
export function useQueueStats(
  options?: Omit<UseQueryOptions<QueueStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queueStatsQueryKey,
    queryFn: fetchQueueStats,
    staleTime: 5000,
    refetchInterval: 15000,
    ...options,
  });
}

/**
 * Hook to fetch pending jobs
 */
export function usePendingJobs(
  params?: { limit?: number },
  options?: Omit<UseQueryOptions<PendingJobsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...pendingJobsQueryKey, params],
    queryFn: () => fetchPendingJobs(params),
    staleTime: 5000,
    refetchInterval: 10000,
    ...options,
  });
}

/**
 * Hook to fetch a single queue job status
 */
export function useQueueJobStatus(
  jobId: string,
  options?: Omit<UseQueryOptions<QueueJobStatusResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queueJobQueryKey(jobId),
    queryFn: () => fetchQueueJobStatus(jobId),
    enabled: !!jobId,
    staleTime: 2000,
    refetchInterval: 5000,
    ...options,
  });
}
