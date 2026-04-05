import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { RetryJobResponse } from '../types/scheduler.types';

/**
 * Retry a failed job using MCP tool
 */
async function retryJob(jobId: string): Promise<RetryJobResponse> {
  return mcpClient.callTool<RetryJobResponse>('jobs_retry', { job_id: jobId });
}

/**
 * Hook to retry a failed job
 *
 * @param options - React Query mutation options
 * @returns Mutation result
 *
 * @example
 * ```tsx
 * const retryJob = useRetryJob();
 *
 * const handleRetry = async (jobId: string) => {
 *   try {
 *     const result = await retryJob.mutateAsync(jobId);
 *     toast.success(`Job retried. New ID: ${result.new_job_id}`);
 *   } catch (error) {
 *     toast.error('Failed to retry job');
 *   }
 * };
 * ```
 */
export function useRetryJob(
  options?: Omit<UseMutationOptions<RetryJobResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryJob,
    onSuccess: () => {
      // Invalidate jobs list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs'] });
      // Invalidate stats as well
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs', 'stats'] });
    },
    ...options,
  });
}
