/**
 * Preferences Types
 *
 * Types for user notification preferences including channel settings,
 * category filters, and quiet hours configuration.
 */

import type { NotificationChannel } from './notification.types';

/**
 * User notification preferences
 */
export interface NotificationPreferences {
  id: number;
  user_id: string;
  email_enabled: boolean;
  webhook_enabled: boolean;
  push_enabled: boolean;
  webhook_url?: string | null;
  fcm_token?: string | null;
  filters: NotificationFilters;
  quiet_hours?: QuietHoursConfig;
  created_at: string;
  updated_at?: string | null;
}

/**
 * Request to update preferences
 */
export interface UpdatePreferencesRequest {
  email_enabled?: boolean;
  webhook_enabled?: boolean;
  push_enabled?: boolean;
  webhook_url?: string;
  fcm_token?: string;
  filters?: NotificationFilters;
  quiet_hours?: QuietHoursConfig;
}

/**
 * Notification filters by event type/category
 */
export interface NotificationFilters {
  // Event type filters
  event_types?: EventTypeFilter[];

  // Category filters
  categories?: CategoryFilter[];

  // Keyword filters
  keywords?: string[];

  // Source filters
  sources?: string[];
}

/**
 * Event type filter configuration
 */
export interface EventTypeFilter {
  event_type: NotificationEventType;
  enabled: boolean;
  channels: NotificationChannel[];
}

/**
 * Category filter configuration
 */
export interface CategoryFilter {
  category: string;
  enabled: boolean;
  priority_threshold?: 'low' | 'normal' | 'high' | 'critical';
}

/**
 * Quiet hours configuration
 */
export interface QuietHoursConfig {
  enabled: boolean;
  start_time: string; // HH:MM format
  end_time: string; // HH:MM format
  timezone: string;
  days: DayOfWeek[];
  allow_critical: boolean; // Allow critical notifications during quiet hours
}

/**
 * Days of the week
 */
export type DayOfWeek =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday';

/**
 * Notification event types
 */
export type NotificationEventType =
  | 'article.new'
  | 'article.analysis_complete'
  | 'article.high_priority'
  | 'feed.new_items'
  | 'feed.error'
  | 'feed.health_warning'
  | 'osint.alert'
  | 'osint.report_ready'
  | 'research.complete'
  | 'research.error'
  | 'system.maintenance'
  | 'system.alert';

/**
 * Channel settings for UI display
 */
export interface ChannelSettingsDisplay {
  channel: NotificationChannel;
  enabled: boolean;
  label: string;
  description: string;
  icon: string;
  requiresConfiguration: boolean;
  configurationUrl?: string;
}

/**
 * Category settings for UI display
 */
export interface CategorySettingsDisplay {
  category: string;
  label: string;
  description: string;
  enabled: boolean;
  eventTypes: NotificationEventType[];
  icon: string;
}
