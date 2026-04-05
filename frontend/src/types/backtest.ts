/**
 * Strategy Lab Backtest Type Definitions
 *
 * Comprehensive TypeScript types for backtesting, walk-forward validation,
 * and parameter optimization.
 * Backend models: services/prediction-service/app/services/backtest_engine.py
 */

import type { StrategyDefinition } from './strategy'

// ============================================================================
// Backtest Configuration
// ============================================================================

export interface BacktestConfig {
  /** Initial capital in USD */
  initial_capital: number
  /** Commission per trade as percentage (e.g., 0.001 = 0.1%) */
  commission: number
  /** Slippage per trade as percentage (e.g., 0.0005 = 0.05%) */
  slippage: number
  /** Maximum concurrent positions */
  max_positions?: number
  /** Enable short positions */
  allow_shorts?: boolean
}

// ============================================================================
// Backtest Results
// ============================================================================

export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface BacktestMetrics {
  /** Total return as percentage (e.g., 0.15 = 15% return) */
  total_return: number
  /** Sharpe ratio (risk-adjusted return) */
  sharpe_ratio: number
  /** Maximum drawdown as percentage (e.g., 0.25 = 25% drawdown) */
  max_drawdown: number
  /** Win rate as percentage (e.g., 0.65 = 65% wins) */
  win_rate: number
  /** Total number of completed trades */
  total_trades: number
  /** Average return per trade */
  avg_trade_return: number
  /** Portfolio volatility (standard deviation of returns) */
  volatility: number
  /** Sortino ratio (downside risk-adjusted return) */
  sortino_ratio?: number
  /** Calmar ratio (return / max drawdown) */
  calmar_ratio?: number
  /** Profit factor (gross profit / gross loss) */
  profit_factor?: number
}

export interface BacktestTrade {
  timestamp: string
  action: 'BUY' | 'SELL' | 'HOLD'
  price: number
  quantity: number
  pnl?: number
  regime?: string
  reason?: string
  entry_price?: number
  exit_price?: number
}

export interface EquityCurvePoint {
  timestamp: string
  value: number
  regime?: string
}

export interface RegimePerformance {
  regime: string
  trades: number
  win_rate: number
  avg_return: number
  sharpe_ratio: number
}

export interface BacktestResult {
  id: string
  strategy_name: string
  strategy_version: number
  symbol: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  status: BacktestStatus
  metrics: BacktestMetrics
  trades: BacktestTrade[]
  equity_curve: EquityCurvePoint[]
  /** Performance breakdown by regime */
  regime_performance?: RegimePerformance[]
  created_at: string
  completed_at?: string
  error?: string
}

// ============================================================================
// Walk-Forward Validation
// ============================================================================

export type WindowType = 'rolling' | 'anchored'

export interface WalkForwardConfig {
  /** Window type: 'rolling' (fixed-size) or 'anchored' (expanding) */
  window_type: WindowType
  /** Training window size in days */
  train_window_days: number
  /** Test window size in days */
  test_window_days: number
  /** Minimum training samples required */
  min_train_samples?: number
  /** Backtest configuration for each window */
  backtest_config: BacktestConfig
}

export interface WalkForwardWindow {
  window_number: number
  train_start: string
  train_end: string
  test_start: string
  test_end: string
  train_sharpe: number
  test_sharpe: number
  train_return: number
  test_return: number
  train_drawdown: number
  test_drawdown: number
}

export interface WalkForwardResult {
  id: string
  strategy_name: string
  strategy_version: number
  symbol: string
  config: WalkForwardConfig
  total_windows: number
  successful_windows: number
  /** Average Sharpe ratio on training sets */
  avg_train_sharpe: number
  /** Average Sharpe ratio on test sets (out-of-sample) */
  avg_test_sharpe: number
  /** Overfitting ratio: test_sharpe / train_sharpe (< 0.7 indicates overfitting) */
  overfitting_ratio: number
  /** Consistency score: 0-1, higher = more consistent across windows */
  consistency_score: number
  /** Correlation between train and test performance */
  train_test_correlation: number
  windows: WalkForwardWindow[]
  created_at: string
  completed_at?: string
  error?: string
}

// ============================================================================
// Parameter Optimization
// ============================================================================

export type ParameterType = 'int' | 'float' | 'categorical'

export interface ParameterSpace {
  /** Parameter name (e.g., "rsi_period", "trend_threshold") */
  name: string
  /** JSON path to parameter in strategy (e.g., "indicators.0.params.period") */
  path: string
  param_type: ParameterType
  /** Minimum value for numeric parameters */
  low?: number
  /** Maximum value for numeric parameters */
  high?: number
  /** Step size for numeric parameters */
  step?: number
  /** Available choices for categorical parameters */
  choices?: any[]
}

export interface OptimizationConfig {
  /** Number of optimization trials */
  n_trials: number
  /** Maximum optimization time in seconds */
  timeout?: number
  /** Number of parallel jobs (1 = sequential) */
  n_jobs?: number
  /** Metric to optimize ("sharpe_ratio", "total_return", "win_rate", etc.) */
  objective_metric: string
  /** Optimization direction ("maximize" or "minimize") */
  direction: 'maximize' | 'minimize'
  /** Enable pruning of unpromising trials */
  pruner_enabled?: boolean
  /** Sampler algorithm ("tpe" or "random") */
  sampler?: 'tpe' | 'random'
}

export interface OptimizationTrial {
  trial_number: number
  objective_value: number
  params: Record<string, any>
}

export interface OptimizationResult {
  id: string
  strategy_name: string
  base_version: number
  optimized_version: number
  /** Best parameter values found */
  best_params: Record<string, any>
  /** Best objective value achieved */
  best_value: number
  /** Best trial number */
  best_trial: number
  /** Total number of trials run */
  n_trials: number
  /** Optimization history: [trial_number, objective_value] */
  optimization_history: Array<[number, number]>
  /** Parameter importance scores (0-1) */
  parameter_importances?: Record<string, number>
  created_at: string
  completed_at?: string
  error?: string
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface BacktestRequest {
  strategy: StrategyDefinition
  symbol: string
  start_date: string
  end_date: string
  config?: BacktestConfig
}

export interface WalkForwardRequest {
  strategy: StrategyDefinition
  symbol: string
  start_date: string
  end_date: string
  config: WalkForwardConfig
}

export interface OptimizationRequest {
  base_strategy: StrategyDefinition
  symbol: string
  start_date: string
  end_date: string
  parameter_space: ParameterSpace[]
  optimization_config: OptimizationConfig
  walk_forward_config: WalkForwardConfig
}

// ============================================================================
// Strategy Lab Backtest Types (API: /api/v1/strategy-lab/backtest)
// ============================================================================

/**
 * Indicator Override for Backtest
 *
 * Allows testing different indicator parameters without modifying the strategy.
 * Part of Phase 2: Backtest Comprehensive Upgrade.
 *
 * @example
 * {
 *   indicator_id: '1h_RSI_14',
 *   params: { period: 7 }
 * }
 */
export interface IndicatorOverride {
  /** Indicator ID to override (e.g., '1h_RSI_14', '4h_EMA_50') */
  indicator_id: string
  /** Parameter overrides (e.g., { period: 7 }, { fast_period: 10, slow_period: 26 }) */
  params: Record<string, number | string>
}

export interface StrategyLabBacktestConfig {
  /** Initial capital in USD (default: 10000) */
  initial_capital: number
  /** Commission per trade as percentage (default: 0.001 = 0.1%) */
  commission?: number
  /** Slippage per trade as percentage (default: 0.0005 = 0.05%) */
  slippage?: number
}

export interface StrategyLabBacktestRequest {
  /** Strategy UUID from database (optional, use this OR strategy_definition) */
  strategy_id?: string
  /** Inline strategy JSON definition (optional, use this OR strategy_id) */
  strategy_definition?: Record<string, unknown>
  /** Trading symbol (e.g., "XRPUSDT", "BTCUSDT") */
  symbol: string
  /** Start date in YYYY-MM-DD format */
  start_date: string
  /** End date in YYYY-MM-DD format */
  end_date: string
  /** Primary timeframe for backtesting (default: "1h") */
  primary_timeframe: string
  /** Higher timeframes for multi-timeframe analysis (default: ["4h", "1d"]) */
  higher_timeframes: string[]
  /** Backtest configuration */
  config?: StrategyLabBacktestConfig
  /** Enable debug logging */
  enable_debug?: boolean
  /** Include Buy & Hold benchmark comparison */
  include_buy_hold?: boolean
  /** Include regime-based performance breakdown */
  include_regime_breakdown?: boolean
  /**
   * Indicator parameter overrides for this backtest run (Phase 2)
   *
   * Allows testing different indicator parameters without modifying the strategy.
   * The backtest engine will apply these overrides to the indicator calculations.
   *
   * @example
   * [
   *   { indicator_id: '1h_RSI_14', params: { period: 7 } },
   *   { indicator_id: '1h_EMA_20', params: { period: 12 } }
   * ]
   */
  indicator_overrides?: IndicatorOverride[]

  /**
   * Module Test Mode (Phase 3)
   *
   * Run isolated tests for specific strategy components instead of full backtest.
   * - 'entry': Test entry signals with random exits
   * - 'exit': Test exit logic with random entries
   * - 'risk': Test SL/TP with fixed-interval entries
   * - 'regime': Test regime detection accuracy
   */
  module_test_mode?: ModuleTestMode

  /**
   * Module Test Parameters (Phase 3)
   *
   * Mode-specific parameters for module isolation testing.
   */
  module_test_params?: {
    /** For entry test: Number of bars to hold before random exit */
    hold_bars?: number
    /** For exit test: Number of random entries to test */
    num_random_entries?: number
    /** For risk test: Fixed interval between systematic entries */
    entry_interval?: number
  }
}

export interface StrategyLabBacktestMetrics {
  /** Total return as percentage */
  total_return_pct: number
  /** Final portfolio value */
  final_capital: number
  /** Total number of trades */
  num_trades: number
  /** Number of winning trades */
  num_wins: number
  /** Number of losing trades */
  num_losses: number
  /** Win rate as percentage */
  win_rate_pct: number
  /** Profit factor (gross profit / gross loss) */
  profit_factor: number | null
  /** Average return per trade as percentage */
  avg_trade_return_pct: number
  /** Maximum drawdown as percentage */
  max_drawdown_pct: number
  /** Sharpe ratio (risk-adjusted return) */
  sharpe_ratio: number | null
  /** Average holding time per trade */
  avg_holding_time: string | null
}

export interface StrategyLabBacktestResult {
  /** Strategy name */
  strategy_name: string
  /** Strategy version */
  strategy_version: string
  /** Initial capital */
  initial_capital: number
  /** Performance metrics */
  metrics: StrategyLabBacktestMetrics
  /** List of executed trades */
  trades: BacktestTrade[]
  /** Equity curve data points */
  equity_curve: EquityCurvePoint[]
}

export interface BuyHoldComparison {
  /** Start price of the asset */
  start_price: number
  /** End price of the asset */
  end_price: number
  /** Buy & Hold return as percentage */
  buy_hold_return_pct: number
  /** Buy & Hold final capital */
  buy_hold_final_capital: number
  /** Strategy return as percentage */
  strategy_return_pct: number
  /** Strategy final capital */
  strategy_final_capital: number
  /** Strategy outperformance vs Buy & Hold */
  outperformance_pct: number
  /** Alpha (strategy return - buy hold return) */
  alpha: number
}

export interface StrategyLabRegimePerformance {
  /** Regime name (TREND, CONSOLIDATION, HIGH_VOLATILITY) */
  regime: string
  /** Number of trades in this regime */
  num_trades: number
  /** Win rate for this regime */
  win_rate_pct: number
  /** Total return in this regime */
  total_return_pct: number
  /** Average trade return in this regime */
  avg_trade_pct: number
  /** Percentage of time spent in this regime */
  time_in_regime_pct: number
}

export interface StrategyLabRegimeBreakdown {
  /** Performance breakdown by regime */
  regimes: StrategyLabRegimePerformance[]
  /** Dominant regime (most time spent) */
  dominant_regime: string
  /** Best performing regime */
  best_regime: string
  /** Worst performing regime */
  worst_regime: string
}

export interface StrategyLabBacktestResponse {
  /** Original request */
  request: StrategyLabBacktestRequest
  /** Backtest result (null on error) */
  result: StrategyLabBacktestResult | null
  /** Buy & Hold comparison (if requested) */
  buy_hold_comparison: BuyHoldComparison | null
  /** Regime breakdown (if requested) */
  regime_breakdown: StrategyLabRegimeBreakdown | null
  /** Data info (candles loaded, etc.) */
  data_info: Record<string, unknown>
  /** Total execution time in seconds */
  execution_time_seconds: number
  /** Data fetch time in seconds */
  data_fetch_time_seconds: number
  /** Backtest execution time in seconds */
  backtest_time_seconds: number
  /** Status: success, partial, or error */
  status: 'success' | 'partial' | 'error'
  /** Warnings generated during backtest */
  warnings: string[]
  /** Error message (if status is error) */
  error_message: string | null
}

// ============================================================================
// Module Test Types (Phase 3: Backtest Comprehensive Upgrade)
// ============================================================================

/**
 * Module Test Mode
 *
 * Test individual strategy components in isolation to identify weaknesses.
 */
export type ModuleTestMode = 'full' | 'entry' | 'exit' | 'risk' | 'regime'

/**
 * Entry Logic Test Metrics
 *
 * Metrics specific to entry signal testing.
 */
export interface EntryTestMetrics {
  /** Total entry signals generated */
  total_entries: number
  /** Entries that became profitable */
  profitable_entries: number
  /** Win rate of entries (0-100) */
  entry_win_rate: number
  /** Average bars until position becomes profitable */
  avg_bars_to_profit: number | null
  /** Entry quality score (0-100) */
  avg_entry_quality: number
  /** Entry count by regime */
  entries_by_regime: Record<string, number>
  /** Entries that never became profitable */
  false_signals: number
}

/**
 * Exit Logic Test Metrics
 *
 * Metrics specific to exit timing testing.
 */
export interface ExitTestMetrics {
  /** Total exits tested */
  total_exits: number
  /** Percentage of exits near optimal (0-100) */
  optimal_exit_rate: number
  /** Average bars from optimal exit point */
  avg_exit_timing_error: number
  /** Exits that left profit on table */
  premature_exits: number
  /** Exits that gave back profit */
  late_exits: number
  /** Exit count by reason */
  exits_by_reason: Record<string, number>
}

/**
 * Risk Management Test Metrics
 *
 * Metrics specific to SL/TP testing.
 */
export interface RiskTestMetrics {
  /** Number of stop-loss triggers */
  stop_loss_hits: number
  /** Number of take-profit triggers */
  take_profit_hits: number
  /** How often SL prevented larger loss (0-100) */
  stop_loss_effectiveness: number
  /** How often TP was near optimal (0-100) */
  take_profit_effectiveness: number
  /** Actual average risk/reward ratio */
  avg_risk_reward_actual: number
  /** Position sizing accuracy (0-100) */
  position_sizing_accuracy: number
  /** Maximum consecutive stop-losses */
  max_consecutive_stops: number
}

/**
 * Regime Detection Test Metrics
 *
 * Metrics specific to regime identification testing.
 */
export interface RegimeTestMetrics {
  /** Total bars analyzed */
  total_bars: number
  /** Number of regime changes detected */
  regime_changes_detected: number
  /** Detection accuracy vs actual (0-100) */
  detection_accuracy: number
  /** Time percentage in each regime */
  regime_distribution: Record<string, number>
  /** Quick regime reversals (noise) */
  false_regime_changes: number
  /** Average duration per regime (bars) */
  avg_regime_duration_bars: Record<string, number>
  /** Correlation with actual trends (-1 to 1) */
  regime_vs_trend_correlation: number
}

/**
 * Module Test Result
 *
 * Result from a module isolation test with mode-specific metrics.
 */
export interface ModuleTestResult {
  /** Which module was tested */
  test_mode: ModuleTestMode
  /** Strategy name */
  strategy_name: string
  /** Test period start */
  period_start: string
  /** Test period end */
  period_end: string
  /** Total bars in test period */
  total_bars: number
  /** Entry metrics (when test_mode=entry) */
  entry_metrics: EntryTestMetrics | null
  /** Exit metrics (when test_mode=exit) */
  exit_metrics: ExitTestMetrics | null
  /** Risk metrics (when test_mode=risk) */
  risk_metrics: RiskTestMetrics | null
  /** Regime metrics (when test_mode=regime) */
  regime_metrics: RegimeTestMetrics | null
  /** Full backtest result (when test_mode=full) */
  full_result: StrategyLabBacktestResult | null
  /** Auto-generated insights */
  insights: string[]
  /** Suggested improvements */
  recommendations: string[]
  /** Whether test completed successfully without major issues */
  success?: boolean
}

/**
 * Module Test Request
 *
 * Request to run a module isolation test.
 */
export interface ModuleTestRequest {
  /** Strategy UUID from database */
  strategy_id?: string
  /** Inline strategy definition */
  strategy_definition?: Record<string, unknown>
  /** Trading symbol */
  symbol: string
  /** Start date (YYYY-MM-DD) */
  start_date: string
  /** End date (YYYY-MM-DD) */
  end_date: string
  /** Primary timeframe */
  primary_timeframe: string
  /** Higher timeframes */
  higher_timeframes: string[]
  /** Test mode */
  test_mode: ModuleTestMode
  /** Entry test: bars to hold before exit */
  entry_test_hold_bars?: number
  /** Exit test: number of random entries */
  exit_test_random_entries?: number
  /** Risk test: enter every N bars */
  risk_test_entry_interval?: number
  /** Indicator overrides */
  indicator_overrides?: IndicatorOverride[]
  /** Backtest config */
  config?: StrategyLabBacktestConfig
}

/**
 * Module Test Response
 *
 * Response from module isolation test API.
 */
export interface ModuleTestResponse {
  /** Original request */
  request: ModuleTestRequest
  /** Test result (null on error) */
  result: ModuleTestResult | null
  /** Total execution time */
  execution_time_seconds: number
  /** Data fetch time */
  data_fetch_time_seconds: number
  /** Test execution time */
  test_time_seconds: number
  /** Status */
  status: 'success' | 'error'
  /** Error message (if status is error) */
  error_message: string | null
}

/**
 * Module Test Mode Info
 *
 * Information about a test mode for UI display.
 */
export interface ModuleTestModeInfo {
  /** Mode ID */
  id: ModuleTestMode
  /** Display name */
  name: string
  /** Description */
  description: string
  /** Use case */
  use_case: string
  /** Metrics collected */
  metrics: string[]
  /** Mode-specific options */
  options?: Record<string, string>
}
