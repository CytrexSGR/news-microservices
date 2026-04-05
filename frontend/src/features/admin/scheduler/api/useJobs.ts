/**
 * Jobs Feature React Query Hooks
 *
 * Provides hooks for job queue operations using @tanstack/react-query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import * as api from './schedulerApi';
import type { JobsQuery } from '../types';

// ============================================================================
// Query Keys
// ============================================================================

export const jobsKeys = {
  all: ['jobs'] as const,
  list: (params?: JobsQuery) => [...jobsKeys.all, 'list', params] as const,
  stats: () => [...jobsKeys.all, 'stats'] as const,
};

// ============================================================================
// Job List Hooks
// ============================================================================

/**
 * Hook to list analysis jobs with pagination and filtering
 */
export function useJobs(params?: JobsQuery, refetchInterval = 5000) {
  return useQuery({
    queryKey: jobsKeys.list(params),
    queryFn: async () => {
      const response = await api.listJobs(params);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    refetchInterval,
    staleTime: 2500,
  });
}

/**
 * Hook to get job queue statistics
 */
export function useJobStats(refetchInterval = 5000) {
  return useQuery({
    queryKey: jobsKeys.stats(),
    queryFn: async () => {
      const response = await api.getJobStats();
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    refetchInterval,
    staleTime: 2500,
  });
}

// ============================================================================
// Job Action Hooks
// ============================================================================

/**
 * Hook to retry a failed job
 */
export function useRetryJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobId: string) => {
      const response = await api.retryJob(jobId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobsKeys.all });
      toast.success('Job queued for retry');
    },
    onError: (error: Error) => {
      toast.error(`Failed to retry job: ${error.message}`);
    },
  });
}

/**
 * Hook to cancel a pending/processing job
 */
export function useCancelJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobId: string) => {
      const response = await api.cancelJob(jobId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobsKeys.all });
      toast.success('Job cancelled');
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel job: ${error.message}`);
    },
  });
}

/**
 * Hook to force feed check
 */
export function useForceFeedCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (feedId: string) => {
      const response = await api.forceFeedCheck(feedId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: jobsKeys.all });
      toast.success(`Feed check triggered: ${data.message}`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to trigger feed check: ${error.message}`);
    },
  });
}

/**
 * Hook to run entity deduplication
 */
export function useRunDeduplication() {
  return useMutation({
    mutationFn: async (dryRun: boolean) => {
      const response = await api.runDeduplication(dryRun);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      if (data.dry_run) {
        toast.success(
          `Dry run complete: ${data.result.duplicates_found} duplicates found`
        );
      } else {
        toast.success(
          `Deduplication complete: ${data.result.merges_performed || 0} merges performed`
        );
      }
    },
    onError: (error: Error) => {
      toast.error(`Deduplication failed: ${error.message}`);
    },
  });
}
