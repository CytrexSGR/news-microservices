/**
 * NarrativeStatsWidget - Overall narrative statistics from Knowledge Graph
 *
 * Displays aggregate statistics, distribution overview, and key metrics.
 */
import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  FileText,
  Users,
  Flame,
  RefreshCw,
  Calendar,
  TrendingUp,
  Activity,
} from 'lucide-react';
import { useNarrativeStats, useRecentNarrativeStats } from '../api/kg';
import type { NarrativeStats, NarrativeType, BiasDirection } from '../types/narrative.types';
import {
  getNarrativeColor,
  getBiasColor,
  getTensionColor,
  getTensionSeverity,
} from '../types/narrative.types';

interface NarrativeStatsWidgetProps {
  title?: string;
  days?: number;
  showFullStats?: boolean;
  className?: string;
}

export function NarrativeStatsWidget({
  title = 'Narrative Statistics',
  days = 7,
  showFullStats = true,
  className = '',
}: NarrativeStatsWidgetProps) {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useRecentNarrativeStats(days);

  if (isLoading) {
    return <NarrativeStatsSkeleton className={className} showFullStats={showFullStats} />;
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-6">
          <div className="text-center text-muted-foreground">
            <p>{error.message}</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardContent className="py-6 text-center text-muted-foreground">
          No statistics available.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          Last {days} days overview | Updated{' '}
          {new Date(data.generated_at).toLocaleTimeString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            icon={<BarChart3 className="h-5 w-5 text-blue-500" />}
            label="Total Frames"
            value={data.stats.total_frames.toLocaleString()}
          />
          <MetricCard
            icon={<FileText className="h-5 w-5 text-green-500" />}
            label="Articles"
            value={data.stats.total_articles_analyzed.toLocaleString()}
          />
          <MetricCard
            icon={<Users className="h-5 w-5 text-purple-500" />}
            label="Entities"
            value={data.stats.total_entities_involved.toLocaleString()}
          />
          <MetricCard
            icon={<Flame className="h-5 w-5 text-orange-500" />}
            label="Avg Tension"
            value={`${(data.stats.avg_tension_score * 100).toFixed(1)}%`}
            valueClass={getTensionColor(data.stats.avg_tension_score)}
          />
        </div>

        {showFullStats && (
          <>
            {/* Frame Distribution */}
            <FrameDistributionSection distribution={data.stats.frame_distribution} />

            {/* Bias Distribution */}
            <BiasDistributionSection distribution={data.stats.bias_distribution} />

            {/* Time Range & Peak Day */}
            <TimeInfoSection stats={data.stats} />
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Metric Card Component
 */
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
  trend?: 'up' | 'down' | 'neutral';
}

function MetricCard({ icon, label, value, valueClass = '', trend }: MetricCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
      <div className="flex-shrink-0">{icon}</div>
      <div>
        <div className={`text-xl font-bold ${valueClass}`}>{value}</div>
        <div className="text-xs text-muted-foreground flex items-center gap-1">
          {label}
          {trend === 'up' && <TrendingUp className="h-3 w-3 text-green-500" />}
          {trend === 'down' && <TrendingUp className="h-3 w-3 text-red-500 rotate-180" />}
        </div>
      </div>
    </div>
  );
}

/**
 * Frame Distribution Section
 */
function FrameDistributionSection({
  distribution,
}: {
  distribution: Record<NarrativeType, number>;
}) {
  const entries = Object.entries(distribution) as [NarrativeType, number][];
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  const sorted = entries.sort(([, a], [, b]) => b - a);

  if (total === 0) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium flex items-center gap-2">
        <BarChart3 className="h-4 w-4" />
        Frame Distribution
      </h4>
      <div className="space-y-2">
        {sorted.slice(0, 5).map(([type, count]) => (
          <div key={type} className="flex items-center gap-3">
            <span
              className={`text-xs capitalize w-20 truncate ${getNarrativeColor(type)}`}
            >
              {type}
            </span>
            <Progress value={(count / total) * 100} className="h-2 flex-1" />
            <span className="text-xs text-muted-foreground w-12 text-right">
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Bias Distribution Section
 */
function BiasDistributionSection({
  distribution,
}: {
  distribution: Record<BiasDirection, number>;
}) {
  const entries = Object.entries(distribution) as [BiasDirection, number][];
  const total = entries.reduce((sum, [, count]) => sum + count, 0);

  if (total === 0) return null;

  const biasOrder: BiasDirection[] = ['left', 'center-left', 'center', 'center-right', 'right'];
  const ordered = biasOrder.map((dir) => [dir, distribution[dir] || 0] as [BiasDirection, number]);

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium">Bias Distribution</h4>
      <div className="flex gap-1 h-8 rounded-lg overflow-hidden">
        {ordered.map(([direction, count]) => {
          const percentage = total > 0 ? (count / total) * 100 : 0;
          if (percentage < 1) return null;

          const colors: Record<BiasDirection, string> = {
            left: 'bg-blue-600',
            'center-left': 'bg-blue-400',
            center: 'bg-gray-400',
            'center-right': 'bg-red-400',
            right: 'bg-red-600',
          };

          return (
            <div
              key={direction}
              className={`${colors[direction]} flex items-center justify-center transition-all`}
              style={{ width: `${percentage}%` }}
              title={`${direction}: ${count} (${percentage.toFixed(1)}%)`}
            >
              {percentage > 10 && (
                <span className="text-xs text-white font-medium">
                  {percentage.toFixed(0)}%
                </span>
              )}
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Left</span>
        <span>Center</span>
        <span>Right</span>
      </div>
    </div>
  );
}

/**
 * Time Info Section
 */
function TimeInfoSection({ stats }: { stats: NarrativeStats }) {
  return (
    <div className="grid md:grid-cols-2 gap-4">
      {/* Time Range */}
      <div className="p-3 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
          <Calendar className="h-4 w-4" />
          Analysis Period
        </div>
        <div className="text-sm font-medium">
          {new Date(stats.time_range.start).toLocaleDateString()} -{' '}
          {new Date(stats.time_range.end).toLocaleDateString()}
        </div>
      </div>

      {/* Most Active Day */}
      {stats.most_active_day && (
        <div className="p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <TrendingUp className="h-4 w-4" />
            Peak Activity
          </div>
          <div className="text-sm font-medium">
            {new Date(stats.most_active_day.date).toLocaleDateString()}
            <Badge variant="secondary" className="ml-2">
              {stats.most_active_day.frame_count} frames
            </Badge>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Loading Skeleton
 */
function NarrativeStatsSkeleton({
  className = '',
  showFullStats = true,
}: {
  className?: string;
  showFullStats?: boolean;
}) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-8 w-8" />
        </div>
        <Skeleton className="h-4 w-60" />
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
        {showFullStats && (
          <>
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-16 w-full" />
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact Stats Widget for Dashboard
 */
export function CompactNarrativeStats({
  days = 7,
  className = '',
}: {
  days?: number;
  className?: string;
}) {
  const { data, isLoading } = useRecentNarrativeStats(days);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="py-4">
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Card className={className}>
      <CardContent className="py-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center">
            <div className="text-2xl font-bold">
              {data.stats.total_frames.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Frames</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {data.stats.total_articles_analyzed.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Articles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {data.stats.total_entities_involved.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Entities</div>
          </div>
          <div className="text-center">
            <div
              className={`text-2xl font-bold ${getTensionColor(
                data.stats.avg_tension_score
              )}`}
            >
              {(data.stats.avg_tension_score * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Tension</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Stats Summary Bar for Headers
 */
export function NarrativeStatsSummaryBar({
  days = 7,
  className = '',
}: {
  days?: number;
  className?: string;
}) {
  const { data, isLoading } = useRecentNarrativeStats(days);

  if (isLoading || !data) {
    return null;
  }

  return (
    <div className={`flex items-center gap-4 text-sm ${className}`}>
      <div className="flex items-center gap-1">
        <BarChart3 className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{data.stats.total_frames.toLocaleString()}</span>
        <span className="text-muted-foreground">frames</span>
      </div>
      <div className="flex items-center gap-1">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{data.stats.total_articles_analyzed.toLocaleString()}</span>
        <span className="text-muted-foreground">articles</span>
      </div>
      <div className="flex items-center gap-1">
        <Users className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{data.stats.total_entities_involved.toLocaleString()}</span>
        <span className="text-muted-foreground">entities</span>
      </div>
      <div className="flex items-center gap-1">
        <Flame className={`h-4 w-4 ${getTensionColor(data.stats.avg_tension_score)}`} />
        <span className={`font-medium ${getTensionColor(data.stats.avg_tension_score)}`}>
          {(data.stats.avg_tension_score * 100).toFixed(0)}%
        </span>
        <span className="text-muted-foreground">tension</span>
      </div>
    </div>
  );
}
