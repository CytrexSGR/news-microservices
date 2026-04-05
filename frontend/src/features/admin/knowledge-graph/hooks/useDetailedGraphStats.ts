/**
 * useDetailedGraphStats Hook
 *
 * Fetches comprehensive graph statistics including quality metrics,
 * relationship breakdown, and data completeness from the knowledge graph.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useDetailedGraphStats({
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getDetailedGraphStats } from '@/lib/api/knowledgeGraphAdmin'
import type { DetailedGraphStats } from '@/types/knowledgeGraph'

export interface UseDetailedGraphStatsOptions {
  refetchInterval?: number
  enabled?: boolean
}

export function useDetailedGraphStats(options?: UseDetailedGraphStatsOptions) {
  return useQuery<DetailedGraphStats>({
    queryKey: ['knowledge-graph', 'detailed-stats'],
    queryFn: () => getDetailedGraphStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled ?? true,
  })
}
