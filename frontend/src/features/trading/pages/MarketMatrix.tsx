import { useQuery } from '@tanstack/react-query';
import { predictionAPI, type MatrixResponse, type StrategyAnalysis, type SignalType } from '@/api/predictionService';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, AlertCircle, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

/**
 * Market Matrix Dashboard
 *
 * Real-time transparency into multi-strategy trading decisions.
 * Shows how each strategy (OI_Trend, MeanReversion, GoldenPocket, VolatilityBreakout)
 * evaluates each asset (BTC, ETH, etc.).
 *
 * Features:
 * - Grid layout: Symbols (rows) × Strategies (columns)
 * - Color-coded signals: GREEN (LONG), RED (SHORT), GRAY (NEUTRAL)
 * - Auto-refresh every 30 seconds
 * - Detailed tooltips with strategy reasoning
 */
export default function MarketMatrix() {
  // Query market matrix with 30s polling
  const {
    data: matrix,
    isLoading,
    isError,
    error,
    dataUpdatedAt,
  } = useQuery<MatrixResponse>({
    queryKey: ['market-matrix'],
    queryFn: () => predictionAPI.getMarketMatrix(),
    refetchInterval: 30000, // Poll every 30 seconds
    refetchOnWindowFocus: true,
  });

  // Helper: Get signal badge variant (color)
  const getSignalVariant = (signal: SignalType): 'default' | 'destructive' | 'secondary' => {
    switch (signal) {
      case 'LONG':
        return 'default'; // Green
      case 'SHORT':
        return 'destructive'; // Red
      case 'NEUTRAL':
        return 'secondary'; // Gray
    }
  };

  // Helper: Get signal icon
  const getSignalIcon = (signal: SignalType) => {
    switch (signal) {
      case 'LONG':
        return <TrendingUp className="h-3 w-3" />;
      case 'SHORT':
        return <TrendingDown className="h-3 w-3" />;
      case 'NEUTRAL':
        return <Minus className="h-3 w-3" />;
    }
  };

  // Helper: Format confidence percentage
  const formatConfidence = (confidence: number): string => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  // Helper: Format price
  const formatPrice = (price?: number): string => {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  // Helper: Format market data for display
  const formatMarketData = (data: Record<string, any>): string => {
    const entries = Object.entries(data)
      .filter(([_, value]) => value !== null && value !== undefined)
      .map(([key, value]) => {
        if (typeof value === 'number') {
          return `${key}: ${value.toFixed(2)}`;
        }
        return `${key}: ${value}`;
      });
    return entries.join(', ');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span className="text-muted-foreground">Loading Market Matrix...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="container mx-auto py-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Failed to Load Market Matrix
            </CardTitle>
            <CardDescription>
              {error instanceof Error ? error.message : 'An unknown error occurred'}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Empty state
  if (!matrix || matrix.symbols.length === 0) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5 text-muted-foreground" />
              No Analysis Data Available
            </CardTitle>
            <CardDescription>
              The trading scheduler is running but hasn't produced any analyses yet.
              Wait for the next scan cycle (runs every 60 minutes) or check the autopilot status.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              💡 Tip: The Market Matrix shows real-time strategy analyses including NEUTRAL signals.
              Once the scheduler runs, you'll see how each strategy evaluates each asset.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Market Matrix</h1>
          <p className="text-muted-foreground">
            Real-time multi-strategy analysis across all assets
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {matrix.last_updated && (
            <p className="text-sm text-muted-foreground">
              Last updated: {formatDistanceToNow(new Date(matrix.last_updated), { addSuffix: true })}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Auto-refreshes every 30 seconds
          </p>
        </div>
      </div>

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Signal Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Badge variant="default" className="gap-1">
                <TrendingUp className="h-3 w-3" />
                LONG
              </Badge>
              <span className="text-muted-foreground">Buy signal (bullish)</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="destructive" className="gap-1">
                <TrendingDown className="h-3 w-3" />
                SHORT
              </Badge>
              <span className="text-muted-foreground">Sell signal (bearish)</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <Minus className="h-3 w-3" />
                NEUTRAL
              </Badge>
              <span className="text-muted-foreground">No trade (waiting)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Matrix Grid */}
      <Card>
        <CardHeader>
          <CardTitle>
            Strategy Analysis Matrix
          </CardTitle>
          <CardDescription>
            {matrix.symbols.length} symbols × {matrix.strategies.length} strategies = {matrix.symbols.length * matrix.strategies.length} analyses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-4 font-medium sticky left-0 bg-card z-10">
                    Symbol
                  </th>
                  {matrix.strategies.map((strategy) => (
                    <th key={strategy} className="text-center p-4 font-medium min-w-[180px]">
                      {strategy}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.symbols.map((symbol) => {
                  const asset = matrix.matrix[symbol];
                  if (!asset) return null;

                  return (
                    <tr key={symbol} className="border-b hover:bg-muted/50">
                      {/* Symbol column (sticky) */}
                      <td className="p-4 font-medium sticky left-0 bg-card z-10">
                        <div>
                          <div className="font-semibold">{symbol.split('/')[0]}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatPrice(asset.current_price)}
                          </div>
                        </div>
                      </td>

                      {/* Strategy columns */}
                      {matrix.strategies.map((strategy) => {
                        const analysis: StrategyAnalysis | undefined = asset.strategies[strategy];

                        if (!analysis) {
                          // No analysis for this symbol+strategy
                          return (
                            <td key={strategy} className="p-4 text-center">
                              <Badge variant="outline" className="text-xs">
                                No Data
                              </Badge>
                            </td>
                          );
                        }

                        return (
                          <td key={strategy} className="p-4">
                            <div className="flex flex-col gap-2">
                              {/* Signal Badge */}
                              <Badge
                                variant={getSignalVariant(analysis.signal)}
                                className="gap-1 justify-center"
                              >
                                {getSignalIcon(analysis.signal)}
                                {analysis.signal}
                                {analysis.confidence > 0 && (
                                  <span className="ml-1 text-xs opacity-75">
                                    {formatConfidence(analysis.confidence)}
                                  </span>
                                )}
                              </Badge>

                              {/* Reason (truncated) */}
                              <div className="text-xs text-muted-foreground line-clamp-2">
                                {analysis.reason}
                              </div>

                              {/* Entry Price (for LONG/SHORT) */}
                              {(analysis.signal === 'LONG' || analysis.signal === 'SHORT') && (
                                <div className="text-xs space-y-0.5">
                                  {analysis.entry_price && (
                                    <div>Entry: {formatPrice(analysis.entry_price)}</div>
                                  )}
                                  {analysis.stop_loss && (
                                    <div className="text-destructive">SL: {formatPrice(analysis.stop_loss)}</div>
                                  )}
                                  {analysis.take_profit && (
                                    <div className="text-green-600">TP: {formatPrice(analysis.take_profit)}</div>
                                  )}
                                </div>
                              )}

                              {/* Market Data */}
                              {analysis.market_data && Object.keys(analysis.market_data).length > 0 && (
                                <div className="text-xs text-muted-foreground truncate" title={formatMarketData(analysis.market_data)}>
                                  📊 {formatMarketData(analysis.market_data)}
                                </div>
                              )}

                              {/* Timestamp */}
                              {analysis.timestamp && (
                                <div className="text-xs text-muted-foreground">
                                  {formatDistanceToNow(new Date(analysis.timestamp), { addSuffix: true })}
                                </div>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Stats Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {matrix.symbols.length * matrix.strategies.length}
            </div>
            <p className="text-xs text-muted-foreground">
              {matrix.symbols.length} symbols × {matrix.strategies.length} strategies
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Signals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {Object.values(matrix.matrix).reduce((count, asset) => {
                return count + Object.values(asset.strategies).filter(a => a.signal === 'LONG' || a.signal === 'SHORT').length;
              }, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              LONG + SHORT signals
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Neutral Signals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-muted-foreground">
              {Object.values(matrix.matrix).reduce((count, asset) => {
                return count + Object.values(asset.strategies).filter(a => a.signal === 'NEUTRAL').length;
              }, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              No trade conditions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Data Freshness</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {matrix.last_updated
                ? formatDistanceToNow(new Date(matrix.last_updated))
                : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Since last update
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
