/**
 * Notification Types
 *
 * Core types for the notification system including notifications,
 * history responses, and related enums.
 */

export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  FAILED = 'failed',
  RETRYING = 'retrying',
  READ = 'read',
  ARCHIVED = 'archived'
}

export enum NotificationChannel {
  EMAIL = 'email',
  WEBHOOK = 'webhook',
  RABBITMQ = 'rabbitmq',
  PUSH = 'push'
}

export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * Single notification entity
 */
export interface Notification {
  id: number;
  user_id: string;
  template_id?: string;
  template_name?: string;
  subject: string | null;
  content: string;
  channel: NotificationChannel;
  status: NotificationStatus;
  priority?: NotificationPriority;
  created_at: string;
  sent_at?: string | null;
  read_at?: string | null;
  archived_at?: string | null;
  metadata?: Record<string, unknown>;
  error_message?: string | null;
}

/**
 * Response from notification history endpoint
 */
export interface NotificationHistoryResponse {
  notifications: Notification[];
  total_count: number;
  unread_count: number;
  has_more: boolean;
  page: number;
  page_size: number;
}

/**
 * Request parameters for notification history
 */
export interface NotificationHistoryParams {
  page?: number;
  page_size?: number;
  status?: NotificationStatus;
  channel?: NotificationChannel;
  start_date?: string;
  end_date?: string;
  unread_only?: boolean;
}

/**
 * Send notification request (using template)
 */
export interface SendNotificationRequest {
  user_id: string;
  channel: NotificationChannel;
  subject?: string;
  content: string;
  metadata?: Record<string, unknown>;
  template_name?: string;
  template_variables?: Record<string, unknown>;
}

/**
 * Send ad-hoc notification request
 */
export interface SendAdhocNotificationRequest {
  recipient: string;
  subject: string;
  body: string;
  body_format?: 'plain' | 'html' | 'markdown';
}

/**
 * Response after sending notification
 */
export interface SendNotificationResponse {
  id: number;
  user_id: string;
  channel: string;
  status: NotificationStatus;
  subject?: string;
  content: string;
  metadata: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  sent_at?: string;
}

/**
 * Notification filter options for UI
 */
export interface NotificationFilterOptions {
  status: NotificationStatus | 'all';
  channel: NotificationChannel | 'all';
  dateRange: 'all' | 'today' | 'week' | 'month' | 'custom';
  startDate?: Date;
  endDate?: Date;
}

/**
 * Delivery attempt record
 */
export interface DeliveryAttempt {
  id: number;
  notification_id: number;
  attempt_number: number;
  status: 'success' | 'failed';
  error_message?: string;
  attempted_at: string;
}
