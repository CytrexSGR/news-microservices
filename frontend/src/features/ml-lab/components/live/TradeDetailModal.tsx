/**
 * Trade Detail Modal
 *
 * Shows comprehensive details for a single paper trade including:
 * - Entry/Exit prices and P&L
 * - All 6 gate predictions with confidence scores
 * - Trade reasoning and duration
 * - Current price for open positions
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Brain,
  Zap,
  Shield,
  Activity,
  BarChart3,
  RefreshCw,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Hash,
} from 'lucide-react';

import type { ShadowTrade } from '../../types';

interface TradeDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trade: ShadowTrade | null;
}

// Fetch current price for unrealized P&L calculation
async function fetchCurrentPrice(symbol: string): Promise<number | null> {
  try {
    const response = await fetch(
      `/api/prediction/v1/ml/live-trading/indicators?symbol=${symbol}&timeframe=5min`
    );
    if (response.ok) {
      const data = await response.json();
      return data.price?.current || null;
    }
    return null;
  } catch {
    return null;
  }
}

// Gate configuration for display
const GATE_CONFIG = {
  direction: {
    icon: TrendingUp,
    label: 'Direction',
    description: 'Predicts market direction (bullish/bearish)',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  entry: {
    icon: Target,
    label: 'Entry',
    description: 'Determines optimal entry timing',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
  exit: {
    icon: Zap,
    label: 'Exit',
    description: 'Predicts exit timing and targets',
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
  },
  regime: {
    icon: Activity,
    label: 'Regime',
    description: 'Market regime detection (trending/ranging)',
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  risk: {
    icon: Shield,
    label: 'Risk',
    description: 'Risk assessment and position sizing',
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
  },
  volatility: {
    icon: BarChart3,
    label: 'Volatility',
    description: 'Volatility regime classification',
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
  },
};

export function TradeDetailModal({ open, onOpenChange, trade }: TradeDetailModalProps) {
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [loadingPrice, setLoadingPrice] = useState(false);

  // Fetch current price for open positions
  useEffect(() => {
    if (open && trade && trade.status === 'open') {
      setLoadingPrice(true);
      fetchCurrentPrice(trade.symbol)
        .then(setCurrentPrice)
        .finally(() => setLoadingPrice(false));
    }
  }, [open, trade]);

  const handleRefreshPrice = async () => {
    if (!trade) return;
    setLoadingPrice(true);
    const price = await fetchCurrentPrice(trade.symbol);
    setCurrentPrice(price);
    setLoadingPrice(false);
  };

  if (!trade) return null;

  const isOpen = trade.status === 'open';
  const isLong = trade.action.includes('long');

  // Calculate P&L
  let pnlPct: number | null = null;
  let pnlDisplay = '--';

  if (trade.pnl_pct !== null) {
    // Closed trade - use stored P&L
    pnlPct = trade.pnl_pct;
    pnlDisplay = `${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(3)}%`;
  } else if (isOpen && currentPrice !== null && trade.entry_price > 0) {
    // Open trade - calculate unrealized P&L
    if (isLong) {
      pnlPct = ((currentPrice - trade.entry_price) / trade.entry_price) * 100;
    } else {
      pnlPct = ((trade.entry_price - currentPrice) / trade.entry_price) * 100;
    }
    pnlDisplay = `${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(3)}%`;
  }

  const isWin = pnlPct !== null && pnlPct > 0;

  // Duration calculation
  const entryTime = new Date(trade.created_at);
  const exitTime = trade.closed_at ? new Date(trade.closed_at) : new Date();
  const durationMs = exitTime.getTime() - entryTime.getTime();
  const durationMinutes = durationMs / (1000 * 60);

  let durationDisplay = '--';
  if (durationMinutes < 60) {
    durationDisplay = `${Math.round(durationMinutes)}m`;
  } else if (durationMinutes < 1440) {
    durationDisplay = `${(durationMinutes / 60).toFixed(1)}h`;
  } else {
    durationDisplay = `${(durationMinutes / 1440).toFixed(1)}d`;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {isLong ? (
              <TrendingUp className="h-6 w-6 text-green-500" />
            ) : (
              <TrendingDown className="h-6 w-6 text-red-500" />
            )}
            <span className={isLong ? 'text-green-500' : 'text-red-500'}>
              {isLong ? 'LONG' : 'SHORT'}
            </span>
            <Badge variant="outline" className="font-mono text-lg">
              {trade.symbol}
            </Badge>
            <Badge
              variant={isOpen ? 'default' : 'secondary'}
              className={isOpen ? 'bg-blue-500' : ''}
            >
              {isOpen ? 'OPEN' : 'CLOSED'}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Trade ID: {trade.trade_id.slice(0, 8)}... | Timeframe: {trade.timeframe}
          </DialogDescription>
        </DialogHeader>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 py-4 border-b">
          {/* Entry Price */}
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Entry Price</p>
            <p className="text-lg font-mono font-bold">${trade.entry_price.toFixed(4)}</p>
          </div>

          {/* Exit/Current Price */}
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
              {isOpen ? 'Current Price' : 'Exit Price'}
              {isOpen && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0"
                  onClick={handleRefreshPrice}
                  disabled={loadingPrice}
                >
                  {loadingPrice ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                </Button>
              )}
            </p>
            <p className="text-lg font-mono font-bold">
              {isOpen ? (
                currentPrice !== null ? (
                  `$${currentPrice.toFixed(4)}`
                ) : loadingPrice ? (
                  <Loader2 className="h-4 w-4 animate-spin mx-auto" />
                ) : (
                  '--'
                )
              ) : trade.exit_price !== null ? (
                `$${trade.exit_price.toFixed(4)}`
              ) : (
                '--'
              )}
            </p>
          </div>

          {/* P&L */}
          <div
            className={`p-3 rounded-lg text-center ${
              pnlPct !== null
                ? isWin
                  ? 'bg-green-500/10'
                  : 'bg-red-500/10'
                : 'bg-muted'
            }`}
          >
            <p className="text-xs text-muted-foreground">
              {isOpen ? 'Unrealized P&L' : 'Realized P&L'}
            </p>
            <div className="flex items-center justify-center gap-1">
              {pnlPct !== null &&
                (isWin ? (
                  <ArrowUpRight className="h-4 w-4 text-green-500" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-red-500" />
                ))}
              <p className={`text-lg font-bold ${isWin ? 'text-green-500' : 'text-red-500'}`}>
                {pnlDisplay}
              </p>
            </div>
          </div>

          {/* Duration */}
          <div className="p-3 bg-muted rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Duration</p>
            <div className="flex items-center justify-center gap-1">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <p className="text-lg font-bold">{durationDisplay}</p>
            </div>
          </div>
        </div>

        {/* Confidence & Result */}
        <div className="grid grid-cols-2 gap-3 py-4 border-b">
          <div className="p-3 bg-muted rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Overall Confidence</p>
            <div className="flex items-center gap-3">
              <Progress value={trade.confidence * 100} className="flex-1" />
              <span className="text-sm font-bold">{(trade.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          {!isOpen && pnlPct !== null && (
            <div className="p-3 bg-muted rounded-lg flex items-center justify-center gap-2">
              {isWin ? (
                <>
                  <CheckCircle2 className="h-8 w-8 text-green-500" />
                  <div>
                    <p className="text-lg font-bold text-green-500">WIN</p>
                    <p className="text-xs text-muted-foreground">Trade was profitable</p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="h-8 w-8 text-red-500" />
                  <div>
                    <p className="text-lg font-bold text-red-500">LOSS</p>
                    <p className="text-xs text-muted-foreground">Trade was unprofitable</p>
                  </div>
                </>
              )}
            </div>
          )}
          {isOpen && (
            <div className="p-3 bg-blue-500/10 rounded-lg flex items-center justify-center gap-2">
              <Target className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-lg font-bold text-blue-500">ACTIVE</p>
                <p className="text-xs text-muted-foreground">Position still open</p>
              </div>
            </div>
          )}
        </div>

        {/* Gate Predictions */}
        <div className="py-4 border-b">
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Brain className="h-4 w-4 text-primary" />
            Gate Predictions
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(GATE_CONFIG).map(([key, config]) => {
              const gateKey = key as keyof typeof trade.gate_predictions;
              const prediction = trade.gate_predictions?.[gateKey];
              const Icon = config.icon;

              return (
                <div
                  key={key}
                  className={`p-3 rounded-lg ${config.bgColor} border border-border/50`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`h-4 w-4 ${config.color}`} />
                    <span className="text-xs font-semibold">{config.label}</span>
                  </div>
                  {prediction ? (
                    <>
                      <p className="text-sm font-mono font-bold">
                        {typeof prediction.prediction === 'number'
                          ? prediction.prediction.toFixed(4)
                          : prediction.prediction}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <Progress
                          value={prediction.confidence * 100}
                          className="flex-1 h-1"
                        />
                        <span className="text-xs text-muted-foreground">
                          {(prediction.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">N/A</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Trade Reasoning */}
        {trade.reasoning && (
          <div className="py-4 border-b">
            <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              Trade Reasoning
            </h4>
            <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
              {trade.reasoning}
            </p>
          </div>
        )}

        {/* Timestamps */}
        <div className="py-4">
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Calendar className="h-4 w-4 text-primary" />
            Timeline
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Entry Time:</span>
              <span className="font-mono">
                {entryTime.toLocaleDateString()} {entryTime.toLocaleTimeString()}
              </span>
            </div>
            {trade.closed_at && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Exit Time:</span>
                <span className="font-mono">
                  {new Date(trade.closed_at).toLocaleDateString()}{' '}
                  {new Date(trade.closed_at).toLocaleTimeString()}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Trade ID:</span>
              <span className="font-mono text-xs">{trade.trade_id}</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TradeDetailModal;
