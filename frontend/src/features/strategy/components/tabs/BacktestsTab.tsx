/**
 * BacktestsTab Component
 *
 * Displays saved backtests with expandable details and supports
 * running new backtests with SSE progress tracking.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  PlayCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Trash2,
  Eye,
} from 'lucide-react';
import type { BacktestSummary, Strategy } from '../../types';
import type { StrategyLabBacktestRequest } from '@/types/backtest';

interface BacktestsTabProps {
  strategyId: string;
  strategy: Strategy;
  backtests: BacktestSummary[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  onOpenBacktestDialog: () => void;
  onDeleteBacktest: (backtestId: number) => void;
  isDeleting: boolean;
  runningBacktestRequest: StrategyLabBacktestRequest | null;
  backtestProgress: {
    percentage: number;
    phase: string;
    current_bar: number;
    total_bars: number;
  } | null;
  isRunning: boolean;
}

export function BacktestsTab({
  strategyId,
  backtests,
  total,
  isLoading,
  error,
  onOpenBacktestDialog,
  onDeleteBacktest,
  isDeleting,
  runningBacktestRequest,
  backtestProgress,
  isRunning,
}: BacktestsTabProps) {
  const navigate = useNavigate();
  const [expandedBacktest, setExpandedBacktest] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <PlayCircle className="h-5 w-5" />
              Saved Backtests
            </CardTitle>
            <CardDescription>
              Historical backtest results for this strategy
            </CardDescription>
          </div>
          <Button onClick={onOpenBacktestDialog} className="gap-2">
            <PlayCircle className="h-4 w-4" />
            Run New Backtest
          </Button>
        </CardHeader>
        <CardContent>
          {/* Running Backtest Progress with SSE */}
          {runningBacktestRequest && (
            <Card className="mb-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-blue-900 dark:text-blue-100">
                      Running backtest...
                    </div>

                    {/* Progress Bar */}
                    {backtestProgress && (
                      <div className="mt-3">
                        <div className="flex justify-between text-sm text-blue-700 dark:text-blue-300 mb-1">
                          <span>
                            {backtestProgress.phase === 'initializing' && 'Initializing...'}
                            {backtestProgress.phase.startsWith('fetching:') &&
                              backtestProgress.phase !== 'fetching:complete' && (
                                <>
                                  Fetching OHLCV data:{' '}
                                  {backtestProgress.phase
                                    .replace('fetching:', '')
                                    .toUpperCase()}{' '}
                                  ({backtestProgress.current_bar + 1}/
                                  {backtestProgress.total_bars})
                                </>
                              )}
                            {backtestProgress.phase === 'fetching:complete' &&
                              'Data fetched, preparing simulation...'}
                            {backtestProgress.phase === 'fetching' &&
                              'Fetching OHLCV data from Bybit...'}
                            {backtestProgress.phase === 'simulation' &&
                              'Running strategy simulation...'}
                            {backtestProgress.phase === 'calculating' &&
                              'Calculating metrics...'}
                          </span>
                          <span className="font-mono">
                            {backtestProgress.phase.startsWith('fetching:') &&
                            backtestProgress.total_bars > 0
                              ? `${Math.round(
                                  ((backtestProgress.current_bar + 1) /
                                    backtestProgress.total_bars) *
                                    100
                                )}%`
                              : `${backtestProgress.percentage}%`}
                          </span>
                        </div>
                        <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-blue-600 dark:bg-blue-400 h-3 rounded-full transition-all duration-300 ease-out"
                            style={{
                              width: `${
                                backtestProgress.phase.startsWith('fetching:') &&
                                backtestProgress.total_bars > 0
                                  ? Math.round(
                                      ((backtestProgress.current_bar + 1) /
                                        backtestProgress.total_bars) *
                                        100
                                    )
                                  : backtestProgress.percentage
                              }%`,
                            }}
                          />
                        </div>
                        {backtestProgress.phase === 'simulation' &&
                          backtestProgress.total_bars > 0 && (
                            <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 text-right">
                              Bar {backtestProgress.current_bar.toLocaleString()} /{' '}
                              {backtestProgress.total_bars.toLocaleString()}
                            </div>
                          )}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2 mt-3">
                      <Badge variant="outline">{runningBacktestRequest.symbol}</Badge>
                      <Badge variant="outline">
                        {runningBacktestRequest.primary_timeframe}
                      </Badge>
                      <Badge variant="outline">
                        {runningBacktestRequest.start_date} →{' '}
                        {runningBacktestRequest.end_date}
                      </Badge>
                      <Badge variant="outline">
                        $
                        {runningBacktestRequest.config?.initial_capital?.toLocaleString() ||
                          '10,000'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Activity className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to load backtests: {error.message}
              </AlertDescription>
            </Alert>
          ) : backtests.length === 0 ? (
            <div className="text-center py-8">
              <PlayCircle className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground mb-4">
                No backtests have been run for this strategy yet.
              </p>
              <Button
                variant="outline"
                onClick={onOpenBacktestDialog}
                className="gap-2"
              >
                <PlayCircle className="h-4 w-4" />
                Run Your First Backtest
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {backtests.map((backtest) => {
                const isExpanded = expandedBacktest === backtest.id;
                const totalReturn = backtest.metrics.total_return_pct;
                const isPositive = totalReturn !== null && totalReturn >= 0;

                return (
                  <div key={backtest.id} className="border rounded-lg overflow-hidden">
                    {/* Backtest Summary Row */}
                    <div
                      className="p-4 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() =>
                        setExpandedBacktest(isExpanded ? null : backtest.id)
                      }
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            )}
                            <Badge variant="outline">{backtest.symbol}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {backtest.period_start && backtest.period_end && (
                              <>
                                {new Date(backtest.period_start).toLocaleDateString()} -{' '}
                                {new Date(backtest.period_end).toLocaleDateString()}
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          {/* Key Metrics */}
                          <div className="flex items-center gap-4 text-sm">
                            <div className="text-center">
                              <p className="text-muted-foreground text-xs">Return</p>
                              <p
                                className={`font-semibold ${
                                  isPositive ? 'text-green-500' : 'text-red-500'
                                }`}
                              >
                                {totalReturn !== null
                                  ? `${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`
                                  : 'N/A'}
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-muted-foreground text-xs">Sharpe</p>
                              <p className="font-mono">
                                {backtest.metrics.sharpe_ratio !== null
                                  ? backtest.metrics.sharpe_ratio.toFixed(2)
                                  : 'N/A'}
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-muted-foreground text-xs">Win Rate</p>
                              <p className="font-mono">
                                {backtest.metrics.win_rate_pct !== null
                                  ? `${backtest.metrics.win_rate_pct.toFixed(1)}%`
                                  : 'N/A'}
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-muted-foreground text-xs">Trades</p>
                              <p className="font-mono">
                                {backtest.metrics.num_trades ?? 'N/A'}
                              </p>
                            </div>
                          </div>

                          {/* Delete Button */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-muted-foreground hover:text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (
                                confirm('Are you sure you want to delete this backtest?')
                              ) {
                                onDeleteBacktest(backtest.id);
                              }
                            }}
                            disabled={isDeleting}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="p-4 border-t space-y-4">
                        {/* Full Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                          <div className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">
                              Initial Capital
                            </p>
                            <p className="font-semibold">
                              {backtest.initial_capital !== null
                                ? `$${backtest.initial_capital.toLocaleString()}`
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">
                              Final Capital
                            </p>
                            <p
                              className={`font-semibold ${
                                backtest.final_capital &&
                                backtest.initial_capital &&
                                backtest.final_capital > backtest.initial_capital
                                  ? 'text-green-500'
                                  : backtest.final_capital &&
                                    backtest.initial_capital &&
                                    backtest.final_capital < backtest.initial_capital
                                  ? 'text-red-500'
                                  : ''
                              }`}
                            >
                              {backtest.final_capital !== null
                                ? `$${backtest.final_capital.toLocaleString()}`
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">
                              Max Drawdown
                            </p>
                            <p className="font-semibold text-red-500">
                              {backtest.metrics.max_drawdown_pct !== null
                                ? `${backtest.metrics.max_drawdown_pct.toFixed(2)}%`
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">
                              Profit Factor
                            </p>
                            <p className="font-semibold">
                              {backtest.metrics.profit_factor !== null
                                ? backtest.metrics.profit_factor.toFixed(2)
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">Created</p>
                            <p className="font-mono text-sm">
                              {backtest.created_at
                                ? new Date(backtest.created_at).toLocaleString()
                                : 'N/A'}
                            </p>
                          </div>
                          {backtest.config && (
                            <div className="p-3 bg-muted/30 rounded-lg">
                              <p className="text-xs text-muted-foreground mb-1">
                                Timeframe
                              </p>
                              <Badge variant="outline">
                                {(backtest.config as any).primary_timeframe || 'N/A'}
                              </Badge>
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              navigate(
                                `/trading/backtest/results?strategyId=${strategyId}&backtestId=${backtest.id}`
                              )
                            }
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Full Details
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
