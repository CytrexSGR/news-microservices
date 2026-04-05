/**
 * GraphIntegrityPanel Component
 *
 * Displays graph integrity metrics from the Knowledge Graph service.
 * Shows orphaned nodes, broken relationships, data quality score, and issues.
 */
import { useMemo } from 'react';
import { useGraphIntegrity, useRefreshGraphIntegrity } from '../../api/useGraphIntegrity';
import { getSeverityColor } from '../../types/quality';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Database,
  Link2,
  AlertCircle,
} from 'lucide-react';

interface GraphIntegrityPanelProps {
  className?: string;
  compact?: boolean;
}

export function GraphIntegrityPanel({ className, compact = false }: GraphIntegrityPanelProps) {
  const { data, isLoading, error, isFetching } = useGraphIntegrity();
  const { refresh } = useRefreshGraphIntegrity();

  // Determine alert severity based on metrics
  const alertSeverity = useMemo(() => {
    if (!data) return 'neutral';

    const { orphaned_nodes, broken_relationships, data_quality_score } = data;

    // Critical: Very low quality score or many issues
    if (data_quality_score < 50 || broken_relationships > 100 || orphaned_nodes > 500) {
      return 'error';
    }

    // Warning: Moderate issues
    if (data_quality_score < 75 || broken_relationships > 20 || orphaned_nodes > 100) {
      return 'warning';
    }

    return 'success';
  }, [data]);

  const alertConfig = {
    error: {
      bgColor: 'bg-red-50 dark:bg-red-950/30',
      borderColor: 'border-red-200 dark:border-red-900',
      icon: XCircle,
      iconColor: 'text-red-500',
      label: 'Critical Issues Detected',
    },
    warning: {
      bgColor: 'bg-yellow-50 dark:bg-yellow-950/30',
      borderColor: 'border-yellow-200 dark:border-yellow-900',
      icon: AlertTriangle,
      iconColor: 'text-yellow-500',
      label: 'Attention Needed',
    },
    success: {
      bgColor: 'bg-green-50 dark:bg-green-950/30',
      borderColor: 'border-green-200 dark:border-green-900',
      icon: CheckCircle,
      iconColor: 'text-green-500',
      label: 'Graph Healthy',
    },
    neutral: {
      bgColor: 'bg-gray-50 dark:bg-gray-950/30',
      borderColor: 'border-gray-200 dark:border-gray-800',
      icon: Database,
      iconColor: 'text-gray-500',
      label: 'Loading...',
    },
  };

  const config = alertConfig[alertSeverity];
  const AlertIcon = config.icon;

  if (error) {
    return (
      <Card className={cn('p-4', className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="text-sm text-destructive">Failed to load graph integrity data</span>
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
          <AlertIcon className={cn('h-5 w-5', config.iconColor)} />
          <h3 className="font-semibold text-sm">{config.label}</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refresh()}
          disabled={isFetching}
          className="h-8"
        >
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          <span className="ml-1 hidden sm:inline">Check</span>
        </Button>
      </div>

      {/* Quality Score Gauge */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Data Quality Score</span>
          <span className="text-2xl font-bold">{data.data_quality_score}</span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all duration-500',
              data.data_quality_score >= 75 ? 'bg-green-500' :
              data.data_quality_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
            )}
            style={{ width: `${data.data_quality_score}%` }}
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className={cn('grid gap-3', compact ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4')}>
        <MetricCard
          icon={<Database className="h-4 w-4 text-blue-500" />}
          label="Total Nodes"
          value={data.total_nodes.toLocaleString()}
        />
        <MetricCard
          icon={<Link2 className="h-4 w-4 text-purple-500" />}
          label="Relationships"
          value={data.total_relationships.toLocaleString()}
        />
        <MetricCard
          icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
          label="Orphaned"
          value={data.orphaned_nodes.toLocaleString()}
          warning={data.orphaned_nodes > 50}
        />
        <MetricCard
          icon={<XCircle className="h-4 w-4 text-red-500" />}
          label="Broken Rels"
          value={data.broken_relationships.toLocaleString()}
          warning={data.broken_relationships > 10}
        />
      </div>

      {/* Issues List */}
      {!compact && data.issues && data.issues.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-medium mb-2">Issues Detected</h4>
          <div className="space-y-2">
            {data.issues.map((issue, index) => (
              <div
                key={`${issue.type}-${index}`}
                className="flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-2">
                  <Badge className={getSeverityColor(issue.severity)} variant="outline">
                    {issue.severity}
                  </Badge>
                  <span className="capitalize">{issue.type.replace('_', ' ')}</span>
                </div>
                <span className="font-mono text-muted-foreground">{issue.count}</span>
              </div>
            ))}
          </div>
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
  warning?: boolean;
}

function MetricCard({ icon, label, value, warning }: MetricCardProps) {
  return (
    <div className={cn(
      'p-2 rounded-lg bg-white/50 dark:bg-gray-800/50',
      warning && 'ring-1 ring-yellow-500/50'
    )}>
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}
