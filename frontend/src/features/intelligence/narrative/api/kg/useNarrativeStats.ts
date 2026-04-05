import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { NarrativeStatsResponse } from '../../types/narrative.types';

/**
 * Parameters for narrative statistics query
 */
export interface NarrativeStatsParams {
  start_date?: string;
  end_date?: string;
  include_trends?: boolean;
}

/**
 * Hook for fetching overall narrative statistics from Knowledge Graph
 *
 * Uses the MCP tool `get_narrative_stats` to retrieve aggregated
 * statistics about all narrative frames in the Knowledge Graph.
 *
 * @param params - Optional date range and trend options
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get overall stats
 * const { data, isLoading } = useNarrativeStats();
 *
 * // Get stats for a specific period
 * const { data } = useNarrativeStats({
 *   start_date: '2024-01-01',
 *   end_date: '2024-01-31',
 *   include_trends: true
 * });
 *
 * // Access the stats
 * if (data) {
 *   console.log('Total frames:', data.stats.total_frames);
 *   console.log('Avg tension:', data.stats.avg_tension_score);
 *   console.log('Frame distribution:', data.stats.frame_distribution);
 * }
 * ```
 */
export function useNarrativeStats(
  params?: NarrativeStatsParams,
  enabled: boolean = true
) {
  return useQuery<NarrativeStatsResponse, Error>({
    queryKey: ['narrative', 'kg', 'stats', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<NarrativeStatsResponse>(
        'kg_get_narrative_stats',
        {
          start_date: params?.start_date,
          end_date: params?.end_date,
          include_trends: params?.include_trends ?? false,
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
 * Hook for fetching stats for last N days
 */
export function useRecentNarrativeStats(
  days: number = 7,
  enabled: boolean = true
) {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

  return useNarrativeStats(
    {
      start_date: startDate,
      end_date: endDate,
      include_trends: true,
    },
    enabled
  );
}

/**
 * Hook for fetching today's narrative stats
 */
export function useTodayNarrativeStats(enabled: boolean = true) {
  const today = new Date().toISOString().split('T')[0];

  return useNarrativeStats(
    {
      start_date: today,
      end_date: today,
    },
    enabled
  );
}
