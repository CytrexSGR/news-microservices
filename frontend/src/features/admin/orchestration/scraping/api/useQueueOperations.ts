import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EnqueueJobParams, QueueJob, QueuePriority } from '../types/scraping.types';
import { queueStatsQueryKey, pendingJobsQueryKey } from './useQueueStats';

/**
 * Enqueue response
 */
interface EnqueueResponse {
  job_id: string;
  position: number;
  estimated_wait_seconds: number;
}

/**
 * Clear queue response
 */
interface ClearQueueResponse {
  success: boolean;
  jobs_cleared: number;
  message: string;
}

/**
 * Retry job response
 */
interface RetryJobResponse {
  success: boolean;
  new_job_id: string;
  message: string;
}

/**
 * Cancel job response
 */
interface CancelJobResponse {
  success: boolean;
  job_id: string;
  message: string;
}

/**
 * Enqueue a URL for scraping
 */
async function enqueueJob(params: EnqueueJobParams): Promise<EnqueueResponse> {
  return mcpClient.callTool<EnqueueResponse>('scraping_enqueue_url', params);
}

/**
 * Clear queue by priority or all
 */
async function clearQueue(priority?: QueuePriority): Promise<ClearQueueResponse> {
  return mcpClient.callTool<ClearQueueResponse>('scraping_clear_queue', priority ? { priority } : {});
}

/**
 * Retry a failed job
 */
async function retryJob(jobId: string): Promise<RetryJobResponse> {
  return mcpClient.callTool<RetryJobResponse>('scraping_retry_job', { job_id: jobId });
}

/**
 * Cancel a pending job
 */
async function cancelJob(jobId: string): Promise<CancelJobResponse> {
  return mcpClient.callTool<CancelJobResponse>('scraping_cancel_job', { job_id: jobId });
}

/**
 * Bulk enqueue multiple URLs
 */
async function bulkEnqueue(urls: string[], priority?: QueuePriority): Promise<{ enqueued: number; job_ids: string[] }> {
  return mcpClient.callTool<{ enqueued: number; job_ids: string[] }>('scraping_bulk_enqueue', { urls, priority });
}

/**
 * Hook to enqueue a URL for scraping
 *
 * @example
 * ```tsx
 * const enqueue = useEnqueueJob();
 *
 * const handleSubmit = async (url: string) => {
 *   const result = await enqueue.mutateAsync({ url, priority: 'HIGH' });
 *   toast.success(`Job enqueued at position ${result.position}`);
 * };
 * ```
 */
export function useEnqueueJob(
  options?: Omit<UseMutationOptions<EnqueueResponse, Error, EnqueueJobParams>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enqueueJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: pendingJobsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to clear the queue
 */
export function useClearQueue(
  options?: Omit<UseMutationOptions<ClearQueueResponse, Error, QueuePriority | undefined>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearQueue,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: pendingJobsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to retry a failed job
 */
export function useRetryQueueJob(
  options?: Omit<UseMutationOptions<RetryJobResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: pendingJobsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to cancel a pending job
 */
export function useCancelQueueJob(
  options?: Omit<UseMutationOptions<CancelJobResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: pendingJobsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to bulk enqueue multiple URLs
 */
export function useBulkEnqueue(
  options?: Omit<UseMutationOptions<{ enqueued: number; job_ids: string[] }, Error, { urls: string[]; priority?: QueuePriority }>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ urls, priority }) => bulkEnqueue(urls, priority),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: pendingJobsQueryKey });
    },
    ...options,
  });
}
