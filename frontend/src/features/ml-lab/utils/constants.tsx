/**
 * ML Lab Constants
 *
 * Shared constants for ML Lab components including icons, colors, and descriptions.
 */

import {
  Activity,
  TrendingUp,
  Target,
  Zap,
  Shield,
  BarChart3,
} from 'lucide-react';
import { MLArea, ModelStatus, TrainingStatus } from '../types';

// ============================================================================
// Area Icons
// ============================================================================

export const AREA_ICONS: Record<MLArea, React.ReactNode> = {
  [MLArea.REGIME]: <Activity className="h-4 w-4" />,
  [MLArea.DIRECTION]: <TrendingUp className="h-4 w-4" />,
  [MLArea.ENTRY]: <Target className="h-4 w-4" />,
  [MLArea.EXIT]: <Zap className="h-4 w-4" />,
  [MLArea.RISK]: <Shield className="h-4 w-4" />,
  [MLArea.VOLATILITY]: <BarChart3 className="h-4 w-4" />,
};

// ============================================================================
// Area Descriptions
// ============================================================================

export const AREA_DESCRIPTIONS: Record<MLArea, string> = {
  [MLArea.REGIME]: 'Detects market regime (trending, ranging, volatile, quiet)',
  [MLArea.DIRECTION]: 'Predicts price direction (bullish, bearish, neutral)',
  [MLArea.ENTRY]: 'Identifies optimal entry points',
  [MLArea.EXIT]: 'Signals when to exit positions',
  [MLArea.RISK]: 'Assesses current risk level (low, medium, high)',
  [MLArea.VOLATILITY]: 'Classifies volatility regime',
};

// ============================================================================
// Status Colors
// ============================================================================

export const STATUS_COLORS: Record<ModelStatus, string> = {
  [ModelStatus.DRAFT]: 'bg-gray-500',
  [ModelStatus.TRAINING]: 'bg-blue-500',
  [ModelStatus.ACTIVE]: 'bg-green-500',
  [ModelStatus.FAILED]: 'bg-red-500',
  [ModelStatus.ARCHIVED]: 'bg-gray-400',
};

export const TRAINING_STATUS_COLORS: Record<TrainingStatus, string> = {
  [TrainingStatus.PENDING]: 'bg-yellow-500',
  [TrainingStatus.RUNNING]: 'bg-blue-500',
  [TrainingStatus.COMPLETED]: 'bg-green-500',
  [TrainingStatus.FAILED]: 'bg-red-500',
};

// ============================================================================
// Trading Constants
// ============================================================================

export const SYMBOLS = [
  { value: 'XRPUSDT', label: 'XRP/USDT' },
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'SOLUSDT', label: 'SOL/USDT' },
  { value: 'ADAUSDT', label: 'ADA/USDT' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT' },
  { value: 'LINKUSDT', label: 'LINK/USDT' },
  { value: 'MATICUSDT', label: 'MATIC/USDT' },
];

export const TIMEFRAMES = [
  { value: '1min', label: '1m' },
  { value: '5min', label: '5m' },
  { value: '15min', label: '15m' },
  { value: '1H', label: '1H' },
  { value: '4H', label: '4H' },
  { value: '1D', label: '1D' },
];

// ============================================================================
// Gate Prediction Labels
// ============================================================================

export const GATE_PREDICTION_LABELS: Record<MLArea, Record<string, string>> = {
  [MLArea.REGIME]: {
    trending: 'Trending',
    ranging: 'Ranging',
    volatile: 'Volatile',
    quiet: 'Quiet',
  },
  [MLArea.DIRECTION]: {
    bullish: 'Bullish',
    bearish: 'Bearish',
    neutral: 'Neutral',
  },
  [MLArea.ENTRY]: {
    enter: 'Enter',
    wait: 'Wait',
  },
  [MLArea.EXIT]: {
    exit: 'Exit',
    hold: 'Hold',
  },
  [MLArea.RISK]: {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
  },
  [MLArea.VOLATILITY]: {
    low: 'Low',
    normal: 'Normal',
    high: 'High',
    extreme: 'Extreme',
  },
};

// ============================================================================
// Prediction Colors
// ============================================================================

export const PREDICTION_COLORS: Record<string, string> = {
  // Direction
  bullish: 'text-green-500',
  bearish: 'text-red-500',
  neutral: 'text-gray-500',

  // Entry/Exit
  enter: 'text-green-500',
  wait: 'text-gray-500',
  exit: 'text-red-500',
  hold: 'text-blue-500',

  // Risk
  low: 'text-green-500',
  medium: 'text-yellow-500',
  high: 'text-red-500',

  // Regime
  trending: 'text-blue-500',
  ranging: 'text-purple-500',
  volatile: 'text-orange-500',
  quiet: 'text-gray-500',

  // Volatility
  normal: 'text-green-500',
  extreme: 'text-red-500',
};

// ============================================================================
// Action Labels
// ============================================================================

export const ACTION_LABELS: Record<string, string> = {
  enter_long: 'Enter Long',
  enter_short: 'Enter Short',
  exit: 'Exit Position',
  hold: 'Hold',
};

export const ACTION_COLORS: Record<string, string> = {
  enter_long: 'text-green-500 bg-green-500/10',
  enter_short: 'text-red-500 bg-red-500/10',
  exit: 'text-orange-500 bg-orange-500/10',
  hold: 'text-gray-500 bg-gray-500/10',
};

// ============================================================================
// Paper Trading Configuration
// ============================================================================

export const PAPER_TRADING_CONFIG = {
  /** Default tick interval in seconds (matches backend default) */
  TICK_INTERVAL_SECONDS: 60,  // Changed from 10s - prevents API overload

  /** Status polling interval in milliseconds */
  STATUS_POLL_INTERVAL_MS: 5000,

  /** Maximum trades to show in history */
  MAX_TRADE_HISTORY: 100,

  /** Default symbol */
  DEFAULT_SYMBOL: 'XRPUSDT',

  /** Default timeframe */
  DEFAULT_TIMEFRAME: '5min',

  /** Indicator refresh interval in milliseconds */
  INDICATOR_REFRESH_INTERVAL_MS: 30000,
} as const;
