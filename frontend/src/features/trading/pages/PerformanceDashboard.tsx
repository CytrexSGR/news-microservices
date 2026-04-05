/**
 * Performance Dashboard
 *
 * Overview of all trading strategies with performance metrics.
 *
 * Features:
 * - Quick overview with strategy summaries
 * - On-demand backtest trigger for detailed metrics
 * - Comparison table across strategies
 * - Real-time updates
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { RefreshCw, TrendingUp, Activity, BarChart3, Target, Settings } from 'lucide-react';
import type { StrategyStats } from '../types/strategy';
import { formatPercent } from '../utils/formatters';
import { OptimizationStartDialog } from '../components/OptimizationStartDialog';
import type { OptimizationJob } from '../types/optimization';
import { predictionClient } from '@/lib/api-client';

// Strategy configurations - matching actual database strategies
const STRATEGIES = [
  { id: 'Freqtrade Adaptive Futures Strategy', name: 'Freqtrade Adaptive', description: 'Adaptive futures with regime-based logic' },
  // Legacy strategies (disabled until implemented in DB)
  // { id: 'OI_Trend', name: 'OI Trend', description: 'Open Interest trend with RSI confirmation' },
  // { id: 'MeanReversion', name: 'Mean Reversion', description: 'RSI + Bollinger Bands' },
  // { id: 'GoldenPocket', name: 'Golden Pocket', description: 'Fibonacci 0.618-0.65 zone' },
  // { id: 'VolatilityBreakout', name: 'Volatility Breakout', description: 'Bollinger Band Squeeze' },
];

// Map frontend strategy IDs to backend backtest strategy names
const STRATEGY_BACKTEST_MAPPING: Record<string, string> = {
  'Freqtrade Adaptive Futures Strategy': 'freqtrade_adaptive_futures_v1',
  // Legacy mappings (commented out)
  // 'OI_Trend': 'oi_trend',
  // 'MeanReversion': 'mean_reversion',
  // 'GoldenPocket': 'golden_pocket',
  // 'VolatilityBreakout': 'volatility_breakout',
};

// Backtest interfaces (from backtesting API)
interface BacktestRequest {
  strategy: string;
  symbol: string;
  timeframe: '15m' | '1h' | '4h' | '1d';
  start_date: string;
  end_date: string;
  initial_capital?: number;
}

interface BacktestMetrics {
  total_return_pct: number;
  win_rate: number;
  max_drawdown_pct: number;
  profit_factor: number;
  sharpe_ratio?: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win?: number;
  avg_loss?: number;
}

interface BacktestResult {
  id: string;
  metrics: BacktestMetrics;
  status: 'completed' | 'failed';
  error_message?: string;
}

export default function PerformanceDashboard() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [optimizationDialogOpen, setOptimizationDialogOpen] = useState(false);
  const [optimizationStrategyId, setOptimizationStrategyId] = useState<string | null>(null);
  const [optimizationJob, setOptimizationJob] = useState<OptimizationJob | null>(null);

  // Fetch quick stats for all strategies
  const { data: strategiesStats, isLoading, isRefetching } = useQuery<Record<string, StrategyStats>>({
    queryKey: ['all-strategies-stats'],
    queryFn: async () => {
      const promises = STRATEGIES.map(async (strategy) => {
        try {
          const response = await predictionClient.get<StrategyStats>(
            `/strategies/${strategy.id}/stats`,
            { days: '7' }
          );
          return [strategy.id, response.data];
        } catch (error) {
          console.warn(`Failed to fetch stats for ${strategy.id}`);
          return [strategy.id, null];
        }
      });
      const results = await Promise.all(promises);
      return Object.fromEntries(results.filter(([_, stats]) => stats !== null));
    },
    refetchInterval: 60000,
    retry: 2,
  });

  // Backtest mutation
  const backtestMutation = useMutation({
    mutationFn: async (request: BacktestRequest) => {
      const response = await predictionClient.post<BacktestResult>(
        '/backtesting/run',
        request
      );

      return response.data;
    },
    onSuccess: (result) => {
      setBacktestResult(result);
    },
  });

  const handleRunBacktest = (strategyId: string) => {
    setSelectedStrategy(strategyId);

    // Calculate date range (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    const request: BacktestRequest = {
      strategy: STRATEGY_BACKTEST_MAPPING[strategyId] || strategyId.toLowerCase(),
      symbol: 'BTC/USDT',
      timeframe: '1h',
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      initial_capital: 10000,
    };

    backtestMutation.mutate(request);
  };

  const handleOptimizeClick = (strategyId: string) => {
    setOptimizationStrategyId(strategyId);
    setOptimizationDialogOpen(true);
  };

  const handleOptimizationSuccess = (job: OptimizationJob) => {
    setOptimizationJob(job);
    // TODO: Navigate to optimization job monitor or show success toast
    console.log('Optimization job created:', job);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin">
          <RefreshCw className="h-8 w-8" />
        </div>
      </div>
    );
  }

  if (!strategiesStats || Object.keys(strategiesStats).length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            No strategy data available
          </CardContent>
        </Card>
      </div>
    );
  }

  // Calculate totals
  const totalAnalyses = Object.values(strategiesStats).reduce(
    (sum, stats) => sum + (stats?.total_analyses || 0),
    0
  );
  const activeStrategies = Object.keys(strategiesStats).length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Performance Dashboard</h1>
          <p className="text-muted-foreground">
            Trading strategy performance overview (last 7 days)
          </p>
        </div>
        {isRefetching && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Updating...
          </div>
        )}
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Analyses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAnalyses}</div>
            <p className="text-xs text-muted-foreground mt-1">Last 7 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Strategies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeStrategies}</div>
            <p className="text-xs text-muted-foreground mt-1">Currently running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Symbols Tracked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-1">
              <Badge variant="outline">BTC/USDT</Badge>
              <Badge variant="outline">ETH/USDT</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategy Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {STRATEGIES.map((strategy) => {
              const stats = strategiesStats[strategy.id];
              if (!stats) return null;

              // Calculate weighted average confidence (excluding NEUTRAL)
              const signalConfidence = Object.entries(stats.avg_confidence_by_signal || {})
                .filter(([signal]) => signal !== 'NEUTRAL')
                .map(([_, conf]) => conf);
              const avgSignalConfidence = signalConfidence.length > 0
                ? signalConfidence.reduce((sum, conf) => sum + conf, 0) / signalConfidence.length
                : 0;

              // Determine dominant signal
              const nonNeutralSignals = Object.entries(stats.signal_distribution || {})
                .filter(([signal]) => signal !== 'NEUTRAL');
              const dominantSignal = nonNeutralSignals.length > 0
                ? nonNeutralSignals.reduce((max, [signal, count]) =>
                    count > (stats.signal_distribution[max] || 0) ? signal : max,
                    nonNeutralSignals[0][0]
                  )
                : 'NEUTRAL';

              const isLoadingBacktest = backtestMutation.isPending && selectedStrategy === strategy.id;

              return (
                <div
                  key={strategy.id}
                  className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{strategy.name}</h3>
                      <Badge variant="outline" className={
                        dominantSignal === 'LONG' ? 'bg-green-100 text-green-800 border-green-300' :
                        dominantSignal === 'SHORT' ? 'bg-red-100 text-red-800 border-red-300' :
                        'bg-gray-100 text-gray-800 border-gray-300'
                      }>
                        {dominantSignal}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{strategy.description}</p>
                  </div>

                  <div className="flex items-center gap-6 mr-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Signals (7d)</p>
                      <p className="text-lg font-semibold">{stats.total_analyses}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Avg. Confidence</p>
                      <p className="text-lg font-semibold">{formatPercent(avgSignalConfidence)}</p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleOptimizeClick(strategy.id)}
                      className="min-w-[120px]"
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Optimize
                    </Button>
                    <Button
                      onClick={() => handleRunBacktest(strategy.id)}
                      disabled={isLoadingBacktest}
                      className="min-w-[140px]"
                    >
                      {isLoadingBacktest ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="mr-2 h-4 w-4" />
                          Run Backtest
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Backtest Result Modal */}
      {backtestResult && (
        <Card className="border-primary">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Backtest Results: {STRATEGIES.find(s => s.id === selectedStrategy)?.name}</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setBacktestResult(null)}>
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {backtestResult.status === 'completed' ? (
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Total Return</p>
                  <p className={`text-2xl font-bold ${
                    backtestResult.metrics.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {backtestResult.metrics.total_return_pct >= 0 ? '+' : ''}
                    {backtestResult.metrics.total_return_pct.toFixed(2)}%
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                  <p className="text-2xl font-bold">
                    {formatPercent(backtestResult.metrics.win_rate)}
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                  <p className="text-2xl font-bold">
                    {backtestResult.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Max Drawdown</p>
                  <p className="text-2xl font-bold text-red-600">
                    {backtestResult.metrics.max_drawdown_pct.toFixed(2)}%
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Profit Factor</p>
                  <p className="text-2xl font-bold">
                    {backtestResult.metrics.profit_factor.toFixed(2)}
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Total Trades</p>
                  <p className="text-2xl font-bold">{backtestResult.metrics.total_trades}</p>
                  <p className="text-xs text-muted-foreground">
                    {backtestResult.metrics.winning_trades}W / {backtestResult.metrics.losing_trades}L
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
                <p className="font-semibold">Backtest Failed</p>
                <p className="text-sm mt-1">{backtestResult.error_message || 'Unknown error occurred'}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Backtest Error */}
      {backtestMutation.isError && (
        <Card className="border-destructive">
          <CardContent className="p-4 text-destructive">
            <p className="font-semibold">Failed to run backtest</p>
            <p className="text-sm mt-1">
              {backtestMutation.error instanceof Error
                ? backtestMutation.error.message
                : 'An unknown error occurred'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Optimization Job Success */}
      {optimizationJob && (
        <Card className="border-primary">
          <CardContent className="p-4 text-primary">
            <p className="font-semibold">✅ Optimization Job Started</p>
            <p className="text-sm mt-1">
              Job ID: {optimizationJob.id} - Status: {optimizationJob.status}
            </p>
            <p className="text-sm mt-1">
              Progress: {optimizationJob.trials_completed} / {optimizationJob.trials_total} trials
            </p>
          </CardContent>
        </Card>
      )}

      {/* Optimization Dialog */}
      {optimizationStrategyId && (
        <OptimizationStartDialog
          strategyId={optimizationStrategyId}
          strategyName={STRATEGIES.find(s => s.id === optimizationStrategyId)?.name || optimizationStrategyId}
          isOpen={optimizationDialogOpen}
          onClose={() => setOptimizationDialogOpen(false)}
          onSuccess={handleOptimizationSuccess}
        />
      )}
    </div>
  );
}
