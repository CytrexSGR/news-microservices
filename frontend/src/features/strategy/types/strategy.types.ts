/**
 * Strategy Types
 *
 * Extracted from StrategyOverview.tsx for reusability across components.
 */

// ============================================================================
// Strategy Definition Types
// ============================================================================

export interface StrategyDefinition {
  strategyId: string;
  name: string;
  version: string;
  description: string;
  regimeDetection: RegimeDetectionConfig;
  indicators: IndicatorConfig[];
  logic: {
    [regime: string]: RegimeLogic;
  };
  execution: ExecutionConfig;
  metadata: StrategyMetadata;
}

export interface RegimeDetectionConfig {
  method: string;
  timeframe: string;
  indicators: {
    adx?: { period: number };
    bbw?: { period: number; std_dev: number };
  };
  thresholds: {
    trend_adx: number;
    volatility_bbw: number;
  };
}

export interface IndicatorConfig {
  /** Unique indicator ID with timeframe prefix (e.g., '1h_RSI_14') */
  id: string;
  /** Indicator type (RSI, MACD, EMA, ATR, etc.) */
  type: string;
  /** Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w) */
  timeframe: string;
  /** Indicator parameters (period, fast, slow, signal, etc.) */
  params: Record<string, number>;
  /** Human-readable description */
  description?: string;
}

export interface RegimeLogic {
  entry: {
    enabled: boolean;
    conditions: EntryCondition[];
    aggregation: string;
    threshold: number;
    description: string;
  };
  exit: {
    rules: ExitRule[];
  };
  risk: {
    stopLoss: StopLossConfig;
    positionSize: PositionSizeConfig;
    leverage: LeverageConfig;
  };
}

export interface EntryCondition {
  expression: string;
  confidence: number;
  description: string;
}

export interface ExitRule {
  type: string;
  value?: number;
  description: string;
}

export interface StopLossConfig {
  method: string;
  value?: number;
  atr_multiplier?: number;
  trailing?: boolean;
}

export interface PositionSizeConfig {
  method: string;
  risk_per_trade?: number;
  max_position?: number;
}

export interface LeverageConfig {
  min: number;
  max: number;
  default: number;
  dynamic?: boolean;
}

export interface ExecutionConfig {
  orderType: string;
  slippage: number;
  commission: number;
  pyramiding: number;
}

export interface StrategyMetadata {
  author?: string;
  createdAt?: string;
  updatedAt?: string;
  tags?: string[];
  backtestResults?: Record<string, unknown>;
}

// ============================================================================
// Strategy Model
// ============================================================================

export interface Strategy {
  id: string;
  name: string;
  version: string;
  description: string;
  definition: StrategyDefinition;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Backtest Types
// ============================================================================

export interface BacktestMetrics {
  total_return_pct: number | null;
  sharpe_ratio: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  profit_factor: number | null;
  num_trades: number | null;
}

export interface BacktestSummary {
  id: number;
  strategy_id: string;
  symbol: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string | null;
  initial_capital: number | null;
  final_capital: number | null;
  metrics: BacktestMetrics;
  config: Record<string, unknown> | null;
}

export interface BacktestListResponse {
  strategy_id: string;
  strategy_name: string;
  backtests: BacktestSummary[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface StrategiesListResponse {
  strategies: Strategy[];
  total: number;
}

// ============================================================================
// Component Prop Types
// ============================================================================

export interface StrategyTabProps {
  strategy: Strategy;
  selectedSymbol: string;
  selectedTimeframe: string;
}

export interface StrategyTabWithEvaluationProps extends StrategyTabProps {
  evaluation: import('@/types/strategy-evaluation').StrategyEvaluationResponse | null;
  indicators: import('@/types/indicators').IndicatorsSnapshot | null;
}

// ============================================================================
// Re-exports for convenience
// ============================================================================

export type { Timeframe, IndicatorsSnapshot } from '@/types/indicators';
export type {
  StrategyEvaluationResponse,
  RegimeType,
  TradeDirection,
} from '@/types/strategy-evaluation';
