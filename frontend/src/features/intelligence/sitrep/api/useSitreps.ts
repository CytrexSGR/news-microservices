/**
 * SITREP React Query Hooks
 *
 * Custom hooks for fetching and mutating SITREP data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSitreps,
  getSitrepById,
  getLatestSitrep,
  generateSitrep,
  markSitrepReviewed,
  deleteSitrep,
} from './sitrepApi';
import type {
  SitrepListParams,
  SitrepGenerateRequest,
} from '../types/sitrep.types';

// =============================================================================
// Query Keys
// =============================================================================

export const sitrepKeys = {
  all: ['sitreps'] as const,
  lists: () => [...sitrepKeys.all, 'list'] as const,
  list: (params: SitrepListParams) => [...sitrepKeys.lists(), params] as const,
  details: () => [...sitrepKeys.all, 'detail'] as const,
  detail: (id: string) => [...sitrepKeys.details(), id] as const,
  latest: (reportType: string) => [...sitrepKeys.all, 'latest', reportType] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook for fetching list of SITREPs
 */
export function useSitreps(params: SitrepListParams = {}) {
  return useQuery({
    queryKey: sitrepKeys.list(params),
    queryFn: () => getSitreps(params),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook for fetching a single SITREP
 */
export function useSitrep(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: sitrepKeys.detail(id),
    queryFn: () => getSitrepById(id),
    enabled: enabled && !!id,
    staleTime: 60000,
  });
}

/**
 * Hook for fetching the latest SITREP
 */
export function useLatestSitrep(reportType: string = 'daily') {
  return useQuery({
    queryKey: sitrepKeys.latest(reportType),
    queryFn: () => getLatestSitrep(reportType),
    staleTime: 60000,
    retry: false, // Don't retry if no SITREP exists
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook for generating a new SITREP
 */
export function useGenerateSitrep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SitrepGenerateRequest) => generateSitrep(request),
    onSuccess: () => {
      // Invalidate all sitrep queries to refetch
      queryClient.invalidateQueries({ queryKey: sitrepKeys.all });
    },
  });
}

/**
 * Hook for marking a SITREP as reviewed
 */
export function useMarkSitrepReviewed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reviewed }: { id: string; reviewed: boolean }) =>
      markSitrepReviewed(id, reviewed),
    onSuccess: (data, variables) => {
      // Update the specific sitrep in cache
      queryClient.setQueryData(sitrepKeys.detail(variables.id), data);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: sitrepKeys.lists() });
    },
  });
}

/**
 * Hook for deleting a SITREP
 */
export function useDeleteSitrep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSitrep(id),
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: sitrepKeys.detail(id) });
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: sitrepKeys.lists() });
    },
  });
}
