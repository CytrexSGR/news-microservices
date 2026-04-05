/**
 * React Query Hook for Strategy Evaluation
 *
 * Fetches real-time strategy evaluation data showing entry/exit conditions
 * for all market regimes with auto-refresh every 30 seconds.
 *
 * @example
 * ```typescript
 * function StrategyMonitor({ strategyId }: { strategyId: string }) {
 *   const { data, isLoading, error } = useStrategyEvaluation(
 *     strategyId,
 *     'BTCUSDT',
 *     '1h'
 *   );
 *
 *   if (isLoading) return <div>Loading evaluation...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *   if (!data) return null;
 *
 *   return (
 *     <div>
 *       <h2>Current Regime: {data.current_regime}</h2>
 *       <RegimeDisplay evaluation={data.regimes[data.current_regime]} />
 *     </div>
 *   );
 * }
 * ```
 */

import { useQuery, type UseQueryResult, type UseQueryOptions } from '@tanstack/react-query'
import { predictionApi } from '@/api/axios'
import type {
  StrategyEvaluationResponse,
  RegimeEvaluation,
  EntryEvaluation,
  ConditionEvaluation,
} from '@/types/strategy-evaluation'

// ============================================================================
// Types
// ============================================================================

/**
 * Options for useStrategyEvaluation hook
 */
export interface UseStrategyEvaluationOptions
  extends Omit<
    UseQueryOptions<StrategyEvaluationResponse, Error, StrategyEvaluationResponse, readonly [string, string, string, string]>,
    'queryKey' | 'queryFn'
  > {
  /**
   * Enable/disable the query
   * @default true (but only if strategyId and symbol are provided)
   */
  enabled?: boolean

  /**
   * Auto-refetch interval in milliseconds
   * @default 30000 (30 seconds)
   */
  refetchInterval?: number

  /**
   * Refetch when tab is not in background
   * @default false (save API calls)
   */
  refetchIntervalInBackground?: boolean

  /**
   * Time in milliseconds after which data is considered stale
   * @default 10000 (10 seconds)
   */
  staleTime?: number

  /**
   * Number of retry attempts for failed requests
   * @default 2
   */
  retry?: number | boolean

  /**
   * Callback when query succeeds
   */
  onSuccess?: (data: StrategyEvaluationResponse) => void

  /**
   * Callback when query fails
   */
  onError?: (error: Error) => void
}

/**
 * Return type for useStrategyEvaluation hook
 */
export type UseStrategyEvaluationResult = UseQueryResult<StrategyEvaluationResponse, Error>

// ============================================================================
// API Client
// ============================================================================

/**
 * Fetch strategy evaluation from prediction-service
 *
 * @param strategyId Strategy UUID
 * @param symbol Trading symbol (e.g., "BTCUSDT", "BTC/USDT:USDT")
 * @param timeframe Timeframe for evaluation (e.g., "1h", "4h")
 * @returns Strategy evaluation response
 */
async function fetchStrategyEvaluation(
  strategyId: string,
  symbol: string,
  timeframe: string
): Promise<StrategyEvaluationResponse> {
  const response = await predictionApi.get<StrategyEvaluationResponse>(
    `/strategies/${strategyId}/evaluate`,
    {
      params: {
        symbol,
        timeframe,
      },
    }
  )
  return response.data
}

// ============================================================================
// Main Hook
// ============================================================================

/**
 * Fetch real-time strategy evaluation with auto-refresh
 *
 * This hook uses React Query to fetch, cache, and manage the state of
 * strategy evaluation data. It includes automatic refetching every 30 seconds,
 * retry logic, and request deduplication.
 *
 * **Features:**
 * - Automatic caching (10 seconds stale time by default)
 * - Auto-refresh every 30 seconds
 * - Request deduplication (multiple components share one request)
 * - Automatic retry on failure (2 attempts with exponential backoff)
 * - Only refetches when tab is active (saves API calls)
 * - Loading and error states
 *
 * **Performance:**
 * - API target: < 100ms response time
 * - Caching prevents unnecessary requests
 * - Background refetch disabled to save resources
 *
 * @param strategyId - Strategy UUID to evaluate
 * @param symbol - Trading symbol (e.g., "BTCUSDT")
 * @param timeframe - Evaluation timeframe (default: "1h")
 * @param options - Optional query configuration
 * @returns React Query result with data, loading state, error, and refetch function
 *
 * @example
 * Basic usage:
 * ```typescript
 * const { data, isLoading, error } = useStrategyEvaluation(
 *   strategyId,
 *   'BTCUSDT',
 *   '1h'
 * );
 * ```
 *
 * @example
 * With custom refresh interval:
 * ```typescript
 * const { data, refetch } = useStrategyEvaluation(
 *   strategyId,
 *   'ETHUSDT',
 *   '4h',
 *   {
 *     refetchInterval: 60000, // 1 minute
 *     onSuccess: (data) => {
 *       console.log('Current regime:', data.current_regime);
 *     },
 *   }
 * );
 * ```
 *
 * @example
 * Conditional query (only when strategyId exists):
 * ```typescript
 * const { data } = useStrategyEvaluation(
 *   selectedStrategy?.id,
 *   'BTCUSDT',
 *   '1h',
 *   {
 *     enabled: !!selectedStrategy,
 *   }
 * );
 * ```
 */
export function useStrategyEvaluation(
  strategyId: string | undefined,
  symbol: string | undefined,
  timeframe: string = '1h',
  options: UseStrategyEvaluationOptions = {}
): UseStrategyEvaluationResult {
  const {
    enabled = true,
    refetchInterval = 30000,
    refetchIntervalInBackground = false,
    staleTime = 10000,
    retry = 2,
    ...restOptions
  } = options

  return useQuery({
    // Query key for caching and deduplication
    // Format: ['strategy-evaluation', strategyId, symbol, timeframe]
    queryKey: ['strategy-evaluation', strategyId ?? '', symbol ?? '', timeframe] as const,

    // Query function - fetches data from API
    queryFn: () => {
      if (!strategyId || !symbol) {
        throw new Error('Strategy ID and symbol are required')
      }
      return fetchStrategyEvaluation(strategyId, symbol, timeframe)
    },

    // Enable only if both strategyId and symbol are provided
    enabled: enabled && !!strategyId && !!symbol,

    // Auto-refresh configuration
    refetchInterval,
    refetchIntervalInBackground,

    // Stale time - consider data stale after 10 seconds
    staleTime,

    // Retry configuration - 2 attempts with exponential backoff
    retry,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),

    // Pass through any additional options
    ...restOptions,
  })
}

// ============================================================================
// Helper Hooks
// ============================================================================

/**
 * Get evaluation for a specific regime
 *
 * Returns the evaluation for a specific market regime and indicates
 * if it's the currently active regime.
 *
 * @param strategyId Strategy UUID
 * @param symbol Trading symbol
 * @param regime Regime type to fetch
 * @param timeframe Evaluation timeframe (default: "1h")
 * @returns Query result with regime-specific data
 *
 * @example
 * ```typescript
 * const { data, isActiveRegime } = useRegimeEvaluation(
 *   strategyId,
 *   'BTCUSDT',
 *   'TREND'
 * );
 *
 * if (data && isActiveRegime) {
 *   console.log('Trend regime is active!');
 * }
 * ```
 */
export function useRegimeEvaluation(
  strategyId: string | undefined,
  symbol: string | undefined,
  regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY',
  timeframe: string = '1h'
) {
  const query = useStrategyEvaluation(strategyId, symbol, timeframe)

  return {
    ...query,
    data: query.data?.regimes[regime],
    isActiveRegime: query.data?.current_regime === regime,
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Calculate entry score display information
 *
 * Provides useful metrics for displaying entry condition status:
 * - Score vs max score
 * - Percentage completion
 * - Threshold comparison
 * - Met/unmet condition counts
 * - Confidence sums
 *
 * @param entry Entry evaluation data
 * @returns Display metrics or null if no data
 *
 * @example
 * ```typescript
 * const displayInfo = calculateEntryScoreDisplay(evaluation.entry);
 *
 * if (displayInfo) {
 *   console.log(`${displayInfo.metCount}/${displayInfo.totalCount} conditions met`);
 *   console.log(`Score: ${displayInfo.score}/${displayInfo.maxScore}`);
 *   console.log(`Entry possible: ${displayInfo.entryPossible}`);
 * }
 * ```
 */
export function calculateEntryScoreDisplay(entry: EntryEvaluation | undefined) {
  if (!entry) return null

  const metConditions = entry.conditions.filter((c) => c.met)
  const unmetConditions = entry.conditions.filter((c) => !c.met)

  const metScore = metConditions.reduce((sum, c) => sum + c.confidence, 0)
  const totalScore = entry.conditions.reduce((sum, c) => sum + c.confidence, 0)

  return {
    /** Current entry score */
    score: entry.score,
    /** Maximum possible score */
    maxScore: entry.max_score,
    /** Score as percentage of total possible */
    percentage: totalScore > 0 ? (entry.score / totalScore) * 100 : 0,
    /** Required threshold as percentage */
    threshold: entry.threshold * 100,
    /** Whether entry is possible */
    entryPossible: entry.entry_possible,
    /** Number of met conditions */
    metCount: metConditions.length,
    /** Total number of conditions */
    totalCount: entry.conditions.length,
    /** Sum of confidence from met conditions */
    metConfidenceSum: metScore,
    /** Sum of confidence from unmet conditions */
    unmetConfidenceSum: totalScore - metScore,
  }
}

/**
 * Check if any exit rule is triggered
 *
 * @param exit Exit evaluation data
 * @returns True if any exit condition would trigger at current price
 */
export function isExitTriggered(exit: RegimeEvaluation['exit'] | undefined): boolean {
  if (!exit) return false

  // Check if any exit conditions are met
  // Note: This depends on backend implementation
  // For now, assume exit has a 'triggered' field or similar
  return false // Placeholder - adjust based on actual backend response
}

/**
 * Get human-readable regime name
 *
 * @param regime Regime type
 * @returns Formatted regime name
 */
export function getRegimeName(regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'): string {
  const names = {
    TREND: 'Trending Market',
    CONSOLIDATION: 'Consolidating Market',
    HIGH_VOLATILITY: 'High Volatility',
  }
  return names[regime]
}

/**
 * Get regime color for UI display
 *
 * @param regime Regime type
 * @returns Tailwind CSS color class
 */
export function getRegimeColor(regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'): string {
  const colors = {
    TREND: 'text-blue-600',
    CONSOLIDATION: 'text-yellow-600',
    HIGH_VOLATILITY: 'text-red-600',
  }
  return colors[regime]
}

// ============================================================================
// Query Key Factory
// ============================================================================

/**
 * Factory for creating query keys
 * Useful for cache invalidation and prefetching
 */
export const strategyEvaluationKeys = {
  /**
   * Base key for all strategy evaluation queries
   */
  all: ['strategy-evaluation'] as const,

  /**
   * Key for specific strategy evaluation
   */
  detail: (strategyId: string, symbol: string, timeframe: string) =>
    ['strategy-evaluation', strategyId, symbol, timeframe] as const,

  /**
   * Key for all evaluations of a strategy (across symbols/timeframes)
   */
  byStrategy: (strategyId: string) => ['strategy-evaluation', strategyId] as const,

  /**
   * Key for all evaluations of a symbol (across strategies/timeframes)
   */
  bySymbol: (symbol: string) => ['strategy-evaluation', symbol] as const,
}
