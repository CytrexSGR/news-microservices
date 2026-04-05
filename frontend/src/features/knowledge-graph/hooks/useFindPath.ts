/**
 * useFindPath Hook
 *
 * Finds shortest paths between two entities in the knowledge graph.
 * Uses Neo4j's allShortestPaths algorithm.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useFindPath('Elon Musk', 'Tesla', {
 *   maxDepth: 3,
 *   limit: 5,
 *   minConfidence: 0.7
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { findPath } from '@/lib/api/knowledgeGraphPublic'
import type { PathfindingResponse } from '@/types/knowledgeGraphPublic'

export interface UseFindPathOptions {
  maxDepth?: number
  limit?: number
  minConfidence?: number
  enabled?: boolean
}

export function useFindPath(
  entity1: string | null,
  entity2: string | null,
  options?: UseFindPathOptions
) {
  return useQuery<PathfindingResponse>({
    queryKey: [
      'knowledge-graph',
      'pathfinding',
      entity1,
      entity2,
      options?.maxDepth,
      options?.limit,
      options?.minConfidence,
    ],
    queryFn: () =>
      findPath(
        entity1!,
        entity2!,
        options?.maxDepth ?? 3,
        options?.limit ?? 3,
        options?.minConfidence ?? 0.5
      ),
    enabled: !!entity1 && !!entity2 && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000, // 10 minutes - pathfinding is expensive
    gcTime: 30 * 60 * 1000, // 30 minutes
  })
}
