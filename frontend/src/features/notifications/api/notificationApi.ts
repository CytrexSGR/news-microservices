/**
 * Notification API Client
 *
 * Connects to notification-service (port 8105)
 */

import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
import type {
  Notification,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  NotificationsListParams,
} from '../types';

// Create axios instance for notification service
const notificationApi = axios.create({
  baseURL: import.meta.env.VITE_NOTIFICATION_API_URL || 'http://localhost:8105/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
notificationApi.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Get user notifications with optional filters
 */
export async function getNotifications(
  params?: NotificationsListParams
): Promise<Notification[]> {
  const { data } = await notificationApi.get('/notifications/history', { params });
  return data;
}

/**
 * Get a single notification by ID
 */
export async function getNotification(id: number): Promise<Notification> {
  const { data } = await notificationApi.get(`/notifications/${id}`);
  return data;
}

/**
 * Mark a notification as read
 * Note: The backend may not have this endpoint yet - this is a placeholder
 * for when read status tracking is implemented
 */
export async function markNotificationAsRead(id: number): Promise<Notification> {
  const { data } = await notificationApi.put(`/notifications/${id}/read`);
  return data;
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsAsRead(): Promise<void> {
  await notificationApi.put('/notifications/read-all');
}

/**
 * Get user notification preferences
 */
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const { data } = await notificationApi.get('/notifications/preferences');
  return data;
}

/**
 * Update user notification preferences
 */
export async function updateNotificationPreferences(
  updates: NotificationPreferencesUpdate
): Promise<NotificationPreferences> {
  const { data } = await notificationApi.post('/notifications/preferences', updates);
  return data;
}

export { notificationApi };
