import axios from 'axios';

const API_BASE_URL = '/api/prediction';

// ============================================================================
// Market Matrix Types
// ============================================================================

export type SignalType = 'LONG' | 'SHORT' | 'NEUTRAL';

export interface StrategyAnalysis {
  signal: SignalType;
  confidence: number; // 0.0 - 1.0
  reason: string;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  market_data: Record<string, any>; // RSI, EMA, Bollinger Bands, etc.
  timestamp: string; // ISO timestamp
}

export interface AssetAnalysis {
  current_price: number;
  strategies: Record<string, StrategyAnalysis>; // Strategy name -> Analysis
}

export interface MatrixResponse {
  matrix: Record<string, AssetAnalysis>; // Symbol -> Asset Analysis
  last_updated: string | null; // ISO timestamp or null if no data
  symbols: string[]; // All symbols in matrix
  strategies: string[]; // All strategies in matrix
}

// ============================================================================
// Backtest Types
// ============================================================================

export interface BacktestConfig {
  strategy: string;
  symbol: string;
  timeframe: '15m' | '1h' | '4h' | '1d';
  start_date: string; // ISO date
  end_date: string; // ISO date
  initial_capital: number;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  metrics: {
    total_return_pct: number;
    win_rate: number;
    max_drawdown_pct: number;
    profit_factor: number;
    sharpe_ratio: number | null; // Can be null if insufficient data
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    avg_win: number | null;
    avg_loss: number | null;
    max_consecutive_wins: number;
    max_consecutive_losses: number;
  };
  equity_curve: Array<{
    timestamp: string;
    equity: number;
  }>;
  trades: Array<{
    id: string;
    entry_time: string;
    exit_time: string;
    symbol: string;
    side: 'LONG' | 'SHORT';
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
    pnl_pct: number;
    exit_reason?: string; // SL, TP, Signal, End of backtest
  }>;
  status: 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at: string | null;
  error_message?: string | null;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  required_data: string[]; // e.g., ["ohlcv", "price", "open_interest"]
}

export interface SchedulerStatus {
  enabled: boolean;
  running: boolean;
  interval_minutes: number;
  trading_pairs: string[];
  strategy: string;
  next_run: string | null; // ISO timestamp or null if paused
}

export interface SchedulerControlResponse {
  status: 'success' | 'error';
  message: string;
  scheduler: SchedulerStatus;
}

// API Client
export const predictionAPI = {
  // Strategies
  async getStrategies(): Promise<Strategy[]> {
    const response = await axios.get<Strategy[]>(`${API_BASE_URL}/api/v1/backtesting/strategies`);
    return response.data;
  },

  // Backtesting
  async runBacktest(config: BacktestConfig): Promise<BacktestResult> {
    const response = await axios.post<BacktestResult>(`${API_BASE_URL}/api/v1/backtesting/run`, config);
    return response.data;
  },

  async getBacktestResult(_backtestId: string): Promise<BacktestResult> {
    // TODO: Implement when backend is ready
    // const response = await axios.get(`${API_BASE_URL}/api/v1/backtest/${_backtestId}`);
    // return response.data;

    throw new Error('Get backtest result endpoint not yet implemented. Backend integration pending.');
  },

  async listBacktests(_params?: { limit?: number; status?: string }): Promise<BacktestResult[]> {
    // TODO: Implement when backend is ready
    // const response = await axios.get(`${API_BASE_URL}/api/v1/backtest`, { params: _params });
    // return response.data.backtests || [];

    return [];
  },

  // Health
  async getHealth(): Promise<{ status: string; [key: string]: any }> {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },

  // Trading Scheduler Control
  async getSchedulerStatus(): Promise<SchedulerStatus> {
    const response = await axios.get<{ status: string; scheduler: SchedulerStatus }>(
      `${API_BASE_URL}/control/autotrade/status`
    );
    return response.data.scheduler;
  },

  async toggleAutotrade(enable: boolean): Promise<SchedulerControlResponse> {
    const action = enable ? 'on' : 'off';
    const response = await axios.post<SchedulerControlResponse>(
      `${API_BASE_URL}/control/autotrade/${action}`
    );
    return response.data;
  },

  // Market Matrix
  async getMarketMatrix(): Promise<MatrixResponse> {
    const response = await axios.get<MatrixResponse>(
      `${API_BASE_URL}/api/v1/analytics/matrix`
    );
    return response.data;
  },

  async getSymbolAnalysis(symbol: string): Promise<{
    symbol: string;
    strategies: Record<string, StrategyAnalysis>;
    last_updated: string | null;
  }> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/analytics/matrix/symbol/${symbol}`
    );
    return response.data;
  },

  async getStrategyAnalysis(strategy: string): Promise<{
    strategy: string;
    symbols: Record<string, StrategyAnalysis>;
    last_updated: string | null;
  }> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/analytics/matrix/strategy/${strategy}`
    );
    return response.data;
  },
};

export default predictionAPI;
