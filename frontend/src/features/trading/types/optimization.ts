/**
 * Parameter Optimization Types
 *
 * Types for ML Parameter Optimization feature.
 * Corresponds to prediction-service optimization API.
 */

// Parameter Space Definition
export interface ParameterSpaceItem {
  name: string;
  path: string;
  param_type: 'int' | 'float' | 'categorical';
  low?: number;
  high?: number;
  step?: number;
  choices?: (string | number)[];
}

// Optimization Request
export interface OptimizationRequest {
  parameter_space: ParameterSpaceItem[];
  objective_metric: 'sharpe_ratio' | 'total_return' | 'win_rate' | 'consistency_score';
  n_trials: number;
  market_data_days: number;
  symbol: string;      // Trading pair (e.g., BTCUSDT, ETHUSDT)
  timeframe: string;   // Candlestick timeframe (1m, 5m, 15m, 1h, 4h, 1d)
}

// Available trading pairs for optimization
export const AVAILABLE_SYMBOLS = [
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'SOLUSDT', label: 'SOL/USDT' },
  { value: 'BNBUSDT', label: 'BNB/USDT' },
  { value: 'XRPUSDT', label: 'XRP/USDT' },
  { value: 'ADAUSDT', label: 'ADA/USDT' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT' },
  { value: 'AVAXUSDT', label: 'AVAX/USDT' },
  { value: 'LINKUSDT', label: 'LINK/USDT' },
  { value: 'DOTUSDT', label: 'DOT/USDT' },
] as const;

// Available timeframes for optimization (all Bybit-compatible intervals)
export const AVAILABLE_TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1w', label: '1 Week' },
] as const;

// Optimization Job Response
export interface OptimizationJob {
  id: string;
  strategy_id: string;
  status: 'pending' | 'loading_data' | 'running' | 'completed' | 'failed' | 'cancelled';
  trials_completed: number;
  trials_total: number;
  progress_percentage: number;
  objective_metric: string;
  best_score: string | null;
  best_params: Record<string, number | string> | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number;
  error_message: string | null;
}

// Optimization Results
export interface OptimizationResult {
  id: string;
  strategy_id: string;
  best_params: Record<string, number | string>;
  best_score: string;
  optimization_history: [number, number][]; // [trial_number, score]
  walk_forward_metrics: WalkForwardMetrics | null;
  parameter_importances: Record<string, number> | null; // Parameter sensitivity analysis
  objective_metric: string;
  trials_completed: number;
  duration_seconds: number;
}

// Walk-Forward Validation Metrics
export interface WalkForwardMetrics {
  avg_train_sharpe: number | null;
  avg_test_sharpe: number | null;
  train_test_correlation: number | null;
  overfitting_ratio: number | null;
  consistency_score: number | null;
  total_windows: number;
  successful_windows: number;
}

// Apply Parameters Request
export interface ApplyParamsRequest {
  create_new_version: boolean;
}

// Apply Parameters Response
export interface ApplyParamsResponse {
  strategy_id: string;
  message: string;
}

// Parameter Validation (Phase 6)
export interface ParameterValidationResult {
  name: string;
  path: string;
  is_valid: boolean;
  error_message: string | null;
  current_value: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

export interface ValidateParametersRequest {
  parameter_space: ParameterSpaceItem[];
}

export interface ValidateParametersResponse {
  strategy_id: string;
  strategy_name: string;
  is_valid: boolean;
  results: ParameterValidationResult[];
  invalid_count: number;
}

// Predefined Parameter Spaces for Freqtrade Adaptive Futures Strategy
// Fixed 2025-12-06: Corrected all parameter paths to match actual strategy structure
// See: services/prediction-service/PARAMETER_PRESET_VALIDATION.md
export const COMMON_PARAMETER_SPACES: Record<string, ParameterSpaceItem[]> = {
  // ✅ FIXED: RSI Optimization (was RSI_Strategy)
  // - rsi_period: ✅ Kept (already correct)
  // - entry_threshold: ✅ Fixed (was conditions.0.threshold)
  // - take_profit_ratio: ✅ Fixed (was exit.conditions.0.threshold)
  RSI_Optimization: [
    {
      name: 'rsi_period',
      path: 'indicators.0.params.period',  // ✅ 1h_RSI_14
      param_type: 'int',
      low: 7,
      high: 21,
    },
    {
      name: 'entry_threshold',
      path: 'logic.TREND.entry.threshold',  // ✅ Fixed: Global threshold, not per-condition
      param_type: 'float',
      low: 0.5,
      high: 0.9,
      step: 0.05,
    },
    {
      name: 'take_profit_ratio',
      path: 'logic.TREND.exit.rules.0.config.profit_ratio',  // ✅ Fixed: Exit rules, not conditions
      param_type: 'float',
      low: 0.02,
      high: 0.05,
      step: 0.005,
    },
  ],

  // ✅ FIXED: EMA Crossover (was MA_Crossover)
  // - Renamed for accuracy (uses EMA, not MA/SMA)
  // - fast_ema_period: ✅ Fixed (was indicators.0 = RSI)
  // - medium_ema_period: ✅ Fixed (was indicators.1 = MACD)
  // - slow_ema_period: ✅ Added (new parameter)
  EMA_Crossover: [
    {
      name: 'fast_ema_period',
      path: 'indicators.2.params.period',  // ✅ Fixed: 1h_EMA_20 (was RSI at index 0)
      param_type: 'int',
      low: 10,
      high: 30,
    },
    {
      name: 'medium_ema_period',
      path: 'indicators.3.params.period',  // ✅ Fixed: 1h_EMA_50 (was MACD at index 1)
      param_type: 'int',
      low: 30,
      high: 100,
    },
    {
      name: 'slow_ema_period',
      path: 'indicators.4.params.period',  // ✅ New: 1h_EMA_200
      param_type: 'int',
      low: 100,
      high: 300,
    },
  ],

  // ✅ FIXED: Bollinger Bands
  // - bb_period: ✅ Fixed (was indicators.0 = RSI)
  // - bb_stddev: ✅ Fixed (was std_dev on RSI, now stddev on BB)
  Bollinger_Bands: [
    {
      name: 'bb_period',
      path: 'indicators.10.params.period',  // ✅ Fixed: 1h_BBW_20 (was RSI at index 0)
      param_type: 'int',
      low: 10,
      high: 30,
    },
    {
      name: 'bb_stddev',
      path: 'indicators.10.params.stddev',  // ✅ Fixed: Correct key (was std_dev)
      param_type: 'float',
      low: 1.5,
      high: 3.0,
      step: 0.1,
    },
  ],

  // ✅ FIXED: Risk Management
  // - take_profit_ratio: ✅ Fixed (was riskManagement.takeProfit.value)
  // - trailing_offset: ✅ Fixed (replaces non-existent stopLoss.value)
  Risk_Management: [
    {
      name: 'take_profit_ratio',
      path: 'logic.TREND.exit.rules.0.config.profit_ratio',  // ✅ Fixed: Exit rules, not risk.takeProfit
      param_type: 'float',
      low: 0.02,
      high: 0.05,
      step: 0.005,
    },
    {
      name: 'trailing_offset',
      path: 'logic.TREND.exit.rules.1.config.trailing_offset',  // ✅ Fixed: Trailing stop config
      param_type: 'float',
      low: 0.003,
      high: 0.01,
      step: 0.001,
    },
  ],

  // ✅ NEW: Regime Detection
  // Optimize market regime detection thresholds
  Regime_Detection: [
    {
      name: 'adx_trend_min',
      path: 'regimeDetection.config.thresholds.TREND.adx_min',
      param_type: 'int',
      low: 20,
      high: 30,
    },
    {
      name: 'bbw_volatility_min',
      path: 'regimeDetection.config.thresholds.HIGH_VOLATILITY.bbw_min',
      param_type: 'float',
      low: 0.04,
      high: 0.08,
      step: 0.01,
    },
  ],
};

// Preset Descriptions for UI
export const PRESET_DESCRIPTIONS: Record<string, string> = {
  RSI_Optimization: 'Optimize RSI-based entry/exit strategy with period, entry threshold, and take profit settings. Best for momentum trading.',
  EMA_Crossover: 'Optimize exponential moving average crossover strategy with fast (20), medium (50), and slow (200) EMA periods. Best for trend following.',
  Bollinger_Bands: 'Optimize Bollinger Bands volatility strategy with configurable period and standard deviation. Best for mean reversion.',
  Risk_Management: 'Optimize risk management parameters including take profit ratio and trailing stop offset. Best for position sizing.',
  Regime_Detection: 'Optimize market regime detection thresholds for ADX trend strength and BBW volatility. Best for adaptive strategies.',
};
