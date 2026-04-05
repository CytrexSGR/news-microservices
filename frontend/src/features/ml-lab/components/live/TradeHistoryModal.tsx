/**
 * Trade History Modal
 *
 * Shows closed paper trading positions with filtering and pagination.
 * Displays realized P&L, trade duration, and gate predictions.
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
  History,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  XCircle,
  ExternalLink,
  BarChart3,
} from 'lucide-react';

import { shadowTradeApi } from '../../api/mlLabApi';
import type { ShadowTrade, ShadowTradeStats } from '../../types';
import { SYMBOLS } from '../../utils/constants';

interface TradeHistoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTradeClick?: (trade: ShadowTrade) => void;
}

const PAGE_SIZE = 20;

export function TradeHistoryModal({ open, onOpenChange, onTradeClick }: TradeHistoryModalProps) {
  const [trades, setTrades] = useState<ShadowTrade[]>([]);
  const [stats, setStats] = useState<ShadowTradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [totalTrades, setTotalTrades] = useState(0);

  const fetchTrades = useCallback(async () => {
    try {
      const params: { symbol?: string; status: 'closed'; limit: number; offset: number } = {
        status: 'closed',
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      };
      if (selectedSymbol !== 'all') {
        params.symbol = selectedSymbol;
      }

      const [tradesResponse, statsResponse] = await Promise.all([
        shadowTradeApi.list(params),
        shadowTradeApi.getStats({
          symbol: selectedSymbol !== 'all' ? selectedSymbol : undefined,
          days: 30,
        }),
      ]);

      setTrades(tradesResponse.trades || []);
      setTotalTrades(tradesResponse.total || 0);
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to fetch trade history:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedSymbol, page]);

  useEffect(() => {
    if (open) {
      setLoading(true);
      fetchTrades();
    }
  }, [open, fetchTrades]);

  // Reset page when symbol changes
  useEffect(() => {
    setPage(0);
  }, [selectedSymbol]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchTrades();
  };

  const totalPages = Math.ceil(totalTrades / PAGE_SIZE);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Trade History
            <Badge variant="outline" className="ml-2">
              {totalTrades.toLocaleString()} trades
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Closed paper trading positions with realized P&L (last 30 days)
          </DialogDescription>
        </DialogHeader>

        {/* Stats Summary */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 py-3 border-b">
            <div className="p-3 bg-muted rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Total Trades</p>
              <p className="text-xl font-bold">{stats.total_trades}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Win Rate</p>
              <p className={`text-xl font-bold ${stats.win_rate_pct >= 50 ? 'text-green-500' : 'text-red-500'}`}>
                {stats.win_rate_pct.toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Total P&L</p>
              <p className={`text-xl font-bold ${stats.total_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {stats.total_pnl_pct >= 0 ? '+' : ''}{stats.total_pnl_pct.toFixed(2)}%
              </p>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Avg P&L</p>
              <p className={`text-xl font-bold ${stats.avg_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {stats.avg_pnl_pct >= 0 ? '+' : ''}{stats.avg_pnl_pct.toFixed(3)}%
              </p>
            </div>
            <div className="p-3 bg-green-500/10 rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Best Trade</p>
              <p className="text-xl font-bold text-green-500">+{stats.max_win_pct.toFixed(2)}%</p>
            </div>
            <div className="p-3 bg-red-500/10 rounded-lg text-center">
              <p className="text-xs text-muted-foreground">Worst Trade</p>
              <p className="text-xl font-bold text-red-500">{stats.max_loss_pct.toFixed(2)}%</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center gap-3 py-2">
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

          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>

          {/* Pagination */}
          <div className="flex items-center gap-2 ml-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              Page {page + 1} of {Math.max(1, totalPages)}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Trades Table */}
        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : trades.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mb-4" />
              <p>No closed trades found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Exit</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((trade) => {
                  const isWin = (trade.pnl_pct || 0) > 0;
                  return (
                    <TableRow key={trade.trade_id} className="cursor-pointer hover:bg-muted">
                      <TableCell className="text-sm">
                        <div className="text-muted-foreground">
                          {new Date(trade.created_at).toLocaleDateString()}
                        </div>
                        <div className="text-xs text-muted-foreground/70">
                          {new Date(trade.created_at).toLocaleTimeString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {trade.symbol}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {trade.action.includes('long') ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <span className={trade.action.includes('long') ? 'text-green-500' : 'text-red-500'}>
                            {trade.action.includes('long') ? 'LONG' : 'SHORT'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        ${trade.entry_price.toFixed(4)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {trade.exit_price !== null ? (
                          `$${trade.exit_price.toFixed(4)}`
                        ) : (
                          <span className="text-muted-foreground">--</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {trade.pnl_pct !== null ? (
                          <span className={`font-bold ${isWin ? 'text-green-500' : 'text-red-500'}`}>
                            {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(3)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground">--</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {trade.duration_minutes !== null ? (
                          trade.duration_minutes < 60
                            ? `${trade.duration_minutes.toFixed(0)}m`
                            : trade.duration_minutes < 1440
                              ? `${(trade.duration_minutes / 60).toFixed(1)}h`
                              : `${(trade.duration_minutes / 1440).toFixed(1)}d`
                        ) : (
                          '--'
                        )}
                      </TableCell>
                      <TableCell>
                        {trade.pnl_pct !== null && (
                          <div className="flex items-center gap-1">
                            {isWin ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                            <span className={`text-xs ${isWin ? 'text-green-500' : 'text-red-500'}`}>
                              {isWin ? 'WIN' : 'LOSS'}
                            </span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onTradeClick?.(trade)}
                          className="h-6 w-6 p-0"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TradeHistoryModal;
