/**
 * Backtest Panel Component
 *
 * Historical backtesting interface for ML-driven trading strategies.
 * Allows users to test strategies against historical OHLCV data
 * with optional ML gate integration.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Play,
  History,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Loader2,
  AlertCircle,
  BarChart3,
  Calendar,
  Percent,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Brain,
} from 'lucide-react';
import toast from 'react-hot-toast';

import {
  backtestApi,
  type BacktestConfig,
  type BacktestStatus,
  type BacktestResultResponse,
  type BacktestTrade,
  type BacktestSummary,
} from '../../api/mlLabApi';
import { SYMBOLS, TIMEFRAMES } from '../../utils/constants';

export function BacktestPanel() {
  // Configuration state
  const [symbol, setSymbol] = useState('XRPUSDT');
  const [timeframe, setTimeframe] = useState('5min');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [useMlGates, setUseMlGates] = useState(true);
  const [initialCapital, setInitialCapital] = useState(10000);
  const [positionSizePct, setPositionSizePct] = useState(100);
  const [stopLoss, setStopLoss] = useState<number | null>(null);
  const [takeProfit, setTakeProfit] = useState<number | null>(null);

  // Backtest state
  const [backtestId, setBacktestId] = useState<string | null>(null);
  const [status, setStatus] = useState<BacktestStatus | null>(null);
  const [results, setResults] = useState<BacktestResultResponse | null>(null);
  const [backtestHistory, setBacktestHistory] = useState<BacktestSummary[]>([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Set default dates (last 7 days)
  useEffect(() => {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    setDateTo(now.toISOString().split('T')[0]);
    setDateFrom(weekAgo.toISOString().split('T')[0]);
  }, []);

  // Load backtest history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Poll status when backtest is running
  useEffect(() => {
    if (!backtestId || status?.status !== 'running') return;

    const interval = setInterval(async () => {
      try {
        const newStatus = await backtestApi.getStatus(backtestId);
        setStatus(newStatus);

        if (newStatus.status === 'completed') {
          const results = await backtestApi.getResults(backtestId);
          setResults(results);
          toast.success('Backtest completed!');
          loadHistory(); // Refresh history
        } else if (newStatus.status === 'failed') {
          toast.error(`Backtest failed: ${newStatus.error_message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Failed to get backtest status:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [backtestId, status?.status]);

  const loadHistory = async () => {
    try {
      const history = await backtestApi.list();
      setBacktestHistory(history);
    } catch (error) {
      console.error('Failed to load backtest history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleStart = async () => {
    if (!dateFrom || !dateTo) {
      toast.error('Please select date range');
      return;
    }

    setLoading(true);
    setResults(null);
    setStatus(null);

    try {
      const config: BacktestConfig = {
        symbol,
        timeframe,
        date_from: new Date(dateFrom).toISOString(),
        date_to: new Date(dateTo).toISOString(),
        use_ml_gates: useMlGates,
        initial_capital: initialCapital,
        position_size_pct: positionSizePct,
        stop_loss_pct: stopLoss || undefined,
        take_profit_pct: takeProfit || undefined,
      };

      const response = await backtestApi.start(config);
      setBacktestId(response.backtest_id);
      setStatus({
        backtest_id: response.backtest_id,
        status: 'running',
        progress_pct: 0,
        candles_processed: 0,
        total_candles: 0,
        trades_so_far: 0,
      });

      toast.success('Backtest started');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to start backtest: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadPreviousResult = async (id: string) => {
    try {
      const results = await backtestApi.getResults(id);
      setResults(results);
      setBacktestId(id);
      setStatus({
        backtest_id: id,
        status: 'completed',
        progress_pct: 100,
        candles_processed: results.metrics.total_candles_processed,
        total_candles: results.metrics.total_candles_processed,
        trades_so_far: results.metrics.total_trades,
      });
    } catch (error) {
      toast.error('Failed to load backtest results');
    }
  };

  const isRunning = status?.status === 'running';

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Historical Backtest
          </CardTitle>
          <CardDescription>
            Test trading strategies against historical OHLCV data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Configuration Form */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
            {/* Symbol */}
            <div className="space-y-2">
              <Label>Symbol</Label>
              <Select value={symbol} onValueChange={setSymbol} disabled={isRunning}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SYMBOLS.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Timeframe */}
            <div className="space-y-2">
              <Label>Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe} disabled={isRunning}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf.value} value={tf.value}>
                      {tf.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date From */}
            <div className="space-y-2">
              <Label>From Date</Label>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                disabled={isRunning}
              />
            </div>

            {/* Date To */}
            <div className="space-y-2">
              <Label>To Date</Label>
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                disabled={isRunning}
              />
            </div>

            {/* Initial Capital */}
            <div className="space-y-2">
              <Label>Capital ($)</Label>
              <Input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                min={100}
                disabled={isRunning}
              />
            </div>

            {/* Position Size */}
            <div className="space-y-2">
              <Label>Position %</Label>
              <Input
                type="number"
                value={positionSizePct}
                onChange={(e) => setPositionSizePct(Number(e.target.value))}
                min={1}
                max={100}
                disabled={isRunning}
              />
            </div>
          </div>

          {/* Second Row - Risk Management */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {/* Stop Loss */}
            <div className="space-y-2">
              <Label>Stop Loss %</Label>
              <Input
                type="number"
                value={stopLoss || ''}
                onChange={(e) => setStopLoss(e.target.value ? Number(e.target.value) : null)}
                placeholder="None"
                min={0.1}
                max={50}
                step={0.1}
                disabled={isRunning}
              />
            </div>

            {/* Take Profit */}
            <div className="space-y-2">
              <Label>Take Profit %</Label>
              <Input
                type="number"
                value={takeProfit || ''}
                onChange={(e) => setTakeProfit(e.target.value ? Number(e.target.value) : null)}
                placeholder="None"
                min={0.1}
                max={100}
                step={0.1}
                disabled={isRunning}
              />
            </div>

            {/* ML Gates Toggle */}
            <div className="space-y-2 flex items-center gap-2">
              <Switch
                checked={useMlGates}
                onCheckedChange={setUseMlGates}
                disabled={isRunning}
              />
              <Label className="flex items-center gap-1">
                <Brain className="h-4 w-4" />
                Use ML Gates
              </Label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-4">
            <Button
              onClick={handleStart}
              disabled={loading || isRunning}
              className="bg-green-600 hover:bg-green-700"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start Backtest
            </Button>

            {useMlGates ? (
              <Badge className="bg-green-500">
                <Brain className="h-3 w-3 mr-1" />
                ML Gates Enabled
              </Badge>
            ) : (
              <Badge variant="outline">
                Simple Strategy
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Progress Card */}
      {isRunning && status && (
        <Card className="border-2 border-yellow-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
              Running Backtest...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={status.progress_pct} className="mb-2" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>
                {status.candles_processed.toLocaleString()} / {status.total_candles.toLocaleString()} candles
              </span>
              <span>{status.trades_so_far} trades so far</span>
              <span>{status.progress_pct.toFixed(1)}%</span>
            </div>
            {status.current_date && (
              <p className="text-xs text-muted-foreground mt-1">
                Processing: {new Date(status.current_date).toLocaleDateString()}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Card */}
      {results && (
        <>
          {/* Performance Metrics */}
          <Card className="border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Performance Metrics
                <Badge variant="outline" className="ml-2">
                  {results.config.symbol} | {results.config.timeframe}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {/* Total P&L */}
                <MetricBox
                  label="Total P&L"
                  value={`${results.metrics.total_pnl_pct >= 0 ? '+' : ''}${results.metrics.total_pnl_pct.toFixed(2)}%`}
                  subValue={`$${results.metrics.total_pnl_usd.toFixed(2)}`}
                  positive={results.metrics.total_pnl_pct >= 0}
                  icon={<DollarSign className="h-4 w-4" />}
                />

                {/* Win Rate */}
                <MetricBox
                  label="Win Rate"
                  value={`${results.metrics.win_rate_pct.toFixed(1)}%`}
                  subValue={`${results.metrics.winning_trades}/${results.metrics.total_trades}`}
                  positive={results.metrics.win_rate_pct >= 50}
                  icon={<Target className="h-4 w-4" />}
                />

                {/* Max Drawdown */}
                <MetricBox
                  label="Max Drawdown"
                  value={`${results.metrics.max_drawdown_pct.toFixed(2)}%`}
                  subValue={`$${results.metrics.max_drawdown_usd.toFixed(2)}`}
                  positive={false}
                  icon={<TrendingDown className="h-4 w-4" />}
                />

                {/* Sharpe Ratio */}
                <MetricBox
                  label="Sharpe Ratio"
                  value={results.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}
                  positive={(results.metrics.sharpe_ratio || 0) > 1}
                  icon={<Activity className="h-4 w-4" />}
                />

                {/* Profit Factor */}
                <MetricBox
                  label="Profit Factor"
                  value={results.metrics.profit_factor?.toFixed(2) || 'N/A'}
                  positive={(results.metrics.profit_factor || 0) > 1}
                  icon={<Percent className="h-4 w-4" />}
                />

                {/* Avg Trade */}
                <MetricBox
                  label="Avg Trade"
                  value={`${results.metrics.avg_trade_pnl_pct >= 0 ? '+' : ''}${results.metrics.avg_trade_pnl_pct.toFixed(3)}%`}
                  positive={results.metrics.avg_trade_pnl_pct >= 0}
                  icon={<BarChart3 className="h-4 w-4" />}
                />
              </div>

              {/* Additional Stats Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">Winning Trades</p>
                  <p className="text-lg font-bold text-green-500">
                    {results.metrics.winning_trades}
                    <span className="text-xs ml-1">
                      (+{results.metrics.avg_winning_trade_pct.toFixed(2)}% avg)
                    </span>
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">Losing Trades</p>
                  <p className="text-lg font-bold text-red-500">
                    {results.metrics.losing_trades}
                    <span className="text-xs ml-1">
                      ({results.metrics.avg_losing_trade_pct.toFixed(2)}% avg)
                    </span>
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">Max Consecutive</p>
                  <p className="text-lg font-bold">
                    <span className="text-green-500">{results.metrics.max_consecutive_wins}W</span>
                    {' / '}
                    <span className="text-red-500">{results.metrics.max_consecutive_losses}L</span>
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">Duration</p>
                  <p className="text-lg font-bold">
                    {results.metrics.backtest_duration_seconds.toFixed(1)}s
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trades Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Trades ({results.trades.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-96 overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-background border-b">
                    <tr>
                      <th className="text-left p-2">Entry Time</th>
                      <th className="text-left p-2">Exit Time</th>
                      <th className="text-center p-2">Side</th>
                      <th className="text-right p-2">Entry</th>
                      <th className="text-right p-2">Exit</th>
                      <th className="text-right p-2">P&L %</th>
                      <th className="text-right p-2">P&L $</th>
                      <th className="text-center p-2">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.trades.map((trade, idx) => (
                      <tr key={idx} className="border-b hover:bg-muted/50">
                        <td className="p-2 font-mono text-xs">
                          {new Date(trade.entry_time).toLocaleString()}
                        </td>
                        <td className="p-2 font-mono text-xs">
                          {new Date(trade.exit_time).toLocaleString()}
                        </td>
                        <td className="p-2 text-center">
                          <Badge
                            className={trade.side === 'long' ? 'bg-green-500' : 'bg-red-500'}
                          >
                            {trade.side}
                          </Badge>
                        </td>
                        <td className="p-2 text-right font-mono">
                          ${trade.entry_price.toFixed(4)}
                        </td>
                        <td className="p-2 text-right font-mono">
                          ${trade.exit_price.toFixed(4)}
                        </td>
                        <td className={`p-2 text-right font-bold ${trade.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(3)}%
                        </td>
                        <td className={`p-2 text-right font-bold ${trade.pnl_usd >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          ${trade.pnl_usd.toFixed(2)}
                        </td>
                        <td className="p-2 text-center">
                          <Badge variant="outline" className="text-xs">
                            {trade.exit_reason}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Backtest History */}
      {backtestHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-4 w-4" />
              Recent Backtests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {backtestHistory.slice(0, 5).map((bt) => (
                <div
                  key={bt.backtest_id}
                  className="flex items-center justify-between p-2 bg-muted/50 rounded-lg cursor-pointer hover:bg-muted"
                  onClick={() => bt.status === 'completed' && loadPreviousResult(bt.backtest_id)}
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{bt.symbol}</Badge>
                    <span className="text-xs text-muted-foreground">{bt.timeframe}</span>
                    <Badge
                      className={
                        bt.status === 'completed'
                          ? 'bg-green-500'
                          : bt.status === 'running'
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                      }
                    >
                      {bt.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <span>{bt.trades_count} trades</span>
                    <span className="text-muted-foreground">
                      {new Date(bt.started_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!results && !isRunning && !loadingHistory && backtestHistory.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <History className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No backtests yet</p>
            <p className="text-muted-foreground">
              Configure the parameters above and click "Start Backtest" to run a historical simulation.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Helper component for metric display
interface MetricBoxProps {
  label: string;
  value: string;
  subValue?: string;
  positive?: boolean;
  icon?: React.ReactNode;
}

function MetricBox({ label, value, subValue, positive, icon }: MetricBoxProps) {
  return (
    <div className="text-center p-3 bg-muted rounded-lg">
      <div className="flex items-center justify-center gap-1 mb-1 text-muted-foreground">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className={`text-xl font-bold ${positive === true ? 'text-green-500' : positive === false ? 'text-red-500' : ''}`}>
        {value}
      </p>
      {subValue && (
        <p className="text-xs text-muted-foreground">{subValue}</p>
      )}
    </div>
  );
}

export default BacktestPanel;
