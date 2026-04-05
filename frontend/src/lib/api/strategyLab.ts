/**
 * Strategy Lab API Client
 *
 * Connects to prediction-service (Port 8116) for:
 * - Strategy CRUD operations
 * - Formula validation
 * - Backtesting
 * - Walk-forward validation
 * - Parameter optimization
 */

import { strategyLabApi } from '@/api/axios'
import type {
  Strategy,
  StrategyDefinition,
  ValidationResult,
} from '@/types/strategy'
import type {
  BacktestResult,
  BacktestRequest,
  WalkForwardResult,
  WalkForwardRequest,
  OptimizationResult,
  OptimizationRequest,
} from '@/types/backtest'

// ============================================================================
// Note: strategyLabApi is imported from @/api/axios with auth interceptor
// ============================================================================

// ============================================================================
// Strategy CRUD Operations
// ============================================================================

export interface CreateStrategyRequest {
  name: string
  definition: StrategyDefinition
  is_public?: boolean
}

export interface UpdateStrategyRequest {
  name?: string
  definition?: StrategyDefinition
  is_public?: boolean
}

export interface ListStrategiesParams {
  /** Filter by strategy name (partial match) */
  name?: string
  /** Filter by public/private */
  is_public?: boolean
  /** Pagination: skip N results */
  skip?: number
  /** Pagination: limit results */
  limit?: number
}

export interface ListStrategiesResponse {
  strategies: Strategy[]
  total: number
  skip: number
  limit: number
}

export const strategyApi = {
  /**
   * Create a new strategy
   */
  create: async (request: CreateStrategyRequest): Promise<Strategy> => {
    const response = await strategyLabApi.post('/strategies', request)
    return response.data
  },

  /**
   * List all strategies with optional filters
   */
  list: async (params?: ListStrategiesParams): Promise<ListStrategiesResponse> => {
    const response = await strategyLabApi.get('/strategies', { params })
    return response.data
  },

  /**
   * Get a specific strategy by ID
   */
  get: async (strategyId: string): Promise<Strategy> => {
    const response = await strategyLabApi.get(`/strategies/${strategyId}`)
    return response.data
  },

  /**
   * Update an existing strategy
   */
  update: async (strategyId: string, request: UpdateStrategyRequest): Promise<Strategy> => {
    const response = await strategyLabApi.put(`/strategies/${strategyId}`, request)
    return response.data
  },

  /**
   * Delete a strategy
   */
  delete: async (strategyId: string): Promise<void> => {
    await strategyLabApi.delete(`/strategies/${strategyId}`)
  },

  /**
   * Validate strategy formulas (entry/exit conditions, risk management)
   */
  validate: async (strategyId: string): Promise<ValidationResult> => {
    const response = await strategyLabApi.post(`/strategies/${strategyId}/validate`)
    return response.data
  },
}

// ============================================================================
// Backtesting Operations
// ============================================================================

export interface ListBacktestsParams {
  /** Filter by strategy ID */
  strategy_id?: string
  /** Filter by symbol */
  symbol?: string
  /** Pagination */
  skip?: number
  limit?: number
}

export interface ListBacktestsResponse {
  backtests: BacktestResult[]
  total: number
  skip: number
  limit: number
}

export const backtestApi = {
  /**
   * Run a backtest for a strategy
   */
  run: async (request: BacktestRequest): Promise<BacktestResult> => {
    const response = await strategyLabApi.post('/backtests', request)
    return response.data
  },

  /**
   * List all backtests with optional filters
   */
  list: async (params?: ListBacktestsParams): Promise<ListBacktestsResponse> => {
    const response = await strategyLabApi.get('/backtests', { params })
    return response.data
  },

  /**
   * Get a specific backtest result by ID
   */
  get: async (backtestId: string): Promise<BacktestResult> => {
    const response = await strategyLabApi.get(`/backtests/${backtestId}`)
    return response.data
  },

  /**
   * Delete a backtest result
   */
  delete: async (backtestId: string): Promise<void> => {
    await strategyLabApi.delete(`/backtests/${backtestId}`)
  },
}

// ============================================================================
// Walk-Forward Validation Operations
// ============================================================================

export interface ListWalkForwardParams {
  /** Filter by strategy ID */
  strategy_id?: string
  /** Filter by symbol */
  symbol?: string
  /** Pagination */
  skip?: number
  limit?: number
}

export interface ListWalkForwardResponse {
  results: WalkForwardResult[]
  total: number
  skip: number
  limit: number
}

export const walkForwardApi = {
  /**
   * Run walk-forward validation for a strategy
   */
  run: async (request: WalkForwardRequest): Promise<WalkForwardResult> => {
    const response = await strategyLabApi.post('/walk-forward', request)
    return response.data
  },

  /**
   * List all walk-forward validation results
   */
  list: async (params?: ListWalkForwardParams): Promise<ListWalkForwardResponse> => {
    const response = await strategyLabApi.get('/walk-forward', { params })
    return response.data
  },

  /**
   * Get a specific walk-forward result by ID
   */
  get: async (walkForwardId: string): Promise<WalkForwardResult> => {
    const response = await strategyLabApi.get(`/walk-forward/${walkForwardId}`)
    return response.data
  },

  /**
   * Delete a walk-forward result
   */
  delete: async (walkForwardId: string): Promise<void> => {
    await strategyLabApi.delete(`/walk-forward/${walkForwardId}`)
  },
}

// ============================================================================
// Parameter Optimization Operations
// ============================================================================

export interface ListOptimizationsParams {
  /** Filter by base strategy ID */
  base_strategy_id?: string
  /** Filter by symbol */
  symbol?: string
  /** Pagination */
  skip?: number
  limit?: number
}

export interface ListOptimizationsResponse {
  optimizations: OptimizationResult[]
  total: number
  skip: number
  limit: number
}

export const optimizationApi = {
  /**
   * Run parameter optimization for a strategy
   */
  run: async (request: OptimizationRequest): Promise<OptimizationResult> => {
    const response = await strategyLabApi.post('/optimize', request)
    return response.data
  },

  /**
   * List all optimization results
   */
  list: async (params?: ListOptimizationsParams): Promise<ListOptimizationsResponse> => {
    const response = await strategyLabApi.get('/optimizations', { params })
    return response.data
  },

  /**
   * Get a specific optimization result by ID
   */
  get: async (optimizationId: string): Promise<OptimizationResult> => {
    const response = await strategyLabApi.get(`/optimizations/${optimizationId}`)
    return response.data
  },

  /**
   * Delete an optimization result
   */
  delete: async (optimizationId: string): Promise<void> => {
    await strategyLabApi.delete(`/optimizations/${optimizationId}`)
  },
}

// ============================================================================
// Convenience Export
// ============================================================================

export const strategyLabClient = {
  strategy: strategyApi,
  backtest: backtestApi,
  walkForward: walkForwardApi,
  optimization: optimizationApi,
}

export default strategyLabClient
