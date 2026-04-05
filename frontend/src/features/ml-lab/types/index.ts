/**
 * ML Lab Types
 *
 * Type definitions for ML Lab Gatekeeper functionality.
 */

// ============================================================================
// Enums
// ============================================================================

export enum MLArea {
  REGIME = 'regime',
  DIRECTION = 'direction',
  ENTRY = 'entry',
  EXIT = 'exit',
  RISK = 'risk',
  VOLATILITY = 'volatility',
}

export enum ModelType {
  XGBOOST = 'xgboost',
  LIGHTGBM = 'lightgbm',
}

export enum ModelStatus {
  DRAFT = 'draft',
  TRAINING = 'training',
  ACTIVE = 'active',
  FAILED = 'failed',
  ARCHIVED = 'archived',
}

export enum TrainingStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// ============================================================================
// Model Types
// ============================================================================

export interface MLModel {
  id: string;
  name: string;
  description: string | null;
  area: MLArea;
  model_type: ModelType;
  status: ModelStatus;
  version: string;
  is_active: boolean;
  model_path: string | null;
  training_metadata: Record<string, unknown> | null;
  metrics: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

export interface MLModelCreate {
  name: string;
  description?: string;
  area: MLArea;
  model_type: ModelType;
}

export interface MLModelUpdate {
  name?: string;
  description?: string;
}

export interface MLModelListResponse {
  models: MLModel[];
  total: number;
}

// ============================================================================
// Training Types
// ============================================================================

export interface TrainingConfig {
  symbol: string;
  timeframe: string;
  date_from: string;
  date_to: string;
  n_trials: number;
  hyperparameters?: Record<string, unknown>;
}

export interface TrainingJobStart {
  model_id: string;
  config: TrainingConfig;
}

export interface TrainingJob {
  id: string;
  model_id: string;
  symbol: string;
  timeframe: string;
  date_from: string;
  date_to: string;
  status: TrainingStatus;
  progress: number;
  current_trial: number;
  total_trials: number;
  best_score: number | null;
  best_hyperparameters: Record<string, unknown> | null;
  metrics: Record<string, number> | null;
  feature_importance: Record<string, number> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TrainingJobListResponse {
  jobs: TrainingJob[];
  total: number;
}

// ============================================================================
// Gate Config Types
// ============================================================================

export interface GateConfig {
  area: MLArea;
  enabled: boolean;
  confidence_threshold: number;
  weight: number;
  settings: Record<string, unknown>;
}

export interface GateConfigUpdate {
  enabled?: boolean;
  confidence_threshold?: number;
  weight?: number;
  settings?: Record<string, unknown>;
}

export interface GateConfigListResponse {
  configs: GateConfig[];
}

// ============================================================================
// Dashboard Types
// ============================================================================

export interface DashboardStats {
  total_models: number;
  active_models: number;
  models_by_area: Record<string, number>;
  running_training_jobs: number;
  completed_training_jobs_24h: number;
  total_trades_24h: number;
  blocked_trades_24h: number;
  overall_win_rate: number | null;
  overall_block_accuracy: number | null;
  best_combination_hash: string | null;
  best_combination_sharpe: number | null;
}

export interface Alert {
  id: string;
  rule_id: string | null;
  severity: string;
  message: string;
  context: Record<string, unknown>;
  acknowledged: boolean;
  created_at: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  recent_alerts: Alert[];
  top_models: MLModel[];
  recent_training_jobs: TrainingJob[];
}

// ============================================================================
// Live Inference Types
// ============================================================================

export interface GateResult {
  prediction: string;
  confidence: number;
  class_id: number;
  model_id: string | null;
  error: string | null;
}

export interface TradingDecision {
  action: 'enter_long' | 'enter_short' | 'exit' | 'hold';
  confidence: number;
  reasoning: string;
}

export interface LiveInferenceRequest {
  symbol: string;
  timeframe: string;
  gates?: string[];
  include_decision?: boolean;
  position_side?: 'long' | 'short' | null;
}

export interface LiveInferenceResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  gates: Record<string, GateResult>;
  decision: TradingDecision | null;
  latency_ms: number;
}

export interface LiveStatusGate {
  model_loaded: boolean;
  model_id: string | null;
  model_name: string | null;
}

export interface LiveStatusResponse {
  status: 'ready' | 'loading' | 'error';
  gates: Record<string, LiveStatusGate>;
  total_models_loaded: number;
  model_reload_interval_minutes: number;
}

// ============================================================================
// Shadow/Paper Trade Types
// ============================================================================

export interface ShadowTradeCreate {
  symbol: string;
  timeframe: string;
  action: 'enter_long' | 'enter_short';
  entry_price: number;
  gate_predictions: Record<string, unknown>;
  confidence: number;
  reasoning?: string;
}

export interface ShadowTradeCloseRequest {
  exit_price: number;
  reason: 'signal' | 'stop_loss' | 'take_profit' | 'timeout' | 'manual';
}

export interface ShadowTrade {
  trade_id: string;
  symbol: string;
  timeframe: string;
  action: string;
  entry_price: number;
  exit_price: number | null;
  leverage: number;  // Leverage multiplier (1.0-5.0x based on Risk Gate)
  pnl_pct: number | null;  // P&L with leverage applied
  base_pnl_pct?: number | null;  // P&L without leverage (optional)
  gate_predictions: Record<string, unknown>;
  confidence: number;
  reasoning: string | null;
  status: 'open' | 'closed';
  duration_minutes: number | null;
  created_at: string;
  closed_at: string | null;
}

export interface ShadowTradeStats {
  period_days: number;
  total_trades: number;
  closed_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  avg_pnl_pct: number;
  total_pnl_pct: number;
  max_win_pct: number;
  max_loss_pct: number;
}

// ============================================================================
// Legacy Shadow Trade Types (blocked trades)
// ============================================================================

export interface LegacyShadowTrade {
  id: string;
  symbol: string;
  signal_type: string;
  entry_price: number;
  blocked_at: string;
  blocked_by_gates: string[];
  would_have_been: string | null;
  exit_price: number | null;
  potential_pnl: number | null;
}

export interface LegacyShadowTradeListResponse {
  shadow_trades: LegacyShadowTrade[];
  total: number;
  total_blocked: number;
  would_have_won: number;
  would_have_lost: number;
  block_accuracy: number | null;
}

// ============================================================================
// Live Paper Trading Types (moved from mlLabApi.ts)
// ============================================================================

/**
 * Trading operation modes for paper trading
 */
export type TradingMode = 'live' | 'test' | 'backtest';

/**
 * Request to force a trade in TEST mode
 */
export interface ForceTradeRequest {
  action: 'enter_long' | 'enter_short' | 'exit';
  reason?: string;
}

/**
 * Response from force trade execution
 */
export interface ForceTradeResponse {
  success: boolean;
  symbol: string;
  action: string;
  trade_id?: string;
  entry_price?: number;
  exit_price?: number;
  pnl_pct?: number;
  message: string;
  timestamp: string;
}

/**
 * Individual test result from auto-test
 */
export interface AutoTestResult {
  status: 'passed' | 'failed' | 'skipped' | 'pending';
  details: Record<string, unknown>;
  direction?: string;
  reason?: string;
}

/**
 * Response from auto-test execution
 */
export interface AutoTestResults {
  test_run_at: string;
  strategy: string;
  symbols: string[];
  tests: {
    market_data_access: AutoTestResult;
    trade_cycle_long: AutoTestResult;
    trade_cycle_short: AutoTestResult;
    stop_loss_trigger: AutoTestResult;
    take_profit_trigger: AutoTestResult;
    ml_gates: AutoTestResult;
    metrics_persistence: AutoTestResult;
  };
  passed: number;
  failed: number;
  total: number;
  success_rate: number;
}

export interface LiveTradingPosition {
  id: string;
  symbol: string;
  direction: string;
  entry_price: number;
  current_price: number;
  pnl_pct: number;
  size?: number;
  entry_time?: string;
}

export interface LiveTradingStats {
  symbol: string;
  timeframe: string;
  mode: TradingMode;  // Trading mode: live, test, backtest
  is_running: boolean;
  capital: number;
  initial_capital: number;
  realized_pnl: number;
  realized_pnl_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  has_position: boolean;
  current_position: LiveTradingPosition | null;
}

export interface LiveTradingTickTrade {
  type: string;
  id: string;
  symbol: string;
  direction: string;
  entry_price: number;
  exit_price?: number;
  pnl_pct?: number;
}

export interface LiveTradingTickResult {
  timestamp: string;
  symbol: string;
  price: number;
  action: string;
  confidence: number;
  reasoning: string;
  gates: Record<string, {
    prediction: string;
    confidence: number;
    class_id: number;
    model_id: string;
  }>;
  position: LiveTradingPosition | null;
  trade: LiveTradingTickTrade | null;
}

export interface LiveTradingSession {
  session_id: string;
  symbol: string;
  timeframe: string;
  mode?: TradingMode;  // Trading mode: live, test, backtest
  status: string;
  initial_capital: number;
  current_capital: number;
  realized_pnl: number;
  realized_pnl_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  check_interval_seconds: number;
  started_at: string | null;
  last_tick_at: string | null;
  is_running: boolean;
  current_price?: number;
  current_position?: LiveTradingPosition | null;
}

// ============================================================================
// Multi-Session Types (for parallel paper trading up to 10 coins)
// ============================================================================

export interface LiveTradingSessionsResponse {
  sessions: LiveTradingSession[];
  total_sessions: number;
  max_sessions: number;
  available_slots: number;
  error?: string;
}

export interface LiveTradingStatusResponse {
  status: 'running' | 'stopped' | 'error';
  sessions: LiveTradingSession[];
  session?: LiveTradingSession | null;  // Backward compat
  stats?: LiveTradingStats | null;  // Backward compat
  total_sessions?: number;
  error?: string;
}

export interface LiveTradingStopResponse {
  status: string;
  message: string;
  final_stats: LiveTradingStats | Record<string, LiveTradingStats>;
  stopped_symbols: string[];
}

export interface LiveTradingTickResponse {
  status: string;
  symbol?: string;  // When single symbol
  tick_result?: LiveTradingTickResult;  // When single symbol
  tick_results?: Record<string, LiveTradingTickResult>;  // When all symbols
  stats: LiveTradingStats | Record<string, LiveTradingStats>;
  ticked_count?: number;
}

// ============================================================================
// Live Indicators Types (moved from mlLabApi.ts)
// ============================================================================

export interface IndicatorValue {
  value: number | boolean | null;
  description: string;
  signal?: string;
  thresholds?: Record<string, number | number[]>;
  increasing?: boolean;
  distance_pct?: number;
  atr_pct?: number;
}

export interface LiveIndicatorsResponse {
  timestamp: string;
  symbol: string;
  timeframe: string;
  price: {
    current: number;
    high: number;
    low: number;
    change_pct: number;
  };
  indicators: {
    trend: {
      ema9: IndicatorValue;
      ema20: IndicatorValue;
      ema50: IndicatorValue;
      ema200: IndicatorValue;
      ema_cross_9_20: IndicatorValue;
      adx: IndicatorValue;
    };
    momentum: {
      rsi: IndicatorValue;
      macd_line: IndicatorValue;
      macd_signal: IndicatorValue;
      macd_histogram: IndicatorValue;
      stochastic_k: IndicatorValue;
      stochastic_d: IndicatorValue;
    };
    volatility: {
      atr: IndicatorValue;
      bollinger_upper: IndicatorValue;
      bollinger_middle: IndicatorValue;
      bollinger_lower: IndicatorValue;
      bollinger_width: IndicatorValue;
      keltner_width: IndicatorValue;
    };
    volume: {
      current: IndicatorValue;
      sma20: IndicatorValue;
      ratio: IndicatorValue;
    };
  };
  signals: {
    trend: {
      direction: string;
      strength: string;
    };
    momentum: {
      rsi_signal: string;
      macd_signal: string;
      stoch_signal: string;
    };
    volatility: {
      regime: string;
      atr_pct: number;
    };
    entry_conditions: {
      long: Record<string, boolean>;
      short: Record<string, boolean>;
    };
    exit_conditions: Record<string, boolean>;
  };
  gate_thresholds: Record<string, Record<string, Record<string, number | number[] | boolean>>>;
}

// ============================================================================
// Backtest Types
// ============================================================================

/**
 * Configuration for historical backtest
 */
export interface BacktestConfig {
  symbol: string;
  timeframe: string;
  date_from: string;  // ISO datetime string
  date_to: string;    // ISO datetime string
  use_ml_gates: boolean;
  initial_capital: number;
  position_size_pct: number;
  stop_loss_pct?: number | null;
  take_profit_pct?: number | null;
}

/**
 * Single trade in backtest results
 */
export interface BacktestTrade {
  entry_time: string;
  exit_time: string;
  side: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  pnl_pct: number;
  pnl_usd: number;
  exit_reason: 'signal' | 'stop_loss' | 'take_profit' | 'end_of_data';
  gate_predictions?: Record<string, unknown> | null;
}

/**
 * Aggregated backtest performance metrics
 */
export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  total_pnl_pct: number;
  total_pnl_usd: number;
  max_drawdown_pct: number;
  max_drawdown_usd: number;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  profit_factor: number | null;
  avg_trade_pnl_pct: number;
  avg_winning_trade_pct: number;
  avg_losing_trade_pct: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  total_candles_processed: number;
  backtest_duration_seconds: number;
}

/**
 * Response when starting a backtest
 */
export interface BacktestStartResponse {
  backtest_id: string;
  status: 'running' | 'completed' | 'failed';
  config: BacktestConfig;
  message: string;
  started_at: string;
}

/**
 * Current status of a running backtest
 */
export interface BacktestStatus {
  backtest_id: string;
  status: 'running' | 'completed' | 'failed';
  progress_pct: number;
  candles_processed: number;
  total_candles: number;
  current_date?: string | null;
  trades_so_far: number;
  error_message?: string | null;
}

/**
 * Equity curve data point
 */
export interface EquityCurvePoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

/**
 * Full backtest results
 */
export interface BacktestResultResponse {
  backtest_id: string;
  config: BacktestConfig;
  status: string;
  metrics: BacktestMetrics;
  trades: BacktestTrade[];
  equity_curve: EquityCurvePoint[];
  started_at: string;
  completed_at?: string | null;
}

/**
 * Summary info for backtest listing
 */
export interface BacktestSummary {
  backtest_id: string;
  symbol: string;
  timeframe: string;
  status: string;
  progress_pct: number;
  trades_count: number;
  started_at: string;
  completed_at?: string | null;
}

// ============ Trading Strategy Types (Strategy-Centric Design) ============

/**
 * Execution mode for strategy runs
 * - backtest: Historical data simulation
 * - paper: Real-time simulation, no real trades
 * - test: Real-time data, force trades bypass ML gates
 * - live: Real trading (future)
 */
export type ExecutionMode = 'backtest' | 'paper' | 'test' | 'live';

/**
 * Status of a strategy execution
 */
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'stopped';

/**
 * Trading strategy configuration
 */
export interface TradingStrategy {
  id: string;
  name: string;
  description?: string | null;

  // Portfolio configuration
  symbols: string[];
  allocations: Record<string, number>;
  total_capital: number;

  // Risk settings
  position_size_pct: number;
  stop_loss_pct?: number | null;
  take_profit_pct?: number | null;
  max_positions: number;

  // Timeframe
  timeframe: string;

  // ML Gates
  ml_gates_enabled: boolean;
  gate_thresholds?: Record<string, number> | null;

  // Status
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Request to create a trading strategy
 */
export interface TradingStrategyCreate {
  name: string;
  description?: string;
  symbols: string[];
  allocations?: Record<string, number>;
  total_capital?: number;
  position_size_pct?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  max_positions?: number;
  timeframe?: string;
  ml_gates_enabled?: boolean;
  gate_thresholds?: Record<string, number>;
}

/**
 * Request to update a trading strategy
 */
export interface TradingStrategyUpdate {
  name?: string;
  description?: string;
  symbols?: string[];
  allocations?: Record<string, number>;
  total_capital?: number;
  position_size_pct?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  max_positions?: number;
  timeframe?: string;
  ml_gates_enabled?: boolean;
  gate_thresholds?: Record<string, number>;
  is_active?: boolean;
}

/**
 * Per-symbol state within an execution
 */
export interface SymbolExecutionState {
  symbol: string;
  allocated_capital: number;
  current_capital: number;
  position_direction?: string | null;  // 'long', 'short', or null
  position_entry_price?: number | null;
  position_size?: number | null;
  total_trades: number;
  realized_pnl: number;
  // Live data (computed, not stored in DB)
  current_price?: number | null;
  unrealized_pnl?: number | null;
  unrealized_pnl_pct?: number | null;
}

/**
 * Strategy execution with per-symbol states
 */
export interface StrategyExecution {
  id: string;
  strategy_id: string;
  strategy_name: string;
  mode: ExecutionMode;
  status: ExecutionStatus;

  // Backtest timing
  backtest_start_date?: string | null;
  backtest_end_date?: string | null;

  // Backtest progress (for progress bar)
  backtest_progress: number;  // 0.0 to 1.0
  backtest_total_candles: number;
  backtest_processed_candles: number;

  // Capital
  initial_capital: number;
  current_capital: number;

  // Metrics
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  realized_pnl: number;
  max_drawdown_pct?: number | null;
  sharpe_ratio?: number | null;
  win_rate?: number | null;

  // Per-symbol states
  symbol_states: SymbolExecutionState[];

  // Timing
  started_at?: string | null;
  completed_at?: string | null;
  last_tick_at?: string | null;
  created_at: string;
}

/**
 * Request to start an execution
 */
export interface StrategyExecutionStart {
  mode: ExecutionMode;
  start_date?: string;  // Required for backtest
  end_date?: string;    // Required for backtest
}

/**
 * List of strategies response
 */
export interface StrategyListResponse {
  strategies: TradingStrategy[];
  total_count: number;
}

/**
 * List of executions for a strategy
 */
export interface StrategyExecutionListResponse {
  strategy_id: string;
  strategy_name: string;
  executions: StrategyExecution[];
  total_count: number;
}
