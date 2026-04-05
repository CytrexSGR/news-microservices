/**
 * useEntityMergeHistory Hook
 *
 * Fetches entity merge events from the canonicalization service.
 * Shows recent entity deduplication operations with merge method and confidence.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useEntityMergeHistory(20, {
 *   refetchInterval: 60 * 1000 // Auto-refresh every minute
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getEntityMergeHistory } from '@/lib/api/knowledgeGraphAdmin'
import type { MergeEvent } from '@/types/knowledgeGraph'

export interface UseEntityMergeHistoryOptions {
  refetchInterval?: number
  enabled?: boolean
}

export function useEntityMergeHistory(
  limit: number = 20,
  options?: UseEntityMergeHistoryOptions
) {
  return useQuery<MergeEvent[]>({
    queryKey: ['entity-canonicalization', 'merge-history', limit],
    queryFn: () => getEntityMergeHistory(limit),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled ?? true,
  })
}
