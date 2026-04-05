import type { OHLCV } from '@/types/market'
import type { BacktestResult, BacktestMetrics, BacktestTrade } from '@/types/backtest'
import type { StrategyConfig } from '@/types/strategy'

/**
 * Generate mock OHLCV data for testing
 */
export function generateMockOHLCV(
  startDate: Date,
  endDate: Date,
  basePrice: number = 100,
  volatility: number = 0.02
): OHLCV[] {
  const data: OHLCV[] = []
  let currentPrice = basePrice
  const oneDay = 24 * 60 * 60 * 1000

  for (
    let timestamp = startDate.getTime();
    timestamp <= endDate.getTime();
    timestamp += oneDay
  ) {
    // Random walk with trend
    const change = (Math.random() - 0.48) * volatility * currentPrice
    currentPrice += change

    const open = currentPrice
    const high = open * (1 + Math.random() * volatility)
    const low = open * (1 - Math.random() * volatility)
    const close = low + Math.random() * (high - low)
    const volume = Math.floor(1000000 + Math.random() * 9000000)

    data.push({
      timestamp: new Date(timestamp).toISOString(),
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume,
    })

    currentPrice = close
  }

  return data
}

/**
 * Generate mock backtest result
 */
export function generateMockBacktest(
  strategyConfig: StrategyConfig,
  symbol: string,
  startDate: string,
  endDate: string,
  initialCapital: number
): BacktestResult {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const ohlcv = generateMockOHLCV(start, end)

  // Simulate trades
  const trades: BacktestTrade[] = []
  let position = 0
  let cash = initialCapital
  let totalTrades = 0
  let winningTrades = 0

  ohlcv.forEach((candle, i) => {
    if (i % 10 === 0 && position === 0) {
      // Buy
      const quantity = Math.floor(cash * 0.1 / candle.close)
      if (quantity > 0) {
        trades.push({
          timestamp: candle.timestamp,
          action: 'BUY',
          price: candle.close,
          quantity,
          reason: 'Mock signal',
        })
        position = quantity
        cash -= quantity * candle.close
        totalTrades++
      }
    } else if (i % 10 === 5 && position > 0) {
      // Sell
      const pnl = position * candle.close - position * trades[trades.length - 1].price
      if (pnl > 0) winningTrades++

      trades.push({
        timestamp: candle.timestamp,
        action: 'SELL',
        price: candle.close,
        quantity: position,
        pnl,
        reason: 'Mock signal',
      })
      cash += position * candle.close
      position = 0
    }
  })

  // Calculate equity curve
  const equityCurve = ohlcv.map((candle) => ({
    timestamp: candle.timestamp,
    value: cash + (position * candle.close),
  }))

  const finalValue = cash + (position * ohlcv[ohlcv.length - 1].close)
  const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100

  const metrics: BacktestMetrics = {
    total_return: Number(totalReturn.toFixed(2)),
    sharpe_ratio: Number((Math.random() * 2).toFixed(2)),
    max_drawdown: Number((Math.random() * -20).toFixed(2)),
    win_rate: Number((winningTrades / totalTrades * 100).toFixed(2)),
    total_trades: totalTrades,
    avg_trade_return: Number((totalReturn / totalTrades).toFixed(2)),
    volatility: Number((Math.random() * 15 + 10).toFixed(2)),
  }

  return {
    id: self.crypto.randomUUID(),
    strategy_config: strategyConfig,
    symbol,
    start_date: startDate,
    end_date: endDate,
    initial_capital: initialCapital,
    status: 'completed',
    metrics,
    trades,
    equity_curve: equityCurve,
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  }
}

