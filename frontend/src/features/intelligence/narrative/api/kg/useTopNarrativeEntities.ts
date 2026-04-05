import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  TopNarrativeEntitiesResponse,
  NarrativeType,
} from '../../types/narrative.types';

/**
 * Parameters for top narrative entities query
 */
export interface TopNarrativeEntitiesParams {
  frame_type?: NarrativeType;
  entity_type?: string;
  min_mentions?: number;
  limit?: number;
  sort_by?: 'frame_mentions' | 'avg_tension' | 'article_count';
}

/**
 * Hook for fetching top entities by narrative frame mentions
 *
 * Uses the MCP tool `get_top_narrative_entities` to retrieve entities
 * ranked by their narrative frame involvement.
 *
 * @param params - Optional filters and sorting options
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get top 20 entities by frame mentions
 * const { data, isLoading } = useTopNarrativeEntities();
 *
 * // Get top entities in conflict narratives
 * const { data } = useTopNarrativeEntities({
 *   frame_type: 'conflict',
 *   limit: 10
 * });
 *
 * // Get entities sorted by tension score
 * const { data } = useTopNarrativeEntities({
 *   sort_by: 'avg_tension',
 *   min_mentions: 5
 * });
 * ```
 */
export function useTopNarrativeEntities(
  params?: TopNarrativeEntitiesParams,
  enabled: boolean = true
) {
  return useQuery<TopNarrativeEntitiesResponse, Error>({
    queryKey: ['narrative', 'kg', 'top-entities', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<TopNarrativeEntitiesResponse>(
        'kg_get_top_narrative_entities',
        {
          frame_type: params?.frame_type,
          entity_type: params?.entity_type,
          min_mentions: params?.min_mentions ?? 1,
          limit: params?.limit ?? 20,
          sort_by: params?.sort_by ?? 'frame_mentions',
        }
      );

      return response;
    },
    enabled,
    staleTime: 3 * 60 * 1000, // 3 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes cache
  });
}

/**
 * Hook for fetching top entities by frame type
 */
export function useTopEntitiesByFrame(
  frameType: NarrativeType,
  limit: number = 10,
  enabled: boolean = true
) {
  return useTopNarrativeEntities(
    {
      frame_type: frameType,
      limit,
      sort_by: 'frame_mentions',
    },
    enabled
  );
}

/**
 * Hook for fetching most controversial entities (highest tension)
 */
export function useMostControversialEntities(
  limit: number = 10,
  enabled: boolean = true
) {
  return useTopNarrativeEntities(
    {
      min_mentions: 3,
      limit,
      sort_by: 'avg_tension',
    },
    enabled
  );
}

/**
 * Hook for fetching top entities by entity type
 */
export function useTopEntitiesByType(
  entityType: 'person' | 'organization' | 'location',
  limit: number = 15,
  enabled: boolean = true
) {
  return useTopNarrativeEntities(
    {
      entity_type: entityType,
      limit,
      sort_by: 'frame_mentions',
    },
    enabled
  );
}
