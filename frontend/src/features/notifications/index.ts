/**
 * Notifications Feature
 *
 * Complete notification management for the News Microservices platform.
 * Supports email, webhook, and push notifications with template management,
 * user preferences, and admin queue monitoring.
 *
 * @module features/notifications
 */

// =============================================================================
// API Hooks (MCP-based)
// =============================================================================

export {
  // Core notification operations
  notificationApi,
  useNotifications,
  useNotification,
  useUnreadNotificationCount,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
  notificationQueryKeys,

  // User preferences
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  preferencesQueryKeys,

  // MCP-based hooks
  useNotificationHistory,
  useRecentNotifications,
  useSendNotification,
  useSendAdhocNotification,
  useMarkAsRead,
  useBulkMarkAsRead,
  useMarkAllAsRead,
  useArchiveNotification,
  useUnarchiveNotification,
  useBulkArchive,

  // Template management (admin)
  useNotificationTemplates,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useTestNotification,

  // Queue management (admin)
  useQueueStats,
  useDLQNotifications,
  useRetryDLQ,
  usePurgeDLQ,
  useRateLimits,

  // Preference mutations
  useToggleChannel,
  useUpdateQuietHours,
} from './api';

// =============================================================================
// Components
// =============================================================================

export {
  // Header components
  NotificationBell,
  NotificationDropdown,
  NotificationDropdownItem,

  // Center components
  NotificationList,
  NotificationItem,
  NotificationFilter,
  NotificationActions,

  // Preferences components
  ChannelSettings,
  CategorySettings,
  QuietHoursSettings,

  // Templates components (admin)
  TemplateList,
  TemplatePreview,
  TemplateTester,
  SendNotificationForm,

  // Queue components (admin)
  QueueStatsCards,
  QueueChart,
  FailedNotificationsList,

  // Legacy components (backward compatibility)
  NotificationPreferences,
} from './components';

// =============================================================================
// Pages
// =============================================================================

export {
  NotificationCenter,
  NotificationPreferences as NotificationPreferencesPage,
  NotificationTemplates,
  NotificationQueue,
} from './pages';

// =============================================================================
// Types
// =============================================================================

export type {
  // Core notification types
  Notification,
  NotificationChannel,
  NotificationStatus,
  NotificationHistoryParams,
  NotificationHistoryResponse,

  // Template types
  NotificationTemplate,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplatesResponse,
  TestNotificationRequest,
  TestNotificationResponse,

  // Preferences types
  NotificationPreferences as NotificationPreferencesType,
  NotificationPreferencesUpdate,
  QuietHoursConfig,
  CategoryPreference,
  ChannelConfig,

  // Queue types
  QueueStats,
  DLQNotification,
  DLQResponse,
  RateLimitInfo,
  RateLimitsResponse,

  // Legacy types (backward compatibility)
  NotificationsListParams,
} from './types';
