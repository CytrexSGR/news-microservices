/**
 * Scheduler Feature React Query Hooks
 *
 * Provides hooks for scheduler-service status and cron job operations
 */

import { useQuery } from '@tanstack/react-query';

import * as api from './schedulerApi';

// ============================================================================
// Query Keys
// ============================================================================

export const schedulerKeys = {
  all: ['scheduler'] as const,
  status: () => [...schedulerKeys.all, 'status'] as const,
  cronJobs: () => [...schedulerKeys.all, 'cronJobs'] as const,
};

// ============================================================================
// Scheduler Status Hooks
// ============================================================================

/**
 * Hook to get scheduler operational status
 * Auto-refreshes every 10 seconds by default
 */
export function useSchedulerStatus(refetchInterval = 10000) {
  return useQuery({
    queryKey: schedulerKeys.status(),
    queryFn: async () => {
      const response = await api.getSchedulerStatus();
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    refetchInterval,
    staleTime: 5000,
  });
}

// ============================================================================
// Cron Jobs Hooks
// ============================================================================

/**
 * Hook to list all cron scheduled jobs
 * Auto-refreshes every 30 seconds
 */
export function useCronJobs(refetchInterval = 30000) {
  return useQuery({
    queryKey: schedulerKeys.cronJobs(),
    queryFn: async () => {
      const response = await api.listCronJobs();
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    refetchInterval,
    staleTime: 15000,
  });
}
