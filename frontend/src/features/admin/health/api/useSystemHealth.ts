/**
 * useSystemHealth Hook
 *
 * React Query hooks for fetching system health data.
 * Provides auto-refresh functionality for real-time monitoring.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchHealthSummary,
  fetchContainerHealth,
  fetchHealthAlerts,
} from './healthApi';
import type {
  HealthSummary,
  ContainerHealth,
  HealthAlert,
} from '../types/health';

const QUERY_KEYS = {
  healthSummary: ['system-health', 'summary'],
  containerHealth: ['system-health', 'containers'],
  healthAlerts: ['system-health', 'alerts'],
} as const;

/**
 * Hook to fetch health summary
 */
export function useHealthSummary({
  refetchInterval = 30000,
  enabled = true,
}: {
  refetchInterval?: number;
  enabled?: boolean;
} = {}) {
  return useQuery<HealthSummary>({
    queryKey: QUERY_KEYS.healthSummary,
    queryFn: fetchHealthSummary,
    refetchInterval,
    staleTime: 10000, // 10 seconds
    enabled,
  });
}

/**
 * Hook to fetch container health
 */
export function useContainerHealth({
  refetchInterval = 30000,
  enabled = true,
}: {
  refetchInterval?: number;
  enabled?: boolean;
} = {}) {
  return useQuery<ContainerHealth[]>({
    queryKey: QUERY_KEYS.containerHealth,
    queryFn: fetchContainerHealth,
    refetchInterval,
    staleTime: 10000, // 10 seconds
    enabled,
  });
}

/**
 * Hook to fetch health alerts
 */
export function useHealthAlerts({
  limit = 20,
  refetchInterval = 30000,
  enabled = true,
}: {
  limit?: number;
  refetchInterval?: number;
  enabled?: boolean;
} = {}) {
  return useQuery<HealthAlert[]>({
    queryKey: [...QUERY_KEYS.healthAlerts, limit],
    queryFn: () => fetchHealthAlerts(limit),
    refetchInterval,
    staleTime: 10000, // 10 seconds
    enabled,
  });
}

/**
 * Hook to fetch all system health data
 *
 * @example
 * ```tsx
 * const { summary, containers, alerts, isLoading, refetch } = useSystemHealth({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useSystemHealth({
  autoRefresh = true,
  refetchInterval = 30000,
  alertLimit = 20,
}: {
  autoRefresh?: boolean;
  refetchInterval?: number;
  alertLimit?: number;
} = {}) {
  const queryClient = useQueryClient();

  const summaryQuery = useHealthSummary({
    refetchInterval: autoRefresh ? refetchInterval : 0,
    enabled: true,
  });

  const containersQuery = useContainerHealth({
    refetchInterval: autoRefresh ? refetchInterval : 0,
    enabled: true,
  });

  const alertsQuery = useHealthAlerts({
    limit: alertLimit,
    refetchInterval: autoRefresh ? refetchInterval : 0,
    enabled: true,
  });

  const isLoading = summaryQuery.isLoading || containersQuery.isLoading || alertsQuery.isLoading;
  const isFetching = summaryQuery.isFetching || containersQuery.isFetching || alertsQuery.isFetching;
  const error = summaryQuery.error || containersQuery.error || alertsQuery.error;

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ['system-health'] });
  };

  return {
    summary: summaryQuery.data ?? null,
    containers: containersQuery.data ?? [],
    alerts: alertsQuery.data ?? [],
    isLoading,
    isFetching,
    error,
    refetch,
  };
}
