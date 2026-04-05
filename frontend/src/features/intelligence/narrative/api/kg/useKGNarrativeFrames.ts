import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  KGNarrativeFramesResponse,
  KGNarrativeFilters,
} from '../../types/narrative.types';

/**
 * Hook for fetching entity-specific narrative frames from Knowledge Graph
 *
 * Uses the MCP tool `get_narrative_frames` via the Knowledge Graph server
 * to retrieve narrative frames associated with specific entities in Neo4j.
 *
 * @param filters - Optional filters including entity name, frame type, confidence threshold
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get all frames for a specific entity
 * const { data, isLoading } = useKGNarrativeFrames({
 *   entity_name: 'Donald Trump',
 *   min_confidence: 0.7
 * });
 *
 * // Get frames of a specific type
 * const { data } = useKGNarrativeFrames({
 *   frame_type: 'conflict',
 *   limit: 50
 * });
 * ```
 */
export function useKGNarrativeFrames(
  filters?: KGNarrativeFilters,
  enabled: boolean = true
) {
  return useQuery<KGNarrativeFramesResponse, Error>({
    queryKey: ['narrative', 'kg', 'frames', filters],
    queryFn: async () => {
      const response = await mcpClient.callTool<KGNarrativeFramesResponse>(
        'kg_get_narrative_frames',
        {
          entity_name: filters?.entity_name,
          entity_id: filters?.entity_id,
          frame_type: filters?.frame_type,
          min_confidence: filters?.min_confidence ?? 0.5,
          start_date: filters?.start_date,
          end_date: filters?.end_date,
          limit: filters?.limit ?? 100,
          page: filters?.page ?? 1,
        }
      );

      return response;
    },
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes cache
  });
}

/**
 * Hook for fetching frames for a specific entity by ID
 */
export function useEntityNarrativeFrames(
  entityId: string,
  options?: { limit?: number; frameType?: string },
  enabled: boolean = true
) {
  return useKGNarrativeFrames(
    {
      entity_id: entityId,
      frame_type: options?.frameType as any,
      limit: options?.limit ?? 50,
    },
    enabled && !!entityId
  );
}
