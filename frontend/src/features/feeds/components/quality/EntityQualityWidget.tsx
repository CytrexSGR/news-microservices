/**
 * EntityQualityWidget Component
 *
 * Displays entity disambiguation quality metrics from the Knowledge Graph service.
 * Shows success rate, pending reviews, and breakdown by entity type.
 */
import { useMemo } from 'react';
import {
  useDisambiguationQuality,
  useRefreshDisambiguationQuality,
  getDisambiguationStatus,
} from '../../api/useDisambiguationQuality';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  RefreshCw,
  Users,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  AlertCircle,
  Eye,
  Building2,
  MapPin,
  Tag,
} from 'lucide-react';

interface EntityQualityWidgetProps {
  className?: string;
  compact?: boolean;
  onReviewClick?: () => void;
}

// Entity type icons mapping
const entityTypeIcons: Record<string, React.ReactNode> = {
  person: <Users className="h-4 w-4" />,
  organization: <Building2 className="h-4 w-4" />,
  location: <MapPin className="h-4 w-4" />,
  default: <Tag className="h-4 w-4" />,
};

export function EntityQualityWidget({
  className,
  compact = false,
  onReviewClick,
}: EntityQualityWidgetProps) {
  const { data, isLoading, error, isFetching } = useDisambiguationQuality();
  const { refresh } = useRefreshDisambiguationQuality();

  // Calculate success rate percentage
  const successRatePercent = useMemo(() => {
    if (!data) return 0;
    return Math.round(data.success_rate * 100);
  }, [data]);

  // Determine status based on success rate
  const status = useMemo(() => {
    if (!data) return 'success';
    return getDisambiguationStatus(data.success_rate);
  }, [data]);

  const statusConfig = {
    success: {
      bgColor: 'bg-green-50 dark:bg-green-950/30',
      borderColor: 'border-green-200 dark:border-green-900',
      icon: CheckCircle,
      iconColor: 'text-green-500',
      progressColor: 'bg-green-500',
    },
    warning: {
      bgColor: 'bg-yellow-50 dark:bg-yellow-950/30',
      borderColor: 'border-yellow-200 dark:border-yellow-900',
      icon: AlertTriangle,
      iconColor: 'text-yellow-500',
      progressColor: 'bg-yellow-500',
    },
    error: {
      bgColor: 'bg-red-50 dark:bg-red-950/30',
      borderColor: 'border-red-200 dark:border-red-900',
      icon: XCircle,
      iconColor: 'text-red-500',
      progressColor: 'bg-red-500',
    },
  };

  const config = statusConfig[status];
  const StatusIcon = config.icon;

  if (error) {
    return (
      <Card className={cn('p-4', className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="text-sm text-destructive">Failed to load disambiguation data</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refresh()}
            disabled={isFetching}
          >
            <RefreshCw className={cn('h-4 w-4 mr-1', isFetching && 'animate-spin')} />
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={cn('p-4', className)}>
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Card className={cn(config.bgColor, config.borderColor, 'border p-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">Entity Disambiguation</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refresh()}
          disabled={isFetching}
          className="h-8"
        >
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
        </Button>
      </div>

      {/* Success Rate */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Success Rate</span>
          <div className="flex items-center gap-2">
            <StatusIcon className={cn('h-4 w-4', config.iconColor)} />
            <span className="text-2xl font-bold">{successRatePercent}%</span>
          </div>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all duration-500',
              config.progressColor
            )}
            style={{ width: `${successRatePercent}%` }}
          />
        </div>
      </div>

      {/* Warning Alert */}
      {successRatePercent < 85 && (
        <div className="mb-4 p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-yellow-800 dark:text-yellow-200">
              Disambiguation rate below threshold
            </p>
            <p className="text-yellow-700 dark:text-yellow-300 text-xs mt-0.5">
              Consider reviewing ambiguous entities to improve data quality.
            </p>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <MetricCard
          icon={<CheckCircle className="h-4 w-4 text-green-500" />}
          label="Resolved"
          value={data.resolved_entities.toLocaleString()}
        />
        <MetricCard
          icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
          label="Ambiguous"
          value={data.ambiguous_entities.toLocaleString()}
        />
        <MetricCard
          icon={<Clock className="h-4 w-4 text-blue-500" />}
          label="Pending"
          value={data.pending_review.toLocaleString()}
          highlight={data.pending_review > 0}
        />
      </div>

      {/* Entity Type Breakdown */}
      {!compact && data.disambiguation_by_type && Object.keys(data.disambiguation_by_type).length > 0 && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-medium mb-2">By Entity Type</h4>
          <div className="space-y-2">
            {Object.entries(data.disambiguation_by_type).map(([type, metrics]) => (
              <EntityTypeRow
                key={type}
                type={type}
                metrics={metrics}
              />
            ))}
          </div>
        </div>
      )}

      {/* Review Pending Button */}
      {data.pending_review > 0 && onReviewClick && (
        <div className="mt-4">
          <Button
            variant="outline"
            className="w-full"
            onClick={onReviewClick}
          >
            <Eye className="h-4 w-4 mr-2" />
            Review {data.pending_review} Pending Entities
          </Button>
        </div>
      )}

      {/* Last Checked */}
      {data.last_checked && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-muted-foreground">
            Last checked: {new Date(data.last_checked).toLocaleString()}
          </p>
        </div>
      )}
    </Card>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}

function MetricCard({ icon, label, value, highlight }: MetricCardProps) {
  return (
    <div className={cn(
      'p-2 rounded-lg bg-white/50 dark:bg-gray-800/50',
      highlight && 'ring-1 ring-blue-500/50'
    )}>
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

interface EntityTypeRowProps {
  type: string;
  metrics: {
    total: number;
    resolved: number;
    rate: number;
    pending?: number;
  };
}

function EntityTypeRow({ type, metrics }: EntityTypeRowProps) {
  const icon = entityTypeIcons[type.toLowerCase()] || entityTypeIcons.default;
  const ratePercent = Math.round(metrics.rate * 100);

  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">{icon}</span>
        <span className="capitalize">{type}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-muted-foreground text-xs">
          {metrics.resolved}/{metrics.total}
        </span>
        <Badge
          variant="outline"
          className={cn(
            'font-mono text-xs',
            ratePercent >= 90 ? 'text-green-600 border-green-300' :
            ratePercent >= 75 ? 'text-yellow-600 border-yellow-300' :
            'text-red-600 border-red-300'
          )}
        >
          {ratePercent}%
        </Badge>
      </div>
    </div>
  );
}
