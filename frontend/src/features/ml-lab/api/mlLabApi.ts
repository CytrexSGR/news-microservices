/**
 * ML Lab API Client
 *
 * Provides typed API calls for the ML Lab Gatekeeper functionality.
 * Includes model management, training, gate config, live inference, and shadow trading.
 */

import { predictionApi } from '@/api/axios';
import {
  MLArea,
  ModelStatus,
  TrainingStatus,
  type MLModel,
  type MLModelCreate,
  type MLModelUpdate,
  type MLModelListResponse,
  type TrainingConfig,
  type TrainingJobStart,
  type TrainingJob,
  type TrainingJobListResponse,
  type GateConfig,
  type GateConfigUpdate,
  type GateConfigListResponse,
  type DashboardResponse,
  type LiveInferenceRequest,
  type LiveInferenceResponse,
  type LiveStatusResponse,
  type ShadowTradeCreate,
  type ShadowTradeCloseRequest,
  type ShadowTrade,
  type ShadowTradeStats,
  type LegacyShadowTrade,
  type LegacyShadowTradeListResponse,
  type Alert,
  // Live Paper Trading types (centralized in types/index.ts)
  type TradingMode,
  type ForceTradeResponse,
  type LiveTradingStats,
  type LiveTradingTickResult,
  type LiveTradingSession,
  type LiveIndicatorsResponse,
  type IndicatorValue,
  // Multi-session types
  type LiveTradingSessionsResponse,
  type LiveTradingStatusResponse,
  type LiveTradingStopResponse,
  type LiveTradingTickResponse,
  // Backtest types
  type BacktestConfig,
  type BacktestStartResponse,
  type BacktestStatus,
  type BacktestResultResponse,
  type BacktestSummary,
  // Strategy-Centric Trading types
  type ExecutionMode,
  type ExecutionStatus,
  type TradingStrategy,
  type TradingStrategyCreate,
  type TradingStrategyUpdate,
  type StrategyListResponse,
  type StrategyExecution,
  type StrategyExecutionStart,
  type StrategyExecutionListResponse,
  // Auto-test types
  type AutoTestResults,
} from '../types';

// Re-export types for convenience
export * from '../types';

const BASE_URL = '/ml';

// ============================================================================
// Models API
// ============================================================================

export const modelsApi = {
  async list(params?: {
    area?: MLArea;
    status?: ModelStatus;
    limit?: number;
    offset?: number;
  }): Promise<MLModelListResponse> {
    const response = await predictionApi.get(`${BASE_URL}/models`, { params });
    return response.data;
  },

  async get(modelId: string): Promise<MLModel> {
    const response = await predictionApi.get(`${BASE_URL}/models/${modelId}`);
    return response.data;
  },

  async create(data: MLModelCreate): Promise<MLModel> {
    const response = await predictionApi.post(`${BASE_URL}/models`, data);
    return response.data;
  },

  async update(modelId: string, data: MLModelUpdate): Promise<MLModel> {
    const response = await predictionApi.put(`${BASE_URL}/models/${modelId}`, data);
    return response.data;
  },

  async delete(modelId: string): Promise<void> {
    await predictionApi.delete(`${BASE_URL}/models/${modelId}`);
  },

  async activate(modelId: string): Promise<{ message: string }> {
    const response = await predictionApi.post(`${BASE_URL}/models/${modelId}/activate`);
    return response.data;
  },

  async deactivate(modelId: string): Promise<{ message: string }> {
    const response = await predictionApi.post(`${BASE_URL}/models/${modelId}/deactivate`);
    return response.data;
  },
};

// ============================================================================
// Areas API
// ============================================================================

export const areasApi = {
  async list(): Promise<string[]> {
    const response = await predictionApi.get(`${BASE_URL}/areas`);
    return response.data;
  },

  async getActiveModel(area: MLArea): Promise<MLModel | null> {
    const response = await predictionApi.get(`${BASE_URL}/areas/${area}/active`);
    return response.data;
  },
};

// ============================================================================
// Training API
// ============================================================================

export const trainingApi = {
  async start(data: TrainingJobStart): Promise<TrainingJob> {
    const response = await predictionApi.post(`${BASE_URL}/training/start`, data);
    return response.data;
  },

  async list(params?: {
    model_id?: string;
    status?: TrainingStatus;
    limit?: number;
    offset?: number;
  }): Promise<TrainingJobListResponse> {
    const response = await predictionApi.get(`${BASE_URL}/training`, { params });
    return response.data;
  },

  async get(jobId: string): Promise<TrainingJob> {
    const response = await predictionApi.get(`${BASE_URL}/training/${jobId}`);
    return response.data;
  },

  async cancel(jobId: string): Promise<TrainingJob> {
    const response = await predictionApi.post(`${BASE_URL}/training/${jobId}/cancel`);
    return response.data;
  },
};

// ============================================================================
// Gate Config API
// ============================================================================

export const gateConfigApi = {
  async list(): Promise<GateConfigListResponse> {
    const response = await predictionApi.get(`${BASE_URL}/config`);
    return response.data;
  },

  async get(area: MLArea): Promise<GateConfig> {
    const response = await predictionApi.get(`${BASE_URL}/config/areas/${area}`);
    return response.data;
  },

  async update(area: MLArea, data: GateConfigUpdate): Promise<GateConfig> {
    const response = await predictionApi.put(`${BASE_URL}/config/areas/${area}`, data);
    return response.data;
  },
};

// ============================================================================
// Dashboard API
// ============================================================================

export const dashboardApi = {
  async get(): Promise<DashboardResponse> {
    const response = await predictionApi.get(`${BASE_URL}/dashboard`);
    return response.data;
  },
};

// ============================================================================
// Live Inference API
// ============================================================================

export const liveInferenceApi = {
  async getStatus(): Promise<LiveStatusResponse> {
    const response = await predictionApi.get(`${BASE_URL}/live/status`);
    return response.data;
  },

  async predict(request: LiveInferenceRequest): Promise<LiveInferenceResponse> {
    const response = await predictionApi.post(`${BASE_URL}/live/inference`, request);
    return response.data;
  },

  async reloadModels(): Promise<{ message: string; models_loaded: number }> {
    const response = await predictionApi.post(`${BASE_URL}/live/reload`);
    return response.data;
  },
};

// ============================================================================
// Live Paper Trading API
// Types are now centralized in types/index.ts
// ============================================================================

export const liveTradingApi = {
  /**
   * Start paper trading for a specific symbol.
   * Supports up to 10 parallel sessions for different coins.
   *
   * @param symbol - Trading symbol (e.g., XRPUSDT)
   * @param timeframe - Candle timeframe (e.g., 5min)
   * @param mode - Trading mode: 'live' (ML gates decide), 'test' (force trades), 'backtest' (historical)
   */
  async start(
    symbol: string = 'XRPUSDT',
    timeframe: string = '5min',
    mode: TradingMode = 'live'
  ): Promise<{ status: string; message: string; stats: LiveTradingStats }> {
    const response = await predictionApi.post(`${BASE_URL}/live-trading/start`, null, {
      params: { symbol, timeframe, mode }
    });
    return response.data;
  },

  /**
   * Stop paper trading.
   * @param symbol - Optional: stop specific symbol. If undefined, stops ALL sessions.
   */
  async stop(symbol?: string): Promise<LiveTradingStopResponse> {
    const response = await predictionApi.post(`${BASE_URL}/live-trading/stop`, null, {
      params: symbol ? { symbol } : {}
    });
    return response.data;
  },

  /**
   * Get trading status.
   * @param symbol - Optional: get status for specific symbol. If undefined, returns ALL sessions.
   */
  async getStatus(symbol?: string): Promise<LiveTradingStatusResponse> {
    const response = await predictionApi.get(`${BASE_URL}/live-trading/status`, {
      params: symbol ? { symbol } : {}
    });
    return response.data;
  },

  /**
   * List all active trading sessions with full details.
   */
  async getSessions(): Promise<LiveTradingSessionsResponse> {
    const response = await predictionApi.get(`${BASE_URL}/live-trading/sessions`);
    return response.data;
  },

  /**
   * Trigger a trading tick.
   * @param symbol - Optional: tick specific symbol. If undefined, ticks ALL running sessions.
   */
  async tick(symbol?: string): Promise<LiveTradingTickResponse> {
    const response = await predictionApi.post(`${BASE_URL}/live-trading/tick`, null, {
      params: symbol ? { symbol } : {}
    });
    return response.data;
  },

  /**
   * Get live indicator values for a symbol.
   */
  async getIndicators(symbol: string = 'XRPUSDT', timeframe: string = '5min'): Promise<LiveIndicatorsResponse> {
    const response = await predictionApi.get(`${BASE_URL}/live-trading/indicators`, {
      params: { symbol, timeframe }
    });
    return response.data;
  },

  /**
   * Force a trade action (TEST mode only).
   * Bypasses ML gate predictions and executes a trade directly.
   *
   * @param symbol - Trading symbol
   * @param action - Trade action: 'enter_long', 'enter_short', or 'exit'
   * @param reason - Optional reason for forcing the trade
   */
  async forceTrade(
    symbol: string,
    action: 'enter_long' | 'enter_short' | 'exit',
    reason: string = 'manual_force'
  ): Promise<ForceTradeResponse> {
    const response = await predictionApi.post(`${BASE_URL}/live-trading/force-trade`, null, {
      params: { symbol, action, reason }
    });
    return response.data;
  },
};

// ============================================================================
// Shadow Trade API (Paper Trading)
// Types for LiveIndicators are now centralized in types/index.ts
// ============================================================================

export const shadowTradeApi = {
  async list(params?: {
    symbol?: string;
    status?: 'open' | 'closed';
    days?: number;
    limit?: number;
    offset?: number;
  }): Promise<{ trades: ShadowTrade[]; total: number }> {
    // Use paper-trades endpoint for actual simulated trades
    const response = await predictionApi.get(`${BASE_URL}/paper-trades`, { params });
    return response.data;
  },

  async get(tradeId: string): Promise<ShadowTrade> {
    const response = await predictionApi.get(`${BASE_URL}/shadow-trades/${tradeId}`);
    return response.data;
  },

  async create(data: ShadowTradeCreate): Promise<ShadowTrade> {
    const response = await predictionApi.post(`${BASE_URL}/shadow-trades`, data);
    return response.data;
  },

  async close(tradeId: string, data: ShadowTradeCloseRequest): Promise<ShadowTrade> {
    const response = await predictionApi.post(`${BASE_URL}/shadow-trades/${tradeId}/close`, data);
    return response.data;
  },

  async getStats(params?: { symbol?: string; days?: number }): Promise<ShadowTradeStats> {
    const response = await predictionApi.get(`${BASE_URL}/shadow-trades/stats`, { params });
    return response.data;
  },

  /**
   * Get open positions from live trading sessions.
   * Uses the shadow-trades/open-positions endpoint which contains actual live trades.
   * Now includes leverage information for each position.
   */
  async getOpenPositions(params?: {
    symbol?: string;
    limit?: number;
  }): Promise<{ positions: ShadowTrade[]; total: number }> {
    const response = await predictionApi.get(`${BASE_URL}/shadow-trades/open-positions`, { params });
    // Map API response to ShadowTrade format with leverage
    const positions = (response.data.open_positions || []).map((p: Record<string, unknown>) => ({
      ...p,
      created_at: p.opened_at, // Map opened_at to created_at for consistency
      leverage: (p.leverage as number) || 1.0,  // Include leverage (default 1.0x)
      status: 'open' as const,
      exit_price: null,
      pnl_pct: null,
      base_pnl_pct: null,
      closed_at: null,
      duration_minutes: null,
    }));
    return { positions, total: positions.length };
  },
};

// ============================================================================
// Legacy Shadow Trades API (Blocked Trades)
// ============================================================================

export const legacyShadowTradesApi = {
  async list(params?: {
    days?: number;
    symbol?: string;
    limit?: number;
    offset?: number;
  }): Promise<LegacyShadowTradeListResponse> {
    const response = await predictionApi.get(`${BASE_URL}/blocked-trades`, { params });
    return response.data;
  },
};

// ============================================================================
// Alerts API
// ============================================================================

export const alertsApi = {
  async list(params?: {
    acknowledged?: boolean;
    severity?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ alerts: Alert[]; total: number }> {
    const response = await predictionApi.get(`${BASE_URL}/alerts`, { params });
    return response.data;
  },

  async acknowledge(alertId: string): Promise<Alert> {
    const response = await predictionApi.post(`${BASE_URL}/alerts/${alertId}/acknowledge`);
    return response.data;
  },
};

// ============================================================================
// Backtest API
// ============================================================================

export const backtestApi = {
  /**
   * Start a new backtest simulation.
   *
   * @param config - Backtest configuration
   * @returns Start response with backtest_id
   */
  async start(config: BacktestConfig): Promise<BacktestStartResponse> {
    const response = await predictionApi.post(`${BASE_URL}/backtest/start`, config);
    return response.data;
  },

  /**
   * Get backtest status and progress.
   *
   * @param backtestId - Backtest ID
   * @returns Current status
   */
  async getStatus(backtestId: string): Promise<BacktestStatus> {
    const response = await predictionApi.get(`${BASE_URL}/backtest/${backtestId}/status`);
    return response.data;
  },

  /**
   * Get full backtest results (when completed).
   *
   * @param backtestId - Backtest ID
   * @returns Full results with metrics, trades, equity curve
   */
  async getResults(backtestId: string): Promise<BacktestResultResponse> {
    const response = await predictionApi.get(`${BASE_URL}/backtest/${backtestId}/results`);
    return response.data;
  },

  /**
   * List all backtests.
   *
   * @returns List of backtest summaries
   */
  async list(): Promise<BacktestSummary[]> {
    const response = await predictionApi.get(`${BASE_URL}/backtest`);
    return response.data;
  },
};

// ============================================================================
// Trading Strategy API (Strategy-Centric Trading)
// ============================================================================

const STRATEGIES_URL = '/trading-strategies';

export const tradingStrategyApi = {
  // ============ Strategy CRUD ============

  /**
   * Create a new trading strategy with portfolio configuration.
   *
   * @param data - Strategy configuration (symbols, allocations, capital, risk params)
   * @returns Created strategy with ID
   */
  async create(data: TradingStrategyCreate): Promise<TradingStrategy> {
    const response = await predictionApi.post(STRATEGIES_URL, data);
    return response.data;
  },

  /**
   * List all trading strategies with optional filtering.
   *
   * @param params - Filter parameters (is_active, limit, offset)
   * @returns List of strategies and total count
   */
  async list(params?: {
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<StrategyListResponse> {
    const response = await predictionApi.get(STRATEGIES_URL, { params });
    return response.data;
  },

  /**
   * Get a trading strategy by ID.
   *
   * @param strategyId - Strategy UUID
   * @returns Strategy details
   */
  async get(strategyId: string): Promise<TradingStrategy> {
    const response = await predictionApi.get(`${STRATEGIES_URL}/${strategyId}`);
    return response.data;
  },

  /**
   * Update a trading strategy (partial update).
   *
   * @param strategyId - Strategy UUID
   * @param data - Fields to update
   * @returns Updated strategy
   */
  async update(strategyId: string, data: TradingStrategyUpdate): Promise<TradingStrategy> {
    const response = await predictionApi.patch(`${STRATEGIES_URL}/${strategyId}`, data);
    return response.data;
  },

  /**
   * Delete a trading strategy and all associated executions.
   *
   * @param strategyId - Strategy UUID
   */
  async delete(strategyId: string): Promise<void> {
    await predictionApi.delete(`${STRATEGIES_URL}/${strategyId}`);
  },

  // ============ Strategy Executions ============

  /**
   * Start a new strategy execution.
   *
   * Modes:
   * - `backtest`: Run against historical data (requires start_date and end_date)
   * - `paper`: Real-time simulation with live data, no real trades
   * - `live`: Real trading (not yet implemented)
   *
   * @param strategyId - Strategy UUID
   * @param data - Execution configuration (mode, dates for backtest)
   * @returns Created execution with per-symbol states
   */
  async startExecution(strategyId: string, data: StrategyExecutionStart): Promise<StrategyExecution> {
    const response = await predictionApi.post(`${STRATEGIES_URL}/${strategyId}/executions`, data);
    return response.data;
  },

  /**
   * List all executions for a strategy.
   *
   * @param strategyId - Strategy UUID
   * @param params - Filter parameters (mode, status, limit)
   * @returns List of executions
   */
  async listExecutions(
    strategyId: string,
    params?: {
      mode?: ExecutionMode;
      status?: ExecutionStatus;
      limit?: number;
    }
  ): Promise<StrategyExecutionListResponse> {
    const response = await predictionApi.get(`${STRATEGIES_URL}/${strategyId}/executions`, { params });
    return response.data;
  },

  /**
   * Get a specific strategy execution with per-symbol states.
   *
   * @param strategyId - Strategy UUID
   * @param executionId - Execution UUID
   * @returns Execution details with symbol states
   */
  async getExecution(strategyId: string, executionId: string): Promise<StrategyExecution> {
    const response = await predictionApi.get(`${STRATEGIES_URL}/${strategyId}/executions/${executionId}`);
    return response.data;
  },

  /**
   * Mark execution as running.
   *
   * For paper trading, call this to start processing live data.
   * For backtests, this is typically called by the backtest engine.
   *
   * @param strategyId - Strategy UUID
   * @param executionId - Execution UUID
   * @returns Updated execution
   */
  async runExecution(strategyId: string, executionId: string): Promise<StrategyExecution> {
    const response = await predictionApi.post(`${STRATEGIES_URL}/${strategyId}/executions/${executionId}/start`);
    return response.data;
  },

  /**
   * Stop a running execution.
   *
   * @param strategyId - Strategy UUID
   * @param executionId - Execution UUID
   * @returns Updated execution
   */
  async stopExecution(strategyId: string, executionId: string): Promise<StrategyExecution> {
    const response = await predictionApi.post(`${STRATEGIES_URL}/${strategyId}/executions/${executionId}/stop`);
    return response.data;
  },

  /**
   * Force a trade action (TEST mode only).
   *
   * Bypasses ML gate predictions and executes a trade directly.
   * Only works when execution is running in TEST mode.
   *
   * @param strategyId - Strategy UUID
   * @param executionId - Execution UUID
   * @param symbol - Symbol to trade (e.g., BTCUSDT)
   * @param action - Trade action: 'enter_long', 'enter_short', or 'exit'
   * @param reason - Optional reason for forcing the trade
   * @returns Force trade response with trade details
   */
  async forceTrade(
    strategyId: string,
    executionId: string,
    symbol: string,
    action: 'enter_long' | 'enter_short' | 'exit',
    reason: string = 'manual_force'
  ): Promise<ForceTradeResponse> {
    const response = await predictionApi.post(
      `${STRATEGIES_URL}/${strategyId}/executions/${executionId}/force-trade`,
      { action, reason },
      { params: { symbol } }
    );
    return response.data;
  },

  /**
   * Run automated tests on a TEST mode execution.
   *
   * Runs a battery of tests to verify all trading modules work correctly:
   * - Market Data Access
   * - Trade Cycles (Long/Short)
   * - Stop Loss / Take Profit Triggers
   * - ML Gates (if enabled)
   * - Metrics Persistence
   *
   * @param strategyId - Strategy UUID
   * @param executionId - Execution UUID (must be TEST mode, running)
   * @returns Auto-test results with pass/fail for each module
   */
  async runAutoTest(
    strategyId: string,
    executionId: string
  ): Promise<AutoTestResults> {
    const response = await predictionApi.post(
      `${STRATEGIES_URL}/${strategyId}/executions/${executionId}/auto-test`
    );
    return response.data;
  },
};

// ============================================================================
// Combined API (Legacy Compatibility)
// ============================================================================

export const mlLabApi = {
  // Models
  listModels: modelsApi.list,
  getModel: modelsApi.get,
  createModel: modelsApi.create,
  updateModel: modelsApi.update,
  deleteModel: modelsApi.delete,
  activateModel: modelsApi.activate,
  deactivateModel: modelsApi.deactivate,

  // Areas
  listAreas: areasApi.list,
  getActiveModelForArea: areasApi.getActiveModel,

  // Training
  startTraining: trainingApi.start,
  listTrainingJobs: trainingApi.list,
  getTrainingJob: trainingApi.get,
  cancelTrainingJob: trainingApi.cancel,

  // Gate Configs
  listGateConfigs: gateConfigApi.list,
  getGateConfig: gateConfigApi.get,
  updateGateConfig: gateConfigApi.update,

  // Dashboard
  getDashboard: dashboardApi.get,

  // Live Inference
  getLiveStatus: liveInferenceApi.getStatus,
  runLiveInference: liveInferenceApi.predict,
  reloadLiveModels: liveInferenceApi.reloadModels,

  // Shadow Trades
  listShadowTrades: shadowTradeApi.list,
  getShadowTrade: shadowTradeApi.get,
  createShadowTrade: shadowTradeApi.create,
  closeShadowTrade: shadowTradeApi.close,
  getShadowTradeStats: shadowTradeApi.getStats,

  // Legacy Shadow Trades
  listBlockedTrades: legacyShadowTradesApi.list,

  // Alerts
  listAlerts: alertsApi.list,
  acknowledgeAlert: alertsApi.acknowledge,

  // Trading Strategies (Strategy-Centric Trading)
  createStrategy: tradingStrategyApi.create,
  listStrategies: tradingStrategyApi.list,
  getStrategy: tradingStrategyApi.get,
  updateStrategy: tradingStrategyApi.update,
  deleteStrategy: tradingStrategyApi.delete,
  startStrategyExecution: tradingStrategyApi.startExecution,
  listStrategyExecutions: tradingStrategyApi.listExecutions,
  getStrategyExecution: tradingStrategyApi.getExecution,
  runStrategyExecution: tradingStrategyApi.runExecution,
  stopStrategyExecution: tradingStrategyApi.stopExecution,
  forceTradeOnExecution: tradingStrategyApi.forceTrade,
};

export default mlLabApi;
