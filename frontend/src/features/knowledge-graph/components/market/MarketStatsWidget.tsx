/**
 * MarketStatsWidget Component
 *
 * Displays aggregate statistics for market nodes in the knowledge graph.
 * Includes total counts, asset type distribution, and most connected markets.
 *
 * @example
 * ```tsx
 * <MarketStatsWidget onMarketClick={(symbol) => console.log(symbol)} />
 * ```
 *
 * @module features/knowledge-graph/components/market/MarketStatsWidget
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { TrendingUp, BarChart3, Link2, Award } from 'lucide-react';
import { cn } from '@/lib/utils';

import { useMarketStats } from '../../api/useMarketStats';
import { ASSET_TYPE_COLORS, ASSET_TYPE_ICONS } from '../../types/market';
import type { AssetType } from '../../types/market';

// ===========================
// Component Props
// ===========================

export interface MarketStatsWidgetProps {
  /** Callback when a market is clicked */
  onMarketClick?: (symbol: string) => void;
  /** Number of top markets to show */
  topCount?: number;
  /** Compact mode for smaller displays */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function MarketStatsWidget({
  onMarketClick,
  topCount = 5,
  compact = false,
  className,
}: MarketStatsWidgetProps) {
  // ===== Data Fetching =====
  const { data, isLoading, error } = useMarketStats({ topCount });

  // ===== Loading State =====
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader className={compact ? 'pb-2' : ''}>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-5 w-5" />
            Market Statistics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
          <Skeleton className="h-24" />
        </CardContent>
      </Card>
    );
  }

  // ===== Error State =====
  if (error || !data) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="py-6 text-center text-muted-foreground">
          Failed to load market statistics
        </CardContent>
      </Card>
    );
  }

  // ===== Render =====
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className={compact ? 'pb-2' : ''}>
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="h-5 w-5" />
          Market Statistics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="Total Markets"
            value={data.total_market_nodes}
            compact={compact}
          />
          <StatCard
            icon={<Link2 className="h-4 w-4" />}
            label="Total Connections"
            value={data.total_connections}
            compact={compact}
          />
        </div>

        {/* Avg Connections */}
        <div className="p-3 rounded-lg bg-muted/50">
          <div className="text-xs text-muted-foreground">Avg Connections/Market</div>
          <div className="text-lg font-bold">
            {data.avg_connections_per_market.toFixed(1)}
          </div>
        </div>

        {/* Asset Type Distribution */}
        {!compact && (
          <div>
            <h4 className="text-sm font-medium mb-2">By Asset Type</h4>
            <div className="space-y-2">
              {Object.entries(data.by_asset_type).map(([type, count]) => {
                const assetType = type as AssetType;
                const icon = ASSET_TYPE_ICONS[assetType] ?? ASSET_TYPE_ICONS.DEFAULT;
                const color = ASSET_TYPE_COLORS[assetType] ?? ASSET_TYPE_COLORS.DEFAULT;
                const percentage = ((count / data.total_market_nodes) * 100).toFixed(1);

                return (
                  <div key={type} className="flex items-center gap-2">
                    <span className="text-lg w-6">{icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize">{type}</span>
                        <span className="text-muted-foreground">{count}</span>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden mt-1">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${percentage}%`,
                            backgroundColor: color,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Most Connected */}
        <div>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
            <Award className="h-4 w-4" />
            Most Connected
          </h4>
          <div className="space-y-1">
            {data.most_connected.slice(0, compact ? 3 : 5).map((market, index) => (
              <button
                key={market.symbol}
                type="button"
                onClick={() => onMarketClick?.(market.symbol)}
                className="w-full flex items-center justify-between p-2 rounded hover:bg-accent transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold',
                      index === 0 && 'bg-yellow-100 text-yellow-800',
                      index === 1 && 'bg-gray-100 text-gray-800',
                      index === 2 && 'bg-orange-100 text-orange-800',
                      index > 2 && 'bg-muted text-muted-foreground'
                    )}
                  >
                    {index + 1}
                  </span>
                  <span className="font-medium text-sm">{market.symbol}</span>
                </div>
                <Badge variant="secondary" className="text-xs">
                  {market.connections} links
                </Badge>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ===========================
// Stat Card Component
// ===========================

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  compact?: boolean;
}

function StatCard({ icon, label, value, compact }: StatCardProps) {
  return (
    <div className={cn('p-3 rounded-lg bg-muted/50', compact && 'p-2')}>
      <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className={cn('font-bold', compact ? 'text-lg' : 'text-xl')}>
        {value.toLocaleString()}
      </div>
    </div>
  );
}

export default MarketStatsWidget;
