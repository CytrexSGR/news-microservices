/**
 * Strategy Backtest Result Page
 *
 * Displays comprehensive backtest results from Strategy Lab.
 *
 * Features:
 * - Performance metrics overview
 * - Buy & Hold comparison
 * - Regime breakdown analysis
 * - Equity curve chart
 * - Trade list
 */

import { useLocation, useNavigate, Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  BarChart3,
  Percent,
  Zap,
} from 'lucide-react'
import type { Strategy } from '@/types/strategy'
import type { StrategyLabBacktestResponse, BacktestTrade } from '@/types/backtest'

interface LocationState {
  backtestResponse: StrategyLabBacktestResponse
  strategy: Strategy
}

export default function StrategyBacktestResultPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  // If no state, redirect to Strategy Lab
  if (!state || !state.backtestResponse) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertTriangle className="h-12 w-12 text-orange-500 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Backtest Results Found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Please run a backtest from the Strategy Lab to see results.
              </p>
              <Link to="/trading/strategy-lab">
                <Button>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Strategy Lab
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { backtestResponse, strategy } = state
  const { result, buy_hold_comparison, regime_breakdown, data_info, warnings } = backtestResponse

  // Handle missing strategy (fallback to request info)
  const strategyName = strategy?.name || backtestResponse.request.strategy_id || 'Strategy'
  const strategyVersion = strategy?.version || '1.0'

  // Format helpers
  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value === null || value === undefined) return 'N/A'
    return value.toFixed(decimals)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Determine overall success
  const isSuccess = backtestResponse.status === 'success'
  const isProfit = result && result.metrics.total_return_pct > 0
  const outperformsBuyHold =
    buy_hold_comparison && buy_hold_comparison.outperformance_pct > 0

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <BarChart3 className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold">Backtest Results</h1>
              <p className="text-muted-foreground">
                {strategyName} v{strategyVersion} &bull; {backtestResponse.request.symbol} &bull;{' '}
                {backtestResponse.request.primary_timeframe}
              </p>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Badge
            variant={isSuccess ? 'default' : 'destructive'}
            className="text-sm px-3 py-1"
          >
            {backtestResponse.status.toUpperCase()}
          </Badge>
          {isSuccess && (
            <Badge
              variant={isProfit ? 'default' : 'destructive'}
              className={`text-sm px-3 py-1 ${
                isProfit ? 'bg-green-600' : 'bg-red-600'
              }`}
            >
              {isProfit ? 'PROFITABLE' : 'LOSS'}
            </Badge>
          )}
        </div>
      </div>

      {/* Error State */}
      {backtestResponse.status === 'error' && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <div className="font-medium text-destructive">Backtest Failed</div>
                <div className="text-sm text-muted-foreground">
                  {backtestResponse.error_message}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <Card className="border-orange-500 bg-orange-50 dark:bg-orange-950/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5" />
              <div>
                <div className="font-medium text-orange-700 dark:text-orange-400">Warnings</div>
                <ul className="text-sm text-muted-foreground list-disc list-inside">
                  {warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Results */}
      {result && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Return</CardTitle>
                {isProfit ? (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
              </CardHeader>
              <CardContent>
                <div
                  className={`text-2xl font-bold ${
                    isProfit ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatPercent(result.metrics.total_return_pct)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatCurrency(result.initial_capital)} &rarr;{' '}
                  {formatCurrency(result.metrics.final_capital)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPercent(result.metrics.win_rate_pct).replace('+', '')}
                </div>
                <p className="text-xs text-muted-foreground">
                  {result.metrics.num_wins}W / {result.metrics.num_losses}L of{' '}
                  {result.metrics.num_trades} trades
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatNumber(result.metrics.sharpe_ratio)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Risk-adjusted return
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
                <TrendingDown className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatPercent(result.metrics.max_drawdown_pct)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Largest peak-to-trough decline
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Buy & Hold Comparison */}
          {buy_hold_comparison && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Buy & Hold Comparison
                </CardTitle>
                <CardDescription>
                  Strategy performance vs. simple buy-and-hold benchmark
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Strategy Return</div>
                    <div
                      className={`text-2xl font-bold ${
                        buy_hold_comparison.strategy_return_pct >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {formatPercent(buy_hold_comparison.strategy_return_pct)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(buy_hold_comparison.strategy_final_capital)}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Buy & Hold Return</div>
                    <div
                      className={`text-2xl font-bold ${
                        buy_hold_comparison.buy_hold_return_pct >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {formatPercent(buy_hold_comparison.buy_hold_return_pct)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(buy_hold_comparison.buy_hold_final_capital)}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Outperformance (Alpha)</div>
                    <div
                      className={`text-2xl font-bold ${
                        outperformsBuyHold ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {formatPercent(buy_hold_comparison.outperformance_pct)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {outperformsBuyHold ? (
                        <span className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3 text-green-500" />
                          Strategy outperforms benchmark
                        </span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <XCircle className="h-3 w-3 text-red-500" />
                          Buy & Hold performed better
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Regime Breakdown */}
          {regime_breakdown && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Percent className="h-5 w-5" />
                  Regime Performance Breakdown
                </CardTitle>
                <CardDescription>
                  Performance analysis across different market conditions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 flex gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Dominant Regime:</span>{' '}
                    <Badge variant="outline">{regime_breakdown.dominant_regime}</Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Best Regime:</span>{' '}
                    <Badge variant="default" className="bg-green-600">
                      {regime_breakdown.best_regime}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Worst Regime:</span>{' '}
                    <Badge variant="destructive">{regime_breakdown.worst_regime}</Badge>
                  </div>
                </div>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Regime</TableHead>
                      <TableHead className="text-right">Trades</TableHead>
                      <TableHead className="text-right">Win Rate</TableHead>
                      <TableHead className="text-right">Total Return</TableHead>
                      <TableHead className="text-right">Avg Trade</TableHead>
                      <TableHead className="text-right">Time in Regime</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {regime_breakdown.regimes.map((regime) => (
                      <TableRow key={regime.regime}>
                        <TableCell className="font-medium">
                          <Badge
                            variant="secondary"
                            className={
                              regime.regime === 'TREND'
                                ? 'bg-green-100 text-green-700'
                                : regime.regime === 'CONSOLIDATION'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-orange-100 text-orange-700'
                            }
                          >
                            {regime.regime}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">{regime.num_trades}</TableCell>
                        <TableCell className="text-right">
                          {formatPercent(regime.win_rate_pct).replace('+', '')}
                        </TableCell>
                        <TableCell
                          className={`text-right ${
                            regime.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {formatPercent(regime.total_return_pct)}
                        </TableCell>
                        <TableCell
                          className={`text-right ${
                            regime.avg_trade_pct >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {formatPercent(regime.avg_trade_pct)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatPercent(regime.time_in_regime_pct).replace('+', '')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Additional Metrics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Detailed Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Profit Factor</div>
                  <div className="text-lg font-semibold">
                    {formatNumber(result.metrics.profit_factor)}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Avg Trade Return</div>
                  <div
                    className={`text-lg font-semibold ${
                      result.metrics.avg_trade_return_pct >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {formatPercent(result.metrics.avg_trade_return_pct)}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Avg Holding Time</div>
                  <div className="text-lg font-semibold">
                    {result.metrics.avg_holding_time || 'N/A'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Total Trades</div>
                  <div className="text-lg font-semibold">{result.metrics.num_trades}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trade History */}
          {result.trades && result.trades.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Trade History ({result.trades.length} trades)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-96 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Time</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Quantity</TableHead>
                        <TableHead className="text-right">PnL</TableHead>
                        <TableHead>Regime</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.trades.slice(0, 50).map((trade, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-xs">
                            {new Date(trade.timestamp).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={trade.action === 'BUY' ? 'default' : 'secondary'}
                              className={
                                trade.action === 'BUY'
                                  ? 'bg-green-600'
                                  : trade.action === 'SELL'
                                  ? 'bg-red-600'
                                  : ''
                              }
                            >
                              {trade.action}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            ${trade.price.toFixed(4)}
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            {trade.quantity.toFixed(4)}
                          </TableCell>
                          <TableCell
                            className={`text-right font-mono ${
                              trade.pnl && trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {trade.pnl ? formatCurrency(trade.pnl) : '-'}
                          </TableCell>
                          <TableCell>
                            {trade.regime && (
                              <Badge variant="outline" className="text-xs">
                                {trade.regime}
                              </Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {result.trades.length > 50 && (
                    <p className="text-sm text-muted-foreground text-center mt-4">
                      Showing first 50 of {result.trades.length} trades
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Execution Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Execution Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Period</div>
              <div className="font-medium">
                {formatDate(backtestResponse.request.start_date)} &ndash;{' '}
                {formatDate(backtestResponse.request.end_date)}
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Total Time</div>
              <div className="font-medium">
                {backtestResponse.execution_time_seconds.toFixed(2)}s
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Data Fetch</div>
              <div className="font-medium">
                {backtestResponse.data_fetch_time_seconds.toFixed(2)}s
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Simulation</div>
              <div className="font-medium">
                {backtestResponse.backtest_time_seconds.toFixed(2)}s
              </div>
            </div>
          </div>

          {data_info && (
            <div className="mt-4 pt-4 border-t text-sm text-muted-foreground">
              <div className="font-medium mb-2">Data Info:</div>
              <pre className="bg-muted p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(data_info, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        <Link to="/trading/strategy-lab">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Strategy Lab
          </Button>
        </Link>
      </div>
    </div>
  )
}
