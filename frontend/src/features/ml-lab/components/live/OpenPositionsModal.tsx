/**
 * Open Positions Modal
 *
 * Shows all open paper trading positions with unrealized P&L.
 * Calculates unrealized P&L based on entry price vs current price.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Loader2,
  DollarSign,
  Clock,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  ExternalLink,
} from 'lucide-react';

import { shadowTradeApi } from '../../api/mlLabApi';
import type { ShadowTrade } from '../../types';
import { SYMBOLS } from '../../utils/constants';

interface OpenPositionsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTradeClick?: (trade: ShadowTrade) => void;
}

interface PositionWithPnL extends ShadowTrade {
  current_price: number | null;
  unrealized_pnl_pct: number | null;  // P&L with leverage applied
  base_unrealized_pnl_pct: number | null;  // P&L without leverage
  duration_hours: number;
}

// Fetch current price from ccxt/bybit
async function fetchCurrentPrice(symbol: string): Promise<number | null> {
  try {
    // Use the live trading indicators endpoint to get current price
    const response = await fetch(`/api/prediction/v1/ml/live-trading/indicators?symbol=${symbol}&timeframe=5min`);
    if (response.ok) {
      const data = await response.json();
      return data.price?.current || null;
    }
    return null;
  } catch {
    return null;
  }
}

export function OpenPositionsModal({ open, onOpenChange, onTradeClick }: OpenPositionsModalProps) {
  const [positions, setPositions] = useState<PositionWithPnL[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'time' | 'pnl' | 'symbol'>('time');

  const fetchPositions = useCallback(async () => {
    try {
      const params: { symbol?: string; limit: number } = {
        limit: 500,
      };
      if (selectedSymbol !== 'all') {
        params.symbol = selectedSymbol;
      }

      // Use getOpenPositions which fetches from the correct endpoint
      const response = await shadowTradeApi.getOpenPositions(params);
      const trades = response.positions || [];

      // Fetch current prices for all unique symbols
      const uniqueSymbols = [...new Set(trades.map((t) => t.symbol))];
      const priceMap: Record<string, number | null> = {};

      await Promise.all(
        uniqueSymbols.map(async (sym) => {
          priceMap[sym] = await fetchCurrentPrice(sym);
        })
      );

      // Calculate unrealized P&L for each position (with leverage)
      const positionsWithPnL: PositionWithPnL[] = trades.map((trade) => {
        const currentPrice = priceMap[trade.symbol];
        let baseUnrealizedPnlPct: number | null = null;
        let unrealizedPnlPct: number | null = null;
        const leverage = trade.leverage || 1.0;

        if (currentPrice !== null && trade.entry_price > 0) {
          // Calculate base P&L (without leverage)
          if (trade.action.includes('long')) {
            baseUnrealizedPnlPct = ((currentPrice - trade.entry_price) / trade.entry_price) * 100;
          } else {
            baseUnrealizedPnlPct = ((trade.entry_price - currentPrice) / trade.entry_price) * 100;
          }
          // Apply leverage to get actual P&L
          unrealizedPnlPct = baseUnrealizedPnlPct * leverage;
        }

        // Calculate duration in hours
        const entryTime = new Date(trade.created_at);
        const now = new Date();
        const durationHours = (now.getTime() - entryTime.getTime()) / (1000 * 60 * 60);

        return {
          ...trade,
          current_price: currentPrice,
          base_unrealized_pnl_pct: baseUnrealizedPnlPct,
          unrealized_pnl_pct: unrealizedPnlPct,
          duration_hours: durationHours,
        };
      });

      // Sort positions
      positionsWithPnL.sort((a, b) => {
        if (sortBy === 'pnl') {
          return (b.unrealized_pnl_pct || 0) - (a.unrealized_pnl_pct || 0);
        } else if (sortBy === 'symbol') {
          return a.symbol.localeCompare(b.symbol);
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });

      setPositions(positionsWithPnL);
    } catch (error) {
      console.error('Failed to fetch open positions:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedSymbol, sortBy]);

  useEffect(() => {
    if (open) {
      setLoading(true);
      fetchPositions();
    }
  }, [open, fetchPositions]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPositions();
  };

  // Calculate totals
  const totalPositions = positions.length;
  const longPositions = positions.filter((p) => p.action.includes('long')).length;
  const shortPositions = positions.filter((p) => p.action.includes('short')).length;

  const totalUnrealizedPnl = positions.reduce((sum, p) => {
    if (p.unrealized_pnl_pct !== null) {
      return sum + p.unrealized_pnl_pct;
    }
    return sum;
  }, 0);

  const avgUnrealizedPnl = totalPositions > 0 ? totalUnrealizedPnl / totalPositions : 0;

  const profitablePositions = positions.filter((p) => (p.unrealized_pnl_pct || 0) > 0).length;
  const losingPositions = positions.filter((p) => (p.unrealized_pnl_pct || 0) < 0).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-500" />
            Open Positions
            <Badge variant="outline" className="ml-2">
              {totalPositions} positions
            </Badge>
          </DialogTitle>
          <DialogDescription>
            All open paper trading positions with unrealized P&L
          </DialogDescription>
        </DialogHeader>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 py-3">
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Total Open</p>
            <p className="text-xl font-bold">{totalPositions}</p>
          </div>
          <div className="p-3 bg-green-500/10 rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Longs</p>
            <p className="text-xl font-bold text-green-500">{longPositions}</p>
          </div>
          <div className="p-3 bg-red-500/10 rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Shorts</p>
            <p className="text-xl font-bold text-red-500">{shortPositions}</p>
          </div>
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Avg Unrealized</p>
            <p className={`text-xl font-bold ${avgUnrealizedPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {avgUnrealizedPnl >= 0 ? '+' : ''}{avgUnrealizedPnl.toFixed(3)}%
            </p>
          </div>
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Profitable / Loss</p>
            <p className="text-xl font-bold">
              <span className="text-green-500">{profitablePositions}</span>
              {' / '}
              <span className="text-red-500">{losingPositions}</span>
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 py-2 border-b">
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Symbol" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Symbols</SelectItem>
              {SYMBOLS.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={(v) => setSortBy(v as 'time' | 'pnl' | 'symbol')}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="time">Newest First</SelectItem>
              <SelectItem value="pnl">Best P&L First</SelectItem>
              <SelectItem value="symbol">By Symbol</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>

          <span className="text-xs text-muted-foreground ml-auto">
            Last updated: {new Date().toLocaleTimeString()}
          </span>
        </div>

        {/* Positions Table */}
        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : positions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
              <Target className="h-12 w-12 mb-4" />
              <p>No open positions</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-center">Leverage</TableHead>
                  <TableHead className="text-right">Entry Price</TableHead>
                  <TableHead className="text-right">Current Price</TableHead>
                  <TableHead className="text-right">Unrealized P&L</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {positions.map((position) => (
                  <TableRow key={position.trade_id} className="cursor-pointer hover:bg-muted">
                    <TableCell>
                      <Badge variant="outline" className="font-mono">
                        {position.symbol}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {position.action.includes('long') ? (
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        )}
                        <span className={position.action.includes('long') ? 'text-green-500' : 'text-red-500'}>
                          {position.action.includes('long') ? 'LONG' : 'SHORT'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge
                        variant={position.leverage >= 3 ? 'destructive' : position.leverage >= 2 ? 'default' : 'secondary'}
                        className="font-mono text-xs"
                      >
                        {position.leverage.toFixed(1)}x
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      ${position.entry_price.toFixed(4)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {position.current_price !== null ? (
                        `$${position.current_price.toFixed(4)}`
                      ) : (
                        <span className="text-muted-foreground">--</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {position.unrealized_pnl_pct !== null ? (
                        <div className="flex flex-col items-end gap-0">
                          <div className="flex items-center gap-1">
                            {position.unrealized_pnl_pct >= 0 ? (
                              <ArrowUpRight className="h-3 w-3 text-green-500" />
                            ) : (
                              <ArrowDownRight className="h-3 w-3 text-red-500" />
                            )}
                            <span
                              className={`font-bold ${
                                position.unrealized_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'
                              }`}
                            >
                              {position.unrealized_pnl_pct >= 0 ? '+' : ''}
                              {position.unrealized_pnl_pct.toFixed(3)}%
                            </span>
                          </div>
                          {position.leverage > 1 && position.base_unrealized_pnl_pct !== null && (
                            <span className="text-xs text-muted-foreground">
                              (base: {position.base_unrealized_pnl_pct >= 0 ? '+' : ''}
                              {position.base_unrealized_pnl_pct.toFixed(3)}%)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">--</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-muted-foreground text-sm">
                        <Clock className="h-3 w-3" />
                        {position.duration_hours < 1
                          ? `${Math.round(position.duration_hours * 60)}m`
                          : position.duration_hours < 24
                            ? `${position.duration_hours.toFixed(1)}h`
                            : `${(position.duration_hours / 24).toFixed(1)}d`}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <div
                          className="h-2 rounded-full bg-primary"
                          style={{ width: `${Math.min(position.confidence * 100, 100)}%`, maxWidth: '60px' }}
                        />
                        <span className="text-xs text-muted-foreground">
                          {(position.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onTradeClick?.(position)}
                        className="h-6 w-6 p-0"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default OpenPositionsModal;
