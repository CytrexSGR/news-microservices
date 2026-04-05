/**
 * Notification Types
 *
 * Matches backend notification-service schemas
 */

export type NotificationChannel = 'email' | 'webhook' | 'rabbitmq' | 'push';

export type NotificationStatus = 'pending' | 'sent' | 'failed' | 'retrying';

export interface Notification {
  id: number;
  user_id: string;
  channel: NotificationChannel;
  status: NotificationStatus;
  subject: string | null;
  content: string;
  metadata: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  sent_at: string | null;
}

export interface NotificationPreferences {
  id: number;
  user_id: string;
  email_enabled: boolean;
  webhook_enabled: boolean;
  push_enabled: boolean;
  webhook_url: string | null;
  fcm_token: string | null;
  filters: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface NotificationPreferencesUpdate {
  email_enabled?: boolean;
  webhook_enabled?: boolean;
  push_enabled?: boolean;
  webhook_url?: string | null;
  fcm_token?: string | null;
  filters?: Record<string, unknown>;
}

export interface NotificationsListParams {
  channel?: NotificationChannel;
  status?: NotificationStatus;
  limit?: number;
  offset?: number;
}
