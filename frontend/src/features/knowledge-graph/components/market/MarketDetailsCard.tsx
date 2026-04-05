/**
 * MarketDetailsCard Component
 *
 * Displays detailed information for a single market node including
 * price data, connected entities, and related articles.
 *
 * @example
 * ```tsx
 * <MarketDetailsCard
 *   symbol="AAPL"
 *   onEntityClick={(name) => console.log(name)}
 * />
 * ```
 *
 * @module features/knowledge-graph/components/market/MarketDetailsCard
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Separator } from '@/components/ui/separator';
import {
  TrendingUp,
  TrendingDown,
  ExternalLink,
  Users,
  Newspaper,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

import { useMarketDetails } from '../../api/useMarketDetails';
import type { MarketConnectedEntity, MarketRelatedArticle } from '../../types/market';
import { ASSET_TYPE_ICONS, ASSET_TYPE_COLORS } from '../../types/market';

// ===========================
// Component Props
// ===========================

export interface MarketDetailsCardProps {
  /** Trading symbol to display */
  symbol: string | null;
  /** Callback when entity is clicked */
  onEntityClick?: (entityName: string) => void;
  /** Callback when article is clicked */
  onArticleClick?: (articleId: string) => void;
  /** Callback to view in graph */
  onViewInGraph?: (symbol: string) => void;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function MarketDetailsCard({
  symbol,
  onEntityClick,
  onArticleClick,
  onViewInGraph,
  className,
}: MarketDetailsCardProps) {
  // ===== Data Fetching =====
  const { data, isLoading, error, refetch, isFetching } = useMarketDetails(symbol);

  // ===== Empty State =====
  if (!symbol) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="py-8 text-center text-muted-foreground">
          Select a market node to view details
        </CardContent>
      </Card>
    );
  }

  // ===== Loading State =====
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  // ===== Error State =====
  if (error || !data) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="py-8">
          <p className="text-sm text-red-600 text-center">
            Failed to load market details
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="mt-2 mx-auto block"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  // ===== Render =====
  const icon = ASSET_TYPE_ICONS[data.asset_type as keyof typeof ASSET_TYPE_ICONS] ?? ASSET_TYPE_ICONS.DEFAULT;
  const color = ASSET_TYPE_COLORS[data.asset_type as keyof typeof ASSET_TYPE_COLORS] ?? ASSET_TYPE_COLORS.DEFAULT;
  const priceChange = data.price_data.change_percent;
  const isPositive = priceChange >= 0;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{icon}</span>
            <div>
              <CardTitle className="text-xl">{data.symbol}</CardTitle>
              <p className="text-sm text-muted-foreground">{data.name}</p>
              <Badge
                variant="outline"
                className="mt-1 text-xs"
                style={{ borderColor: color, color }}
              >
                {data.asset_type.toUpperCase()} - {data.exchange}
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Price Data */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">
                ${data.price_data.current.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {isPositive ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span
                  className={cn(
                    'text-sm font-medium',
                    isPositive ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  {isPositive ? '+' : ''}
                  {data.price_data.change_24h.toFixed(2)} (
                  {isPositive ? '+' : ''}
                  {priceChange.toFixed(2)}%)
                </span>
              </div>
            </div>
            {onViewInGraph && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewInGraph(data.symbol)}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View in Graph
              </Button>
            )}
          </div>
        </div>

        <Separator />

        {/* Connected Entities */}
        <div>
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Users className="h-4 w-4" />
            Connected Entities ({data.connected_entities.length})
          </h4>
          <div className="space-y-2">
            {data.connected_entities.length === 0 ? (
              <p className="text-sm text-muted-foreground">No connected entities</p>
            ) : (
              data.connected_entities.map((entity) => (
                <ConnectedEntityItem
                  key={entity.name}
                  entity={entity}
                  onClick={() => onEntityClick?.(entity.name)}
                />
              ))
            )}
          </div>
        </div>

        <Separator />

        {/* Related Articles */}
        <div>
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Newspaper className="h-4 w-4" />
            Related Articles ({data.related_articles.length})
          </h4>
          <div className="space-y-2">
            {data.related_articles.length === 0 ? (
              <p className="text-sm text-muted-foreground">No related articles</p>
            ) : (
              data.related_articles.map((article) => (
                <RelatedArticleItem
                  key={article.id}
                  article={article}
                  onClick={() => onArticleClick?.(article.id)}
                />
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ===========================
// Connected Entity Item
// ===========================

interface ConnectedEntityItemProps {
  entity: MarketConnectedEntity;
  onClick?: () => void;
}

function ConnectedEntityItem({ entity, onClick }: ConnectedEntityItemProps) {
  const sentimentColor =
    entity.sentiment_avg > 0.2
      ? 'text-green-600'
      : entity.sentiment_avg < -0.2
      ? 'text-red-600'
      : 'text-gray-600';

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full p-2 rounded border text-left hover:bg-accent transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium text-sm">{entity.name}</span>
          <span className="text-xs text-muted-foreground ml-2">
            ({entity.type})
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">
            {entity.relationship_count} rel
          </span>
          <span className={cn('font-medium', sentimentColor)}>
            {entity.sentiment_avg >= 0 ? '+' : ''}
            {(entity.sentiment_avg * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </button>
  );
}

// ===========================
// Related Article Item
// ===========================

interface RelatedArticleItemProps {
  article: MarketRelatedArticle;
  onClick?: () => void;
}

function RelatedArticleItem({ article, onClick }: RelatedArticleItemProps) {
  const sentimentColor =
    article.sentiment > 0.2
      ? 'bg-green-100 text-green-800'
      : article.sentiment < -0.2
      ? 'bg-red-100 text-red-800'
      : 'bg-gray-100 text-gray-800';

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full p-2 rounded border text-left hover:bg-accent transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{article.title}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}
          </p>
        </div>
        <Badge className={cn('text-xs shrink-0', sentimentColor)}>
          {article.sentiment >= 0 ? '+' : ''}
          {(article.sentiment * 100).toFixed(0)}%
        </Badge>
      </div>
    </button>
  );
}

export default MarketDetailsCard;
