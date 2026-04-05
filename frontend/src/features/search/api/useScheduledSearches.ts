/**
 * useScheduledSearches Hooks
 *
 * Query and mutation hooks for managing scheduled searches.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import toast from 'react-hot-toast';
import type {
  ScheduledSearch,
  ScheduledSearchListResponse,
  ScheduleConfig,
} from '../types/search.types';
import { savedSearchKeys } from './useSavedSearches';

// =============================================================================
// Query Keys
// =============================================================================

export const scheduledSearchKeys = {
  all: ['scheduled-searches'] as const,
  list: () => [...scheduledSearchKeys.all, 'list'] as const,
  detail: (id: string) => [...scheduledSearchKeys.all, 'detail', id] as const,
  history: (id: string) => [...scheduledSearchKeys.all, 'history', id] as const,
};

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch all scheduled searches
 */
const fetchScheduledSearches = async (): Promise<ScheduledSearchListResponse> => {
  const { data } = await searchApi.get<ScheduledSearchListResponse>(
    '/search/saved',
    { params: { is_scheduled: true } }
  );
  return data;
};

/**
 * Get execution history for a scheduled search
 */
const fetchScheduleHistory = async (
  id: string
): Promise<Array<{
  executed_at: string;
  result_count: number;
  execution_time_ms: number;
  success: boolean;
  error?: string;
}>> => {
  const { data } = await searchApi.get(`/search/saved/${id}/history`);
  return data;
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to fetch all scheduled searches
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useScheduledSearches();
 *
 * if (isLoading) return <Loading />;
 *
 * return (
 *   <div>
 *     {data.items.map(search => (
 *       <ScheduledSearchCard key={search.id} search={search} />
 *     ))}
 *   </div>
 * );
 * ```
 */
export function useScheduledSearches() {
  return useQuery<ScheduledSearchListResponse>({
    queryKey: scheduledSearchKeys.list(),
    queryFn: fetchScheduledSearches,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to get scheduled searches with upcoming runs
 *
 * Sorted by next_run time
 */
export function useUpcomingScheduledSearches(limit = 5) {
  return useQuery<ScheduledSearch[]>({
    queryKey: [...scheduledSearchKeys.list(), 'upcoming', limit],
    queryFn: async () => {
      const { data } = await searchApi.get<ScheduledSearchListResponse>(
        '/search/saved',
        {
          params: {
            is_scheduled: true,
            sort_by: 'next_run',
            sort_order: 'asc',
            limit,
          },
        }
      );
      return data.items;
    },
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to get execution history for a scheduled search
 *
 * @param id - Saved search ID
 *
 * @example
 * ```tsx
 * const { data: history } = useScheduleHistory('123');
 *
 * history?.map(run => (
 *   <div key={run.executed_at}>
 *     {run.executed_at}: {run.result_count} results
 *   </div>
 * ));
 * ```
 */
export function useScheduleHistory(id: string | undefined) {
  return useQuery({
    queryKey: scheduledSearchKeys.history(id || ''),
    queryFn: () => fetchScheduleHistory(id!),
    enabled: !!id,
    staleTime: 60000, // 1 minute
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to schedule a saved search
 *
 * @example
 * ```tsx
 * const { mutate: scheduleSearch } = useScheduleSearch();
 *
 * scheduleSearch({
 *   id: '123',
 *   config: {
 *     frequency: 'daily',
 *     hour: 9,
 *     timezone: 'Europe/Berlin',
 *   },
 * });
 * ```
 */
export function useScheduleSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      config,
    }: {
      id: string;
      config: ScheduleConfig;
    }) => {
      // Convert config to cron expression
      const cron = configToCron(config);

      const { data } = await searchApi.patch<ScheduledSearch>(
        `/search/saved/${id}/schedule`,
        {
          is_scheduled: true,
          schedule_cron: cron,
        }
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: scheduledSearchKeys.list() });
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      queryClient.setQueryData(
        savedSearchKeys.detail(Number(data.id)),
        data
      );
      toast.success(`Search "${data.name}" scheduled successfully`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to schedule search');
    },
  });
}

/**
 * Hook to unschedule a search
 *
 * @example
 * ```tsx
 * const { mutate: unschedule } = useUnscheduleSearch();
 * unschedule('123');
 * ```
 */
export function useUnscheduleSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await searchApi.patch<ScheduledSearch>(
        `/search/saved/${id}/schedule`,
        { is_scheduled: false }
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: scheduledSearchKeys.list() });
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success(`Schedule removed for "${data.name}"`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to remove schedule');
    },
  });
}

/**
 * Hook to run a scheduled search immediately
 *
 * Triggers execution outside of the normal schedule.
 *
 * @example
 * ```tsx
 * const { mutate: runNow, isPending } = useRunScheduledSearchNow();
 *
 * <Button onClick={() => runNow('123')} disabled={isPending}>
 *   Run Now
 * </Button>
 * ```
 */
export function useRunScheduledSearchNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await searchApi.post(`/search/saved/${id}/execute`);
      return data;
    },
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({
        queryKey: scheduledSearchKeys.history(id),
      });
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success(`Search executed: ${data.total} results found`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to run search');
    },
  });
}

/**
 * Hook to update schedule configuration
 */
export function useUpdateScheduleConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      config,
    }: {
      id: string;
      config: ScheduleConfig;
    }) => {
      const cron = configToCron(config);
      const { data } = await searchApi.patch<ScheduledSearch>(
        `/search/saved/${id}/schedule`,
        { schedule_cron: cron }
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: scheduledSearchKeys.list() });
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success(`Schedule updated for "${data.name}"`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update schedule');
    },
  });
}

// =============================================================================
// Utilities
// =============================================================================

/**
 * Convert schedule config to cron expression
 */
function configToCron(config: ScheduleConfig): string {
  if (config.frequency === 'custom' && config.cron) {
    return config.cron;
  }

  const hour = config.hour ?? 9;
  const dayOfWeek = config.day_of_week ?? 1;

  switch (config.frequency) {
    case 'hourly':
      return '0 * * * *';
    case 'daily':
      return `0 ${hour} * * *`;
    case 'weekly':
      return `0 ${hour} * * ${dayOfWeek}`;
    default:
      return '0 9 * * *'; // Default to daily at 9am
  }
}

/**
 * Parse cron expression to schedule config
 */
export function cronToConfig(cron: string): ScheduleConfig {
  const parts = cron.split(' ');

  if (parts.length !== 5) {
    return { frequency: 'custom', cron };
  }

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Hourly: 0 * * * *
  if (minute === '0' && hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return { frequency: 'hourly' };
  }

  // Daily: 0 H * * *
  if (minute === '0' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return {
      frequency: 'daily',
      hour: parseInt(hour, 10),
    };
  }

  // Weekly: 0 H * * D
  if (minute === '0' && dayOfMonth === '*' && month === '*') {
    return {
      frequency: 'weekly',
      hour: parseInt(hour, 10),
      day_of_week: parseInt(dayOfWeek, 10),
    };
  }

  return { frequency: 'custom', cron };
}

/**
 * Get human-readable description of schedule
 */
export function describeSchedule(config: ScheduleConfig): string {
  switch (config.frequency) {
    case 'hourly':
      return 'Every hour';
    case 'daily':
      return `Daily at ${config.hour ?? 9}:00`;
    case 'weekly':
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const day = days[config.day_of_week ?? 1];
      return `Every ${day} at ${config.hour ?? 9}:00`;
    case 'custom':
      return `Custom: ${config.cron}`;
    default:
      return 'Not scheduled';
  }
}
