/**
 * useNotificationPreferences Hook
 *
 * Query and mutation hooks for user notification preferences.
 * Supports both direct API and MCP tool calls.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from './notificationApi';
import type { NotificationPreferences, UpdatePreferencesRequest } from '../types';
import toast from 'react-hot-toast';

export const preferencesQueryKeys = {
  all: ['notification-preferences'] as const,
  current: () => [...preferencesQueryKeys.all, 'current'] as const,
};

/**
 * Hook to fetch current user's notification preferences
 *
 * @example
 * ```tsx
 * const { data: preferences, isLoading } = useNotificationPreferences();
 * ```
 */
export function useNotificationPreferences(enabled = true) {
  return useQuery<NotificationPreferences>({
    queryKey: preferencesQueryKeys.current(),
    queryFn: getNotificationPreferences,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled,
  });
}

/**
 * Hook to fetch preferences via MCP
 */
export function useNotificationPreferencesMCP(enabled = true) {
  return useQuery<NotificationPreferences>({
    queryKey: ['notifications', 'preferences', 'mcp'],
    queryFn: async () => {
      const response = await mcpClient.callTool<NotificationPreferences>(
        'get_notification_preferences',
        {}
      );
      return response;
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    enabled,
  });
}

/**
 * Hook to update notification preferences
 *
 * @example
 * ```tsx
 * const updatePreferences = useUpdateNotificationPreferences();
 * updatePreferences.mutate({
 *   email_enabled: true,
 *   push_enabled: false,
 * });
 * ```
 */
export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (updates: UpdatePreferencesRequest) =>
      updateNotificationPreferences(updates),
    onSuccess: (updatedPreferences) => {
      // Update cache with new preferences
      queryClient.setQueryData<NotificationPreferences>(
        preferencesQueryKeys.current(),
        updatedPreferences
      );
      toast.success('Preferences updated');
    },
    onError: (error: Error) => {
      toast.error(`Failed to update preferences: ${error.message}`);
    },
  });
}

/**
 * Hook to update preferences via MCP
 */
export function useUpdateNotificationPreferencesMCP() {
  const queryClient = useQueryClient();

  return useMutation<NotificationPreferences, Error, UpdatePreferencesRequest>({
    mutationFn: async (updates: UpdatePreferencesRequest) => {
      const response = await mcpClient.callTool<NotificationPreferences>(
        'update_notification_preferences',
        updates
      );
      return response;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['notifications', 'preferences', 'mcp'], data);
      queryClient.setQueryData(preferencesQueryKeys.current(), data);
      toast.success('Preferences updated');
    },
    onError: (error) => {
      console.error('Failed to update notification preferences:', error);
      toast.error(`Failed to update preferences: ${error.message}`);
    },
  });
}

/**
 * Hook to toggle a specific channel on/off
 *
 * @example
 * ```tsx
 * const toggleChannel = useToggleChannel();
 * toggleChannel.mutate({ channel: 'email', enabled: false });
 * ```
 */
export function useToggleChannel() {
  const queryClient = useQueryClient();

  return useMutation<
    NotificationPreferences,
    Error,
    { channel: 'email' | 'webhook' | 'push'; enabled: boolean }
  >({
    mutationFn: async ({ channel, enabled }) => {
      const fieldName = `${channel}_enabled` as
        | 'email_enabled'
        | 'webhook_enabled'
        | 'push_enabled';

      const response = await mcpClient.callTool<NotificationPreferences>(
        'update_notification_preferences',
        { [fieldName]: enabled }
      );
      return response;
    },
    onMutate: async ({ channel, enabled }) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({
        queryKey: preferencesQueryKeys.current(),
      });

      // Get current preferences
      const previousPreferences = queryClient.getQueryData<NotificationPreferences>(
        preferencesQueryKeys.current()
      );

      // Optimistically update
      if (previousPreferences) {
        const fieldName = `${channel}_enabled` as
          | 'email_enabled'
          | 'webhook_enabled'
          | 'push_enabled';

        queryClient.setQueryData<NotificationPreferences>(
          preferencesQueryKeys.current(),
          {
            ...previousPreferences,
            [fieldName]: enabled,
          }
        );
      }

      return { previousPreferences };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousPreferences) {
        queryClient.setQueryData(
          preferencesQueryKeys.current(),
          context.previousPreferences
        );
      }
      toast.error(`Failed to toggle ${variables.channel}`);
    },
    onSuccess: () => {
      toast.success('Channel preference updated');
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: preferencesQueryKeys.current(),
      });
    },
  });
}

/**
 * Hook to update quiet hours settings
 */
export function useUpdateQuietHours() {
  const queryClient = useQueryClient();

  return useMutation<
    NotificationPreferences,
    Error,
    {
      enabled: boolean;
      start_time?: string;
      end_time?: string;
      timezone?: string;
      days?: string[];
      allow_critical?: boolean;
    }
  >({
    mutationFn: async (quietHours) => {
      const response = await mcpClient.callTool<NotificationPreferences>(
        'update_notification_preferences',
        { quiet_hours: quietHours }
      );
      return response;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(preferencesQueryKeys.current(), data);
      toast.success('Quiet hours updated');
    },
    onError: (error) => {
      toast.error(`Failed to update quiet hours: ${error.message}`);
    },
  });
}
