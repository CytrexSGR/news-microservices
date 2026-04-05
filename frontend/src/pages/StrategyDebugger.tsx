import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Play, Info, ListTree, BarChart3, TrendingUp, History, Trash2, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { TradeTimeline } from '@/components/trading/TradeTimeline';
import { ConditionTimeline } from '@/components/trading/ConditionTimeline';
import { NoEntrySummary } from '@/components/trading/NoEntrySummary';
import { IndicatorCharts } from '@/components/trading/IndicatorCharts';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

// Storage key for debug run history
const DEBUG_HISTORY_KEY = 'strategy-debug-history';
const MAX_HISTORY_ITEMS = 20;

interface SavedDebugRun {
  id: string;
  timestamp: string;
  config: DebugConfig;
  results: any;
  name?: string;
}

interface DebugConfig {
  strategyId: string;
  symbol: string;
  timeframe: string;
  days: number;
  parameters: Record<string, number>;
}

export const StrategyDebugger: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const prefilledState = location.state as { strategyId?: string; parameters?: Record<string, number> } | null;

  const [config, setConfig] = useState<DebugConfig>({
    strategyId: prefilledState?.strategyId || '9675ccea-f520-4557-b54c-a98e1972cc1f',
    symbol: 'BTCUSDT',
    timeframe: '1h',
    days: 30,
    parameters: prefilledState?.parameters || {
      rsi_period: 14,
      entry_threshold: 0.7,
      take_profit_ratio: 0.03
    }
  });

  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [debugHistory, setDebugHistory] = useState<SavedDebugRun[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  // Load debug history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(DEBUG_HISTORY_KEY);
    if (saved) {
      try {
        setDebugHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse debug history:', e);
      }
    }
  }, []);

  // Save a debug run to history
  const saveDebugRun = (runConfig: DebugConfig, runResults: any) => {
    const newRun: SavedDebugRun = {
      id: `run-${Date.now()}`,
      timestamp: new Date().toISOString(),
      config: runConfig,
      results: runResults,
    };

    setDebugHistory(prev => {
      const updated = [newRun, ...prev].slice(0, MAX_HISTORY_ITEMS);
      localStorage.setItem(DEBUG_HISTORY_KEY, JSON.stringify(updated));
      return updated;
    });

    setSelectedRunId(newRun.id);
  };

  // Load a saved debug run
  const loadDebugRun = (run: SavedDebugRun) => {
    setConfig(run.config);
    setResults(run.results);
    setSelectedRunId(run.id);
    setHistoryOpen(false);
  };

  // Delete a debug run from history
  const deleteDebugRun = (runId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDebugHistory(prev => {
      const updated = prev.filter(r => r.id !== runId);
      localStorage.setItem(DEBUG_HISTORY_KEY, JSON.stringify(updated));
      return updated;
    });
    if (selectedRunId === runId) {
      setSelectedRunId(null);
    }
  };

  // Clear all history
  const clearHistory = () => {
    setDebugHistory([]);
    localStorage.removeItem(DEBUG_HISTORY_KEY);
    setSelectedRunId(null);
  };

  // Format timestamp for display
  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleRunDebug = async () => {
    setIsRunning(true);

    try {
      // Use Vite proxy path instead of direct localhost:8116
      // Proxy rewrites /api/prediction/v1/* to http://localhost:8116/api/v1/*
      const response = await fetch('/api/prediction/v1/strategy-debug/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          strategy_id: config.strategyId,
          parameters: config.parameters,
          market_data_config: {
            symbol: config.symbol,
            timeframe: config.timeframe,
            days: config.days
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Debug run failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
      // Save to history
      saveDebugRun(config, data);
    } catch (error) {
      console.error('Debug run error:', error);
      alert(`Error: ${(error as Error).message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">Strategy Debugger</h1>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate(`/trading/strategy/${config.strategyId}`)}
        >
          <Info className="mr-2 h-4 w-4" />
          View Strategy Details
        </Button>
      </div>

      {/* Pre-filled Parameters Alert */}
      {prefilledState?.parameters && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Parameters pre-filled from optimization results for strategy: <strong>{prefilledState.strategyId}</strong>
          </AlertDescription>
        </Alert>
      )}

      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle>Debug Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                value={config.symbol}
                onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                placeholder="BTCUSDT"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeframe">Timeframe</Label>
              <Select
                value={config.timeframe}
                onValueChange={(value) => setConfig({ ...config, timeframe: value })}
              >
                <SelectTrigger id="timeframe">
                  <SelectValue placeholder="Select timeframe" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15m">15 Minutes</SelectItem>
                  <SelectItem value="1h">1 Hour</SelectItem>
                  <SelectItem value="4h">4 Hours</SelectItem>
                  <SelectItem value="1d">1 Day</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="days">Days</Label>
              <Input
                id="days"
                type="number"
                value={config.days}
                onChange={(e) => setConfig({ ...config, days: parseInt(e.target.value) })}
                min={1}
                max={365}
              />
            </div>

            <div className="flex items-end">
              <Button
                onClick={handleRunDebug}
                disabled={isRunning}
                className="w-full"
              >
                {isRunning ? (
                  <>
                    <Activity className="mr-2 h-4 w-4 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Debug
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debug History */}
      {debugHistory.length > 0 && (
        <Collapsible open={historyOpen} onOpenChange={setHistoryOpen}>
          <Card>
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <div className="flex items-center justify-between cursor-pointer hover:bg-muted/50 -mx-2 px-2 py-1 rounded-lg transition-colors">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <History className="h-5 w-5" />
                    Debug History ({debugHistory.length})
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    {historyOpen && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          clearHistory();
                        }}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Clear All
                      </Button>
                    )}
                    {historyOpen ? (
                      <ChevronUp className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                </div>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="pt-0">
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {debugHistory.map((run) => (
                    <div
                      key={run.id}
                      onClick={() => loadDebugRun(run)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-muted/50 ${
                        selectedRunId === run.id ? 'border-primary bg-primary/5' : 'border-border'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{run.config.symbol}</span>
                              <Badge variant="outline" className="text-xs">{run.config.timeframe}</Badge>
                              <Badge variant="secondary" className="text-xs">{run.config.days}d</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {formatTimestamp(run.timestamp)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right text-sm">
                            <p className="font-mono">
                              {run.results.total_trades} trades
                            </p>
                            <p className={`text-xs ${run.results.win_rate >= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                              {(run.results.win_rate * 100).toFixed(1)}% win
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => deleteDebugRun(run.id, e)}
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      )}

      {/* Results Section with Tabs */}
      {results && (
        <>
          {/* Summary Metrics Card */}
          <Card>
            <CardHeader>
              <CardTitle>Debug Results Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                  <p className="text-2xl font-bold">{results.sharpe_ratio.toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Trades</p>
                  <p className="text-2xl font-bold">{results.total_trades}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                  <p className="text-2xl font-bold">{(results.win_rate * 100).toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Debug Logs</p>
                  <p className="text-2xl font-bold">{results.debug_logs.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trade Timeline (if trades exist) */}
          {results.trades && results.trades.length > 0 && results.price_data && (
            <TradeTimeline
              trades={results.trades}
              priceData={results.price_data}
            />
          )}

          {/* Debug Analysis Tabs */}
          {results.debug_logs && results.debug_logs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Strategy Debug Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="timeline" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="timeline" className="flex items-center gap-2">
                      <ListTree className="h-4 w-4" />
                      <span>Timeline</span>
                    </TabsTrigger>
                    <TabsTrigger value="summary" className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      <span>Summary</span>
                    </TabsTrigger>
                    <TabsTrigger value="charts" className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      <span>Charts</span>
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="timeline" className="mt-6">
                    <ConditionTimeline logs={results.debug_logs} />
                  </TabsContent>

                  <TabsContent value="summary" className="mt-6">
                    <NoEntrySummary logs={results.debug_logs} />
                  </TabsContent>

                  <TabsContent value="charts" className="mt-6">
                    <IndicatorCharts logs={results.debug_logs} />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};
