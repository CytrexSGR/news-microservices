/**
 * useNotApplicableTrends Hook
 *
 * Fetches NOT_APPLICABLE relationship trends over time from the knowledge graph service.
 * Tracks data quality improvements by monitoring NOT_APPLICABLE ratio changes.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useNotApplicableTrends(30, {
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getNotApplicableTrends } from '@/lib/api/knowledgeGraphAdmin'
import type { NotApplicableTrendDataPoint } from '@/types/knowledgeGraph'

export interface UseNotApplicableTrendsOptions {
  refetchInterval?: number
  enabled?: boolean
}

export function useNotApplicableTrends(
  days: number = 30,
  options?: UseNotApplicableTrendsOptions
) {
  return useQuery<NotApplicableTrendDataPoint[]>({
    queryKey: ['knowledge-graph', 'not-applicable-trends', days],
    queryFn: () => getNotApplicableTrends(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled ?? true,
  })
}
