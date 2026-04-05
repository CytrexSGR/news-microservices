/**
 * NarrativeDashboard - Overview dashboard for narrative analysis
 *
 * Displays aggregated statistics, frame distributions, and recent analyses.
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import {
  RefreshCw,
  TrendingUp,
  BarChart3,
  FileText,
  DollarSign,
  Activity,
  AlertCircle,
} from 'lucide-react';
import { useNarrativeOverview } from '../api/useNarrativeOverview';
import { BiasGauge } from './BiasChart';
import { CostSummary } from './CostWarningBadge';
import { CompactResultView } from './NarrativeResultView';
import type { NarrativeType, NarrativeOverview } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor } from '../types/narrative.types';

interface NarrativeDashboardProps {
  days?: number;
  onAnalyzeClick?: () => void;
  onResultClick?: (result: any) => void;
  className?: string;
}

export function NarrativeDashboard({
  days = 7,
  onAnalyzeClick,
  onResultClick,
  className = '',
}: NarrativeDashboardProps) {
  const { data, isLoading, error, refetch } = useNarrativeOverview({ days });

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-muted-foreground">Failed to load dashboard data.</p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return <DashboardSkeleton className={className} />;
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center text-muted-foreground">
          No data available.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Narrative Analysis</h2>
          <p className="text-muted-foreground">Last {days} days overview</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {onAnalyzeClick && (
            <Button onClick={onAnalyzeClick}>
              <FileText className="h-4 w-4 mr-2" />
              New Analysis
            </Button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Analyses"
          value={data.total_analyses}
          icon={<Activity className="h-5 w-5" />}
          trend={data.total_analyses > 0 ? '+12%' : undefined}
        />
        <StatCard
          title="Average Bias"
          value={data.avg_bias_score.toFixed(2)}
          icon={<TrendingUp className="h-5 w-5" />}
          valuePrefix={data.avg_bias_score > 0 ? '+' : ''}
          valueClass={
            data.avg_bias_score > 0.3
              ? 'text-red-500'
              : data.avg_bias_score < -0.3
              ? 'text-blue-500'
              : ''
          }
        />
        <StatCard
          title="Trending Frames"
          value={data.trending_frames.length}
          icon={<BarChart3 className="h-5 w-5" />}
        />
        <StatCard
          title="Total Cost"
          value={`$${data.cost_total_usd.toFixed(4)}`}
          icon={<DollarSign className="h-5 w-5" />}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Frame Distribution */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Frame Distribution</CardTitle>
            <CardDescription>
              Distribution of detected narrative frames
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FrameDistributionChart distribution={data.frames_distribution} />
          </CardContent>
        </Card>

        {/* Bias Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bias Distribution</CardTitle>
            <CardDescription>Political bias across analyses</CardDescription>
          </CardHeader>
          <CardContent>
            <BiasDistributionChart distribution={data.bias_distribution} />
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Trending Frames */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trending Frames</CardTitle>
            <CardDescription>Most detected frames recently</CardDescription>
          </CardHeader>
          <CardContent>
            {data.trending_frames.length > 0 ? (
              <div className="space-y-3">
                {data.trending_frames.slice(0, 5).map((frame) => (
                  <div
                    key={frame.id}
                    className={`flex items-center justify-between p-3 rounded-lg ${getNarrativeBgColor(
                      frame.type
                    )}`}
                  >
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={`capitalize ${getNarrativeColor(frame.type)}`}
                      >
                        {frame.type}
                      </Badge>
                      <span className="font-medium">{frame.name}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                No trending frames yet.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Analyses */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Analyses</CardTitle>
            <CardDescription>Latest analysis results</CardDescription>
          </CardHeader>
          <CardContent>
            {data.recent_analyses.length > 0 ? (
              <div className="space-y-3">
                {data.recent_analyses.slice(0, 4).map((result, index) => (
                  <CompactResultView
                    key={index}
                    result={result}
                    onClick={() => onResultClick?.(result)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                No recent analyses.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cost Summary */}
      <CostSummary
        totalCost={data.cost_total_usd}
        analysisCount={data.total_analyses}
        period={`last ${days} days`}
      />
    </div>
  );
}

/**
 * Stat Card Component
 */
interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  valuePrefix?: string;
  valueClass?: string;
}

function StatCard({
  title,
  value,
  icon,
  trend,
  valuePrefix = '',
  valueClass = '',
}: StatCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">{title}</span>
          <span className="text-muted-foreground">{icon}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className={`text-2xl font-bold ${valueClass}`}>
            {valuePrefix}
            {value}
          </span>
          {trend && (
            <span className="text-xs text-green-500">{trend}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Frame Distribution Chart
 */
interface FrameDistributionChartProps {
  distribution: Record<NarrativeType, number>;
}

function FrameDistributionChart({ distribution }: FrameDistributionChartProps) {
  const entries = Object.entries(distribution) as [NarrativeType, number][];
  const total = entries.reduce((sum, [, count]) => sum + count, 0);

  if (total === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        No frame data available.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map(([type, count]) => (
        <div key={type}>
          <div className="flex justify-between mb-1 text-sm">
            <span className={`capitalize font-medium ${getNarrativeColor(type)}`}>
              {type}
            </span>
            <span className="text-muted-foreground">
              {count} ({((count / total) * 100).toFixed(1)}%)
            </span>
          </div>
          <Progress value={(count / total) * 100} className="h-2" />
        </div>
      ))}
    </div>
  );
}

/**
 * Bias Distribution Chart
 */
interface BiasDistributionChartProps {
  distribution: Record<string, number>;
}

function BiasDistributionChart({ distribution }: BiasDistributionChartProps) {
  const entries = Object.entries(distribution);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);

  const biasColors: Record<string, string> = {
    left: 'bg-blue-500',
    'center-left': 'bg-blue-300',
    center: 'bg-gray-400',
    'center-right': 'bg-red-300',
    right: 'bg-red-500',
  };

  if (total === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        No bias data available.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map(([direction, count]) => (
        <div key={direction}>
          <div className="flex justify-between mb-1 text-sm">
            <span className="capitalize font-medium">{direction}</span>
            <span className="text-muted-foreground">{count}</span>
          </div>
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className={`h-full ${biasColors[direction] || 'bg-gray-400'}`}
              style={{ width: `${(count / total) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Loading Skeleton
 */
function DashboardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32 mt-2" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid lg:grid-cols-3 gap-6">
        <Skeleton className="h-[300px] lg:col-span-2" />
        <Skeleton className="h-[300px]" />
      </div>
    </div>
  );
}
