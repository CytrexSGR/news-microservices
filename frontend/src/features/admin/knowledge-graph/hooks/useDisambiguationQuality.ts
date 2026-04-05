/**
 * useDisambiguationQuality Hook
 *
 * Fetches entity disambiguation quality metrics from the knowledge graph.
 * Measures how accurately the system distinguishes between entities with similar names.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useDisambiguationQuality({
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getDisambiguationQuality } from '@/lib/api/knowledgeGraphAdmin'
import type { DisambiguationQualityResponse } from '@/types/knowledgeGraph'

export interface UseDisambiguationQualityOptions {
  refetchInterval?: number
  enabled?: boolean
}

export function useDisambiguationQuality(options?: UseDisambiguationQualityOptions) {
  return useQuery<DisambiguationQualityResponse>({
    queryKey: ['knowledge-graph', 'disambiguation-quality'],
    queryFn: () => getDisambiguationQuality(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled ?? true,
  })
}
