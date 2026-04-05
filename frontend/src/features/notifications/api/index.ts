/**
 * Notification API Hooks
 *
 * Re-exports all notification-related hooks.
 * Includes both direct API calls and MCP tool-based implementations.
 */

// API client
export { notificationApi } from './notificationApi';

// Core notification hooks (existing - direct API)
export {
  useNotifications,
  useNotification,
  useUnreadNotificationCount,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
  notificationQueryKeys,
} from './useNotifications';

// Preferences hooks
export {
  useNotificationPreferences,
  useNotificationPreferencesMCP,
  useUpdateNotificationPreferences,
  useUpdateNotificationPreferencesMCP,
  useToggleChannel,
  useUpdateQuietHours,
  preferencesQueryKeys,
} from './useNotificationPreferences';

// Notification history (MCP-based)
export {
  useNotificationHistory,
  useRecentNotifications,
} from './useNotificationHistory';

// Mark as read mutations
export {
  useMarkAsRead,
  useBulkMarkAsRead,
  useMarkAllAsRead,
} from './useMarkAsRead';

// Archive mutations
export {
  useArchiveNotification,
  useUnarchiveNotification,
  useBulkArchive,
  useDeleteNotification,
} from './useArchiveNotification';

// Templates
export {
  useNotificationTemplates,
  useNotificationTemplate,
  useNotificationTemplateByName,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
} from './useNotificationTemplates';

// Sending notifications
export {
  useSendNotification,
  useSendAdhocNotification,
  useSendBulkNotification,
  useResendNotification,
} from './useSendNotification';

// Testing (Admin)
export {
  useTestNotification,
  usePreviewTemplate,
  useValidateTemplateVariables,
} from './useTestNotification';

// Queue management (Admin)
export {
  useQueueStats,
  useDLQItems,
  useRetryDLQItem,
  useRetryAllDLQ,
  useDetailedHealth,
  useUserRateLimits,
  useResetUserRateLimits,
  useRateLimits,
  // Alias hooks for component compatibility
  useDLQNotifications,
  useRetryDLQ,
  usePurgeDLQ,
} from './useQueueStats';
