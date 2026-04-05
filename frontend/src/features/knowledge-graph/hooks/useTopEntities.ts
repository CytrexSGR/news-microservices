/**
 * useTopEntities Hook
 *
 * Fetches trending/top entities from the knowledge graph.
 * Uses admin API endpoint for analytics data.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useTopEntities({
 *   limit: 10,
 *   entityType: 'PERSON',
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getTopEntities } from '@/lib/api/knowledgeGraphAdmin'
import type { TopEntity } from '@/types/knowledgeGraph'

export interface UseTopEntitiesOptions {
  limit?: number
  entityType?: string
  refetchInterval?: number
  enabled?: boolean
}

export function useTopEntities(options?: UseTopEntitiesOptions) {
  return useQuery<TopEntity[]>({
    queryKey: [
      'knowledge-graph',
      'top-entities',
      options?.limit,
      options?.entityType,
    ],
    queryFn: () =>
      getTopEntities(options?.limit ?? 10, options?.entityType),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: options?.refetchInterval, // Optional auto-refresh
    enabled: options?.enabled ?? true,
  })
}
