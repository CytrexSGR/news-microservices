/**
 * React Query hooks for watchlist management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { watchlistApi } from '../api/watchlistApi';
import type { WatchlistItemCreate } from '../types/security.types';

const WATCHLIST_KEY = ['watchlist'];
const ALERTS_KEY = ['watchlist', 'alerts'];
const ALERT_STATS_KEY = ['watchlist', 'stats'];

/**
 * Hook to fetch watchlist items.
 */
export function useWatchlist(itemType?: string) {
  return useQuery({
    queryKey: [...WATCHLIST_KEY, itemType],
    queryFn: () => watchlistApi.getWatchlist(itemType),
    staleTime: 30_000,
  });
}

/**
 * Hook to add item to watchlist.
 */
export function useAddWatchlistItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (item: WatchlistItemCreate) => watchlistApi.addItem(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY });
    },
  });
}

/**
 * Hook to remove item from watchlist.
 */
export function useRemoveWatchlistItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: string) => watchlistApi.removeItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY });
    },
  });
}

/**
 * Hook to fetch alerts.
 */
export function useAlerts(unreadOnly = false, page = 1) {
  return useQuery({
    queryKey: [...ALERTS_KEY, unreadOnly, page],
    queryFn: () => watchlistApi.getAlerts(unreadOnly, page),
    staleTime: 10_000,
    refetchInterval: 30_000,  // Poll for new alerts
  });
}

/**
 * Hook to mark alerts as read.
 */
export function useMarkAlertsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertIds: string[]) => watchlistApi.markAlertsRead(alertIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ALERTS_KEY });
      queryClient.invalidateQueries({ queryKey: ALERT_STATS_KEY });
    },
  });
}

/**
 * Hook to fetch alert statistics for badge.
 */
export function useAlertStats() {
  return useQuery({
    queryKey: ALERT_STATS_KEY,
    queryFn: () => watchlistApi.getAlertStats(),
    staleTime: 10_000,
    refetchInterval: 30_000,
  });
}
