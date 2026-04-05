/**
 * MarketNodePanel Component
 *
 * Displays a list of market nodes with filtering and selection.
 * Shows asset type badges, connection counts, and supports search.
 *
 * @example
 * ```tsx
 * <MarketNodePanel
 *   onSelect={(symbol) => console.log(symbol)}
 *   selectedSymbol="AAPL"
 * />
 * ```
 *
 * @module features/knowledge-graph/components/market/MarketNodePanel
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/Skeleton';
import { Search, TrendingUp, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

import { useMarketNodes } from '../../api/useMarketNodes';
import type { MarketNode, AssetType } from '../../types/market';
import { ASSET_TYPE_COLORS, ASSET_TYPE_ICONS } from '../../types/market';

// ===========================
// Component Props
// ===========================

export interface MarketNodePanelProps {
  /** Callback when a market node is selected */
  onSelect?: (symbol: string) => void;
  /** Currently selected symbol */
  selectedSymbol?: string | null;
  /** Maximum number of items to display */
  limit?: number;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Asset Type Options
// ===========================

const ASSET_TYPE_OPTIONS: { value: AssetType | 'all'; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
  { value: 'commodity', label: 'Commodities' },
  { value: 'index', label: 'Indices' },
];

// ===========================
// Main Component
// ===========================

export function MarketNodePanel({
  onSelect,
  selectedSymbol,
  limit = 50,
  className,
}: MarketNodePanelProps) {
  // ===== State =====
  const [search, setSearch] = useState('');
  const [assetTypeFilter, setAssetTypeFilter] = useState<AssetType | 'all'>('all');

  // ===== Data Fetching =====
  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useMarketNodes({
    assetType: assetTypeFilter === 'all' ? undefined : assetTypeFilter,
    search: search.length >= 2 ? search : undefined,
    limit,
    sortBy: 'connection_count',
    sortOrder: 'desc',
  });

  // ===== Derived State =====
  const markets = data?.markets ?? [];

  // ===== Handlers =====
  const handleSelect = (symbol: string) => {
    onSelect?.(symbol);
  };

  // ===== Loading State =====
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Market Nodes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  // ===== Error State =====
  if (error) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <TrendingUp className="h-5 w-5" />
            Market Nodes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">
            Failed to load market nodes: {error.message}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="mt-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  // ===== Render =====
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Market Nodes
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          </Button>
        </CardTitle>

        {/* Filters */}
        <div className="flex gap-2 mt-3">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search symbols..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select
            value={assetTypeFilter}
            onValueChange={(v) => setAssetTypeFilter(v as AssetType | 'all')}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Asset Type" />
            </SelectTrigger>
            <SelectContent>
              {ASSET_TYPE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Results Count */}
        <div className="text-xs text-muted-foreground mb-3">
          {data?.total ?? 0} market nodes
        </div>

        {/* Market List */}
        <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
          {markets.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No market nodes found
            </div>
          ) : (
            markets.map((market) => (
              <MarketNodeItem
                key={market.symbol}
                market={market}
                isSelected={market.symbol === selectedSymbol}
                onClick={() => handleSelect(market.symbol)}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ===========================
// Market Node Item
// ===========================

interface MarketNodeItemProps {
  market: MarketNode;
  isSelected: boolean;
  onClick: () => void;
}

function MarketNodeItem({ market, isSelected, onClick }: MarketNodeItemProps) {
  const icon = ASSET_TYPE_ICONS[market.asset_type] ?? ASSET_TYPE_ICONS.DEFAULT;
  const color = ASSET_TYPE_COLORS[market.asset_type] ?? ASSET_TYPE_COLORS.DEFAULT;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full p-3 rounded-lg border text-left transition-all',
        'hover:bg-accent hover:border-accent-foreground/20',
        isSelected && 'ring-2 ring-primary bg-primary/5 border-primary'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl" title={market.asset_type}>
            {icon}
          </span>
          <div>
            <div className="font-semibold text-sm">{market.symbol}</div>
            <div className="text-xs text-muted-foreground truncate max-w-[150px]">
              {market.name}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Badge
            variant="secondary"
            className="text-xs"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {market.connection_count} links
          </Badge>
          <span className="text-xs text-muted-foreground">
            {market.exchange}
          </span>
        </div>
      </div>
    </button>
  );
}

export default MarketNodePanel;
