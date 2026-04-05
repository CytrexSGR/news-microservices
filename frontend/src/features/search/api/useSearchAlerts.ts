/**
 * useSearchAlerts Hooks
 *
 * Query and mutation hooks for managing search alert configurations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import toast from 'react-hot-toast';
import type {
  SearchAlertConfig,
  SearchAlertConfigRequest,
  SearchAlertHistoryResponse,
  SearchAlertHistoryEntry,
} from '../types/search.types';
import { savedSearchKeys } from './useSavedSearches';

// =============================================================================
// Query Keys
// =============================================================================

export const searchAlertKeys = {
  all: ['search-alerts'] as const,
  configs: () => [...searchAlertKeys.all, 'configs'] as const,
  config: (savedSearchId: string) =>
    [...searchAlertKeys.all, 'config', savedSearchId] as const,
  history: () => [...searchAlertKeys.all, 'history'] as const,
  historyBySearch: (savedSearchId: string) =>
    [...searchAlertKeys.all, 'history', savedSearchId] as const,
};

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch all alert configurations
 */
const fetchAlertConfigs = async (): Promise<SearchAlertConfig[]> => {
  const { data } = await searchApi.get<SearchAlertConfig[]>('/search/alerts/configs');
  return data;
};

/**
 * Fetch alert configuration for a specific saved search
 */
const fetchAlertConfig = async (
  savedSearchId: string
): Promise<SearchAlertConfig | null> => {
  try {
    const { data } = await searchApi.get<SearchAlertConfig>(
      `/search/saved/${savedSearchId}/alert`
    );
    return data;
  } catch (error) {
    // Return null if no config exists
    return null;
  }
};

/**
 * Fetch alert history
 */
const fetchAlertHistory = async (
  savedSearchId?: string,
  limit = 50
): Promise<SearchAlertHistoryResponse> => {
  const params: Record<string, unknown> = { limit };
  if (savedSearchId) {
    params.saved_search_id = savedSearchId;
  }
  const { data } = await searchApi.get<SearchAlertHistoryResponse>(
    '/search/alerts/history',
    { params }
  );
  return data;
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to fetch all search alert configurations
 *
 * @example
 * ```tsx
 * const { data: alertConfigs, isLoading } = useSearchAlerts();
 *
 * alertConfigs?.map(config => (
 *   <AlertConfigCard key={config.saved_search_id} config={config} />
 * ));
 * ```
 */
export function useSearchAlerts() {
  return useQuery<SearchAlertConfig[]>({
    queryKey: searchAlertKeys.configs(),
    queryFn: fetchAlertConfigs,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to fetch alert configuration for a specific saved search
 *
 * @param savedSearchId - ID of the saved search
 *
 * @example
 * ```tsx
 * const { data: alertConfig } = useSearchAlertConfig('123');
 *
 * if (alertConfig?.enabled) {
 *   console.log(`Alerting via ${alertConfig.alert_type}`);
 * }
 * ```
 */
export function useSearchAlertConfig(savedSearchId: string | undefined) {
  return useQuery<SearchAlertConfig | null>({
    queryKey: searchAlertKeys.config(savedSearchId || ''),
    queryFn: () => fetchAlertConfig(savedSearchId!),
    enabled: !!savedSearchId,
    staleTime: 60000,
  });
}

/**
 * Hook to fetch alert history
 *
 * @param savedSearchId - Optional filter by saved search ID
 * @param limit - Maximum number of history entries
 *
 * @example
 * ```tsx
 * // All alert history
 * const { data: allHistory } = useSearchAlertHistory();
 *
 * // History for specific search
 * const { data: searchHistory } = useSearchAlertHistory('123');
 * ```
 */
export function useSearchAlertHistory(
  savedSearchId?: string,
  limit = 50
) {
  return useQuery<SearchAlertHistoryResponse>({
    queryKey: savedSearchId
      ? searchAlertKeys.historyBySearch(savedSearchId)
      : searchAlertKeys.history(),
    queryFn: () => fetchAlertHistory(savedSearchId, limit),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to get recent alerts count
 */
export function useRecentAlertsCount(hours = 24) {
  return useQuery<number>({
    queryKey: [...searchAlertKeys.all, 'recent-count', hours],
    queryFn: async () => {
      const { data } = await searchApi.get<{ count: number }>(
        '/search/alerts/recent',
        { params: { hours } }
      );
      return data.count;
    },
    staleTime: 60000,
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to configure search alerts
 *
 * @example
 * ```tsx
 * const { mutate: configureAlert } = useConfigureSearchAlert();
 *
 * configureAlert({
 *   savedSearchId: '123',
 *   config: {
 *     alert_type: 'email',
 *     threshold: 10,
 *     cooldown_minutes: 60,
 *     enabled: true,
 *   },
 * });
 * ```
 */
export function useConfigureSearchAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      savedSearchId,
      config,
    }: {
      savedSearchId: string;
      config: SearchAlertConfigRequest;
    }) => {
      const { data } = await searchApi.put<SearchAlertConfig>(
        `/search/saved/${savedSearchId}/alert`,
        config
      );
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: searchAlertKeys.configs() });
      queryClient.setQueryData(
        searchAlertKeys.config(variables.savedSearchId),
        data
      );
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success('Alert configuration saved');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to configure alert');
    },
  });
}

/**
 * Hook to enable/disable an alert
 *
 * @example
 * ```tsx
 * const { mutate: toggleAlert } = useToggleSearchAlert();
 *
 * toggleAlert({
 *   savedSearchId: '123',
 *   enabled: false,
 * });
 * ```
 */
export function useToggleSearchAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      savedSearchId,
      enabled,
    }: {
      savedSearchId: string;
      enabled: boolean;
    }) => {
      const { data } = await searchApi.patch<SearchAlertConfig>(
        `/search/saved/${savedSearchId}/alert`,
        { enabled }
      );
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: searchAlertKeys.configs() });
      queryClient.setQueryData(
        searchAlertKeys.config(variables.savedSearchId),
        data
      );
      const status = data.enabled ? 'enabled' : 'disabled';
      toast.success(`Alert ${status}`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to toggle alert');
    },
  });
}

/**
 * Hook to delete an alert configuration
 *
 * @example
 * ```tsx
 * const { mutate: deleteAlert } = useDeleteSearchAlert();
 *
 * deleteAlert('123');
 * ```
 */
export function useDeleteSearchAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (savedSearchId: string) => {
      await searchApi.delete(`/search/saved/${savedSearchId}/alert`);
      return savedSearchId;
    },
    onSuccess: (savedSearchId) => {
      queryClient.invalidateQueries({ queryKey: searchAlertKeys.configs() });
      queryClient.removeQueries({
        queryKey: searchAlertKeys.config(savedSearchId),
      });
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success('Alert configuration removed');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to remove alert');
    },
  });
}

/**
 * Hook to test an alert configuration
 *
 * Sends a test notification using the configured channel.
 *
 * @example
 * ```tsx
 * const { mutate: testAlert, isPending } = useTestSearchAlert();
 *
 * <Button onClick={() => testAlert('123')} disabled={isPending}>
 *   Test Alert
 * </Button>
 * ```
 */
export function useTestSearchAlert() {
  return useMutation({
    mutationFn: async (savedSearchId: string) => {
      const { data } = await searchApi.post<{ success: boolean; message: string }>(
        `/search/saved/${savedSearchId}/alert/test`
      );
      return data;
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Test alert sent successfully');
      } else {
        toast.error(data.message || 'Test alert failed');
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to send test alert');
    },
  });
}

/**
 * Hook to acknowledge/dismiss an alert history entry
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (alertId: string) => {
      await searchApi.patch(`/search/alerts/history/${alertId}/acknowledge`);
      return alertId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: searchAlertKeys.history() });
      toast.success('Alert acknowledged');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to acknowledge alert');
    },
  });
}
