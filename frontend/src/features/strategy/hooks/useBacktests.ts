/**
 * useBacktests Hook
 *
 * Fetches and manages backtest data for a strategy.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { BacktestListResponse, BacktestSummary } from '../types';

// ============================================================================
// Query Keys
// ============================================================================

export const backtestKeys = {
  all: ['backtests'] as const,
  lists: () => [...backtestKeys.all, 'list'] as const,
  list: (strategyId: string) => [...backtestKeys.lists(), strategyId] as const,
  details: () => [...backtestKeys.all, 'detail'] as const,
  detail: (strategyId: string, backtestId: number) =>
    [...backtestKeys.details(), strategyId, backtestId] as const,
};

// ============================================================================
// Main Hook
// ============================================================================

export interface UseBacktestsOptions {
  enabled?: boolean;
}

export interface UseBacktestsResult {
  backtests: BacktestSummary[];
  strategyName: string | null;
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch backtests for a strategy
 *
 * @param strategyId - The strategy UUID
 * @param options - Query options
 * @returns Backtest list, loading state, error, and refetch function
 *
 * @example
 * ```tsx
 * const { backtests, isLoading } = useBacktests(strategyId);
 *
 * return (
 *   <BacktestTable backtests={backtests} loading={isLoading} />
 * );
 * ```
 */
export function useBacktests(
  strategyId: string | undefined,
  options: UseBacktestsOptions = {}
): UseBacktestsResult {
  const { enabled = true } = options;

  const query = useQuery({
    queryKey: backtestKeys.list(strategyId ?? ''),
    queryFn: async () => {
      if (!strategyId) {
        throw new Error('Strategy ID is required');
      }
      const response = await fetch(`/api/prediction/v1/strategies/${strategyId}/backtests`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch backtests');
      }
      return response.json() as Promise<BacktestListResponse>;
    },
    enabled: enabled && !!strategyId,
    staleTime: 30000,
  });

  return {
    backtests: query.data?.backtests ?? [],
    strategyName: query.data?.strategy_name ?? null,
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

// ============================================================================
// Mutations
// ============================================================================

/**
 * Delete a backtest
 */
export function useDeleteBacktest(strategyId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (backtestId: number) => {
      if (!strategyId) {
        throw new Error('Strategy ID is required');
      }
      const response = await fetch(
        `/api/prediction/v1/strategies/${strategyId}/backtests/${backtestId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      if (!response.ok) {
        throw new Error('Failed to delete backtest');
      }
    },
    onSuccess: () => {
      if (strategyId) {
        queryClient.invalidateQueries({ queryKey: backtestKeys.list(strategyId) });
      }
    },
  });
}
