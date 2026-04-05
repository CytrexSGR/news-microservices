/**
 * useAsyncJobResult Hook
 *
 * Query hook for fetching completed async batch job results.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAsyncJobResult } from './entitiesApi';
import type { AsyncJobResult } from '../types/entities.types';

interface UseAsyncJobResultOptions {
  enabled?: boolean;
  onSuccess?: (data: AsyncJobResult) => void;
  onError?: (error: Error) => void;
}

export function useAsyncJobResult(jobId: string | null, options?: UseAsyncJobResultOptions) {
  const { enabled = true, onSuccess, onError } = options || {};
  const queryClient = useQueryClient();

  return useQuery<AsyncJobResult, Error>({
    queryKey: ['entities', 'jobs', jobId, 'result'],
    queryFn: async () => {
      const result = await getAsyncJobResult(jobId!);

      // Invalidate stats after successful result fetch
      queryClient.invalidateQueries({ queryKey: ['entities', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['entities', 'clusters'] });

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    },
    enabled: enabled && !!jobId,
    staleTime: Infinity, // Results don't change
    retry: false, // Don't retry - job might not be completed
  });
}
