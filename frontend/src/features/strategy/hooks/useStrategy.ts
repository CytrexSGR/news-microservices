/**
 * useStrategy Hook
 *
 * Fetches and manages a single strategy by ID.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { predictionClient } from '@/lib/api-client';
import type { Strategy } from '../types';

// ============================================================================
// Query Keys
// ============================================================================

export const strategyKeys = {
  all: ['strategies'] as const,
  lists: () => [...strategyKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...strategyKeys.lists(), filters] as const,
  details: () => [...strategyKeys.all, 'detail'] as const,
  detail: (id: string) => [...strategyKeys.details(), id] as const,
};

// ============================================================================
// Main Hook
// ============================================================================

export interface UseStrategyOptions {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
}

export interface UseStrategyResult {
  strategy: Strategy | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch a single strategy by ID
 *
 * @param strategyId - The strategy UUID
 * @param options - Query options
 * @returns Strategy data, loading state, error, and refetch function
 *
 * @example
 * ```tsx
 * const { strategy, isLoading, error } = useStrategy(strategyId);
 *
 * if (isLoading) return <Loading />;
 * if (error) return <Error message={error.message} />;
 * if (!strategy) return <NotFound />;
 *
 * return <StrategyDetails strategy={strategy} />;
 * ```
 */
export function useStrategy(
  strategyId: string | undefined,
  options: UseStrategyOptions = {}
): UseStrategyResult {
  const { enabled = true, refetchOnWindowFocus = false } = options;

  const query = useQuery({
    queryKey: strategyKeys.detail(strategyId ?? ''),
    queryFn: async () => {
      if (!strategyId) {
        throw new Error('Strategy ID is required');
      }
      const response = await predictionClient.get<Strategy>(`/strategies/${strategyId}`);
      return response.data;
    },
    enabled: enabled && !!strategyId,
    refetchOnWindowFocus,
    staleTime: 30000, // 30 seconds
  });

  return {
    strategy: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

// ============================================================================
// List Hook
// ============================================================================

export interface UseStrategiesListResult {
  strategies: Strategy[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch all strategies
 *
 * @returns List of strategies, total count, loading state, error, and refetch function
 *
 * @example
 * ```tsx
 * const { strategies, isLoading } = useStrategiesList();
 *
 * return (
 *   <StrategyGrid strategies={strategies} loading={isLoading} />
 * );
 * ```
 */
export function useStrategiesList(): UseStrategiesListResult {
  const query = useQuery({
    queryKey: strategyKeys.lists(),
    queryFn: async () => {
      const response = await predictionClient.get<{ strategies: Strategy[]; total: number }>(
        '/strategies/'
      );
      return response.data;
    },
    staleTime: 30000,
  });

  return {
    strategies: query.data?.strategies ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

// ============================================================================
// Mutations
// ============================================================================

export interface CloneStrategyParams {
  strategyId: string;
  newName: string;
}

/**
 * Clone a strategy
 */
export function useCloneStrategy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ strategyId, newName }: CloneStrategyParams) => {
      // First, fetch the original strategy
      const originalResponse = await predictionClient.get<Strategy>(`/strategies/${strategyId}`);
      const original = originalResponse.data;

      // Create a new strategy with the cloned definition
      const clonedDefinition = {
        ...original.definition,
        name: newName,
        strategyId: undefined, // Will be assigned by backend
      };

      const response = await predictionClient.post<Strategy>('/strategies/', {
        name: newName,
        version: original.version,
        description: `Cloned from ${original.name}`,
        definition: clonedDefinition,
        is_public: false,
      });

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategyKeys.lists() });
    },
  });
}

/**
 * Delete a strategy
 */
export function useDeleteStrategy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (strategyId: string) => {
      await predictionClient.delete(`/strategies/${strategyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategyKeys.lists() });
    },
  });
}

// Alias for convenience
export const useStrategyList = useStrategiesList;
