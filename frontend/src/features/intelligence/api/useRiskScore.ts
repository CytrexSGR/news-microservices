import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRiskHistory,
  intelligenceEndpoints,
  type RiskCalculateRequest,
  type RiskCalculateResponse,
} from './intelligenceApi';
import type { RiskHistoryResponse } from '../types/intelligence.types';

/**
 * Hook for fetching risk history data
 */
export function useRiskHistory(days: number = 7, refetchInterval: number = 60000) {
  return useQuery<RiskHistoryResponse>({
    queryKey: ['intelligence', 'risk-history', days],
    queryFn: () => getRiskHistory(days),
    refetchInterval,
    staleTime: 30000,
  });
}

/**
 * Hook for calculating risk scores
 *
 * Uses mutation pattern since this is a POST endpoint that may take time
 * and shouldn't be automatically refetched.
 *
 * Supports three modes:
 * 1. Cluster mode: Provide cluster_id
 * 2. Entity mode: Provide entities (array of names)
 * 3. Text mode: Provide text content
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useRiskCalculation();
 *
 * // Calculate risk for a cluster
 * mutate({ cluster_id: 'abc-123', include_factors: true });
 *
 * // Or for specific entities
 * mutate({ entities: ['Goldman Sachs', 'Federal Reserve'] });
 *
 * // Or analyze text directly
 * mutate({ text: 'Breaking: Major cyberattack reported...' });
 * ```
 */
export function useRiskCalculation() {
  const queryClient = useQueryClient();

  return useMutation<RiskCalculateResponse, Error, RiskCalculateRequest>({
    mutationFn: (data) => intelligenceEndpoints.calculateRisk(data),
    onSuccess: () => {
      // Invalidate risk history to reflect new calculation
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'risk-history'] });
    },
  });
}
