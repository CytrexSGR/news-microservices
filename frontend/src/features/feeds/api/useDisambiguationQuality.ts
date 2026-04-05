/**
 * Entity Disambiguation Quality API Hook
 *
 * Fetches disambiguation quality metrics from the Knowledge Graph service
 * including success rates, pending reviews, and breakdown by entity type.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * Disambiguation metrics for a specific entity type
 */
export interface DisambiguationTypeMetrics {
  /** Total entities of this type */
  total: number;
  /** Successfully resolved entities */
  resolved: number;
  /** Disambiguation success rate (0-1) */
  rate: number;
  /** Entities pending manual review */
  pending?: number;
  /** Average confidence score for resolved entities */
  avg_confidence?: number;
}

/**
 * Result from disambiguation quality check
 */
export interface DisambiguationQualityResult {
  /** Overall disambiguation success rate (0-1, multiply by 100 for percentage) */
  success_rate: number;
  /** Number of entities that could not be uniquely identified */
  ambiguous_entities: number;
  /** Number of successfully resolved entities */
  resolved_entities: number;
  /** Number of entities pending manual review */
  pending_review: number;
  /** Breakdown of disambiguation metrics by entity type */
  disambiguation_by_type: Record<string, DisambiguationTypeMetrics>;
  /** Total entities processed */
  total_entities?: number;
  /** Timestamp of the last quality check */
  last_checked?: string;
  /** Recent disambiguation events (for trend analysis) */
  recent_events?: {
    timestamp: string;
    success_rate: number;
    resolved_count: number;
  }[];
}

/**
 * Query key for disambiguation quality data
 */
export const disambiguationQualityQueryKey = ['feeds', 'disambiguation-quality'] as const;

/**
 * Hook to fetch entity disambiguation quality metrics from Knowledge Graph service
 *
 * @example
 * ```tsx
 * const { data, isLoading, refetch } = useDisambiguationQuality();
 *
 * if (data) {
 *   console.log(`Success Rate: ${(data.success_rate * 100).toFixed(1)}%`);
 *   console.log(`Pending Review: ${data.pending_review}`);
 * }
 * ```
 */
export const useDisambiguationQuality = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: disambiguationQualityQueryKey,
    queryFn: async () => {
      const result = await mcpClient.callTool<DisambiguationQualityResult>(
        'get_quality_disambiguation',
        {},
        { timeout: 60000 } // Allow 60s for potentially slow queries
      );
      return result;
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000, // Consider data stale after 30 seconds
    enabled: options?.enabled !== false,
  });
};

/**
 * Hook to manually trigger a disambiguation quality check
 */
export const useRefreshDisambiguationQuality = () => {
  const queryClient = useQueryClient();

  return {
    refresh: () => queryClient.invalidateQueries({ queryKey: disambiguationQualityQueryKey }),
  };
};

/**
 * Helper to determine if disambiguation quality needs attention
 * @param successRate - The success rate from the API (0-1)
 * @returns Status level for UI display
 */
export const getDisambiguationStatus = (
  successRate: number
): 'success' | 'warning' | 'error' => {
  if (successRate >= 0.9) return 'success';
  if (successRate >= 0.75) return 'warning';
  return 'error';
};
