/**
 * Strategy Execution Panel
 *
 * Shows strategy details and allows running in different modes:
 * - Backtest: Run against historical data
 * - Paper: Real-time simulation
 * - Test: Force trades to verify infrastructure
 * - Live: Real trading (future)
 */

import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Play,
  Square,
  History,
  TestTube,
  Radio,
  TrendingUp,
  TrendingDown,
  Wallet,
  Target,
  Activity,
  RefreshCw,
  Loader2,
  Calendar,
  Zap,
  ArrowUpCircle,
  ArrowDownCircle,
  LogOut,
  BarChart3,
  Settings,
  Save,
  Plus,
  X,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FlaskConical,
} from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import toast from 'react-hot-toast';

import { tradingStrategyApi } from '../../api/mlLabApi';
import type {
  TradingStrategy,
  TradingStrategyUpdate,
  StrategyExecution,
  StrategyExecutionStart,
  ExecutionMode,
  ExecutionStatus,
  SymbolExecutionState,
  ForceTradeResponse,
  AutoTestResults,
} from '../../types';

// Available symbols for trading
const AVAILABLE_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT',
  'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT',
  'LTCUSDT', 'UNIUSDT', 'ATOMUSDT', 'XLMUSDT', 'NEARUSDT',
];

// Available timeframes
const AVAILABLE_TIMEFRAMES = [
  { value: '1min', label: '1 Minute' },
  { value: '5min', label: '5 Minutes' },
  { value: '15min', label: '15 Minutes' },
  { value: '30min', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
];

// Tab type for main navigation
type MainTab = 'settings' | 'execution';

// Status badge colors
const STATUS_COLORS: Record<ExecutionStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  running: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  stopped: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

interface StrategyExecutionPanelProps {
  strategy: TradingStrategy;
  onBack: () => void;
  onRefresh: () => void;
}

export function StrategyExecutionPanel({ strategy: initialStrategy, onBack, onRefresh }: StrategyExecutionPanelProps) {
  // Local strategy state (for editing)
  const [strategy, setStrategy] = useState<TradingStrategy>(initialStrategy);

  // Main tab state
  const [mainTab, setMainTab] = useState<MainTab>('execution');

  // Settings form state
  const [editedName, setEditedName] = useState(strategy.name);
  const [editedDescription, setEditedDescription] = useState(strategy.description || '');
  const [editedSymbols, setEditedSymbols] = useState<string[]>(strategy.symbols);
  const [editedTimeframe, setEditedTimeframe] = useState(strategy.timeframe);
  const [editedCapital, setEditedCapital] = useState(strategy.total_capital);
  const [editedPositionSize, setEditedPositionSize] = useState(strategy.position_size_pct);
  const [editedStopLoss, setEditedStopLoss] = useState(strategy.stop_loss_pct || 0);
  const [editedTakeProfit, setEditedTakeProfit] = useState(strategy.take_profit_pct || 0);
  const [editedMaxPositions, setEditedMaxPositions] = useState(strategy.max_positions);
  const [editedMlGatesEnabled, setEditedMlGatesEnabled] = useState(strategy.ml_gates_enabled);
  const [savingSettings, setSavingSettings] = useState(false);

  // Execution state
  const [executions, setExecutions] = useState<StrategyExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingExecution, setStartingExecution] = useState(false);
  const [selectedMode, setSelectedMode] = useState<ExecutionMode>('backtest');

  // Backtest date range
  const [backtestStartDate, setBacktestStartDate] = useState(
    format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd')
  );
  const [backtestEndDate, setBacktestEndDate] = useState(
    format(new Date(), 'yyyy-MM-dd')
  );

  // Force-Trade state (TEST mode)
  const [forceTradeSymbol, setForceTradeSymbol] = useState<string>(strategy.symbols[0] || '');
  const [forcingTrade, setForcingTrade] = useState(false);

  // Auto-Test state (TEST mode)
  const [runningAutoTest, setRunningAutoTest] = useState(false);
  const [autoTestResults, setAutoTestResults] = useState<AutoTestResults | null>(null);

  // Symbol being added
  const [newSymbol, setNewSymbol] = useState<string>('');

  const fetchExecutions = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data = await tradingStrategyApi.listExecutions(strategy.id);
      setExecutions(data.executions);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
      if (!silent) toast.error('Failed to load executions');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [strategy.id]);

  useEffect(() => {
    fetchExecutions();
  }, [fetchExecutions]);

  // Auto-refresh for running backtests (every 2 seconds)
  useEffect(() => {
    const hasRunningBacktest = executions.some(
      (e) => e.mode === 'backtest' && e.status === 'running'
    );

    if (!hasRunningBacktest) return;

    const intervalId = setInterval(() => {
      fetchExecutions(true); // Silent refresh
    }, 2000);

    return () => clearInterval(intervalId);
  }, [executions, fetchExecutions]);

  const handleStartExecution = async () => {
    setStartingExecution(true);
    try {
      const data: StrategyExecutionStart = {
        mode: selectedMode,
      };

      if (selectedMode === 'backtest') {
        data.start_date = new Date(backtestStartDate).toISOString();
        data.end_date = new Date(backtestEndDate).toISOString();
      }

      const execution = await tradingStrategyApi.startExecution(strategy.id, data);
      toast.success(`${selectedMode} execution created`);

      // Start running for all modes (paper, test, backtest)
      if (selectedMode === 'paper' || selectedMode === 'test' || selectedMode === 'backtest') {
        await tradingStrategyApi.runExecution(strategy.id, execution.id);
        if (selectedMode === 'test') {
          toast.success('TEST mode started - use Force Trade buttons');
        } else if (selectedMode === 'backtest') {
          toast.success('Backtest started');
        } else {
          toast.success('Paper trading started');
        }
      }

      fetchExecutions();
    } catch (error: any) {
      console.error('Failed to start execution:', error);
      toast.error(error.response?.data?.detail || 'Failed to start execution');
    } finally {
      setStartingExecution(false);
    }
  };

  // Handle Force Trade (TEST mode only)
  const handleForceTrade = async (action: 'enter_long' | 'enter_short' | 'exit') => {
    const testExecution = runningExecutions.find((e) => e.mode === 'test');
    if (!testExecution) {
      toast.error('No TEST mode execution running');
      return;
    }

    setForcingTrade(true);
    try {
      const response = await tradingStrategyApi.forceTrade(
        strategy.id,
        testExecution.id,
        forceTradeSymbol,
        action,
        'manual_ui_force'
      );

      if (response.success) {
        toast.success(response.message);
        // Refresh executions to see updated state
        fetchExecutions();
      } else {
        toast.error(response.message);
      }
    } catch (error: any) {
      console.error('Force trade failed:', error);
      toast.error(error.response?.data?.detail || 'Force trade failed');
    } finally {
      setForcingTrade(false);
    }
  };

  // Handle Auto-Test (TEST mode only)
  const handleAutoTest = async () => {
    const testExecution = runningExecutions.find((e) => e.mode === 'test');
    if (!testExecution) {
      toast.error('No TEST mode execution running');
      return;
    }

    setRunningAutoTest(true);
    setAutoTestResults(null);
    try {
      const results = await tradingStrategyApi.runAutoTest(
        strategy.id,
        testExecution.id
      );
      setAutoTestResults(results);

      if (results.success_rate === 100) {
        toast.success(`All ${results.total} tests passed!`);
      } else if (results.failed > 0) {
        toast.error(`${results.failed}/${results.total} tests failed`);
      } else {
        toast.success(`${results.passed}/${results.total} tests passed`);
      }

      // Refresh executions to see updated state
      fetchExecutions();
    } catch (error: any) {
      console.error('Auto-test failed:', error);
      toast.error(error.response?.data?.detail || 'Auto-test failed');
    } finally {
      setRunningAutoTest(false);
    }
  };

  const handleStopExecution = async (executionId: string) => {
    try {
      await tradingStrategyApi.stopExecution(strategy.id, executionId);
      toast.success('Execution stopped');
      fetchExecutions();
    } catch (error) {
      toast.error('Failed to stop execution');
    }
  };

  // Settings handlers
  const handleAddSymbol = () => {
    if (newSymbol && !editedSymbols.includes(newSymbol)) {
      setEditedSymbols([...editedSymbols, newSymbol]);
      setNewSymbol('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setEditedSymbols(editedSymbols.filter(s => s !== symbol));
  };

  const handleSaveSettings = async () => {
    if (editedSymbols.length === 0) {
      toast.error('At least one symbol is required');
      return;
    }

    setSavingSettings(true);
    try {
      const updateData: TradingStrategyUpdate = {
        name: editedName,
        description: editedDescription || undefined,
        symbols: editedSymbols,
        timeframe: editedTimeframe,
        total_capital: editedCapital,
        position_size_pct: editedPositionSize,
        stop_loss_pct: editedStopLoss || undefined,
        take_profit_pct: editedTakeProfit || undefined,
        max_positions: editedMaxPositions,
        ml_gates_enabled: editedMlGatesEnabled,
      };

      const updatedStrategy = await tradingStrategyApi.update(strategy.id, updateData);
      setStrategy(updatedStrategy);
      toast.success('Strategy settings saved');
      onRefresh(); // Refresh parent list
    } catch (error: any) {
      console.error('Failed to save settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSavingSettings(false);
    }
  };

  const hasSettingsChanges = () => {
    return (
      editedName !== strategy.name ||
      editedDescription !== (strategy.description || '') ||
      JSON.stringify(editedSymbols) !== JSON.stringify(strategy.symbols) ||
      editedTimeframe !== strategy.timeframe ||
      editedCapital !== strategy.total_capital ||
      editedPositionSize !== strategy.position_size_pct ||
      editedStopLoss !== (strategy.stop_loss_pct || 0) ||
      editedTakeProfit !== (strategy.take_profit_pct || 0) ||
      editedMaxPositions !== strategy.max_positions ||
      editedMlGatesEnabled !== strategy.ml_gates_enabled
    );
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPnL = (value: number) => {
    const formatted = formatCurrency(Math.abs(value));
    const prefix = value >= 0 ? '+' : '-';
    return `${prefix}${formatted}`;
  };

  const formatPercent = (value: number | null) => {
    if (value === null) return 'N/A';
    return `${value.toFixed(2)}%`;
  };

  // Get running executions
  const runningExecutions = executions.filter((e) => e.status === 'running');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            {strategy.name}
          </h2>
          <p className="text-muted-foreground">
            {strategy.symbols.join(', ')} | {formatCurrency(strategy.total_capital)} Capital
          </p>
        </div>
        <Button variant="outline" onClick={() => fetchExecutions()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Main Navigation Tabs */}
      <Tabs value={mainTab} onValueChange={(v) => setMainTab(v as MainTab)}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="execution" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            Execution
          </TabsTrigger>
        </TabsList>

        {/* ==================== SETTINGS TAB ==================== */}
        <TabsContent value="settings" className="space-y-6 mt-4">
          {/* Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>Strategy name and description</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="strategyName">Strategy Name</Label>
                  <Input
                    id="strategyName"
                    value={editedName}
                    onChange={(e) => setEditedName(e.target.value)}
                    placeholder="My Trading Strategy"
                  />
                </div>
                <div>
                  <Label htmlFor="timeframe">Timeframe</Label>
                  <Select value={editedTimeframe} onValueChange={setEditedTimeframe}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select timeframe" />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_TIMEFRAMES.map((tf) => (
                        <SelectItem key={tf.value} value={tf.value}>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4" />
                            {tf.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  placeholder="Optional description..."
                />
              </div>
            </CardContent>
          </Card>

          {/* Symbols Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Trading Symbols</CardTitle>
              <CardDescription>Select the symbols to trade with this strategy</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current Symbols */}
              <div className="flex flex-wrap gap-2">
                {editedSymbols.map((symbol) => (
                  <Badge key={symbol} variant="secondary" className="text-sm py-1 px-3">
                    {symbol.replace('USDT', '')}
                    <button
                      onClick={() => handleRemoveSymbol(symbol)}
                      className="ml-2 hover:text-red-500"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
                {editedSymbols.length === 0 && (
                  <span className="text-muted-foreground text-sm">No symbols selected</span>
                )}
              </div>

              {/* Add Symbol */}
              <div className="flex gap-2">
                <Select value={newSymbol} onValueChange={setNewSymbol}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Add symbol..." />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_SYMBOLS.filter(s => !editedSymbols.includes(s)).map((symbol) => (
                      <SelectItem key={symbol} value={symbol}>
                        {symbol.replace('USDT', '')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleAddSymbol}
                  disabled={!newSymbol}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Capital & Risk Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Capital & Risk Management</CardTitle>
              <CardDescription>Configure position sizing and risk parameters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="capital">Total Capital ($)</Label>
                  <Input
                    id="capital"
                    type="number"
                    value={editedCapital}
                    onChange={(e) => setEditedCapital(Number(e.target.value))}
                    min={100}
                  />
                </div>
                <div>
                  <Label htmlFor="positionSize">Position Size (%)</Label>
                  <Input
                    id="positionSize"
                    type="number"
                    value={editedPositionSize}
                    onChange={(e) => setEditedPositionSize(Number(e.target.value))}
                    min={1}
                    max={100}
                  />
                </div>
                <div>
                  <Label htmlFor="stopLoss">Stop Loss (%)</Label>
                  <Input
                    id="stopLoss"
                    type="number"
                    value={editedStopLoss}
                    onChange={(e) => setEditedStopLoss(Number(e.target.value))}
                    min={0}
                    max={50}
                    step={0.1}
                  />
                </div>
                <div>
                  <Label htmlFor="takeProfit">Take Profit (%)</Label>
                  <Input
                    id="takeProfit"
                    type="number"
                    value={editedTakeProfit}
                    onChange={(e) => setEditedTakeProfit(Number(e.target.value))}
                    min={0}
                    max={100}
                    step={0.1}
                  />
                </div>
                <div>
                  <Label htmlFor="maxPositions">Max Positions</Label>
                  <Input
                    id="maxPositions"
                    type="number"
                    value={editedMaxPositions}
                    onChange={(e) => setEditedMaxPositions(Number(e.target.value))}
                    min={1}
                    max={20}
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="mlGates"
                    checked={editedMlGatesEnabled}
                    onChange={(e) => setEditedMlGatesEnabled(e.target.checked)}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="mlGates" className="cursor-pointer">ML Gates Enabled</Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleSaveSettings}
              disabled={savingSettings || !hasSettingsChanges()}
            >
              {savingSettings ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Settings
            </Button>
          </div>
        </TabsContent>

        {/* ==================== EXECUTION TAB ==================== */}
        <TabsContent value="execution" className="space-y-6 mt-4">
          {/* Strategy Summary */}
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-muted-foreground mb-1">
                  <Wallet className="h-4 w-4" />
                  <span className="text-sm">Total Capital</span>
                </div>
                <div className="text-2xl font-bold">{formatCurrency(strategy.total_capital)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-muted-foreground mb-1">
                  <Target className="h-4 w-4" />
                  <span className="text-sm">Position Size</span>
                </div>
                <div className="text-2xl font-bold">{strategy.position_size_pct}%</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-muted-foreground mb-1">
                  <TrendingDown className="h-4 w-4 text-red-500" />
                  <span className="text-sm">Stop Loss</span>
                </div>
                <div className="text-2xl font-bold text-red-500">{strategy.stop_loss_pct || 0}%</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-muted-foreground mb-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Take Profit</span>
                </div>
                <div className="text-2xl font-bold text-green-500">{strategy.take_profit_pct || 0}%</div>
              </CardContent>
            </Card>
          </div>

          {/* Execution Modes */}
          <Card>
            <CardHeader>
              <CardTitle>Start Execution</CardTitle>
              <CardDescription>
                Choose a mode to run your strategy
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs value={selectedMode} onValueChange={(v) => setSelectedMode(v as ExecutionMode)}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="backtest" className="flex items-center gap-2">
                    <History className="h-4 w-4" />
                    Backtest
                  </TabsTrigger>
                  <TabsTrigger value="paper" className="flex items-center gap-2">
                    <TestTube className="h-4 w-4" />
                    Paper
                  </TabsTrigger>
                  <TabsTrigger value="test" className="flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    TEST
                  </TabsTrigger>
                  <TabsTrigger value="live" className="flex items-center gap-2" disabled>
                    <Radio className="h-4 w-4" />
                    Live
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="backtest" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="startDate">Start Date</Label>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="startDate"
                          type="date"
                          value={backtestStartDate}
                          onChange={(e) => setBacktestStartDate(e.target.value)}
                          className="pl-9"
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="endDate">End Date</Label>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="endDate"
                          type="date"
                          value={backtestEndDate}
                          onChange={(e) => setBacktestEndDate(e.target.value)}
                          className="pl-9"
                        />
                      </div>
                    </div>
                  </div>
                  <Button onClick={handleStartExecution} disabled={startingExecution}>
                    {startingExecution ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Run Backtest
                  </Button>
                </TabsContent>

                <TabsContent value="paper" className="space-y-4 mt-4">
                  <p className="text-muted-foreground">
                    Paper trading will simulate real-time trades using live market data.
                    No real money is involved.
                  </p>
                  <Button onClick={handleStartExecution} disabled={startingExecution || runningExecutions.some(e => e.mode === 'paper')}>
                    {startingExecution ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    {runningExecutions.some(e => e.mode === 'paper') ? 'Paper Trading Active' : 'Start Paper Trading'}
                  </Button>
                </TabsContent>

                {/* TEST Mode - Force Trade */}
                <TabsContent value="test" className="space-y-4 mt-4">
                  <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Zap className="h-5 w-5 text-amber-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-amber-800 dark:text-amber-200">TEST Mode</h4>
                        <p className="text-sm text-amber-700 dark:text-amber-300">
                          Force trades to verify infrastructure works. ML gates are bypassed.
                          Uses real-time market data but no actual trading.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Start TEST Mode or Show Force Trade Controls */}
                  {runningExecutions.some(e => e.mode === 'test') ? (
                    <div className="space-y-4">
                      {/* Symbol Selector */}
                      <div>
                        <Label htmlFor="forceTradeSymbol">Select Symbol</Label>
                        <Select value={forceTradeSymbol} onValueChange={setForceTradeSymbol}>
                          <SelectTrigger className="w-48">
                            <SelectValue placeholder="Select symbol" />
                          </SelectTrigger>
                          <SelectContent>
                            {strategy.symbols.map((symbol) => (
                              <SelectItem key={symbol} value={symbol}>
                                {symbol.replace('USDT', '')}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Force Trade Buttons */}
                      <div className="flex gap-3">
                        <Button
                          onClick={() => handleForceTrade('enter_long')}
                          disabled={forcingTrade}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {forcingTrade ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <ArrowUpCircle className="h-4 w-4 mr-2" />
                          )}
                          Enter Long
                        </Button>
                        <Button
                          onClick={() => handleForceTrade('enter_short')}
                          disabled={forcingTrade}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          {forcingTrade ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <ArrowDownCircle className="h-4 w-4 mr-2" />
                          )}
                          Enter Short
                        </Button>
                        <Button
                          onClick={() => handleForceTrade('exit')}
                          disabled={forcingTrade}
                          variant="outline"
                        >
                          {forcingTrade ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <LogOut className="h-4 w-4 mr-2" />
                          )}
                          Exit Position
                        </Button>
                      </div>

                      {/* Current Position Status */}
                      {runningExecutions.filter(e => e.mode === 'test').map((exec) => (
                        <div key={exec.id} className="text-sm text-muted-foreground mt-2">
                          <span className="font-medium">Active TEST execution:</span>{' '}
                          {exec.total_trades} trades, P&L: {formatCurrency(exec.realized_pnl)}
                        </div>
                      ))}

                      {/* Auto-Test Section */}
                      <div className="mt-6 pt-6 border-t">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h4 className="font-medium flex items-center gap-2">
                              <FlaskConical className="h-4 w-4" />
                              Automated Module Tests
                            </h4>
                            <p className="text-sm text-muted-foreground">
                              Verify all trading modules work correctly
                            </p>
                          </div>
                          <Button
                            onClick={handleAutoTest}
                            disabled={runningAutoTest}
                            variant="secondary"
                          >
                            {runningAutoTest ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <FlaskConical className="h-4 w-4 mr-2" />
                            )}
                            Run Auto-Test
                          </Button>
                        </div>

                        {/* Auto-Test Results */}
                        {autoTestResults && (
                          <div className="space-y-3">
                            {/* Summary */}
                            <div className="flex items-center gap-4 p-3 bg-muted rounded-lg">
                              <div className={`text-2xl font-bold ${
                                autoTestResults.success_rate === 100 ? 'text-green-600' :
                                autoTestResults.failed > 0 ? 'text-red-600' : 'text-yellow-600'
                              }`}>
                                {autoTestResults.success_rate.toFixed(0)}%
                              </div>
                              <div className="flex-1">
                                <div className="text-sm font-medium">
                                  {autoTestResults.passed}/{autoTestResults.total} tests passed
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  Run at {new Date(autoTestResults.test_run_at).toLocaleTimeString()}
                                </div>
                              </div>
                              {autoTestResults.success_rate === 100 ? (
                                <CheckCircle2 className="h-6 w-6 text-green-600" />
                              ) : autoTestResults.failed > 0 ? (
                                <XCircle className="h-6 w-6 text-red-600" />
                              ) : (
                                <AlertCircle className="h-6 w-6 text-yellow-600" />
                              )}
                            </div>

                            {/* Individual Test Results */}
                            <div className="grid grid-cols-2 gap-2">
                              {Object.entries(autoTestResults.tests).map(([testName, result]) => (
                                <div
                                  key={testName}
                                  className={`flex items-center gap-2 p-2 rounded text-sm ${
                                    result.status === 'passed' ? 'bg-green-50 dark:bg-green-900/20' :
                                    result.status === 'failed' ? 'bg-red-50 dark:bg-red-900/20' :
                                    result.status === 'skipped' ? 'bg-gray-50 dark:bg-gray-900/20' :
                                    'bg-yellow-50 dark:bg-yellow-900/20'
                                  }`}
                                >
                                  {result.status === 'passed' ? (
                                    <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                                  ) : result.status === 'failed' ? (
                                    <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                                  ) : result.status === 'skipped' ? (
                                    <AlertCircle className="h-4 w-4 text-gray-500 flex-shrink-0" />
                                  ) : (
                                    <AlertCircle className="h-4 w-4 text-yellow-600 flex-shrink-0" />
                                  )}
                                  <span className="truncate" title={testName.replace(/_/g, ' ')}>
                                    {testName.replace(/_/g, ' ')}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <Button onClick={handleStartExecution} disabled={startingExecution}>
                      {startingExecution ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4 mr-2" />
                      )}
                      Start TEST Mode
                    </Button>
                  )}
                </TabsContent>

                <TabsContent value="live" className="mt-4">
                  <p className="text-muted-foreground">
                    Live trading is coming soon. Make sure to test your strategy with backtesting
                    and paper trading first.
                  </p>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Executions List */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Execution History</CardTitle>
                  <CardDescription>
                    {executions.length} executions
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : executions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No executions yet</p>
                  <p className="text-sm">Start a backtest or paper trading session above</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {executions.map((execution) => (
                    <ExecutionCard
                      key={execution.id}
                      execution={execution}
                      onStop={() => handleStopExecution(execution.id)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface ExecutionCardProps {
  execution: StrategyExecution;
  onStop: () => void;
}

function ExecutionCard({ execution, onStop }: ExecutionCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPnL = (value: number) => {
    const isPositive = value >= 0;
    return (
      <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
        {isPositive ? '+' : ''}{formatCurrency(value)}
      </span>
    );
  };

  const modeIcon = {
    backtest: <History className="h-4 w-4" />,
    paper: <TestTube className="h-4 w-4" />,
    test: <Zap className="h-4 w-4 text-amber-500" />,
    live: <Radio className="h-4 w-4" />,
  }[execution.mode];

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-muted rounded">
            {modeIcon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium capitalize">{execution.mode}</span>
              <Badge className={STATUS_COLORS[execution.status]}>
                {execution.status}
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              {execution.mode === 'backtest' && execution.backtest_start_date && (
                <>
                  {format(new Date(execution.backtest_start_date), 'MMM d, yyyy')} →{' '}
                  {format(new Date(execution.backtest_end_date!), 'MMM d, yyyy')}
                </>
              )}
              {(execution.mode === 'paper' || execution.mode === 'test') && execution.started_at && (
                <>Started {format(new Date(execution.started_at), 'MMM d, yyyy HH:mm')}</>
              )}
              {!execution.started_at && (
                <>Created {format(new Date(execution.created_at), 'MMM d, yyyy HH:mm')}</>
              )}
            </div>
          </div>
        </div>

        {execution.status === 'running' && (
          <Button variant="outline" size="sm" onClick={onStop}>
            <Square className="h-4 w-4 mr-1" />
            Stop
          </Button>
        )}
      </div>

      {/* Backtest Progress Bar */}
      {execution.mode === 'backtest' && execution.status === 'running' && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <BarChart3 className="h-4 w-4" />
              <span>Progress</span>
            </div>
            <span className="font-medium">
              {(execution.backtest_progress * 100).toFixed(1)}%
              {execution.backtest_total_candles > 0 && (
                <span className="text-muted-foreground ml-2">
                  ({execution.backtest_processed_candles.toLocaleString()} / {execution.backtest_total_candles.toLocaleString()} candles)
                </span>
              )}
            </span>
          </div>
          <Progress value={execution.backtest_progress * 100} className="h-2" />
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-5 gap-4 text-sm">
        <div>
          <div className="text-muted-foreground">Capital</div>
          <div className="font-medium">{formatCurrency(execution.current_capital)}</div>
        </div>
        <div>
          <div className="text-muted-foreground">P&L</div>
          <div className="font-medium">{formatPnL(execution.realized_pnl)}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Trades</div>
          <div className="font-medium">{execution.total_trades}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Win Rate</div>
          <div className="font-medium">
            {execution.win_rate !== null ? `${execution.win_rate.toFixed(1)}%` : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-muted-foreground">Max DD</div>
          <div className="font-medium text-red-600">
            {execution.max_drawdown_pct !== null ? `${execution.max_drawdown_pct.toFixed(2)}%` : 'N/A'}
          </div>
        </div>
      </div>

      {/* Per-Symbol States */}
      {execution.symbol_states.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="text-sm font-medium mb-2">Symbol Breakdown</div>
          <div className="grid grid-cols-3 gap-2">
            {execution.symbol_states.map((state) => (
              <div key={state.symbol} className="bg-muted rounded p-2 text-sm">
                <div className="flex items-center justify-between mb-1">
                  <Badge variant="outline" className="font-mono text-xs">
                    {state.symbol.replace('USDT', '')}
                  </Badge>
                  {state.position_direction && (
                    <Badge variant={state.position_direction === 'long' ? 'default' : 'destructive'} className="text-xs">
                      {state.position_direction}
                    </Badge>
                  )}
                </div>
                {state.position_entry_price && (
                  <div className="text-muted-foreground text-xs flex justify-between">
                    <span>Entry: ${state.position_entry_price.toFixed(state.position_entry_price < 1 ? 4 : 2)}</span>
                    {state.current_price && (
                      <span className="font-medium">Now: ${state.current_price.toFixed(state.current_price < 1 ? 4 : 2)}</span>
                    )}
                  </div>
                )}
                {state.position_size && (
                  <div className="text-muted-foreground text-xs">
                    Size: {state.position_size.toFixed(state.position_size < 1 ? 6 : 2)}
                  </div>
                )}
                {state.unrealized_pnl !== null && state.unrealized_pnl !== undefined && (
                  <div className={`text-xs font-medium ${state.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    Unrealized: {state.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(state.unrealized_pnl)}
                    {state.unrealized_pnl_pct !== null && state.unrealized_pnl_pct !== undefined && (
                      <span className="ml-1">({state.unrealized_pnl_pct >= 0 ? '+' : ''}{state.unrealized_pnl_pct.toFixed(2)}%)</span>
                    )}
                  </div>
                )}
                <div className="text-muted-foreground text-xs">
                  Capital: {formatCurrency(state.current_capital)}
                </div>
                <div className={`text-xs ${state.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  Realized: {state.realized_pnl >= 0 ? '+' : ''}{formatCurrency(state.realized_pnl)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyExecutionPanel;
