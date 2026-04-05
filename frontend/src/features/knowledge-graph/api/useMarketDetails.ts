/**
 * useMarketDetails Hook
 *
 * Fetches detailed information for a single market node including
 * price data, connected entities, and related articles.
 * Uses MCP tool: get_market_details
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMarketDetails('AAPL')
 * ```
 *
 * @module features/knowledge-graph/api/useMarketDetails
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MarketNodeDetails } from '../types/market';

// ===========================
// Hook Options
// ===========================

export interface UseMarketDetailsOptions {
  /** Enable/disable query */
  enabled?: boolean;
  /** Include related articles */
  includeArticles?: boolean;
  /** Limit for connected entities */
  entityLimit?: number;
  /** Limit for related articles */
  articleLimit?: number;
  /** Stale time in ms */
  staleTime?: number;
}

// ===========================
// Query Key Factory
// ===========================

export const marketDetailsKeys = {
  all: ['knowledge-graph', 'market-details'] as const,
  detail: (symbol: string) => [...marketDetailsKeys.all, symbol] as const,
  detailWithOptions: (symbol: string, options: UseMarketDetailsOptions) =>
    [...marketDetailsKeys.detail(symbol), options] as const,
};

// ===========================
// API Function
// ===========================

interface MarketDetailsParams {
  symbol: string;
  include_articles?: boolean;
  entity_limit?: number;
  article_limit?: number;
}

async function fetchMarketDetails(params: MarketDetailsParams): Promise<MarketNodeDetails> {
  return mcpClient.callTool<MarketNodeDetails>('get_market_details', {
    symbol: params.symbol,
    include_articles: params.include_articles ?? true,
    entity_limit: params.entity_limit ?? 10,
    article_limit: params.article_limit ?? 5,
  });
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch detailed market node information.
 *
 * @param symbol - Trading symbol (e.g., "AAPL", "BTCUSD")
 * @param options - Query options
 * @returns React Query result with market details
 */
export function useMarketDetails(
  symbol: string | null,
  options: UseMarketDetailsOptions = {}
) {
  const {
    enabled = true,
    includeArticles = true,
    entityLimit = 10,
    articleLimit = 5,
    staleTime = 60 * 1000, // 1 minute default
  } = options;

  return useQuery({
    queryKey: marketDetailsKeys.detailWithOptions(symbol ?? '', options),
    queryFn: () =>
      fetchMarketDetails({
        symbol: symbol!,
        include_articles: includeArticles,
        entity_limit: entityLimit,
        article_limit: articleLimit,
      }),
    enabled: !!symbol && enabled,
    staleTime,
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ===========================
// Prefetch Function
// ===========================

/**
 * Prefetch market details for hover states.
 * Useful for preloading data on mouse enter.
 */
export async function prefetchMarketDetails(
  queryClient: ReturnType<typeof import('@tanstack/react-query').useQueryClient>,
  symbol: string
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: marketDetailsKeys.detail(symbol),
    queryFn: () =>
      fetchMarketDetails({
        symbol,
        include_articles: false,
        entity_limit: 5,
      }),
    staleTime: 60 * 1000,
  });
}
