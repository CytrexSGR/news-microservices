import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { KGFrameDistributionResponse } from '../../types/narrative.types';

/**
 * Parameters for frame distribution query
 */
export interface FrameDistributionParams {
  start_date?: string;
  end_date?: string;
  entity_type?: string;
  include_entity_counts?: boolean;
}

/**
 * Hook for fetching frame type distribution from Knowledge Graph
 *
 * Uses the MCP tool `get_frame_distribution` to retrieve the distribution
 * of narrative frame types across all analyzed content in Neo4j.
 *
 * @param params - Optional date range and entity type filters
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get overall distribution
 * const { data, isLoading } = useFrameDistribution();
 *
 * // Get distribution for a specific time range
 * const { data } = useFrameDistribution({
 *   start_date: '2024-01-01',
 *   end_date: '2024-01-31',
 *   include_entity_counts: true
 * });
 * ```
 */
export function useFrameDistribution(
  params?: FrameDistributionParams,
  enabled: boolean = true
) {
  return useQuery<KGFrameDistributionResponse, Error>({
    queryKey: ['narrative', 'kg', 'distribution', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<KGFrameDistributionResponse>(
        'kg_get_frame_distribution',
        {
          start_date: params?.start_date,
          end_date: params?.end_date,
          entity_type: params?.entity_type,
          include_entity_counts: params?.include_entity_counts ?? true,
        }
      );

      return response;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes cache
  });
}

/**
 * Hook for fetching frame distribution for last N days
 */
export function useRecentFrameDistribution(
  days: number = 7,
  enabled: boolean = true
) {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

  return useFrameDistribution(
    {
      start_date: startDate,
      end_date: endDate,
      include_entity_counts: true,
    },
    enabled
  );
}
