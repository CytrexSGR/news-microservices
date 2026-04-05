/**
 * Template Types
 *
 * Types for notification templates including CRUD operations
 * and template testing functionality.
 */

import type { NotificationChannel } from './notification.types';

/**
 * Notification template entity
 */
export interface NotificationTemplate {
  id: number;
  name: string;
  channel: NotificationChannel;
  subject?: string | null;
  body: string;
  variables: string[];
  description?: string;
  created_at: string;
  updated_at?: string | null;
  is_active?: boolean;
}

/**
 * Request to create a new template
 */
export interface CreateTemplateRequest {
  name: string;
  channel: NotificationChannel;
  subject?: string;
  body: string;
  variables?: string[];
  description?: string;
}

/**
 * Request to update an existing template
 */
export interface UpdateTemplateRequest {
  name?: string;
  channel?: NotificationChannel;
  subject?: string;
  body?: string;
  variables?: string[];
  description?: string;
  is_active?: boolean;
}

/**
 * Request to test a notification template
 */
export interface TestNotificationRequest {
  channel: NotificationChannel;
  recipient: string;
  template_name?: string;
  test_data?: Record<string, unknown>;
}

/**
 * Response from testing a template
 */
export interface TestNotificationResponse {
  success: boolean;
  message: string;
  notification_id?: number;
  rendered_subject?: string;
  rendered_body?: string;
  error?: string;
}

/**
 * Template list response
 */
export interface TemplateListResponse {
  templates: NotificationTemplate[];
  total_count: number;
}

/**
 * Template variable definition for preview
 */
export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object';
  required: boolean;
  default_value?: unknown;
  description?: string;
}

/**
 * Template preview data
 */
export interface TemplatePreviewData {
  template: NotificationTemplate;
  rendered_subject?: string;
  rendered_body?: string;
  variables: Record<string, unknown>;
}
