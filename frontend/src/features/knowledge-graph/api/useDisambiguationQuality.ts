/**
 * useDisambiguationQuality Hook
 *
 * Fetches entity disambiguation quality metrics including
 * success rates and by-type breakdowns.
 * Uses MCP tool: get_quality_disambiguation
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useDisambiguationQuality()
 * console.log(data?.success_rate)
 * ```
 *
 * @module features/knowledge-graph/api/useDisambiguationQuality
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DisambiguationQuality } from '../types/quality';

// ===========================
// Hook Options
// ===========================

export interface UseDisambiguationQualityOptions {
  /** Enable/disable query */
  enabled?: boolean;
  /** Stale time in ms */
  staleTime?: number;
  /** Refetch interval in ms */
  refetchInterval?: number;
}

// ===========================
// Query Key Factory
// ===========================

export const disambiguationQualityKeys = {
  all: ['knowledge-graph', 'disambiguation-quality'] as const,
  current: () => [...disambiguationQualityKeys.all, 'current'] as const,
};

// ===========================
// API Function
// ===========================

async function fetchDisambiguationQuality(): Promise<DisambiguationQuality> {
  return mcpClient.callTool<DisambiguationQuality>('get_quality_disambiguation', {});
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch disambiguation quality metrics.
 *
 * @param options - Query options
 * @returns React Query result with disambiguation data
 */
export function useDisambiguationQuality(options: UseDisambiguationQualityOptions = {}) {
  const {
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
    refetchInterval,
  } = options;

  return useQuery({
    queryKey: disambiguationQualityKeys.current(),
    queryFn: fetchDisambiguationQuality,
    enabled,
    staleTime,
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval,
  });
}

// ===========================
// Derived Data Hooks
// ===========================

/**
 * Hook to get success rate as percentage.
 */
export function useDisambiguationRate() {
  const { data, ...rest } = useDisambiguationQuality();

  return {
    rate: data ? (data.success_rate * 100).toFixed(1) : '0',
    rateDecimal: data?.success_rate ?? 0,
    ...rest,
  };
}

/**
 * Hook to get entities needing attention.
 */
export function useAmbiguousEntities() {
  const { data, ...rest } = useDisambiguationQuality();

  return {
    count: data?.ambiguous_entities ?? 0,
    resolved: data?.resolved_entities ?? 0,
    total: (data?.ambiguous_entities ?? 0) + (data?.resolved_entities ?? 0),
    ...rest,
  };
}

/**
 * Hook to get disambiguation by entity type for charts.
 */
export function useDisambiguationByType() {
  const { data, ...rest } = useDisambiguationQuality();

  const chartData = data
    ? Object.entries(data.by_entity_type).map(([type, stats]) => ({
        type,
        total: stats.total,
        resolved: stats.resolved,
        pending: stats.pending,
        rate: (stats.rate * 100).toFixed(1),
      }))
    : [];

  return {
    data: chartData,
    ...rest,
  };
}

/**
 * Hook to get disambiguation summary for widgets.
 */
export function useDisambiguationSummary() {
  const { data, isLoading, error } = useDisambiguationQuality();

  if (!data) {
    return {
      isLoading,
      error,
      summary: null,
    };
  }

  const summary = {
    successRate: (data.success_rate * 100).toFixed(1),
    ambiguousCount: data.ambiguous_entities,
    resolvedCount: data.resolved_entities,
    totalEntities: data.ambiguous_entities + data.resolved_entities,
    byTypeCount: Object.keys(data.by_entity_type).length,
    status: getDisambiguationStatus(data.success_rate),
  };

  return {
    isLoading,
    error,
    summary,
  };
}

/**
 * Get status label from success rate.
 */
function getDisambiguationStatus(rate: number): 'excellent' | 'good' | 'fair' | 'poor' {
  if (rate >= 0.9) return 'excellent';
  if (rate >= 0.75) return 'good';
  if (rate >= 0.5) return 'fair';
  return 'poor';
}
