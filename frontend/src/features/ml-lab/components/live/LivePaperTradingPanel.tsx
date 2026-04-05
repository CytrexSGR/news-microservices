/**
 * ML Lab Live Paper Trading Panel
 *
 * Real-time paper trading dashboard with live ML strategy execution.
 * Supports up to 10 parallel trading sessions for different coins.
 * Shows current positions, P&L, and gate predictions for all sessions.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Play,
  Square,
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Clock,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  BarChart3,
  Zap,
  Radio,
  History,
  Plus,
  X,
  Layers,
  Eye,
  BookOpen,
  ExternalLink,
} from 'lucide-react';
import toast from 'react-hot-toast';

import {
  liveTradingApi,
  shadowTradeApi,
  type LiveTradingStats,
  type LiveTradingTickResult,
  type LiveTradingSession,
  type TradingMode,
  type ForceTradeResponse,
} from '../../api/mlLabApi';
import { MLArea } from '../../types';
import type { ShadowTrade, ShadowTradeStats } from '../../types';
import {
  AREA_ICONS,
  SYMBOLS,
  TIMEFRAMES,
  PREDICTION_COLORS,
  PAPER_TRADING_CONFIG,
} from '../../utils/constants';

// Import modals
import { OpenPositionsModal } from './OpenPositionsModal';
import { TradeHistoryModal } from './TradeHistoryModal';
import { TradeDetailModal } from './TradeDetailModal';

// Maximum parallel sessions
const MAX_SESSIONS = 10;

// Activity log entry type
interface ActivityLogEntry {
  id: number;
  timestamp: Date;
  symbol: string;
  action: string;
  price: number;
  confidence: number;
  reasoning: string;
}

export function LivePaperTradingPanel() {
  // Multi-session state
  const [sessions, setSessions] = useState<LiveTradingSession[]>([]);
  const [lastTicks, setLastTicks] = useState<Record<string, LiveTradingTickResult>>({});

  // Legacy single-session state (for backward compatibility)
  const [stats, setStats] = useState<LiveTradingStats | null>(null);
  const [lastTick, setLastTick] = useState<LiveTradingTickResult | null>(null);

  // New session form state
  const [selectedSymbol, setSelectedSymbol] = useState(PAPER_TRADING_CONFIG.DEFAULT_SYMBOL);
  const [selectedTimeframe, setSelectedTimeframe] = useState(PAPER_TRADING_CONFIG.DEFAULT_TIMEFRAME);
  const [selectedMode, setSelectedMode] = useState<TradingMode>('live');

  // Force trade state
  const [forcingTrade, setForcingTrade] = useState<string | null>(null);

  // UI state
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [stoppingSymbol, setStoppingSymbol] = useState<string | null>(null);
  const [ticking, setTicking] = useState(false);
  const [autoTick, setAutoTick] = useState(false);
  const [countdown, setCountdown] = useState(PAPER_TRADING_CONFIG.TICK_INTERVAL_SECONDS);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  // Modal states
  const [openPositionsModalOpen, setOpenPositionsModalOpen] = useState(false);
  const [tradeHistoryModalOpen, setTradeHistoryModalOpen] = useState(false);
  const [tradeDetailModalOpen, setTradeDetailModalOpen] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<ShadowTrade | null>(null);

  // Shadow trade stats for summary
  const [shadowStats, setShadowStats] = useState<ShadowTradeStats | null>(null);
  const [openPositionsCount, setOpenPositionsCount] = useState(0);

  const autoTickRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);
  const activityIdRef = useRef(0);

  // Computed values
  const activeSymbols = sessions.map(s => s.symbol);
  const availableSymbols = SYMBOLS.filter(s => !activeSymbols.includes(s.value));
  const canAddMore = sessions.length < MAX_SESSIONS && availableSymbols.length > 0;
  const hasRunningSessions = sessions.length > 0;

  // Fetch all sessions status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await liveTradingApi.getSessions();
      setSessions(response.sessions || []);

      // Legacy support: set first session as main stats
      if (response.sessions && response.sessions.length > 0) {
        const firstSession = response.sessions[0];
        setStats({
          symbol: firstSession.symbol,
          timeframe: firstSession.timeframe,
          is_running: firstSession.is_running,
          capital: firstSession.current_capital,
          initial_capital: firstSession.initial_capital,
          realized_pnl: firstSession.realized_pnl,
          realized_pnl_pct: firstSession.realized_pnl_pct,
          total_trades: firstSession.total_trades,
          winning_trades: firstSession.winning_trades,
          losing_trades: firstSession.losing_trades,
          win_rate: firstSession.win_rate,
          has_position: !!firstSession.current_position,
          current_position: firstSession.current_position || null,
        });

        // Auto-start auto-tick if any session is running
        if (!autoTick && response.sessions.some(s => s.is_running)) {
          setAutoTick(true);
        }
      } else {
        setStats(null);
      }
    } catch (error) {
      console.error('Failed to fetch live trading status:', error);
    } finally {
      setLoading(false);
    }
  }, [autoTick]);

  // Fetch shadow trade stats for summary display
  const fetchShadowStats = useCallback(async () => {
    try {
      const [statsResponse, openResponse] = await Promise.all([
        shadowTradeApi.getStats({ days: 30 }),
        shadowTradeApi.list({ status: 'open', limit: 1 }), // Just need total count
      ]);
      setShadowStats(statsResponse);
      setOpenPositionsCount(openResponse.total || 0);
    } catch (error) {
      console.error('Failed to fetch shadow stats:', error);
    }
  }, []);

  // Handle trade click from modals
  const handleTradeClick = (trade: ShadowTrade) => {
    setSelectedTrade(trade);
    setTradeDetailModalOpen(true);
  };

  // Start live trading for a new symbol
  const handleStart = async () => {
    if (!selectedSymbol || activeSymbols.includes(selectedSymbol)) {
      toast.error('Symbol already active or invalid');
      return;
    }

    setStarting(true);
    try {
      const response = await liveTradingApi.start(selectedSymbol, selectedTimeframe, selectedMode);
      const modeLabel = selectedMode === 'test' ? ' (TEST MODE)' : selectedMode === 'backtest' ? ' (BACKTEST)' : '';
      toast.success(`Live trading started for ${selectedSymbol}${modeLabel}`);

      // Refresh sessions list
      await fetchStatus();

      // Select next available symbol for convenience
      if (availableSymbols.length > 1) {
        const nextSymbol = availableSymbols.find(s => s.value !== selectedSymbol);
        if (nextSymbol) {
          setSelectedSymbol(nextSymbol.value);
        }
      }
    } catch (error: unknown) {
      console.error('Failed to start live trading:', error);
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to start: ${message}`);
    } finally {
      setStarting(false);
    }
  };

  // Stop live trading for a specific symbol or all
  const handleStop = async (symbol?: string) => {
    setStoppingSymbol(symbol || 'all');
    try {
      const response = await liveTradingApi.stop(symbol);

      if (symbol) {
        toast.success(`Stopped trading for ${symbol}`);
      } else {
        toast.success(`Stopped ${response.stopped_symbols?.length || 0} trading sessions`);
        setAutoTick(false);
      }

      // Refresh sessions list
      await fetchStatus();
    } catch (error) {
      console.error('Failed to stop live trading:', error);
      toast.error('Failed to stop trading');
    } finally {
      setStoppingSymbol(null);
    }
  };

  // Manual tick for all sessions
  const handleTick = async () => {
    if (sessions.length === 0) return;

    setTicking(true);
    try {
      const response = await liveTradingApi.tick();

      // Handle multi-symbol tick results
      if (response.tick_results) {
        setLastTicks(response.tick_results);

        // Add entries to activity log for each symbol
        Object.entries(response.tick_results).forEach(([symbol, result]) => {
          if (result && !('error' in result)) {
            const newEntry: ActivityLogEntry = {
              id: ++activityIdRef.current,
              timestamp: new Date(),
              symbol,
              action: result.action,
              price: result.price,
              confidence: result.confidence,
              reasoning: result.reasoning,
            };
            setActivityLog(prev => [newEntry, ...prev].slice(0, 20));
          }
        });

        // Set first result as legacy lastTick
        const firstSymbol = Object.keys(response.tick_results)[0];
        if (firstSymbol) {
          setLastTick(response.tick_results[firstSymbol]);
        }
      } else if (response.tick_result) {
        // Single symbol response (backward compatibility)
        setLastTick(response.tick_result);
        const symbol = response.symbol || sessions[0]?.symbol || 'UNKNOWN';
        setLastTicks({ [symbol]: response.tick_result });

        const newEntry: ActivityLogEntry = {
          id: ++activityIdRef.current,
          timestamp: new Date(),
          symbol,
          action: response.tick_result.action,
          price: response.tick_result.price,
          confidence: response.tick_result.confidence,
          reasoning: response.tick_result.reasoning,
        };
        setActivityLog(prev => [newEntry, ...prev].slice(0, 20));
      }

      // Refresh sessions to get updated stats
      await fetchStatus();

      // Reset countdown after successful tick
      setCountdown(PAPER_TRADING_CONFIG.TICK_INTERVAL_SECONDS);
    } catch (error: unknown) {
      console.error('Tick failed:', error);
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Tick failed: ${message}`);
    } finally {
      setTicking(false);
    }
  };

  // Toggle auto-tick
  const toggleAutoTick = () => {
    setAutoTick((prev) => !prev);
  };

  // Force trade handler (TEST mode only)
  const handleForceTrade = async (symbol: string, action: 'enter_long' | 'enter_short' | 'exit') => {
    setForcingTrade(`${symbol}-${action}`);
    try {
      const response = await liveTradingApi.forceTrade(symbol, action);

      if (response.success) {
        toast.success(response.message);
        // Refresh sessions to get updated stats
        await fetchStatus();
      } else {
        toast.error(response.message);
      }
    } catch (error: unknown) {
      console.error('Force trade failed:', error);
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Force trade failed: ${message}`);
    } finally {
      setForcingTrade(null);
    }
  };

  // Auto-tick effect - runs for ALL sessions
  useEffect(() => {
    if (autoTick && hasRunningSessions) {
      // Run immediately then every TICK_INTERVAL seconds
      handleTick();
      autoTickRef.current = setInterval(() => {
        handleTick();
      }, PAPER_TRADING_CONFIG.TICK_INTERVAL_SECONDS * 1000);
    } else {
      if (autoTickRef.current) {
        clearInterval(autoTickRef.current);
        autoTickRef.current = null;
      }
    }
    return () => {
      if (autoTickRef.current) {
        clearInterval(autoTickRef.current);
      }
    };
  }, [autoTick, hasRunningSessions]);

  // Countdown effect for auto-tick
  useEffect(() => {
    if (autoTick && hasRunningSessions) {
      countdownRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) return PAPER_TRADING_CONFIG.TICK_INTERVAL_SECONDS;
          return prev - 1;
        });
      }, 1000);
    } else {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
      setCountdown(PAPER_TRADING_CONFIG.TICK_INTERVAL_SECONDS);
    }
    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    };
  }, [autoTick, hasRunningSessions]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
    fetchShadowStats();
    const statusInterval = setInterval(fetchStatus, 30000);
    const statsInterval = setInterval(fetchShadowStats, 60000); // Update stats every minute
    return () => {
      clearInterval(statusInterval);
      clearInterval(statsInterval);
    };
  }, [fetchStatus, fetchShadowStats]);

  // Calculate totals across all sessions
  const totalPnl = sessions.reduce((sum, s) => sum + s.realized_pnl, 0);
  const totalInitialCapital = sessions.reduce((sum, s) => sum + s.initial_capital, 0);
  const totalPnlPct = totalInitialCapital > 0 ? (totalPnl / totalInitialCapital) * 100 : 0;
  const totalTrades = sessions.reduce((sum, s) => sum + s.total_trades, 0);
  const totalWins = sessions.reduce((sum, s) => sum + s.winning_trades, 0);
  const avgWinRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Multi-Coin Paper Trading
            {hasRunningSessions && (
              <Badge className="ml-2 bg-green-500">
                {sessions.length} / {MAX_SESSIONS} active
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            Trade up to {MAX_SESSIONS} coins simultaneously with ML-driven strategies
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Add New Session Row */}
          <div className="flex flex-wrap items-center gap-4 p-4 bg-muted/50 rounded-lg mb-4">
            <div className="flex items-center gap-2">
              <Plus className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Add Coin:</span>
            </div>

            {/* Symbol Selection - only show available symbols */}
            <Select
              value={selectedSymbol}
              onValueChange={setSelectedSymbol}
              disabled={!canAddMore}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Select..." />
              </SelectTrigger>
              <SelectContent>
                {availableSymbols.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Timeframe Selection */}
            <Select
              value={selectedTimeframe}
              onValueChange={setSelectedTimeframe}
              disabled={!canAddMore}
            >
              <SelectTrigger className="w-24">
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

            {/* Mode Selection */}
            <Select
              value={selectedMode}
              onValueChange={(v) => setSelectedMode(v as TradingMode)}
              disabled={!canAddMore}
            >
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="live">
                  <span className="flex items-center gap-1">
                    <Activity className="h-3 w-3 text-green-500" />
                    Live
                  </span>
                </SelectItem>
                <SelectItem value="test">
                  <span className="flex items-center gap-1">
                    <Zap className="h-3 w-3 text-yellow-500" />
                    Test
                  </span>
                </SelectItem>
                <SelectItem value="backtest" disabled>
                  <span className="flex items-center gap-1">
                    <History className="h-3 w-3 text-blue-500" />
                    Backtest
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>

            <Button
              onClick={handleStart}
              disabled={starting || !canAddMore}
              size="sm"
            >
              {starting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start
            </Button>

            {!canAddMore && (
              <span className="text-xs text-muted-foreground">
                {sessions.length >= MAX_SESSIONS
                  ? 'Max sessions reached'
                  : 'No more symbols available'}
              </span>
            )}
          </div>

          {/* Global Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {hasRunningSessions && (
              <>
                <Button
                  variant="outline"
                  onClick={handleTick}
                  disabled={ticking}
                  size="sm"
                >
                  {ticking ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Tick All
                </Button>
                <Button
                  variant={autoTick ? 'default' : 'outline'}
                  onClick={toggleAutoTick}
                  size="sm"
                >
                  <Zap className="h-4 w-4 mr-2" />
                  {autoTick ? 'Auto: ON' : 'Auto: OFF'}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleStop()}
                  disabled={stoppingSymbol === 'all'}
                  size="sm"
                >
                  {stoppingSymbol === 'all' ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Square className="h-4 w-4 mr-2" />
                  )}
                  Stop All
                </Button>
              </>
            )}

            {/* Status Badges */}
            <div className="flex items-center gap-2 ml-auto">
              {hasRunningSessions ? (
                <Badge className="bg-green-500">
                  <span className="relative flex h-2 w-2 mr-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                  </span>
                  LIVE
                </Badge>
              ) : (
                <Badge className="bg-gray-500">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  No Sessions
                </Badge>
              )}

              {autoTick && hasRunningSessions && (
                <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30 animate-pulse">
                  <Radio className="h-3 w-3 mr-1" />
                  Next tick: {countdown}s
                </Badge>
              )}

              {ticking && (
                <Badge className="bg-orange-500 animate-pulse">
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Analyzing...
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Sessions Grid */}
      {hasRunningSessions && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Active Sessions ({sessions.length})
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sessions.map((session) => {
              const sessionPnlColor = session.realized_pnl >= 0 ? 'text-green-500' : 'text-red-500';
              const sessionLastTick = lastTicks[session.symbol];

              return (
                <Card key={session.session_id} className="relative">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between text-base">
                      <span className="flex items-center gap-2">
                        <Badge variant="outline">{session.symbol}</Badge>
                        <span className="text-xs text-muted-foreground">{session.timeframe}</span>
                        {/* Mode Badge */}
                        {session.mode === 'test' && (
                          <Badge className="bg-yellow-500 text-[10px]">TEST</Badge>
                        )}
                        {session.mode === 'backtest' && (
                          <Badge className="bg-blue-500 text-[10px]">BACKTEST</Badge>
                        )}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStop(session.symbol)}
                        disabled={stoppingSymbol === session.symbol}
                        className="h-6 w-6 p-0"
                      >
                        {stoppingSymbol === session.symbol ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <X className="h-3 w-3" />
                        )}
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {/* Session Stats */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Capital:</span>
                        <span className="ml-1 font-medium">
                          ${session.current_capital.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">P&L:</span>
                        <span className={`ml-1 font-medium ${sessionPnlColor}`}>
                          {session.realized_pnl_pct >= 0 ? '+' : ''}{session.realized_pnl_pct.toFixed(2)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Trades:</span>
                        <span className="ml-1 font-medium">{session.total_trades}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Win Rate:</span>
                        <span className="ml-1 font-medium">{session.win_rate.toFixed(0)}%</span>
                      </div>
                    </div>

                    {/* Position Info */}
                    {session.current_position && (
                      <div className="mt-2 p-2 bg-muted rounded text-xs">
                        <div className="flex items-center gap-1">
                          {session.current_position.direction === 'long' ? (
                            <TrendingUp className="h-3 w-3 text-green-500" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-red-500" />
                          )}
                          <span className="capitalize font-medium">{session.current_position.direction}</span>
                          <span className="text-muted-foreground">@</span>
                          <span className="font-mono">${session.current_position.entry_price.toFixed(4)}</span>
                          <span className={session.current_position.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}>
                            ({session.current_position.pnl_pct >= 0 ? '+' : ''}{session.current_position.pnl_pct.toFixed(2)}%)
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Current Price */}
                    {session.current_price && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        Price: <span className="font-mono">${session.current_price.toFixed(4)}</span>
                      </div>
                    )}

                    {/* Last Tick Action */}
                    {sessionLastTick && (
                      <div className="mt-2 flex items-center gap-1 text-xs">
                        <Badge
                          className={`text-[10px] ${
                            sessionLastTick.action === 'enter_long'
                              ? 'bg-green-500'
                              : sessionLastTick.action === 'enter_short'
                                ? 'bg-red-500'
                                : sessionLastTick.action === 'exit'
                                  ? 'bg-orange-500'
                                  : 'bg-gray-500'
                          }`}
                        >
                          {sessionLastTick.action.replace('_', ' ')}
                        </Badge>
                        <span className="text-muted-foreground truncate">
                          {sessionLastTick.reasoning.substring(0, 40)}...
                        </span>
                      </div>
                    )}

                    {/* Force Trade Controls (TEST mode only) */}
                    {session.mode === 'test' && (
                      <div className="mt-3 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded">
                        <div className="text-xs font-medium text-yellow-600 mb-2 flex items-center gap-1">
                          <Zap className="h-3 w-3" />
                          Force Trade (Test Mode)
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {!session.current_position ? (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs bg-green-500/10 border-green-500/30 hover:bg-green-500/20"
                                onClick={() => handleForceTrade(session.symbol, 'enter_long')}
                                disabled={forcingTrade === `${session.symbol}-enter_long`}
                              >
                                {forcingTrade === `${session.symbol}-enter_long` ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <>
                                    <TrendingUp className="h-3 w-3 mr-1" />
                                    Long
                                  </>
                                )}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs bg-red-500/10 border-red-500/30 hover:bg-red-500/20"
                                onClick={() => handleForceTrade(session.symbol, 'enter_short')}
                                disabled={forcingTrade === `${session.symbol}-enter_short`}
                              >
                                {forcingTrade === `${session.symbol}-enter_short` ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <>
                                    <TrendingDown className="h-3 w-3 mr-1" />
                                    Short
                                  </>
                                )}
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-6 text-xs bg-orange-500/10 border-orange-500/30 hover:bg-orange-500/20"
                              onClick={() => handleForceTrade(session.symbol, 'exit')}
                              disabled={forcingTrade === `${session.symbol}-exit`}
                            >
                              {forcingTrade === `${session.symbol}-exit` ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <>
                                  <X className="h-3 w-3 mr-1" />
                                  Exit Position
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      {hasRunningSessions && (
        <Card className="border-2 border-primary/20">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Portfolio Summary
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setOpenPositionsModalOpen(true)}
                  className="h-8"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  Open Positions
                  {openPositionsCount > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5">
                      {openPositionsCount}
                    </Badge>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTradeHistoryModalOpen(true)}
                  className="h-8"
                >
                  <BookOpen className="h-4 w-4 mr-1" />
                  Trade History
                  {shadowStats && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5">
                      {shadowStats.total_trades}
                    </Badge>
                  )}
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Live Session Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center p-3 bg-muted rounded-lg">
                <p className="text-xs text-muted-foreground">Total Capital</p>
                <p className="text-xl font-bold">
                  ${sessions.reduce((sum, s) => sum + s.current_capital, 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <p className="text-xs text-muted-foreground">Session P&L</p>
                <p className={`text-xl font-bold ${totalPnlPct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%
                </p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <p className="text-xs text-muted-foreground">Session Trades</p>
                <p className="text-xl font-bold">{totalTrades}</p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <p className="text-xs text-muted-foreground">Session Win Rate</p>
                <p className="text-xl font-bold">{avgWinRate.toFixed(1)}%</p>
              </div>
            </div>

            {/* All-Time Shadow Trade Stats */}
            {shadowStats && (
              <div className="border-t pt-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-1">
                  <History className="h-3 w-3" />
                  All-Time Paper Trading Stats (30 days)
                </p>
                <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                  <div
                    className="text-center p-2 bg-blue-500/10 rounded-lg cursor-pointer hover:bg-blue-500/20 transition-colors"
                    onClick={() => setOpenPositionsModalOpen(true)}
                  >
                    <p className="text-[10px] text-muted-foreground">Open Positions</p>
                    <p className="text-lg font-bold text-blue-500">{openPositionsCount}</p>
                  </div>
                  <div
                    className="text-center p-2 bg-muted rounded-lg cursor-pointer hover:bg-muted/80 transition-colors"
                    onClick={() => setTradeHistoryModalOpen(true)}
                  >
                    <p className="text-[10px] text-muted-foreground">Closed Trades</p>
                    <p className="text-lg font-bold">{shadowStats.total_trades}</p>
                  </div>
                  <div className="text-center p-2 bg-muted rounded-lg">
                    <p className="text-[10px] text-muted-foreground">Win Rate</p>
                    <p className={`text-lg font-bold ${shadowStats.win_rate_pct >= 50 ? 'text-green-500' : 'text-red-500'}`}>
                      {shadowStats.win_rate_pct.toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-2 bg-muted rounded-lg">
                    <p className="text-[10px] text-muted-foreground">Total P&L</p>
                    <p className={`text-lg font-bold ${shadowStats.total_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {shadowStats.total_pnl_pct >= 0 ? '+' : ''}{shadowStats.total_pnl_pct.toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-center p-2 bg-green-500/10 rounded-lg">
                    <p className="text-[10px] text-muted-foreground">Best Trade</p>
                    <p className="text-lg font-bold text-green-500">+{shadowStats.max_win_pct.toFixed(2)}%</p>
                  </div>
                  <div className="text-center p-2 bg-red-500/10 rounded-lg">
                    <p className="text-[10px] text-muted-foreground">Worst Trade</p>
                    <p className="text-lg font-bold text-red-500">{shadowStats.max_loss_pct.toFixed(2)}%</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}


      {/* Last Tick Decision Panel - Shows most recent ML decision across all sessions */}
      {hasRunningSessions && lastTick && (
        <Card className="border-2 border-primary/20">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Last ML Decision
                <Badge variant="outline" className="font-mono">{lastTick.symbol}</Badge>
              </span>
              <span className="text-sm font-normal text-muted-foreground">
                {new Date(lastTick.timestamp).toLocaleTimeString()}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Main Decision Row */}
            <div className="grid grid-cols-3 gap-4 mb-4 p-4 bg-muted rounded-lg">
              <div className="text-center">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Action</p>
                <p
                  className={`text-2xl font-bold capitalize ${
                    lastTick.action === 'enter_long'
                      ? 'text-green-500'
                      : lastTick.action === 'enter_short'
                        ? 'text-red-500'
                        : lastTick.action === 'exit'
                          ? 'text-orange-500'
                          : 'text-gray-400'
                  }`}
                >
                  {lastTick.action.replace('_', ' ')}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Price</p>
                <p className="text-2xl font-bold font-mono">${lastTick.price.toFixed(4)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Confidence</p>
                <p className="text-2xl font-bold">{(lastTick.confidence * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Reasoning */}
            <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Why?</p>
              <p className="text-sm font-medium">{lastTick.reasoning}</p>
            </div>

            {/* Gate Results Grid */}
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Gate Predictions</p>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                {Object.entries(lastTick.gates).map(([gate, result]) => (
                  <div
                    key={gate}
                    className={`p-2 rounded-lg text-center border ${
                      result.prediction === 'bullish' || result.prediction === 'enter' || result.prediction === 'low'
                        ? 'bg-green-500/10 border-green-500/30'
                        : result.prediction === 'bearish' || result.prediction === 'exit' || result.prediction === 'high'
                          ? 'bg-red-500/10 border-red-500/30'
                          : 'bg-muted border-muted-foreground/20'
                    }`}
                  >
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      {AREA_ICONS[gate as MLArea]}
                    </div>
                    <p className="text-[10px] text-muted-foreground uppercase">{gate}</p>
                    <p
                      className={`text-xs font-bold capitalize ${
                        result.prediction === 'bullish' || result.prediction === 'enter' || result.prediction === 'low'
                          ? 'text-green-500'
                          : result.prediction === 'bearish' || result.prediction === 'exit' || result.prediction === 'high'
                            ? 'text-red-500'
                            : 'text-muted-foreground'
                      }`}
                    >
                      {result.prediction}
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      {(result.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Trade Execution Info */}
            {lastTick.trade && (
              <div className="mt-4 p-3 border-2 border-primary rounded-lg bg-primary/5">
                <p className="text-sm font-bold mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Trade Executed: {lastTick.trade.type}
                </p>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Direction: </span>
                    <span className="font-medium capitalize">{lastTick.trade.direction}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Entry: </span>
                    <span className="font-medium">${lastTick.trade.entry_price.toFixed(4)}</span>
                  </div>
                  {lastTick.trade.pnl_pct !== undefined && (
                    <div>
                      <span className="text-muted-foreground">P&L: </span>
                      <span className={`font-bold ${lastTick.trade.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {lastTick.trade.pnl_pct >= 0 ? '+' : ''}{lastTick.trade.pnl_pct.toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Activity Log - Shows recent ticks */}
      {hasRunningSessions && activityLog.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="h-4 w-4" />
              Activity Log
              <Badge variant="outline" className="ml-auto text-xs">
                {activityLog.length} entries
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {activityLog.map((entry, index) => (
                <div
                  key={entry.id}
                  className={`flex items-center justify-between p-2 rounded-lg text-sm ${
                    index === 0 ? 'bg-primary/10 border border-primary/20' : 'bg-muted/50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground w-16">
                      {entry.timestamp.toLocaleTimeString()}
                    </span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {entry.symbol.replace('USDT', '')}
                    </Badge>
                    <Badge
                      className={`text-xs ${
                        entry.action === 'enter_long'
                          ? 'bg-green-500'
                          : entry.action === 'enter_short'
                            ? 'bg-red-500'
                            : entry.action === 'exit'
                              ? 'bg-orange-500'
                              : 'bg-gray-500'
                      }`}
                    >
                      {entry.action.replace('_', ' ')}
                    </Badge>
                    <span className="text-xs text-muted-foreground truncate max-w-[150px]">
                      {entry.reasoning}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="font-mono">${entry.price.toFixed(4)}</span>
                    <span className="text-muted-foreground">
                      {(entry.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State with Trade History Access */}
      {!hasRunningSessions && (
        <Card>
          <CardContent className="py-12 text-center">
            <Layers className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No active trading sessions</p>
            <p className="text-muted-foreground mb-6">
              Select a coin above and click "Start" to begin paper trading.
              You can run up to {MAX_SESSIONS} coins simultaneously.
            </p>

            {/* Quick access to trade history even when no sessions are running */}
            {(shadowStats || openPositionsCount > 0) && (
              <div className="border-t pt-6 mt-4">
                <p className="text-sm text-muted-foreground mb-4">View your paper trading history:</p>
                <div className="flex justify-center gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setOpenPositionsModalOpen(true)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Open Positions
                    {openPositionsCount > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {openPositionsCount}
                      </Badge>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setTradeHistoryModalOpen(true)}
                  >
                    <BookOpen className="h-4 w-4 mr-2" />
                    Trade History
                    {shadowStats && (
                      <Badge variant="secondary" className="ml-2">
                        {shadowStats.total_trades}
                      </Badge>
                    )}
                  </Button>
                </div>

                {/* Mini stats display */}
                {shadowStats && (
                  <div className="grid grid-cols-3 gap-4 mt-6 max-w-md mx-auto">
                    <div className="text-center">
                      <p className="text-2xl font-bold">{shadowStats.total_trades}</p>
                      <p className="text-xs text-muted-foreground">Trades</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-2xl font-bold ${shadowStats.win_rate_pct >= 50 ? 'text-green-500' : 'text-red-500'}`}>
                        {shadowStats.win_rate_pct.toFixed(1)}%
                      </p>
                      <p className="text-xs text-muted-foreground">Win Rate</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-2xl font-bold ${shadowStats.total_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {shadowStats.total_pnl_pct >= 0 ? '+' : ''}{shadowStats.total_pnl_pct.toFixed(2)}%
                      </p>
                      <p className="text-xs text-muted-foreground">Total P&L</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modals */}
      <OpenPositionsModal
        open={openPositionsModalOpen}
        onOpenChange={setOpenPositionsModalOpen}
        onTradeClick={handleTradeClick}
      />
      <TradeHistoryModal
        open={tradeHistoryModalOpen}
        onOpenChange={setTradeHistoryModalOpen}
        onTradeClick={handleTradeClick}
      />
      <TradeDetailModal
        open={tradeDetailModalOpen}
        onOpenChange={setTradeDetailModalOpen}
        trade={selectedTrade}
      />
    </div>
  );
}

export default LivePaperTradingPanel;
