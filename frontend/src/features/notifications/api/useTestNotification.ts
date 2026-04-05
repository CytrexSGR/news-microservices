/**
 * useTestNotification Hook
 *
 * Mutation hook for testing notification templates (Admin only).
 */

import { useMutation } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  TestNotificationRequest,
  TestNotificationResponse,
} from '../types';

/**
 * Hook to test a notification template
 *
 * Sends a test notification to verify template rendering and delivery.
 * Admin only.
 *
 * @example
 * ```tsx
 * const testNotification = useTestNotification();
 * testNotification.mutate({
 *   channel: NotificationChannel.EMAIL,
 *   recipient: 'admin@test.com',
 *   template_name: 'alert_template',
 *   test_data: { alert_level: 'high', message: 'Test alert' },
 * });
 * ```
 */
export function useTestNotification() {
  return useMutation<TestNotificationResponse, Error, TestNotificationRequest>({
    mutationFn: async (request: TestNotificationRequest) => {
      const response = await mcpClient.callTool<TestNotificationResponse>(
        'test_notification',
        request
      );
      return response;
    },
  });
}

/**
 * Hook to preview a template without sending
 *
 * Renders template with test data and returns the preview.
 */
export function usePreviewTemplate() {
  return useMutation<
    { rendered_subject: string; rendered_body: string },
    Error,
    { template_name: string; variables: Record<string, unknown> }
  >({
    mutationFn: async ({ template_name, variables }) => {
      const response = await mcpClient.callTool<{
        rendered_subject: string;
        rendered_body: string;
      }>('preview_notification_template', {
        template_name,
        variables,
      });
      return response;
    },
  });
}

/**
 * Hook to validate template variables
 */
export function useValidateTemplateVariables() {
  return useMutation<
    { valid: boolean; missing_variables: string[]; extra_variables: string[] },
    Error,
    { template_name: string; variables: Record<string, unknown> }
  >({
    mutationFn: async ({ template_name, variables }) => {
      const response = await mcpClient.callTool<{
        valid: boolean;
        missing_variables: string[];
        extra_variables: string[];
      }>('validate_template_variables', {
        template_name,
        variables,
      });
      return response;
    },
  });
}
