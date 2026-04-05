/**
 * PaperTradeTab Component
 *
 * Mini paper trading interface within Strategy Page.
 * Supports multi-coin testing for the current strategy.
 * Connected to Paper Trading API (prediction-service).
 */

import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/Switch';
import { Label } from '@/components/ui/Label';
import {
  Play,
  Square,
  Activity,
  TrendingUp,
  TrendingDown,
  Plus,
  X,
  Loader2,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import type { Strategy } from '../../types';
import { BYBIT_SYMBOLS } from '@/constants/symbols';
import { usePaperTrading } from '../../hooks/usePaperTrading';

interface PaperTradeTabProps {
  strategy: Strategy;
}

const MAX_SESSIONS = 5;

export function PaperTradeTab({ strategy }: PaperTradeTabProps) {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  const {
    sessions,
    isLoading,
    autoTick,
    setAutoTick,
    totalPnl,
    totalTrades,
    activeSymbols,
    startSession,
    stopSession,
    stopAllSessions,
    manualTick,
    enterPosition,
    exitPosition,
    isCreating,
    isStopping,
    isStoppingAll,
    isTicking,
  } = usePaperTrading({
    strategyId: strategy.id,
    autoTickInterval: 5000,
  });

  const availableSymbols = BYBIT_SYMBOLS.filter(s => !activeSymbols.includes(s.symbol));
  const canAddMore = sessions.length < MAX_SESSIONS && availableSymbols.length > 0;

  const handleStartSession = useCallback(() => {
    if (!selectedSymbol || activeSymbols.includes(selectedSymbol)) {
      return;
    }

    startSession(selectedSymbol, 10000);

    // Select next available symbol
    const nextAvailable = availableSymbols.find(s => s.symbol !== selectedSymbol);
    if (nextAvailable) {
      setSelectedSymbol(nextAvailable.symbol);
    }
  }, [selectedSymbol, activeSymbols, availableSymbols, startSession]);

  const handleStopAll = useCallback(() => {
    stopAllSessions();
  }, [stopAllSessions]);

  // Format position display
  const formatPosition = (position: { direction: 'long' | 'short'; entry_price: number; size: number } | null) => {
    if (!position) return null;
    return {
      direction: position.direction,
      entryPrice: position.entry_price,
      size: position.size,
    };
  };

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Mini Paper Trading
              </CardTitle>
              <CardDescription>
                Test {strategy.name} with live market data (simulated trades)
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  id="auto-tick"
                  checked={autoTick}
                  onCheckedChange={setAutoTick}
                />
                <Label htmlFor="auto-tick" className="text-sm">
                  Auto-tick (5s)
                </Label>
              </div>
              {sessions.length > 0 && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleStopAll}
                  disabled={isStoppingAll}
                >
                  {isStoppingAll ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Square className="h-4 w-4 mr-1" />
                  )}
                  Stop All
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Add Session */}
          {canAddMore && (
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg mb-4">
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select coin" />
                </SelectTrigger>
                <SelectContent>
                  {availableSymbols.map((s) => (
                    <SelectItem key={s.symbol} value={s.symbol}>
                      {s.base}/USDT
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={handleStartSession} disabled={isCreating}>
                {isCreating ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4 mr-1" />
                )}
                Add Session
              </Button>
              <span className="text-sm text-muted-foreground">
                {sessions.length}/{MAX_SESSIONS} sessions
              </span>
            </div>
          )}

          {/* Portfolio Summary */}
          {sessions.length > 0 && (
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">Total P&L</p>
                <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${totalPnl.toFixed(2)}
                </p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">Active Sessions</p>
                <p className="text-2xl font-bold">{sessions.length}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">Total Trades</p>
                <p className="text-2xl font-bold">{totalTrades}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-8 text-muted-foreground">
              <Loader2 className="h-12 w-12 mx-auto mb-3 animate-spin opacity-50" />
              <p>Loading sessions...</p>
            </div>
          )}

          {/* Session List */}
          {!isLoading && sessions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No active sessions</p>
              <p className="text-sm">Add a session to start paper trading</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => {
                const position = formatPosition(session.current_position);
                return (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border"
                  >
                    <div className="flex items-center gap-4">
                      <Badge variant={session.status === 'running' ? 'default' : 'secondary'}>
                        {session.symbol.replace('USDT', '')}
                      </Badge>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className={`font-mono font-bold ${session.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${session.pnl.toFixed(2)} ({session.pnl_percent.toFixed(2)}%)
                          </p>
                          {session.last_price > 0 && (
                            <span className="text-xs text-muted-foreground">
                              @ ${session.last_price.toLocaleString()}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {session.trades} trades | {session.win_rate.toFixed(0)}% win rate
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Position Badge */}
                      {position && (
                        <Badge variant={position.direction === 'long' ? 'default' : 'destructive'}>
                          {position.direction === 'long' ? (
                            <TrendingUp className="h-3 w-3 mr-1" />
                          ) : (
                            <TrendingDown className="h-3 w-3 mr-1" />
                          )}
                          {position.direction.toUpperCase()} @ ${position.entryPrice.toLocaleString()}
                        </Badge>
                      )}

                      {/* Manual Tick */}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => manualTick(session.id)}
                        disabled={isTicking}
                        title="Manual tick"
                      >
                        <RefreshCw className={`h-4 w-4 ${isTicking ? 'animate-spin' : ''}`} />
                      </Button>

                      {/* Enter/Exit Position */}
                      {!position ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => enterPosition(session.id, 'long', 0.1)}
                            title="Enter Long"
                            className="text-green-600 border-green-600 hover:bg-green-50"
                          >
                            <ArrowUpRight className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => enterPosition(session.id, 'short', 0.1)}
                            title="Enter Short"
                            className="text-red-600 border-red-600 hover:bg-red-50"
                          >
                            <ArrowDownRight className="h-4 w-4" />
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => exitPosition(session.id)}
                          title="Close Position"
                        >
                          Close
                        </Button>
                      )}

                      {/* Stop Session */}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => stopSession(session.id)}
                        disabled={isStopping}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-sm text-muted-foreground space-y-2">
            <p><strong>Note:</strong> This is a mini paper trading environment for quick strategy validation.</p>
            <p>
              <strong>Controls:</strong> Use the arrow buttons to manually enter long/short positions,
              or enable auto-tick to fetch live prices every 5 seconds.
            </p>
            <p>
              For long-running multi-strategy tests, use <strong>Extended Paper Trading</strong> after deploying from the Lab.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
