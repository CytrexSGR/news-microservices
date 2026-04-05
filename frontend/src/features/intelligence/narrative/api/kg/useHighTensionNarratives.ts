import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  HighTensionNarrativesResponse,
  TensionFilters,
} from '../../types/narrative.types';

/**
 * Hook for fetching high tension narratives from Knowledge Graph
 *
 * Uses the MCP tool `get_high_tension_narratives` to retrieve emotionally
 * charged content with high tension scores from Neo4j.
 *
 * @param filters - Optional filters for tension threshold, frame type, entity
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get all high tension narratives
 * const { data, isLoading } = useHighTensionNarratives();
 *
 * // Get critical tension narratives only
 * const { data } = useHighTensionNarratives({
 *   min_tension: 0.8,
 *   limit: 20
 * });
 *
 * // Get conflict narratives with high tension
 * const { data } = useHighTensionNarratives({
 *   frame_type: 'conflict',
 *   min_tension: 0.6
 * });
 * ```
 */
export function useHighTensionNarratives(
  filters?: TensionFilters,
  enabled: boolean = true
) {
  return useQuery<HighTensionNarrativesResponse, Error>({
    queryKey: ['narrative', 'kg', 'high-tension', filters],
    queryFn: async () => {
      const response = await mcpClient.callTool<HighTensionNarrativesResponse>(
        'kg_get_high_tension_narratives',
        {
          min_tension: filters?.min_tension ?? 0.6,
          max_tension: filters?.max_tension,
          frame_type: filters?.frame_type,
          entity_name: filters?.entity_name,
          limit: filters?.limit ?? 25,
        }
      );

      return response;
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute - tension data changes frequently
    gcTime: 5 * 60 * 1000, // 5 minutes cache
    refetchInterval: 2 * 60 * 1000, // Auto-refetch every 2 minutes
  });
}

/**
 * Hook for fetching critical tension narratives (score >= 0.8)
 */
export function useCriticalTensionNarratives(
  limit: number = 10,
  enabled: boolean = true
) {
  return useHighTensionNarratives(
    {
      min_tension: 0.8,
      limit,
    },
    enabled
  );
}

/**
 * Hook for fetching tension narratives for a specific entity
 */
export function useEntityTensionNarratives(
  entityName: string,
  minTension: number = 0.5,
  enabled: boolean = true
) {
  return useHighTensionNarratives(
    {
      entity_name: entityName,
      min_tension: minTension,
      limit: 20,
    },
    enabled && !!entityName
  );
}

/**
 * Hook for tension alert monitoring
 * Auto-refreshes frequently to catch new high-tension content
 */
export function useTensionAlerts(
  tensionThreshold: number = 0.7,
  enabled: boolean = true
) {
  return useQuery<HighTensionNarrativesResponse, Error>({
    queryKey: ['narrative', 'kg', 'tension-alerts', tensionThreshold],
    queryFn: async () => {
      const response = await mcpClient.callTool<HighTensionNarrativesResponse>(
        'kg_get_high_tension_narratives',
        {
          min_tension: tensionThreshold,
          limit: 15,
        }
      );

      return response;
    },
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}
