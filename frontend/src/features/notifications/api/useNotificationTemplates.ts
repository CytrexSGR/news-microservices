/**
 * useNotificationTemplates Hook
 *
 * Query hooks for listing and managing notification templates.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NotificationTemplate,
  TemplateListResponse,
  CreateTemplateRequest,
  UpdateTemplateRequest,
} from '../types';

/**
 * Hook to list all notification templates
 *
 * @example
 * ```tsx
 * const { data: templates, isLoading } = useNotificationTemplates();
 * ```
 */
export function useNotificationTemplates() {
  return useQuery<TemplateListResponse>({
    queryKey: ['notifications', 'templates'],
    queryFn: async () => {
      const response = await mcpClient.callTool<TemplateListResponse>(
        'list_notification_templates',
        {}
      );
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook to get a single template by ID
 */
export function useNotificationTemplate(templateId: number | undefined) {
  return useQuery<NotificationTemplate>({
    queryKey: ['notifications', 'templates', templateId],
    queryFn: async () => {
      if (!templateId) throw new Error('Template ID required');
      const response = await mcpClient.callTool<NotificationTemplate>(
        'get_notification_template',
        { template_id: templateId }
      );
      return response;
    },
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to get a template by name
 */
export function useNotificationTemplateByName(templateName: string | undefined) {
  return useQuery<NotificationTemplate>({
    queryKey: ['notifications', 'templates', 'byName', templateName],
    queryFn: async () => {
      if (!templateName) throw new Error('Template name required');
      const response = await mcpClient.callTool<NotificationTemplate>(
        'get_notification_template_by_name',
        { template_name: templateName }
      );
      return response;
    },
    enabled: !!templateName,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to create a new template (Admin)
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<NotificationTemplate, Error, CreateTemplateRequest>({
    mutationFn: async (templateData: CreateTemplateRequest) => {
      const response = await mcpClient.callTool<NotificationTemplate>(
        'create_notification_template',
        templateData
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'templates'],
      });
    },
  });
}

/**
 * Hook to update an existing template (Admin)
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    NotificationTemplate,
    Error,
    { templateId: number; updates: UpdateTemplateRequest }
  >({
    mutationFn: async ({ templateId, updates }) => {
      const response = await mcpClient.callTool<NotificationTemplate>(
        'update_notification_template',
        { template_id: templateId, ...updates }
      );
      return response;
    },
    onSuccess: (data, { templateId }) => {
      // Update the specific template in cache
      queryClient.setQueryData(
        ['notifications', 'templates', templateId],
        data
      );
      // Invalidate the list
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'templates'],
        exact: true,
      });
    },
  });
}

/**
 * Hook to delete a template (Admin)
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean }, Error, number>({
    mutationFn: async (templateId: number) => {
      const response = await mcpClient.callTool<{ success: boolean }>(
        'delete_notification_template',
        { template_id: templateId }
      );
      return response;
    },
    onSuccess: (_, templateId) => {
      queryClient.removeQueries({
        queryKey: ['notifications', 'templates', templateId],
      });
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'templates'],
      });
    },
  });
}
