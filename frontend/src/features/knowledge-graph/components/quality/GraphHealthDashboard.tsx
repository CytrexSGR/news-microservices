/**
 * GraphHealthDashboard Component
 *
 * Comprehensive dashboard for graph health monitoring.
 * Shows integrity metrics, quality score, and issue summary.
 *
 * @example
 * ```tsx
 * <GraphHealthDashboard onIssueClick={(issue) => console.log(issue)} />
 * ```
 *
 * @module features/knowledge-graph/components/quality/GraphHealthDashboard
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Link2Off,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

import { useGraphIntegrity, useIntegritySummary } from '../../api/useGraphIntegrity';
import type { QualityIssue, IssueSeverity } from '../../types/quality';
import {
  getQualityLevel,
  QUALITY_LEVEL_COLORS,
  SEVERITY_COLORS,
  SEVERITY_ICONS,
} from '../../types/quality';

// ===========================
// Component Props
// ===========================

export interface GraphHealthDashboardProps {
  /** Callback when an issue is clicked */
  onIssueClick?: (issue: QualityIssue) => void;
  /** Compact mode for smaller displays */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function GraphHealthDashboard({
  onIssueClick,
  compact = false,
  className,
}: GraphHealthDashboardProps) {
  // ===== Data Fetching =====
  const { data, isLoading, error, refetch, isFetching } = useGraphIntegrity({
    includeExamples: true,
  });
  const { summary } = useIntegritySummary();

  // ===== Loading State =====
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Graph Health
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
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
            <XCircle className="h-5 w-5" />
            Graph Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">Failed to load graph health data</p>
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

  const qualityLevel = getQualityLevel(data.data_quality_score);
  const qualityColor = QUALITY_LEVEL_COLORS[qualityLevel];

  // ===== Render =====
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Graph Health
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
        {/* Quality Score */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Data Quality Score</span>
            <Badge
              variant="secondary"
              style={{ backgroundColor: `${qualityColor}20`, color: qualityColor }}
            >
              {qualityLevel.toUpperCase()}
            </Badge>
          </div>
          <div className="flex items-end gap-3">
            <span
              className="text-4xl font-bold"
              style={{ color: qualityColor }}
            >
              {data.data_quality_score.toFixed(0)}
            </span>
            <span className="text-muted-foreground text-sm mb-1">/ 100</span>
          </div>
          <Progress
            value={data.data_quality_score}
            className="h-2 mt-3"
            style={
              {
                '--progress-color': qualityColor,
              } as React.CSSProperties
            }
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3">
          <StatItem
            icon={<CheckCircle2 className="h-4 w-4 text-green-600" />}
            label="Total Nodes"
            value={data.total_nodes.toLocaleString()}
          />
          <StatItem
            icon={<Link2Off className="h-4 w-4 text-orange-600" />}
            label="Orphaned Nodes"
            value={data.orphaned_nodes.toLocaleString()}
            warning={data.orphaned_nodes > 0}
          />
          <StatItem
            icon={<Activity className="h-4 w-4 text-blue-600" />}
            label="Relationships"
            value={data.total_relationships.toLocaleString()}
          />
          <StatItem
            icon={<AlertTriangle className="h-4 w-4 text-red-600" />}
            label="Broken Rels"
            value={data.broken_relationships.toLocaleString()}
            warning={data.broken_relationships > 0}
          />
        </div>

        {!compact && (
          <>
            <Separator />

            {/* Issues List */}
            <div>
              <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
                <AlertTriangle className="h-4 w-4" />
                Issues ({data.issues.length})
              </h4>
              {data.issues.length === 0 ? (
                <div className="text-center py-4 text-green-600 flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  No issues detected
                </div>
              ) : (
                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                  {data.issues.map((issue, index) => (
                    <IssueItem
                      key={`${issue.type}-${index}`}
                      issue={issue}
                      onClick={() => onIssueClick?.(issue)}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* Quick Summary for Compact Mode */}
        {compact && summary && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {summary.criticalCount} critical, {summary.warningCount} warnings
            </span>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ===========================
// Stat Item Component
// ===========================

interface StatItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  warning?: boolean;
}

function StatItem({ icon, label, value, warning }: StatItemProps) {
  return (
    <div className={cn(
      'p-3 rounded-lg',
      warning ? 'bg-orange-50 border border-orange-200' : 'bg-muted/50'
    )}>
      <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}

// ===========================
// Issue Item Component
// ===========================

interface IssueItemProps {
  issue: QualityIssue;
  onClick?: () => void;
}

function IssueItem({ issue, onClick }: IssueItemProps) {
  const icon = SEVERITY_ICONS[issue.severity];
  const color = SEVERITY_COLORS[issue.severity];

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full p-3 rounded-lg border text-left hover:bg-accent transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2">
          <span className="text-lg">{icon}</span>
          <div>
            <div className="font-medium text-sm capitalize">
              {issue.type.replace(/_/g, ' ')}
            </div>
            {issue.description && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {issue.description}
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Badge
            variant="secondary"
            className="text-xs"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {issue.count.toLocaleString()}
          </Badge>
          <span
            className="text-xs capitalize"
            style={{ color }}
          >
            {issue.severity}
          </span>
        </div>
      </div>
    </button>
  );
}

export default GraphHealthDashboard;
