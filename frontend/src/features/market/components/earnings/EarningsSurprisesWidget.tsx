/**
 * EarningsSurprisesWidget Component
 * Shows recent earnings surprises across all symbols
 */

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { TrendingUp, TrendingDown, Sparkles, ArrowRight } from 'lucide-react';
import { useRecentSurprises, getTopSurprises } from '../../api/useEarningsSurprises';
import type { EarningsSurprise } from '../../types/earnings.types';
import { getSurpriseColor, getSurpriseType } from '../../types/earnings.types';

interface EarningsSurprisesWidgetProps {
  limit?: number;
  onSymbolClick?: (symbol: string) => void;
  className?: string;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function EarningsSurprisesWidget({
  limit = 20,
  onSymbolClick,
  className,
}: EarningsSurprisesWidgetProps) {
  const { data: surprises, isLoading, error } = useRecentSurprises(limit);

  const { topBeats, topMisses } = useMemo(() => {
    if (!surprises) return { topBeats: [], topMisses: [] };
    return getTopSurprises(surprises, 5);
  }, [surprises]);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load earnings surprises
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Recent Earnings Surprises
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {/* Top Beats */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span className="font-semibold text-sm">Top Beats</span>
              </div>
              <div className="space-y-2">
                {topBeats.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No recent beats</div>
                ) : (
                  topBeats.map((surprise) => (
                    <SurpriseItem
                      key={`${surprise.symbol}-${surprise.date}`}
                      surprise={surprise}
                      onClick={() => onSymbolClick?.(surprise.symbol)}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Top Misses */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="h-4 w-4 text-red-600" />
                <span className="font-semibold text-sm">Biggest Misses</span>
              </div>
              <div className="space-y-2">
                {topMisses.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No recent misses</div>
                ) : (
                  topMisses.map((surprise) => (
                    <SurpriseItem
                      key={`${surprise.symbol}-${surprise.date}`}
                      surprise={surprise}
                      onClick={() => onSymbolClick?.(surprise.symbol)}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface SurpriseItemProps {
  surprise: EarningsSurprise;
  onClick?: () => void;
}

function SurpriseItem({ surprise, onClick }: SurpriseItemProps) {
  const surpriseType = getSurpriseType(surprise.eps_actual, surprise.eps_estimated);
  const isBeat = surpriseType === 'beat';

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg border hover:bg-muted/50 transition-colors group"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-primary group-hover:underline">
              {surprise.symbol}
            </span>
            <span className="text-xs text-muted-foreground">
              {surprise.fiscal_quarter}
            </span>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {formatDate(surprise.date)}
          </div>
        </div>

        <div className="text-right">
          <div className="flex items-center gap-1">
            <span className="text-xs text-muted-foreground">EPS:</span>
            <span className="text-xs font-mono">${surprise.eps_actual.toFixed(2)}</span>
            <span className="text-xs text-muted-foreground">vs</span>
            <span className="text-xs font-mono">${surprise.eps_estimated.toFixed(2)}</span>
          </div>
          <Badge
            variant={isBeat ? 'default' : 'destructive'}
            className="mt-1 text-xs"
          >
            {isBeat ? '+' : ''}
            {surprise.surprise_percent.toFixed(1)}%
          </Badge>
        </div>
      </div>

      {/* Revenue surprise indicator */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Revenue Surprise:</span>
        <span
          className={`font-mono ${
            surprise.revenue_surprise_percent > 0
              ? 'text-green-600'
              : surprise.revenue_surprise_percent < 0
                ? 'text-red-600'
                : ''
          }`}
        >
          {surprise.revenue_surprise_percent >= 0 ? '+' : ''}
          {surprise.revenue_surprise_percent.toFixed(1)}%
        </span>
      </div>
    </button>
  );
}

export default EarningsSurprisesWidget;
