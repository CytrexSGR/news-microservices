/**
 * React Query Hooks for Agent Control API (SuperTrader Engine)
 *
 * Provides real-time trading data with automatic polling.
 * All requests go through Vite proxy: /api/prediction → http://localhost:8116/api
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = '/api/prediction/v1/agent-control'
const AGENT_KEY = 'supertrader-dev-key'

const agentApi = axios.create({
  headers: { 'X-Agent-Key': AGENT_KEY },
})

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentPosition {
  symbol: string
  direction: 'LONG' | 'SHORT'
  entry_price: number
  current_price: number
  unrealized_pnl: number
  size: number
  size_usd?: number
  stop_loss: number
  take_profit: number
  trailing_activated: boolean
  leverage?: number
  confidence?: number
  entry_time?: string
  pnl_pct?: number
}

export interface CircuitBreaker {
  type: string
  reason: string
  expires_at?: string
}

export interface AgentState {
  engine_status: string
  paused: boolean
  tick_count: number
  portfolio: {
    capital: number
    peak_capital: number
    initial_capital?: number
    unrealized_pnl?: number
  }
  open_positions: number
  active_breakers: CircuitBreaker[]
  [key: string]: unknown
}

export interface RiskStatus {
  portfolio: {
    capital: number
    peak_capital: number
    drawdown_pct: number
  }
  circuit_breakers: CircuitBreaker[]
  position_size_multiplier: number
  trading_blocked: boolean
}

export interface Decision {
  timestamp: string
  symbol: string
  decision: string
  reason: string | Record<string, unknown>
  confidence: number
  executed: boolean
}

export interface AgentConfig {
  paused: boolean
  watchlist: string[]
  max_positions: number
  risk_per_trade_pct: number
  max_size_usd: number
  max_leverage: number
  direction_bias: string
  tick_interval_seconds: number
  hard_limits?: {
    max_risk_per_trade: number
    max_positions: number
    max_size_usd: number
    max_leverage: number
  }
  [key: string]: unknown
}

export interface ConfigUpdate {
  max_positions?: number
  risk_per_trade_pct?: number
  max_size_usd?: number
  max_leverage?: number
  direction_bias?: string
  tick_interval_seconds?: number
}

export interface PaperTrade {
  id: string
  symbol: string
  direction: 'LONG' | 'SHORT'
  entry_price: number
  exit_price: number
  pnl: number
  pnl_pct: number
  exit_reason?: string
  entry_time?: string
  exit_time?: string
  size?: number
  confidence?: number
  reasoning?: string
}

// ---------------------------------------------------------------------------
// Query key factory
// ---------------------------------------------------------------------------

export const agentKeys = {
  all: ['agent-control'] as const,
  state: () => [...agentKeys.all, 'state'] as const,
  positions: () => [...agentKeys.all, 'positions'] as const,
  riskStatus: () => [...agentKeys.all, 'risk-status'] as const,
  decisionLog: (since: string) => [...agentKeys.all, 'decisions', since] as const,
  config: () => [...agentKeys.all, 'config'] as const,
  trades: () => [...agentKeys.all, 'trades'] as const,
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/** Engine state + portfolio summary. Polls every 5s. */
export function useAgentState() {
  return useQuery<AgentState>({
    queryKey: agentKeys.state(),
    queryFn: async () => {
      const { data } = await agentApi.get(API_BASE + '/state')
      return data
    },
    refetchInterval: 5_000,
    staleTime: 3_000,
    retry: 2,
  })
}

/** Open positions with live PnL. Polls every 5s. */
export function useAgentPositions() {
  return useQuery<AgentPosition[]>({
    queryKey: agentKeys.positions(),
    queryFn: async () => {
      const { data } = await agentApi.get(API_BASE + '/positions')
      return data
    },
    refetchInterval: 5_000,
    staleTime: 3_000,
    retry: 2,
  })
}

/** Risk metrics + circuit breakers. Polls every 10s. */
export function useAgentRiskStatus() {
  return useQuery<RiskStatus>({
    queryKey: agentKeys.riskStatus(),
    queryFn: async () => {
      const { data } = await agentApi.get(API_BASE + '/risk-status')
      return data
    },
    refetchInterval: 10_000,
    staleTime: 8_000,
    retry: 2,
  })
}

/** Decision log. Polls every 15s. */
export function useAgentDecisionLog(since: string = '24h') {
  return useQuery<Decision[]>({
    queryKey: agentKeys.decisionLog(since),
    queryFn: async () => {
      const { data } = await agentApi.get(API_BASE + '/decision-log', {
        params: { since },
      })
      return Array.isArray(data) ? data : data?.decisions ?? []
    },
    refetchInterval: 15_000,
    staleTime: 10_000,
    retry: 2,
  })
}

/** Engine config. Polls every 30s. */
export function useAgentConfig() {
  return useQuery<AgentConfig>({
    queryKey: agentKeys.config(),
    queryFn: async () => {
      const { data } = await agentApi.get(API_BASE + '/config')
      return data
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

export interface ShadowTradesResponse {
  shadow_trades: PaperTrade[]
  total: number
  total_blocked: number
  would_have_won: number
  would_have_lost: number
}

/** Shadow trades (tracked trades). Polls every 30s. */
export function useAgentTrades() {
  return useQuery<ShadowTradesResponse>({
    queryKey: agentKeys.trades(),
    queryFn: async () => {
      const { data } = await agentApi.get('/api/prediction/v1/ml/shadow-trades')
      return data
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useAgentPause() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await agentApi.post(API_BASE + '/pause')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.state() })
      qc.invalidateQueries({ queryKey: agentKeys.config() })
    },
  })
}

export function useAgentResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await agentApi.post(API_BASE + '/resume')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.state() })
      qc.invalidateQueries({ queryKey: agentKeys.config() })
    },
  })
}

/** Update engine config (partial). */
export function useUpdateConfig() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (update: ConfigUpdate) => {
      const { data } = await agentApi.patch(API_BASE + '/config', update)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.config() })
      qc.invalidateQueries({ queryKey: agentKeys.state() })
    },
  })
}

/** Update trading capital directly. */
export function useUpdateCapital() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (capital: number) => {
      const { data } = await agentApi.patch(API_BASE + '/capital', { capital })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.state() })
      qc.invalidateQueries({ queryKey: agentKeys.riskStatus() })
    },
  })
}

/** Emergency stop: close all positions + lock trading. */
export function useEmergencyStop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await agentApi.post(API_BASE + '/emergency-stop')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.all })
    },
  })
}

/** Unlock trading after emergency stop. Engine stays paused. */
export function useEmergencyReset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await agentApi.post(API_BASE + '/emergency-reset')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: agentKeys.all })
    },
  })
}
