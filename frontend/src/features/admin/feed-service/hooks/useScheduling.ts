import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getScheduleTimeline,
  getDistributionStats,
  optimizeSchedule,
  detectConflicts,
  getSchedulingStats,
  rescheduleFeed,
} from '@/lib/api/feedServiceAdmin'
import type {
  ScheduleTimeline,
  DistributionStats,
  OptimizationResult,
  ConflictAnalysis,
  SchedulingStats,
  RescheduleResponse,
} from '@/types/feedServiceAdmin'
import toast from 'react-hot-toast'

/**
 * Hook to fetch schedule timeline for visualization
 * @param hours - Number of hours to look ahead (default: 24)
 * @param refetchInterval - Auto-refresh interval in milliseconds
 */
export const useScheduleTimeline = (hours: number = 24, refetchInterval?: number) => {
  return useQuery<ScheduleTimeline>({
    queryKey: ['feed-service', 'scheduling', 'timeline', hours],
    queryFn: () => getScheduleTimeline(hours),
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

/**
 * Hook to fetch distribution statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds
 */
export const useDistributionStats = (refetchInterval?: number) => {
  return useQuery<DistributionStats>({
    queryKey: ['feed-service', 'scheduling', 'distribution'],
    queryFn: getDistributionStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

/**
 * Hook to fetch scheduling conflicts
 * @param refetchInterval - Auto-refresh interval in milliseconds
 */
export const useSchedulingConflicts = (refetchInterval?: number) => {
  return useQuery<ConflictAnalysis>({
    queryKey: ['feed-service', 'scheduling', 'conflicts'],
    queryFn: detectConflicts,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

/**
 * Hook to fetch comprehensive scheduling statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds
 */
export const useSchedulingStats = (refetchInterval?: number) => {
  return useQuery<SchedulingStats>({
    queryKey: ['feed-service', 'scheduling', 'stats'],
    queryFn: getSchedulingStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

/**
 * Hook to trigger schedule optimization
 * Invalidates all scheduling queries after success
 */
export const useOptimizeSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation<OptimizationResult, Error, boolean>({
    mutationFn: (apply: boolean) => optimizeSchedule(apply),
    onSuccess: (data, apply) => {
      // Invalidate all scheduling queries
      queryClient.invalidateQueries({ queryKey: ['feed-service', 'scheduling'] })

      // Show success toast
      if (apply) {
        toast.success(
          `Schedule optimized! ${data.feeds_optimized} feeds adjusted. ` +
          `Max concurrent reduced from ${data.before.max_concurrent} to ${data.after.max_concurrent} ` +
          `(${data.improvement_percentage}% improvement)`
        )
      } else {
        toast.success('Preview generated successfully')
      }
    },
    onError: (error) => {
      toast.error(`Optimization failed: ${error.message}`)
    },
  })
}

/**
 * Hook to reschedule a specific feed
 * Invalidates all scheduling queries after success
 */
export const useRescheduleFeed = () => {
  const queryClient = useQueryClient()

  return useMutation<RescheduleResponse, Error, { feedId: string; offsetMinutes: number }>({
    mutationFn: ({ feedId, offsetMinutes }) => rescheduleFeed(feedId, offsetMinutes),
    onSuccess: (data) => {
      // Invalidate all scheduling queries
      queryClient.invalidateQueries({ queryKey: ['feed-service', 'scheduling'] })

      // Show success toast
      toast.success(`${data.feed_name} rescheduled successfully`)
    },
    onError: (error) => {
      toast.error(`Rescheduling failed: ${error.message}`)
    },
  })
}
