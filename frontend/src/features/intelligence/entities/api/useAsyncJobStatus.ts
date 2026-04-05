/**
 * useAsyncJobStatus Hook
 *
 * Query hook for polling async batch job status.
 * Automatically polls until job completes or fails.
 */
import { useQuery } from '@tanstack/react-query';
import { getAsyncJobStatus } from './entitiesApi';
import type { AsyncJob } from '../types/entities.types';

interface UseAsyncJobStatusOptions {
  enabled?: boolean;
  pollingInterval?: number;
  onCompleted?: (job: AsyncJob) => void;
  onFailed?: (job: AsyncJob) => void;
}

export function useAsyncJobStatus(jobId: string | null, options?: UseAsyncJobStatusOptions) {
  const {
    enabled = true,
    pollingInterval = 2000, // 2 seconds
    onCompleted,
    onFailed,
  } = options || {};

  const query = useQuery<AsyncJob>({
    queryKey: ['entities', 'jobs', jobId, 'status'],
    queryFn: () => getAsyncJobStatus(jobId!),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      // Stop polling when job is completed or failed
      if (job?.status === 'completed' || job?.status === 'failed') {
        return false;
      }
      return pollingInterval;
    },
    staleTime: 0, // Always refetch for status updates
  });

  // Call callbacks based on status
  if (query.data?.status === 'completed' && onCompleted) {
    onCompleted(query.data);
  }
  if (query.data?.status === 'failed' && onFailed) {
    onFailed(query.data);
  }

  return {
    ...query,
    isProcessing: query.data?.status === 'processing' || query.data?.status === 'queued',
    isCompleted: query.data?.status === 'completed',
    isFailed: query.data?.status === 'failed',
    progress: query.data?.progress_percent ?? 0,
  };
}
