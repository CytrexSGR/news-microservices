/**
 * Central Hook for Market Data - Parallel fetching of all quote types
 */

import { useQuery } from '@tanstack/react-query'
import * as fmpMarket from '@/lib/api/fmpMarket'
import type {
  UnifiedQuote,
  MarketCategory,
} from '@/features/market/types/market.types'

/**
 * Hook to fetch all market quotes in parallel
 * Auto-refresh based on asset type update frequency
 */
export function useMarketData() {
  // Indices - Update every 1 minute
  const {
    data: indices,
    isLoading: indicesLoading,
    error: indicesError,
    dataUpdatedAt: indicesUpdatedAt,
  } = useQuery({
    queryKey: ['market', 'quotes', 'indices'],
    queryFn: fmpMarket.getIndices,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  })

  // Forex - Update every 1 minute
  const {
    data: forex,
    isLoading: forexLoading,
    error: forexError,
    dataUpdatedAt: forexUpdatedAt,
  } = useQuery({
    queryKey: ['market', 'quotes', 'forex'],
    queryFn: fmpMarket.getForex,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000,
  })

  // Commodities - Update every 5 minutes
  const {
    data: commodities,
    isLoading: commoditiesLoading,
    error: commoditiesError,
    dataUpdatedAt: commoditiesUpdatedAt,
  } = useQuery({
    queryKey: ['market', 'quotes', 'commodities'],
    queryFn: fmpMarket.getCommodities,
    refetchInterval: 300000, // 5 minutes
    staleTime: 120000, // 2 minutes
  })

  // Crypto - Update every 1 minute
  const {
    data: crypto,
    isLoading: cryptoLoading,
    error: cryptoError,
    dataUpdatedAt: cryptoUpdatedAt,
  } = useQuery({
    queryKey: ['market', 'quotes', 'crypto'],
    queryFn: fmpMarket.getCrypto,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000,
  })

  // Combine all quotes into unified array
  const allQuotes: UnifiedQuote[] = [
    ...(indices || []),
    ...(forex || []),
    ...(commodities || []),
    ...(crypto || []),
  ]

  // Loading state - true if ANY category is loading
  const isLoading = indicesLoading || forexLoading || commoditiesLoading || cryptoLoading

  // Error state - combine all errors
  const error = indicesError || forexError || commoditiesError || cryptoError

  // Get most recent fetch time across all categories
  const lastFetchedAt = Math.max(
    indicesUpdatedAt || 0,
    forexUpdatedAt || 0,
    commoditiesUpdatedAt || 0,
    cryptoUpdatedAt || 0,
  )

  return {
    // Individual categories
    indices: indices || [],
    forex: forex || [],
    commodities: commodities || [],
    crypto: crypto || [],

    // Combined data
    allQuotes,

    // By category map
    byCategory: {
      index: (indices || []) as UnifiedQuote[],
      forex: (forex || []) as UnifiedQuote[],
      commodity: (commodities || []) as UnifiedQuote[],
      crypto: (crypto || []) as UnifiedQuote[],
    },

    // Loading states
    isLoading,
    loading: {
      indices: indicesLoading,
      forex: forexLoading,
      commodities: commoditiesLoading,
      crypto: cryptoLoading,
    },

    // Error state
    error,

    // Last fetch timestamp (React Query dataUpdatedAt)
    lastFetchedAt,
  }
}

/**
 * Hook to fetch specific quote category
 */
export function useQuotes(category: MarketCategory) {
  const queryFn = {
    index: fmpMarket.getIndices,
    forex: fmpMarket.getForex,
    commodity: fmpMarket.getCommodities,
    crypto: fmpMarket.getCrypto,
  }[category]

  const refetchInterval = category === 'commodity' ? 300000 : 60000

  return useQuery({
    queryKey: ['market', 'quotes', category],
    queryFn,
    refetchInterval,
    staleTime: refetchInterval / 2,
  })
}
