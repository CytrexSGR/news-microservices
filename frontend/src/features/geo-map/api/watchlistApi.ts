/**
 * Watchlist API client for managing watched entities and alerts.
 */

import type {
  WatchlistItem,
  WatchlistItemCreate,
  AlertList,
  AlertStats,
} from '../types/security.types';

const getApiBase = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:8115/api/v1/geo/watchlist`;
};

export const watchlistApi = {
  /**
   * Get all watchlist items with match counts.
   */
  async getWatchlist(itemType?: string): Promise<WatchlistItem[]> {
    const params = itemType ? `?item_type=${itemType}` : '';
    const response = await fetch(`${getApiBase()}${params}`);
    if (!response.ok) throw new Error('Failed to fetch watchlist');
    return response.json();
  },

  /**
   * Add item to watchlist.
   */
  async addItem(item: WatchlistItemCreate): Promise<WatchlistItem> {
    const response = await fetch(getApiBase(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!response.ok) throw new Error('Failed to add watchlist item');
    return response.json();
  },

  /**
   * Remove item from watchlist.
   */
  async removeItem(itemId: string): Promise<void> {
    const response = await fetch(`${getApiBase()}/${itemId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to remove watchlist item');
  },

  /**
   * Get alerts for watchlist items.
   */
  async getAlerts(unreadOnly = false, page = 1, perPage = 50): Promise<AlertList> {
    const params = new URLSearchParams({
      unread_only: String(unreadOnly),
      page: String(page),
      per_page: String(perPage),
    });
    const response = await fetch(`${getApiBase()}/alerts?${params}`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  },

  /**
   * Mark alerts as read.
   */
  async markAlertsRead(alertIds: string[]): Promise<{ updated: number }> {
    const response = await fetch(`${getApiBase()}/alerts/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(alertIds),
    });
    if (!response.ok) throw new Error('Failed to mark alerts as read');
    return response.json();
  },

  /**
   * Get alert statistics for badge display.
   */
  async getAlertStats(): Promise<AlertStats> {
    const response = await fetch(`${getApiBase()}/stats`);
    if (!response.ok) throw new Error('Failed to fetch alert stats');
    return response.json();
  },
};
