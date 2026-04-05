// frontend/src/features/intelligence/bursts/api/useBursts.ts

/**
 * React Query hooks for Burst Detection API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBursts,
  getActiveBursts,
  getBurstStats,
  getBurstById,
  acknowledgeBurst,
} from './burstApi';
import type { BurstListParams } from '../types';

// =============================================================================
// Query Keys
// =============================================================================

export const burstKeys = {
  all: ['bursts'] as const,
  lists: () => [...burstKeys.all, 'list'] as const,
  list: (params: BurstListParams) => [...burstKeys.lists(), params] as const,
  active: (params: BurstListParams) => [...burstKeys.all, 'active', params] as const,
  stats: () => [...burstKeys.all, 'stats'] as const,
  detail: (id: string) => [...burstKeys.all, 'detail', id] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Fetch paginated burst alerts
 */
export function useBursts(params: BurstListParams = {}) {
  return useQuery({
    queryKey: burstKeys.list(params),
    queryFn: () => getBursts(params),
    staleTime: 30_000, // 30 seconds
  });
}

/**
 * Fetch active (unacknowledged) burst alerts
 */
export function useActiveBursts(params: BurstListParams = {}) {
  return useQuery({
    queryKey: burstKeys.active(params),
    queryFn: () => getActiveBursts(params),
    staleTime: 30_000,
    refetchInterval: 60_000, // Auto-refresh every minute for active alerts
  });
}

/**
 * Fetch burst statistics
 */
export function useBurstStats() {
  return useQuery({
    queryKey: burstKeys.stats(),
    queryFn: getBurstStats,
    staleTime: 60_000, // 1 minute
  });
}

/**
 * Fetch single burst alert
 */
export function useBurst(id: string, enabled = true) {
  return useQuery({
    queryKey: burstKeys.detail(id),
    queryFn: () => getBurstById(id),
    enabled: enabled && !!id,
  });
}

/**
 * Acknowledge a burst alert
 */
export function useAcknowledgeBurst() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: acknowledgeBurst,
    onSuccess: () => {
      // Invalidate all burst queries to refresh lists
      queryClient.invalidateQueries({ queryKey: burstKeys.all });
    },
  });
}
