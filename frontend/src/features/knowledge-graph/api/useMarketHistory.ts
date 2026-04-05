/**
 * useMarketHistory Hook
 *
 * Fetches historical data for a market node from Neo4j.
 * Includes connection count, article count, and sentiment over time.
 * Uses MCP tool: get_market_history
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMarketHistory('AAPL', {
 *   granularity: 'day',
 *   startDate: '2024-01-01'
 * })
 * ```
 *
 * @module features/knowledge-graph/api/useMarketHistory
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MarketHistoryResponse, MarketHistoryQueryParams } from '../types/market';

// ===========================
// Hook Options
// ===========================

export interface UseMarketHistoryOptions {
  /** Start date (ISO 8601) */
  startDate?: string;
  /** End date (ISO 8601) */
  endDate?: string;
  /** Data granularity */
  granularity?: 'hour' | 'day' | 'week';
  /** Enable/disable query */
  enabled?: boolean;
  /** Stale time in ms */
  staleTime?: number;
}

// ===========================
// Query Key Factory
// ===========================

export const marketHistoryKeys = {
  all: ['knowledge-graph', 'market-history'] as const,
  history: (symbol: string) => [...marketHistoryKeys.all, symbol] as const,
  historyWithRange: (symbol: string, options: UseMarketHistoryOptions) =>
    [...marketHistoryKeys.history(symbol), options] as const,
};

// ===========================
// API Function
// ===========================

interface MarketHistoryParams {
  symbol: string;
  start_date?: string;
  end_date?: string;
  granularity?: 'hour' | 'day' | 'week';
}

async function fetchMarketHistory(params: MarketHistoryParams): Promise<MarketHistoryResponse> {
  return mcpClient.callTool<MarketHistoryResponse>('get_market_history', {
    symbol: params.symbol,
    start_date: params.start_date,
    end_date: params.end_date,
    granularity: params.granularity ?? 'day',
  });
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch market node historical data.
 *
 * @param symbol - Trading symbol (e.g., "AAPL", "BTCUSD")
 * @param options - Query options including date range and granularity
 * @returns React Query result with historical data
 */
export function useMarketHistory(
  symbol: string | null,
  options: UseMarketHistoryOptions = {}
) {
  const {
    startDate,
    endDate,
    granularity = 'day',
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
  } = options;

  // Default to last 30 days if no dates provided
  const defaultStartDate = startDate ?? getDefaultStartDate();
  const defaultEndDate = endDate ?? new Date().toISOString();

  return useQuery({
    queryKey: marketHistoryKeys.historyWithRange(symbol ?? '', {
      startDate: defaultStartDate,
      endDate: defaultEndDate,
      granularity,
    }),
    queryFn: () =>
      fetchMarketHistory({
        symbol: symbol!,
        start_date: defaultStartDate,
        end_date: defaultEndDate,
        granularity,
      }),
    enabled: !!symbol && enabled,
    staleTime,
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

// ===========================
// Utility Functions
// ===========================

/**
 * Get default start date (30 days ago)
 */
function getDefaultStartDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  return date.toISOString();
}

/**
 * Hook for weekly history (convenience wrapper)
 */
export function useMarketWeeklyHistory(symbol: string | null) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 90); // 90 days

  return useMarketHistory(symbol, {
    startDate: startDate.toISOString(),
    granularity: 'week',
  });
}

/**
 * Hook for daily history (convenience wrapper)
 */
export function useMarketDailyHistory(symbol: string | null, days = 30) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  return useMarketHistory(symbol, {
    startDate: startDate.toISOString(),
    granularity: 'day',
  });
}
