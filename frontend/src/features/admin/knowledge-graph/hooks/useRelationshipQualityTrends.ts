/**
 * useRelationshipQualityTrends Hook
 *
 * Fetches relationship quality distribution trends over time from the knowledge graph service.
 * Tracks high/medium/low confidence ratios to monitor quality improvements.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useRelationshipQualityTrends(30, {
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getRelationshipQualityTrends } from '@/lib/api/knowledgeGraphAdmin'
import type { RelationshipQualityTrendDataPoint } from '@/types/knowledgeGraph'

export interface UseRelationshipQualityTrendsOptions {
  refetchInterval?: number
  enabled?: boolean
}

export function useRelationshipQualityTrends(
  days: number = 30,
  options?: UseRelationshipQualityTrendsOptions
) {
  return useQuery<RelationshipQualityTrendDataPoint[]>({
    queryKey: ['knowledge-graph', 'relationship-quality-trends', days],
    queryFn: () => getRelationshipQualityTrends(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled ?? true,
  })
}
