/**
 * useNarrativeOverview Hook
 *
 * Fetches narrative dashboard overview data from the Narrative Service.
 * Uses direct REST API calls to port 8119.
 */
import { useQuery } from '@tanstack/react-query';
import { fetchNarrativeOverview } from './narrativeApi';
import type { NarrativeOverview } from '../types/narrative.types';

/**
 * Parameters for fetching narrative overview
 */
export interface NarrativeOverviewParams {
  days?: number;
  include_recent?: boolean;
  max_recent?: number;
}

/**
 * Hook for fetching narrative dashboard overview data
 *
 * Retrieves aggregated statistics, frame distributions, and recent analyses
 * from the Narrative Service REST API.
 *
 * @param params - Query parameters for time range and included data
 * @param refetchInterval - Interval to refetch data in ms (default: 60000)
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useNarrativeOverview();
 *
 * // Custom time range
 * const { data } = useNarrativeOverview({ days: 30 });
 * ```
 */
export function useNarrativeOverview(
  params?: NarrativeOverviewParams,
  refetchInterval: number = 60000
) {
  return useQuery<NarrativeOverview, Error>({
    queryKey: ['narrative', 'overview', params],
    queryFn: async () => {
      const response = await fetchNarrativeOverview({
        days: params?.days ?? 7,
        include_recent: params?.include_recent ?? true,
        max_recent: params?.max_recent ?? 10,
      });

      // Map API response to NarrativeOverview type
      // Backend returns: total_frames, total_clusters, frame_distribution, bias_distribution,
      //                  avg_bias_score, avg_sentiment, top_narratives
      return {
        total_analyses: response.total_frames || 0,
        avg_bias_score: response.avg_bias_score ?? 0,
        frames_distribution: response.frame_distribution as Record<string, number>,
        bias_distribution: response.bias_distribution ?? {},
        // Map top_narratives (backend) to trending_frames (frontend)
        trending_frames: (response.top_narratives ?? []).map((n) => ({
          id: n.id,
          name: n.name,
          type: n.dominant_frame as any,
          count: n.frame_count,
        })),
        // recent_analyses not available in backend, return empty array
        recent_analyses: [],
        // cost tracking not implemented in narrative service
        cost_total_usd: 0,
      };
    },
    staleTime: 30000, // 30 seconds
    refetchInterval,
  });
}

/**
 * Hook for fetching just the frame distribution
 */
export function useFrameDistribution(days: number = 7, enabled: boolean = true) {
  const overviewQuery = useNarrativeOverview({ days }, 0);

  return {
    ...overviewQuery,
    data: overviewQuery.data?.frames_distribution,
  };
}

/**
 * Hook for fetching total cost statistics
 */
export function useNarrativeCosts(days: number = 30, enabled: boolean = true) {
  const overviewQuery = useNarrativeOverview({ days }, 0);

  return {
    ...overviewQuery,
    data: overviewQuery.data
      ? {
          total_cost_usd: overviewQuery.data.cost_total_usd,
          total_analyses: overviewQuery.data.total_analyses,
          avg_cost_per_analysis:
            overviewQuery.data.total_analyses > 0
              ? overviewQuery.data.cost_total_usd /
                overviewQuery.data.total_analyses
              : 0,
        }
      : undefined,
  };
}
