/**
 * useUpdateStrategy Hook
 *
 * Handles strategy definition updates with optimistic updates and cache invalidation.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { predictionClient } from '@/lib/api-client';
import type { Strategy, StrategyDefinition } from '../types';
import { strategyKeys } from './useStrategy';

// ============================================================================
// Types
// ============================================================================

export interface UpdateStrategyParams {
  strategyId: string;
  updates: Partial<{
    name: string;
    version: string;
    description: string;
    definition: Partial<StrategyDefinition>;
  }>;
}

export interface UseUpdateStrategyResult {
  updateStrategy: (params: UpdateStrategyParams) => Promise<Strategy>;
  isPending: boolean;
  error: Error | null;
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Update a strategy with optimistic updates
 *
 * @returns Mutation object with mutateAsync, isPending, and error
 *
 * @example
 * ```tsx
 * const { mutateAsync, isPending } = useUpdateStrategy();
 *
 * const handleSave = async () => {
 *   await mutateAsync({
 *     strategyId: strategy.id,
 *     updates: { definition: { indicators: newIndicators } },
 *   });
 * };
 * ```
 */
export function useUpdateStrategy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ strategyId, updates }: UpdateStrategyParams) => {
      const response = await predictionClient.patch<Strategy>(
        `/strategies/${strategyId}`,
        updates
      );
      return response.data;
    },
    onMutate: async ({ strategyId, updates }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: strategyKeys.detail(strategyId) });

      // Snapshot previous value
      const previousStrategy = queryClient.getQueryData<Strategy>(
        strategyKeys.detail(strategyId)
      );

      // Optimistically update
      if (previousStrategy) {
        queryClient.setQueryData(strategyKeys.detail(strategyId), {
          ...previousStrategy,
          ...updates,
          definition: updates.definition
            ? { ...previousStrategy.definition, ...updates.definition }
            : previousStrategy.definition,
        });
      }

      return { previousStrategy };
    },
    onError: (err, { strategyId }, context) => {
      // Rollback on error
      if (context?.previousStrategy) {
        queryClient.setQueryData(
          strategyKeys.detail(strategyId),
          context.previousStrategy
        );
      }
    },
    onSettled: (_, __, { strategyId }) => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: strategyKeys.detail(strategyId) });
      queryClient.invalidateQueries({ queryKey: strategyKeys.lists() });
    },
  });
}
