/**
 * React Query Hooks for Market Data (OHLCV)
 *
 * Provides candlestick data with automatic caching and multi-timeframe support
 */

import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'
import { predictionService } from '@/lib/api/prediction-service'
import type { OHLCV } from '@/types/market'

/**
 * Query key factory for market data
 */
export const marketDataKeys = {
  all: ['market-data'] as const,
  ohlcv: (symbol: string, timeframe: string, limit: number) =>
    [...marketDataKeys.all, 'ohlcv', symbol, timeframe, limit] as const,
}

/**
 * Hook to fetch OHLCV candlestick data
 *
 * Features:
 * - Multi-timeframe support (1m, 5m, 15m, 1h, 4h, 1d)
 * - Redis cache on backend (60s TTL)
 * - Frontend cache (stale-while-revalidate)
 *
 * @param symbol Trading symbol (e.g., "BTCUSDT")
 * @param timeframe Candle interval
 * @param limit Number of candles (default: 300)
 * @param options Query options
 * @returns OHLCV data
 */
export function useOHLCV(
  symbol: string,
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' = '1h',
  limit: number = 300,
  options?: Omit<UseQueryOptions<OHLCV[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<OHLCV[], Error>({
    queryKey: marketDataKeys.ohlcv(symbol, timeframe, limit),
    queryFn: () => predictionService.getOHLCV(symbol, timeframe, limit),

    // Refresh based on timeframe
    // - 1m, 5m, 15m: Refresh every 30s
    // - 1h: Refresh every 60s
    // - 4h, 1d: Refresh every 5min
    refetchInterval:
      timeframe === '1m' || timeframe === '5m' || timeframe === '15m'
        ? 30_000
        : timeframe === '1h'
        ? 60_000
        : 300_000,

    // Consider data fresh for slightly less than refresh interval
    staleTime:
      timeframe === '1m' || timeframe === '5m' || timeframe === '15m'
        ? 20_000
        : timeframe === '1h'
        ? 40_000
        : 240_000,

    // Retry on failure
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

    ...options,
  })
}

/**
 * Hook to fetch multi-timeframe OHLCV data
 *
 * Fetches data for multiple timeframes simultaneously
 *
 * @param symbol Trading symbol
 * @param timeframes Array of timeframes to fetch
 * @param limit Number of candles per timeframe
 * @returns Map of timeframe → OHLCV data
 */
export function useMultiTimeframeOHLCV(
  symbol: string,
  timeframes: Array<'1m' | '5m' | '15m' | '1h' | '4h' | '1d'>,
  limit: number = 300
) {
  const queries = timeframes.map((tf) => ({
    timeframe: tf,
    query: useOHLCV(symbol, tf, limit),
  }))

  return {
    data: Object.fromEntries(
      queries.map(({ timeframe, query }) => [timeframe, query.data])
    ),
    isLoading: queries.some((q) => q.query.isLoading),
    isError: queries.some((q) => q.query.isError),
    errors: queries
      .filter((q) => q.query.isError)
      .map((q) => ({ timeframe: q.timeframe, error: q.query.error })),
  }
}
