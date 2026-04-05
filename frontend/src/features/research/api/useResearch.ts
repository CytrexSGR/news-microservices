/**
 * Research Feature React Query Hooks
 *
 * Provides hooks for all research-service operations using @tanstack/react-query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import * as api from './researchApi';
import type {
  ResearchTaskCreate,
  ResearchTaskBatchCreate,
  ResearchTasksQuery,
  ResearchHistoryQuery,
  TemplateApply,
  ExportFormat,
  ExportRequest,
} from '../types';

// ============================================================================
// Query Keys
// ============================================================================

export const researchKeys = {
  all: ['research'] as const,
  tasks: () => [...researchKeys.all, 'tasks'] as const,
  taskList: (params?: ResearchTasksQuery) =>
    [...researchKeys.tasks(), params] as const,
  task: (id: number) => [...researchKeys.tasks(), id] as const,
  history: (params?: ResearchHistoryQuery) =>
    [...researchKeys.all, 'history', params] as const,
  feedTasks: (feedId: string) =>
    [...researchKeys.tasks(), 'feed', feedId] as const,
  stats: (days?: number) => [...researchKeys.all, 'stats', days] as const,
  templates: () => [...researchKeys.all, 'templates'] as const,
  template: (id: number) => [...researchKeys.templates(), id] as const,
  functions: () => [...researchKeys.all, 'functions'] as const,
  sources: (taskId: number) => [...researchKeys.all, 'sources', taskId] as const,
};

// ============================================================================
// Research Task Hooks
// ============================================================================

/**
 * Hook to list research tasks with pagination
 */
export function useResearchTasks(params?: ResearchTasksQuery) {
  return useQuery({
    queryKey: researchKeys.taskList(params),
    queryFn: async () => {
      const response = await api.listResearchTasks(params);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Hook to get a single research task
 * Auto-refreshes if task is in pending/processing state
 */
export function useResearchTask(taskId: number | undefined) {
  return useQuery({
    queryKey: researchKeys.task(taskId!),
    queryFn: async () => {
      const response = await api.getResearchTask(taskId!);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    enabled: taskId !== undefined,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Auto-refresh every 2s while task is running
      return status === 'pending' || status === 'processing' ? 2000 : false;
    },
  });
}

/**
 * Hook to get research history
 */
export function useResearchHistory(params?: ResearchHistoryQuery) {
  return useQuery({
    queryKey: researchKeys.history(params),
    queryFn: async () => {
      const response = await api.getResearchHistory(params);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to get research tasks for a specific feed
 */
export function useFeedResearchTasks(feedId: string, limit = 10) {
  return useQuery({
    queryKey: researchKeys.feedTasks(feedId),
    queryFn: async () => {
      const response = await api.getFeedResearchTasks(feedId, limit);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    enabled: !!feedId,
  });
}

/**
 * Hook to get usage statistics
 */
export function useUsageStats(days = 30) {
  return useQuery({
    queryKey: researchKeys.stats(days),
    queryFn: async () => {
      const response = await api.getUsageStats(days);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to create a research task
 */
export function useCreateResearchTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskData: ResearchTaskCreate) => {
      const response = await api.createResearchTask(taskData);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
      toast.success('Research task created');
    },
    onError: (error: Error) => {
      toast.error(`Failed to create task: ${error.message}`);
    },
  });
}

/**
 * Hook to create batch research tasks
 */
export function useCreateBatchTasks() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (batchData: ResearchTaskBatchCreate) => {
      const response = await api.createBatchTasks(batchData);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
      toast.success(`Created ${data.length} research tasks`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create batch: ${error.message}`);
    },
  });
}

// ============================================================================
// Template Hooks
// ============================================================================

/**
 * Hook to list available templates
 */
export function useResearchTemplates(includePublic = true) {
  return useQuery({
    queryKey: researchKeys.templates(),
    queryFn: async () => {
      const response = await api.listTemplates(includePublic);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    staleTime: 1000 * 60 * 60, // 1 hour (templates rarely change)
  });
}

/**
 * Hook to get a specific template
 */
export function useResearchTemplate(templateId: number | undefined) {
  return useQuery({
    queryKey: researchKeys.template(templateId!),
    queryFn: async () => {
      const response = await api.getTemplate(templateId!);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    enabled: templateId !== undefined,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

/**
 * Hook to apply a template
 */
export function useApplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      templateId,
      applyData,
    }: {
      templateId: number;
      applyData: TemplateApply;
    }) => {
      const response = await api.applyTemplate(templateId, applyData);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
      toast.success('Template applied - research task created');
    },
    onError: (error: Error) => {
      toast.error(`Failed to apply template: ${error.message}`);
    },
  });
}

/**
 * Hook to list research functions
 */
export function useResearchFunctions() {
  return useQuery({
    queryKey: researchKeys.functions(),
    queryFn: async () => {
      const response = await api.listResearchFunctions();
      if (response.error) throw new Error(response.error);
      return response.data!.functions;
    },
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

// ============================================================================
// Cancel, Retry, Sources, Export Hooks
// ============================================================================

/**
 * Hook to cancel a research task
 */
export function useCancelResearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await api.cancelResearchTask(taskId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.task(data.task_id) });
      queryClient.invalidateQueries({ queryKey: researchKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
      toast.success('Research task cancelled');
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel task: ${error.message}`);
    },
  });
}

/**
 * Hook to retry a failed research task
 */
export function useRetryResearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await api.retryResearchTask(taskId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.task(data.original_task_id) });
      queryClient.invalidateQueries({ queryKey: researchKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
      toast.success(`Research task retried - new task #${data.new_task_id}`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to retry task: ${error.message}`);
    },
  });
}

/**
 * Hook to get sources for a research task
 */
export function useResearchSources(taskId: number | undefined) {
  return useQuery({
    queryKey: researchKeys.sources(taskId!),
    queryFn: async () => {
      const response = await api.getResearchSources(taskId!);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    enabled: taskId !== undefined,
    staleTime: 1000 * 60 * 30, // 30 minutes (sources don't change)
  });
}

/**
 * Hook to export a research task
 */
export function useExportResearch() {
  return useMutation({
    mutationFn: async ({
      taskId,
      format,
      options,
    }: {
      taskId: number;
      format: ExportFormat;
      options?: Omit<ExportRequest, 'format'>;
    }) => {
      const response = await api.exportResearchTask(taskId, format, options);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    onSuccess: (data) => {
      // Create and download the file
      const blob = new Blob([data.content], { type: data.mime_type });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success(`Exported as ${data.format.toUpperCase()}`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to export: ${error.message}`);
    },
  });
}
