/**
 * useMarketStats Hook
 *
 * Fetches aggregate statistics for market nodes in the knowledge graph.
 * Includes totals, breakdowns by asset type, and most connected markets.
 * Uses MCP tool: get_market_stats
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMarketStats()
 * console.log(data?.total_market_nodes)
 * ```
 *
 * @module features/knowledge-graph/api/useMarketStats
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MarketStats } from '../types/market';

// ===========================
// Hook Options
// ===========================

export interface UseMarketStatsOptions {
  /** Enable/disable query */
  enabled?: boolean;
  /** Stale time in ms */
  staleTime?: number;
  /** Refetch interval in ms */
  refetchInterval?: number;
  /** Number of most connected markets to return */
  topCount?: number;
}

// ===========================
// Query Key Factory
// ===========================

export const marketStatsKeys = {
  all: ['knowledge-graph', 'market-stats'] as const,
  stats: (topCount?: number) => [...marketStatsKeys.all, { topCount }] as const,
};

// ===========================
// API Function
// ===========================

interface MarketStatsParams {
  top_count?: number;
}

async function fetchMarketStats(params: MarketStatsParams = {}): Promise<MarketStats> {
  return mcpClient.callTool<MarketStats>('get_market_stats', {
    top_count: params.top_count ?? 10,
  });
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch market node statistics.
 *
 * @param options - Query options
 * @returns React Query result with market statistics
 */
export function useMarketStats(options: UseMarketStatsOptions = {}) {
  const {
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
    refetchInterval,
    topCount = 10,
  } = options;

  return useQuery({
    queryKey: marketStatsKeys.stats(topCount),
    queryFn: () => fetchMarketStats({ top_count: topCount }),
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
 * Hook to get asset type distribution as percentages.
 */
export function useAssetTypeDistribution() {
  const { data, ...rest } = useMarketStats();

  const distribution = data
    ? Object.entries(data.by_asset_type).map(([type, count]) => ({
        type,
        count,
        percentage: data.total_market_nodes > 0
          ? ((count / data.total_market_nodes) * 100).toFixed(1)
          : '0',
      }))
    : [];

  return { data: distribution, ...rest };
}

/**
 * Hook to get top connected markets only.
 */
export function useTopConnectedMarkets(limit = 5) {
  const { data, ...rest } = useMarketStats({ topCount: limit });

  return {
    data: data?.most_connected ?? [],
    ...rest,
  };
}
