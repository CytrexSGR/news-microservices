/**
 * useCanonStats Hook
 *
 * Query hook for fetching canonicalization statistics.
 */
import { useQuery } from '@tanstack/react-query';
import { getDetailedStats, getBasicStats } from './entitiesApi';
import type { CanonStats, BasicCanonStats } from '../types/entities.types';

interface UseCanonStatsOptions {
  detailed?: boolean;
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * Fetch detailed canonicalization stats
 */
export function useCanonStats(options?: UseCanonStatsOptions) {
  const { detailed = true, enabled = true, refetchInterval = 60000 } = options || {};

  return useQuery<CanonStats>({
    queryKey: ['entities', 'stats', 'detailed'],
    queryFn: getDetailedStats,
    enabled: enabled && detailed,
    refetchInterval,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Fetch basic canonicalization stats (lighter weight)
 */
export function useBasicCanonStats(options?: Omit<UseCanonStatsOptions, 'detailed'>) {
  const { enabled = true, refetchInterval = 60000 } = options || {};

  return useQuery<BasicCanonStats>({
    queryKey: ['entities', 'stats', 'basic'],
    queryFn: getBasicStats,
    enabled,
    refetchInterval,
    staleTime: 30000,
  });
}
