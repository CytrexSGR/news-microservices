/**
 * React Query Hooks for Strategy Lab API (SuperTrader Engine)
 *
 * Provides real-time strategy lab data with automatic polling.
 * All requests go through Vite proxy: /api/prediction → http://localhost:8116/api
 */

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = '/api/prediction/v1/strategy-lab'
const AGENT_KEY = 'supertrader-dev-key'

const labApi = axios.create({
  headers: { 'X-Agent-Key': AGENT_KEY },
})

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface IndexComponent {
  symbol: string
  weight: number
  source?: string
}

export interface CustomIndex {
  id: string
  name: string
  type: string
  version: number
  description: string
  components: IndexComponent[]
  created_at: string
  updated_at?: string
}

export interface RoutingCell {
  strategy: string
  weight: number
  parameters?: Record<string, unknown>
}

export interface RoutingMatrix {
  [symbolGroup: string]: {
    [regime: string]: RoutingCell
  }
}

export interface StrategyPortfolio {
  id: string
  version: string
  name: string
  routing_matrix: RoutingMatrix
  score: number
  is_champion: boolean
  created_at: string
  updated_at?: string
  metrics?: Record<string, number>
}

export interface ExperimentVariant {
  id: string
  name: string
  portfolio_version: string
  metrics?: Record<string, number>
}

export interface StrategyExperiment {
  experiment_id: string
  hypothesis: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  variants: ExperimentVariant[]
  created_at: string
  completed_at?: string
  result_summary?: string
}

export interface BacktestResult {
  id: string
  portfolio_version: string
  period: string
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  completed_at: string
}

export interface SymbolGroup {
  name: string
  symbols: string[]
  description?: string
}

export interface ChampionInfo {
  version: string
  score: number
  promoted_at: string
  portfolio: StrategyPortfolio
}

export interface RankingEntry {
  version: string
  score: number
  rank: number
  is_champion: boolean
}

// ---------------------------------------------------------------------------
// Query key factory
// ---------------------------------------------------------------------------

export const labKeys = {
  all: ['strategy-lab'] as const,
  indices: () => [...labKeys.all, 'indices'] as const,
  portfolios: () => [...labKeys.all, 'portfolios'] as const,
  champion: () => [...labKeys.all, 'champion'] as const,
  ranking: () => [...labKeys.all, 'ranking'] as const,
  experiments: (status?: string) => [...labKeys.all, 'experiments', status] as const,
  experiment: (id: string) => [...labKeys.all, 'experiment', id] as const,
  backtests: () => [...labKeys.all, 'backtests'] as const,
  symbolGroups: () => [...labKeys.all, 'symbol-groups'] as const,
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/** Custom indices register. Polls every 30s. */
export function useIndices() {
  return useQuery<CustomIndex[]>({
    queryKey: labKeys.indices(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/indices')
      return Array.isArray(data) ? data : data?.indices ?? []
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

/** All strategy portfolios. Polls every 30s. */
export function usePortfolios() {
  return useQuery<StrategyPortfolio[]>({
    queryKey: labKeys.portfolios(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/portfolios')
      return Array.isArray(data) ? data : data?.portfolios ?? []
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

/** Current champion portfolio. Polls every 30s. */
export function useChampion() {
  return useQuery<ChampionInfo>({
    queryKey: labKeys.champion(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/champion')
      return data
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

/** Portfolio ranking by score. Polls every 60s. */
export function useRanking() {
  return useQuery<RankingEntry[]>({
    queryKey: labKeys.ranking(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/ranking')
      return Array.isArray(data) ? data : data?.ranking ?? []
    },
    refetchInterval: 60_000,
    staleTime: 50_000,
    retry: 2,
  })
}

/** Experiments list, optionally filtered by status. Polls every 15s. */
export function useExperiments(status?: string) {
  return useQuery<StrategyExperiment[]>({
    queryKey: labKeys.experiments(status),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/experiments', {
        params: status ? { status } : undefined,
      })
      return Array.isArray(data) ? data : data?.experiments ?? []
    },
    refetchInterval: 15_000,
    staleTime: 10_000,
    retry: 2,
  })
}

/** Single experiment detail. Polls every 10s. */
export function useExperiment(id: string) {
  return useQuery<StrategyExperiment>({
    queryKey: labKeys.experiment(id),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/experiments/' + id)
      return data
    },
    refetchInterval: 10_000,
    staleTime: 8_000,
    retry: 2,
    enabled: !!id,
  })
}

/** Backtest results across portfolios. Polls every 30s. */
export function useBacktestResults() {
  return useQuery<BacktestResult[]>({
    queryKey: labKeys.backtests(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/backtests')
      return Array.isArray(data) ? data : data?.results ?? []
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    retry: 2,
  })
}

/** Symbol groups configuration. Polls every 60s. */
export function useSymbolGroups() {
  return useQuery<SymbolGroup[]>({
    queryKey: labKeys.symbolGroups(),
    queryFn: async () => {
      const { data } = await labApi.get(API_BASE + '/symbol-groups')
      return Array.isArray(data) ? data : data?.groups ?? []
    },
    refetchInterval: 60_000,
    staleTime: 50_000,
    retry: 2,
  })
}
