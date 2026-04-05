/**
 * EntityQualityPanel Component
 *
 * Displays entity disambiguation quality metrics.
 * Shows success rates and breakdowns by entity type.
 *
 * @example
 * ```tsx
 * <EntityQualityPanel onEntityTypeClick={(type) => console.log(type)} />
 * ```
 *
 * @module features/knowledge-graph/components/quality/EntityQualityPanel
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import {
  Users,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';

import {
  useDisambiguationQuality,
  useDisambiguationSummary,
} from '../../api/useDisambiguationQuality';
import { ENTITY_TYPE_COLORS } from '../../utils/colorScheme';

// ===========================
// Component Props
// ===========================

export interface EntityQualityPanelProps {
  /** Callback when entity type is clicked */
  onEntityTypeClick?: (entityType: string) => void;
  /** Compact mode for smaller displays */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function EntityQualityPanel({
  onEntityTypeClick,
  compact = false,
  className,
}: EntityQualityPanelProps) {
  // ===== Data Fetching =====
  const { data, isLoading, error, refetch, isFetching } = useDisambiguationQuality();
  const { summary } = useDisambiguationSummary();

  // ===== Loading State =====
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Entity Disambiguation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  // ===== Error State =====
  if (error || !data) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            Entity Disambiguation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">Failed to load disambiguation data</p>
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

  const successRate = (data.success_rate * 100).toFixed(1);
  const isGoodRate = data.success_rate >= 0.75;

  // ===== Render =====
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Entity Disambiguation
          </CardTitle>
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
        {/* Success Rate Gauge */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Disambiguation Rate</span>
            <div className="flex items-center gap-1">
              {isGoodRate ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-orange-600" />
              )}
              <Badge
                variant="secondary"
                className={cn(
                  'text-xs',
                  isGoodRate
                    ? 'bg-green-100 text-green-800'
                    : 'bg-orange-100 text-orange-800'
                )}
              >
                {isGoodRate ? 'Good' : 'Needs Attention'}
              </Badge>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <span
              className={cn(
                'text-4xl font-bold',
                isGoodRate ? 'text-green-600' : 'text-orange-600'
              )}
            >
              {successRate}%
            </span>
          </div>
          <Progress
            value={data.success_rate * 100}
            className="h-2 mt-3"
          />
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-green-50 border border-green-200">
            <div className="flex items-center gap-1.5 text-green-700 mb-1">
              <CheckCircle className="h-4 w-4" />
              <span className="text-xs">Resolved</span>
            </div>
            <div className="text-lg font-bold text-green-800">
              {data.resolved_entities.toLocaleString()}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-orange-50 border border-orange-200">
            <div className="flex items-center gap-1.5 text-orange-700 mb-1">
              <AlertCircle className="h-4 w-4" />
              <span className="text-xs">Pending</span>
            </div>
            <div className="text-lg font-bold text-orange-800">
              {data.ambiguous_entities.toLocaleString()}
            </div>
          </div>
        </div>

        {/* By Entity Type */}
        {!compact && (
          <div>
            <h4 className="text-sm font-semibold mb-3">By Entity Type</h4>
            <div className="space-y-2 max-h-[250px] overflow-y-auto pr-1">
              {Object.entries(data.by_entity_type).map(([type, stats]) => {
                const color = ENTITY_TYPE_COLORS[type] ?? ENTITY_TYPE_COLORS.DEFAULT;
                const rate = (stats.rate * 100).toFixed(0);

                return (
                  <button
                    key={type}
                    type="button"
                    onClick={() => onEntityTypeClick?.(type)}
                    className="w-full p-3 rounded-lg border text-left hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        <span className="font-medium text-sm capitalize">
                          {type.toLowerCase().replace('_', ' ')}
                        </span>
                      </div>
                      <span className="text-sm font-medium">{rate}%</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{stats.resolved} resolved</span>
                      <span>|</span>
                      <span>{stats.pending} pending</span>
                      <span>|</span>
                      <span>{stats.total} total</span>
                    </div>
                    <Progress
                      value={stats.rate * 100}
                      className="h-1.5 mt-2"
                    />
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Quick Stats for Compact Mode */}
        {compact && (
          <div className="text-sm text-muted-foreground">
            {Object.keys(data.by_entity_type).length} entity types tracked
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default EntityQualityPanel;
