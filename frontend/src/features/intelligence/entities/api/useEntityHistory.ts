/**
 * useEntityHistory Hook
 *
 * Query hook for fetching entity merge/deduplication history.
 */
import { useQuery } from '@tanstack/react-query';
import { getEntityHistory } from './entitiesApi';
import type { MergeEvent } from '../types/entities.types';

interface UseEntityHistoryOptions {
  limit?: number;
  enabled?: boolean;
  refetchInterval?: number;
}

export function useEntityHistory(options?: UseEntityHistoryOptions) {
  const { limit = 20, enabled = true, refetchInterval = 60000 } = options || {};

  return useQuery<MergeEvent[]>({
    queryKey: ['entities', 'history', limit],
    queryFn: () => getEntityHistory(limit),
    enabled,
    refetchInterval,
    staleTime: 30000, // 30 seconds
  });
}
