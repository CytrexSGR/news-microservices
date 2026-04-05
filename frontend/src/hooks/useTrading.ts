/**
 * Trading Hooks - TanStack Query hooks for trading data
 *
 * Provides real-time data fetching for:
 * - Positions
 * - Portfolio
 * - System status
 *
 * With automatic refetching and mutations for actions.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tradingApi } from '@/lib/api/trading'

// ============================================================================
// Queries
// ============================================================================

/**
 * Get all positions with auto-refresh every 5 seconds
 */
export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: tradingApi.getPositions,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

/**
 * Get only open positions with auto-refresh every 5 seconds
 */
export function useOpenPositions() {
  return useQuery({
    queryKey: ['positions', 'open'],
    queryFn: tradingApi.getOpenPositions,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

/**
 * Get portfolio summary with auto-refresh every 5 seconds
 */
export function usePortfolio() {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: tradingApi.getPortfolio,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

/**
 * Get system status with auto-refresh every 10 seconds
 */
export function useSystemStatus() {
  return useQuery({
    queryKey: ['systemStatus'],
    queryFn: tradingApi.getSystemStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

// ============================================================================
// Mutations
// ============================================================================

/**
 * Close a specific position
 */
export function useClosePosition() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tradingApi.closePosition,
    onSuccess: () => {
      // Invalidate and refetch position data
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
  })
}

/**
 * Panic button - Close ALL positions
 */
export function useCloseAllPositions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tradingApi.closeAllPositions,
    onSuccess: () => {
      // Invalidate and refetch all data
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
  })
}

/**
 * Stop trading (halt signal processing)
 */
export function useStopTrading() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tradingApi.stopTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] })
    },
  })
}

/**
 * Resume trading
 */
export function useResumeTrading() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tradingApi.resumeTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] })
    },
  })
}
