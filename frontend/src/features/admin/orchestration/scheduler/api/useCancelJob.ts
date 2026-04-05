import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { CancelJobResponse } from '../types/scheduler.types';

/**
 * Cancel a job using MCP tool
 */
async function cancelJob(jobId: string): Promise<CancelJobResponse> {
  return mcpClient.callTool<CancelJobResponse>('jobs_cancel', { job_id: jobId });
}

/**
 * Hook to cancel a running or pending job
 *
 * @param options - React Query mutation options
 * @returns Mutation result
 *
 * @example
 * ```tsx
 * const cancelJob = useCancelJob();
 *
 * const handleCancel = async (jobId: string) => {
 *   try {
 *     await cancelJob.mutateAsync(jobId);
 *     toast.success('Job cancelled');
 *   } catch (error) {
 *     toast.error('Failed to cancel job');
 *   }
 * };
 * ```
 */
export function useCancelJob(
  options?: Omit<UseMutationOptions<CancelJobResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelJob,
    onSuccess: () => {
      // Invalidate jobs list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs'] });
      // Invalidate stats as well
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs', 'stats'] });
    },
    ...options,
  });
}
