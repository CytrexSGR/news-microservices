import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  BiasAnalysisResponse,
  BiasFilters,
  BiasResult,
  BiasDirection,
} from '../types/narrative.types';

/**
 * Parameters for fetching bias analysis data
 */
export interface BiasAnalysisParams extends BiasFilters {
  page?: number;
  per_page?: number;
  start_date?: string;
  end_date?: string;
  /** @deprecated Use start_date instead */
  date_from?: string;
  /** @deprecated Use end_date instead */
  date_to?: string;
  sort_by?: 'date' | 'score' | 'confidence';
  sort_order?: 'asc' | 'desc';
  include_indicators?: boolean;
  bias_direction?: BiasDirection;
}

/**
 * Hook for fetching bias analysis data
 *
 * Uses the MCP tool `get_bias_analysis` to retrieve historical
 * bias analysis results with filtering capabilities.
 *
 * @param params - Query parameters including filters and pagination
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get all bias analyses
 * const { data, isLoading } = useBiasAnalysis();
 *
 * // With date range parameters
 * const { data } = useBiasAnalysis({
 *   bias_type: 'political',
 *   start_date: '2024-01-01',
 *   end_date: '2024-01-31',
 *   min_score: -0.5,
 *   max_score: 0.5,
 *   include_indicators: true
 * });
 * ```
 */
export function useBiasAnalysis(
  params?: BiasAnalysisParams,
  enabled: boolean = true
) {
  return useQuery<BiasAnalysisResponse, Error>({
    queryKey: ['narrative', 'bias', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<BiasAnalysisResponse>(
        'get_bias_analysis',
        {
          page: params?.page ?? 1,
          per_page: params?.per_page ?? 20,
          bias_type: params?.bias_type,
          min_score: params?.min_score,
          max_score: params?.max_score,
          source: params?.source,
          // Support both old and new date parameter names
          start_date: params?.start_date ?? params?.date_from,
          end_date: params?.end_date ?? params?.date_to,
          sort_by: params?.sort_by ?? 'date',
          sort_order: params?.sort_order ?? 'desc',
          include_indicators: params?.include_indicators ?? false,
          bias_direction: params?.bias_direction,
        }
      );

      return response;
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

/**
 * Hook for fetching aggregated bias statistics
 */
export function useBiasStats(days: number = 7, enabled: boolean = true) {
  return useQuery<{
    avg_bias: number;
    distribution: Record<string, number>;
    trend: Array<{ date: string; avg_bias: number; count: number }>;
  }, Error>({
    queryKey: ['narrative', 'bias', 'stats', days],
    queryFn: async () => {
      const response = await mcpClient.callTool<{
        avg_bias: number;
        distribution: Record<string, number>;
        trend: Array<{ date: string; avg_bias: number; count: number }>;
      }>('get_bias_analysis', {
        aggregate: true,
        days,
      });

      return response;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
