import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EntityFramingAnalysisResponse } from '../../types/narrative.types';

/**
 * Parameters for entity framing analysis
 */
export interface EntityFramingParams {
  entity_name?: string;
  entity_id?: string;
  include_related?: boolean;
  related_limit?: number;
}

/**
 * Hook for fetching comprehensive entity framing analysis from Knowledge Graph
 *
 * Uses the MCP tool `get_entity_framing_analysis` to retrieve detailed
 * framing analysis for a specific entity, including frame distribution,
 * bias scores, and related entities.
 *
 * @param params - Entity identification (name or ID) and related entity options
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get framing analysis for an entity by name
 * const { data, isLoading } = useEntityFramingAnalysis({
 *   entity_name: 'Apple Inc.',
 *   include_related: true,
 *   related_limit: 10
 * });
 *
 * // Access the analysis
 * if (data) {
 *   console.log('Frame distribution:', data.analysis.frame_distribution);
 *   console.log('Average confidence:', data.analysis.avg_confidence);
 *   console.log('Related entities:', data.related_entities);
 * }
 * ```
 */
export function useEntityFramingAnalysis(
  params: EntityFramingParams,
  enabled: boolean = true
) {
  const hasIdentifier = !!(params.entity_name || params.entity_id);

  return useQuery<EntityFramingAnalysisResponse, Error>({
    queryKey: ['narrative', 'kg', 'entity-framing', params],
    queryFn: async () => {
      if (!hasIdentifier) {
        throw new Error('Either entity_name or entity_id is required');
      }

      const response = await mcpClient.callTool<EntityFramingAnalysisResponse>(
        'kg_get_entity_framing_analysis',
        {
          entity_name: params.entity_name,
          entity_id: params.entity_id,
          include_related: params.include_related ?? true,
          related_limit: params.related_limit ?? 5,
        }
      );

      return response;
    },
    enabled: enabled && hasIdentifier,
    staleTime: 3 * 60 * 1000, // 3 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes cache
  });
}

/**
 * Hook for fetching entity framing by name (convenience wrapper)
 */
export function useEntityFramingByName(
  entityName: string,
  includeRelated: boolean = true,
  enabled: boolean = true
) {
  return useEntityFramingAnalysis(
    {
      entity_name: entityName,
      include_related: includeRelated,
      related_limit: 10,
    },
    enabled && !!entityName
  );
}
