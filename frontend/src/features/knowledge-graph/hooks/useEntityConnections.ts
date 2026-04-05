/**
 * useEntityConnections Hook
 *
 * Fetches entity connections from the knowledge graph.
 * Returns nodes and edges for React Flow visualization.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useEntityConnections('Tesla', {
 *   relationshipType: 'WORKS_FOR',
 *   limit: 50
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getEntityConnections } from '@/lib/api/knowledgeGraphPublic'
import type { GraphResponse } from '@/types/knowledgeGraphPublic'

export interface UseEntityConnectionsOptions {
  relationshipType?: string
  limit?: number
  enabled?: boolean
}

export function useEntityConnections(
  entityName: string | null,
  options?: UseEntityConnectionsOptions
) {
  return useQuery<GraphResponse>({
    queryKey: [
      'knowledge-graph',
      'entity-connections',
      entityName,
      options?.relationshipType,
      options?.limit,
    ],
    queryFn: () =>
      getEntityConnections(
        entityName!,
        options?.relationshipType,
        options?.limit ?? 100
      ),
    enabled: !!entityName && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
  })
}
