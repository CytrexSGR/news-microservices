import type { StrategyConfig } from './strategy'

export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed'

export type BacktestMetrics = {
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  avg_trade_return: number
  volatility: number
}

export type BacktestTrade = {
  timestamp: string
  action: 'BUY' | 'SELL' | 'HOLD'
  price: number
  quantity: number
  pnl?: number
  reason?: string
}

export type BacktestResult = {
  id: string
  strategy_config: StrategyConfig
  symbol: string
  start_date: string
  end_date: string
  initial_capital: number
  status: BacktestStatus
  metrics?: BacktestMetrics
  trades?: BacktestTrade[]
  equity_curve?: { timestamp: string; value: number }[]
  created_at: string
  completed_at?: string
  error?: string
}

export type BacktestRequest = {
  strategy_config: StrategyConfig
  symbol: string
  start_date: string
  end_date: string
  initial_capital: number
}
