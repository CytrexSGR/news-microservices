/**
 * Notification Components
 *
 * Re-exports all notification UI components organized by category.
 */

// Header components (for app header integration)
export * from './header';

// Center components (notification center page)
export * from './center';

// Preferences components (user settings)
export * from './preferences';

// Templates components (admin template management)
export * from './templates';

// Queue components (admin queue monitoring)
export * from './queue';

// Legacy exports for backward compatibility
export { NotificationItem } from './NotificationItem';
export { NotificationList } from './NotificationList';
export { NotificationBell } from './NotificationBell';
export { NotificationPreferences } from './NotificationPreferences';
