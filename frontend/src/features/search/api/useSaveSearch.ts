/**
 * useSaveSearch Mutation Hooks
 *
 * Mutation hooks for creating, updating, and deleting saved searches.
 * Re-exports from useSavedSearches for backward compatibility.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import toast from 'react-hot-toast';
import type {
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
} from '../types/search.types';
import { savedSearchKeys } from './useSavedSearches';

// =============================================================================
// API Functions
// =============================================================================

/**
 * Create a new saved search
 */
const createSavedSearch = async (
  params: SavedSearchCreate
): Promise<SavedSearch> => {
  const { data } = await searchApi.post<SavedSearch>('/search/saved', params);
  return data;
};

/**
 * Update an existing saved search
 */
const updateSavedSearch = async ({
  id,
  ...params
}: SavedSearchUpdate & { id: string }): Promise<SavedSearch> => {
  const { data } = await searchApi.put<SavedSearch>(
    `/search/saved/${id}`,
    params
  );
  return data;
};

/**
 * Delete a saved search
 */
const deleteSavedSearch = async (id: string): Promise<void> => {
  await searchApi.delete(`/search/saved/${id}`);
};

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to save a new search
 *
 * Creates a new saved search with the provided configuration.
 * Supports scheduling and alert configuration.
 *
 * @example
 * ```tsx
 * const { mutate: saveSearch, isPending } = useSaveSearch();
 *
 * const handleSave = () => {
 *   saveSearch({
 *     name: 'AI Technology News',
 *     query: 'artificial intelligence OR machine learning',
 *     filters: {
 *       date_from: '2024-01-01',
 *       sentiment: 'positive',
 *     },
 *     is_scheduled: true,
 *     schedule_cron: '0 9 * * *', // Daily at 9am
 *     alert_enabled: true,
 *     alert_threshold: 5,
 *   });
 * };
 * ```
 */
export function useSaveSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSavedSearch,
    onSuccess: (savedSearch) => {
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      // Pre-populate the detail cache
      queryClient.setQueryData(
        savedSearchKeys.detail(Number(savedSearch.id)),
        savedSearch
      );
      toast.success(`Search "${savedSearch.name}" saved successfully`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to save search');
    },
  });
}

/**
 * Hook to update an existing saved search
 *
 * @example
 * ```tsx
 * const { mutate: updateSearch, isPending } = useUpdateSavedSearch();
 *
 * const handleUpdate = () => {
 *   updateSearch({
 *     id: '123',
 *     name: 'Updated Search Name',
 *     is_scheduled: false,
 *   });
 * };
 * ```
 */
export function useUpdateSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateSavedSearch,
    onSuccess: (savedSearch) => {
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      // Update detail cache
      queryClient.setQueryData(
        savedSearchKeys.detail(Number(savedSearch.id)),
        savedSearch
      );
      toast.success(`Search "${savedSearch.name}" updated`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update search');
    },
  });
}

/**
 * Hook to delete a saved search
 *
 * @example
 * ```tsx
 * const { mutate: deleteSearch, isPending } = useDeleteSavedSearch();
 *
 * const handleDelete = (id: string) => {
 *   if (confirm('Delete this saved search?')) {
 *     deleteSearch(id);
 *   }
 * };
 * ```
 */
export function useDeleteSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => {
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success('Search deleted');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete search');
    },
  });
}

/**
 * Hook to toggle scheduling for a saved search
 *
 * @example
 * ```tsx
 * const { mutate: toggleSchedule } = useToggleSearchSchedule();
 *
 * toggleSchedule({
 *   id: '123',
 *   is_scheduled: true,
 *   schedule_cron: '0 0 * * *', // Daily at midnight
 * });
 * ```
 */
export function useToggleSearchSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      is_scheduled,
      schedule_cron,
    }: {
      id: string;
      is_scheduled: boolean;
      schedule_cron?: string;
    }) => {
      const { data } = await searchApi.patch<SavedSearch>(
        `/search/saved/${id}/schedule`,
        { is_scheduled, schedule_cron }
      );
      return data;
    },
    onSuccess: (savedSearch) => {
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      queryClient.setQueryData(
        savedSearchKeys.detail(Number(savedSearch.id)),
        savedSearch
      );
      const status = savedSearch.is_scheduled ? 'enabled' : 'disabled';
      toast.success(`Schedule ${status} for "${savedSearch.name}"`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update schedule');
    },
  });
}

/**
 * Hook to toggle alerts for a saved search
 *
 * @example
 * ```tsx
 * const { mutate: toggleAlert } = useToggleSearchAlert();
 *
 * toggleAlert({
 *   id: '123',
 *   alert_enabled: true,
 *   alert_threshold: 10,
 * });
 * ```
 */
export function useToggleSearchAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      alert_enabled,
      alert_threshold,
    }: {
      id: string;
      alert_enabled: boolean;
      alert_threshold?: number;
    }) => {
      const { data } = await searchApi.patch<SavedSearch>(
        `/search/saved/${id}/alert`,
        { alert_enabled, alert_threshold }
      );
      return data;
    },
    onSuccess: (savedSearch) => {
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      queryClient.setQueryData(
        savedSearchKeys.detail(Number(savedSearch.id)),
        savedSearch
      );
      const status = savedSearch.alert_enabled ? 'enabled' : 'disabled';
      toast.success(`Alerts ${status} for "${savedSearch.name}"`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update alert settings');
    },
  });
}
