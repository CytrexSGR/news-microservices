/**
 * Shadow Trades Panel
 *
 * Paper trading panel for tracking simulated trades based on ML predictions.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  DollarSign,
  Target,
  Clock,
  Loader2,
  BarChart3,
  CheckCircle2,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { shadowTradeApi } from '../../api/mlLabApi';
import { type ShadowTrade, type ShadowTradeStats } from '../../types';
import { SYMBOLS, ACTION_LABELS } from '../../utils/constants';

export function ShadowTradesPanel() {
  const [trades, setTrades] = useState<ShadowTrade[]>([]);
  const [stats, setStats] = useState<ShadowTradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'open' | 'closed'>('all');
  const [closingTradeId, setClosingTradeId] = useState<string | null>(null);
  const [exitPrice, setExitPrice] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const params: { symbol?: string; status?: 'open' | 'closed'; limit?: number } = { limit: 50 };
      if (selectedSymbol !== 'all') params.symbol = selectedSymbol;
      if (selectedStatus !== 'all') params.status = selectedStatus;

      const [tradesData, statsData] = await Promise.all([
        shadowTradeApi.list(params).catch(() => ({ trades: [] })),
        shadowTradeApi.getStats({
          symbol: selectedSymbol !== 'all' ? selectedSymbol : undefined,
          days: 7,
        }).catch(() => null),
      ]);
      setTrades(tradesData?.trades || []);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch shadow trades:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, selectedStatus]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleCloseTrade = async (tradeId: string) => {
    if (!exitPrice || isNaN(parseFloat(exitPrice))) {
      toast.error('Please enter a valid exit price');
      return;
    }

    try {
      await shadowTradeApi.close(tradeId, {
        exit_price: parseFloat(exitPrice),
        reason: 'manual',
      });
      toast.success('Trade closed');
      setClosingTradeId(null);
      setExitPrice('');
      fetchData();
    } catch (error) {
      toast.error('Failed to close trade');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                <div>
                  <p className="text-xl font-bold">{stats.total_trades}</p>
                  <p className="text-xs text-muted-foreground">Total Trades</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-green-500" />
                <div>
                  <p className="text-xl font-bold">{stats.win_rate_pct.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">Win Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <DollarSign
                  className={`h-4 w-4 ${stats.total_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}
                />
                <div>
                  <p
                    className={`text-xl font-bold ${stats.total_pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}
                  >
                    {stats.total_pnl_pct >= 0 ? '+' : ''}
                    {stats.total_pnl_pct.toFixed(2)}%
                  </p>
                  <p className="text-xs text-muted-foreground">Total P&L</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <ArrowUpRight className="h-4 w-4 text-green-500" />
                <div>
                  <p className="text-xl font-bold text-green-500">+{stats.max_win_pct.toFixed(2)}%</p>
                  <p className="text-xs text-muted-foreground">Best Trade</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <ArrowDownRight className="h-4 w-4 text-red-500" />
                <div>
                  <p className="text-xl font-bold text-red-500">{stats.max_loss_pct.toFixed(2)}%</p>
                  <p className="text-xs text-muted-foreground">Worst Trade</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trades List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Shadow Trades
              </CardTitle>
              <CardDescription>Paper trades based on ML predictions (7 days)</CardDescription>
            </div>
            <div className="flex items-center gap-2">
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

              <Select
                value={selectedStatus}
                onValueChange={(v) => setSelectedStatus(v as 'all' | 'open' | 'closed')}
              >
                <SelectTrigger className="w-28">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="icon" onClick={fetchData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">No shadow trades</p>
              <p className="text-muted-foreground">
                Run live inference and trades will appear here
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {trades.map((trade) => (
                <div
                  key={trade.trade_id}
                  className="flex items-center justify-between p-4 bg-muted rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`p-2 rounded-lg ${
                        trade.action.includes('long')
                          ? 'bg-green-500/10 text-green-500'
                          : 'bg-red-500/10 text-red-500'
                      }`}
                    >
                      {trade.action.includes('long') ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : (
                        <TrendingDown className="h-4 w-4" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{trade.symbol}</span>
                        <Badge
                          variant="outline"
                          className={
                            trade.status === 'open'
                              ? 'border-blue-500 text-blue-500'
                              : 'border-gray-500 text-gray-500'
                          }
                        >
                          {trade.status}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {ACTION_LABELS[trade.action] || trade.action}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>Entry: ${trade.entry_price.toFixed(4)}</span>
                        {trade.exit_price && <span>Exit: ${trade.exit_price.toFixed(4)}</span>}
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(trade.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {trade.status === 'closed' && trade.pnl_pct !== null ? (
                      <div className="text-right">
                        <p
                          className={`text-lg font-bold ${trade.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}
                        >
                          {trade.pnl_pct >= 0 ? '+' : ''}
                          {trade.pnl_pct.toFixed(2)}%
                        </p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          {trade.pnl_pct >= 0 ? (
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-500" />
                          )}
                          {trade.duration_minutes?.toFixed(0)}min
                        </p>
                      </div>
                    ) : trade.status === 'open' ? (
                      closingTradeId === trade.trade_id ? (
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            placeholder="Exit price"
                            value={exitPrice}
                            onChange={(e) => setExitPrice(e.target.value)}
                            className="w-28"
                            step="0.0001"
                          />
                          <Button size="sm" onClick={() => handleCloseTrade(trade.trade_id)}>
                            Close
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setClosingTradeId(null);
                              setExitPrice('');
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setClosingTradeId(trade.trade_id)}
                        >
                          Close Trade
                        </Button>
                      )
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ShadowTradesPanel;
