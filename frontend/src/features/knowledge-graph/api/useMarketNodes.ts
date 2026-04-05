/**
 * useMarketNodes Hook
 *
 * Fetches market nodes from the knowledge graph with filtering and pagination.
 * Uses MCP tool: query_markets
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMarketNodes({
 *   asset_type: 'stock',
 *   limit: 20
 * })
 * ```
 *
 * @module features/knowledge-graph/api/useMarketNodes
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MarketNode, MarketNodesQueryParams, AssetType } from '../types/market';

// ===========================
// Response Types
// ===========================

interface MarketNodesResponse {
  markets: MarketNode[];
  total: number;
  limit: number;
  offset: number;
}

// ===========================
// Hook Options
// ===========================

export interface UseMarketNodesOptions {
  /** Filter by asset type */
  assetType?: AssetType;
  /** Filter by exchange */
  exchange?: string;
  /** Search by symbol or name */
  search?: string;
  /** Minimum connection count */
  minConnections?: number;
  /** Sort field */
  sortBy?: 'symbol' | 'name' | 'connection_count' | 'last_updated';
  /** Sort direction */
  sortOrder?: 'asc' | 'desc';
  /** Pagination limit */
  limit?: number;
  /** Pagination offset */
  offset?: number;
  /** Enable/disable query */
  enabled?: boolean;
  /** Refetch interval in ms */
  refetchInterval?: number;
}

// ===========================
// Query Key Factory
// ===========================

export const marketNodesKeys = {
  all: ['knowledge-graph', 'market-nodes'] as const,
  list: (params: Partial<UseMarketNodesOptions>) =>
    [...marketNodesKeys.all, 'list', params] as const,
};

// ===========================
// API Function
// ===========================

async function fetchMarketNodes(params: MarketNodesQueryParams): Promise<MarketNodesResponse> {
  return mcpClient.callTool<MarketNodesResponse>('query_markets', {
    asset_type: params.asset_type,
    exchange: params.exchange,
    search: params.search,
    min_connections: params.min_connections,
    sort_by: params.sort_by,
    sort_order: params.sort_order,
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
  });
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch market nodes from the knowledge graph.
 *
 * @param options - Query options and filters
 * @returns React Query result with market nodes data
 */
export function useMarketNodes(options: UseMarketNodesOptions = {}) {
  const {
    assetType,
    exchange,
    search,
    minConnections,
    sortBy = 'connection_count',
    sortOrder = 'desc',
    limit = 50,
    offset = 0,
    enabled = true,
    refetchInterval,
  } = options;

  // Build query params
  const queryParams: MarketNodesQueryParams = {
    asset_type: assetType,
    exchange,
    search,
    min_connections: minConnections,
    sort_by: sortBy,
    sort_order: sortOrder,
    limit,
    offset,
  };

  return useQuery({
    queryKey: marketNodesKeys.list(options),
    queryFn: () => fetchMarketNodes(queryParams),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval,
  });
}

// ===========================
// Utility Hooks
// ===========================

/**
 * Hook to fetch market nodes by asset type.
 * Convenience wrapper around useMarketNodes.
 */
export function useMarketNodesByType(assetType: AssetType, limit = 20) {
  return useMarketNodes({
    assetType,
    limit,
    sortBy: 'connection_count',
    sortOrder: 'desc',
  });
}

/**
 * Hook to search market nodes.
 * Convenience wrapper with debounced search.
 */
export function useMarketSearch(searchTerm: string, options?: Omit<UseMarketNodesOptions, 'search'>) {
  return useMarketNodes({
    ...options,
    search: searchTerm,
    enabled: searchTerm.length >= 2,
  });
}
