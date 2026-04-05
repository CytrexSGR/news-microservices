import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NarrativeCooccurrenceResponse,
  CooccurrenceFilters,
} from '../../types/narrative.types';

/**
 * Hook for fetching narrative co-occurrence data from Knowledge Graph
 *
 * Uses the MCP tool `get_narrative_cooccurrence` to retrieve pairs of entities
 * that frequently appear together in the same narrative frames.
 *
 * @param filters - Optional filters for entity, frame type, and minimum shared frames
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get all co-occurrences
 * const { data, isLoading } = useNarrativeCooccurrence();
 *
 * // Get co-occurrences for a specific entity
 * const { data } = useNarrativeCooccurrence({
 *   entity_name: 'Elon Musk',
 *   min_shared_frames: 3
 * });
 *
 * // Get co-occurrences in conflict narratives
 * const { data } = useNarrativeCooccurrence({
 *   frame_type: 'conflict',
 *   limit: 20
 * });
 * ```
 */
export function useNarrativeCooccurrence(
  filters?: CooccurrenceFilters,
  enabled: boolean = true
) {
  return useQuery<NarrativeCooccurrenceResponse, Error>({
    queryKey: ['narrative', 'kg', 'cooccurrence', filters],
    queryFn: async () => {
      const response = await mcpClient.callTool<NarrativeCooccurrenceResponse>(
        'kg_get_narrative_cooccurrence',
        {
          entity_name: filters?.entity_name,
          frame_type: filters?.frame_type,
          min_shared_frames: filters?.min_shared_frames ?? 2,
          limit: filters?.limit ?? 50,
        }
      );

      return response;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 20 * 60 * 1000, // 20 minutes cache
  });
}

/**
 * Hook for fetching co-occurrences for a specific entity
 */
export function useEntityCooccurrences(
  entityName: string,
  options?: { minSharedFrames?: number; limit?: number },
  enabled: boolean = true
) {
  return useNarrativeCooccurrence(
    {
      entity_name: entityName,
      min_shared_frames: options?.minSharedFrames ?? 2,
      limit: options?.limit ?? 20,
    },
    enabled && !!entityName
  );
}

/**
 * Hook for fetching high-affinity entity pairs (frequently co-framed)
 */
export function useHighAffinityPairs(
  minSharedFrames: number = 5,
  limit: number = 10,
  enabled: boolean = true
) {
  return useNarrativeCooccurrence(
    {
      min_shared_frames: minSharedFrames,
      limit,
    },
    enabled
  );
}
