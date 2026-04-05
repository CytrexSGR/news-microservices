/**
 * useSendNotification Hook
 *
 * Mutation hooks for sending notifications (templated and ad-hoc).
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  SendNotificationRequest,
  SendAdhocNotificationRequest,
  SendNotificationResponse,
} from '../types';

/**
 * Hook to send a templated notification
 *
 * @example
 * ```tsx
 * const sendNotification = useSendNotification();
 * sendNotification.mutate({
 *   user_id: 'user123',
 *   channel: NotificationChannel.EMAIL,
 *   template_name: 'welcome_email',
 *   template_variables: { name: 'John' },
 * });
 * ```
 */
export function useSendNotification() {
  const queryClient = useQueryClient();

  return useMutation<SendNotificationResponse, Error, SendNotificationRequest>({
    mutationFn: async (request: SendNotificationRequest) => {
      const response = await mcpClient.callTool<SendNotificationResponse>(
        'send_notification',
        request
      );
      return response;
    },
    onSuccess: () => {
      // Refresh notification history
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'history'],
      });
      // Refresh queue stats if viewing admin panel
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to send an ad-hoc notification (without template)
 *
 * @example
 * ```tsx
 * const sendAdhoc = useSendAdhocNotification();
 * sendAdhoc.mutate({
 *   recipient: 'user@example.com',
 *   subject: 'Important Update',
 *   body: 'This is the email content...',
 *   body_format: 'markdown',
 * });
 * ```
 */
export function useSendAdhocNotification() {
  const queryClient = useQueryClient();

  return useMutation<SendNotificationResponse, Error, SendAdhocNotificationRequest>({
    mutationFn: async (request: SendAdhocNotificationRequest) => {
      const response = await mcpClient.callTool<SendNotificationResponse>(
        'send_adhoc_notification',
        request
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'history'],
      });
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to send a notification to multiple recipients
 */
export function useSendBulkNotification() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; sent_count: number; failed_count: number },
    Error,
    {
      recipients: string[];
      template_name: string;
      template_variables: Record<string, unknown>;
      channel: string;
    }
  >({
    mutationFn: async ({ recipients, template_name, template_variables, channel }) => {
      const results = await Promise.all(
        recipients.map((user_id) =>
          mcpClient.callTool<SendNotificationResponse>('send_notification', {
            user_id,
            channel,
            template_name,
            template_variables,
          })
        )
      );

      const sent = results.filter((r) => r.status === 'sent' || r.status === 'pending');
      const failed = results.filter((r) => r.status === 'failed');

      return {
        success: failed.length === 0,
        sent_count: sent.length,
        failed_count: failed.length,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications'],
      });
    },
  });
}

/**
 * Hook to resend a failed notification
 */
export function useResendNotification() {
  const queryClient = useQueryClient();

  return useMutation<SendNotificationResponse, Error, number>({
    mutationFn: async (notificationId: number) => {
      const response = await mcpClient.callTool<SendNotificationResponse>(
        'resend_notification',
        { notification_id: notificationId }
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications'],
      });
    },
  });
}
