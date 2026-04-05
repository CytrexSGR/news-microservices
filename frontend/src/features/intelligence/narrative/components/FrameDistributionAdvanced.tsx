/**
 * FrameDistributionAdvanced - Enhanced frame distribution visualization with KG data
 *
 * Provides bar chart with entity counts, time-based filtering, and trend indicators.
 */
import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Users,
} from 'lucide-react';
import { useFrameDistribution, useRecentFrameDistribution } from '../api/kg';
import type { KGFrameDistribution, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor } from '../types/narrative.types';

interface FrameDistributionAdvancedProps {
  title?: string;
  showEntityCounts?: boolean;
  showTrends?: boolean;
  onFrameClick?: (frameType: NarrativeType) => void;
  className?: string;
}

export function FrameDistributionAdvanced({
  title = 'Frame Distribution',
  showEntityCounts = true,
  showTrends = true,
  onFrameClick,
  className = '',
}: FrameDistributionAdvancedProps) {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('7d');
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');

  // Calculate date range based on selection
  const dateParams = useMemo(() => {
    if (timeRange === 'all') return {};
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0];
    return { start_date: startDate, end_date: endDate };
  }, [timeRange]);

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useFrameDistribution({
    ...dateParams,
    include_entity_counts: showEntityCounts,
  });

  // Calculate total for percentage
  const totalFrames = useMemo(() => {
    return data?.distribution.reduce((sum, d) => sum + d.count, 0) ?? 0;
  }, [data]);

  // Sort by count
  const sortedDistribution = useMemo(() => {
    if (!data) return [];
    return [...data.distribution].sort((a, b) => b.count - a.count);
  }, [data]);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={timeRange}
              onValueChange={(value) => setTimeRange(value as typeof timeRange)}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="30d">30 Days</SelectItem>
                <SelectItem value="90d">90 Days</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {data && (
          <CardDescription>
            {totalFrames.toLocaleString()} total frames
            {data.period && (
              <>
                {' | '}
                {new Date(data.period.start).toLocaleDateString()} -{' '}
                {new Date(data.period.end).toLocaleDateString()}
              </>
            )}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        {/* View Mode Tabs */}
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as typeof viewMode)}>
          <TabsList className="mb-4">
            <TabsTrigger value="chart">Chart</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
          </TabsList>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-6 text-muted-foreground">
              <p>{error.message}</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          )}

          {/* Chart View */}
          <TabsContent value="chart" className="mt-0">
            {data && !isLoading && (
              <div className="space-y-4">
                {sortedDistribution.map((item) => (
                  <FrameBarItem
                    key={item.frame_type}
                    distribution={item}
                    total={totalFrames}
                    showEntityCount={showEntityCounts}
                    onClick={() => onFrameClick?.(item.frame_type)}
                  />
                ))}
                {sortedDistribution.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No frame data available for the selected period.
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Table View */}
          <TabsContent value="table" className="mt-0">
            {data && !isLoading && (
              <FrameDistributionTable
                distribution={sortedDistribution}
                total={totalFrames}
                showEntityCount={showEntityCounts}
                onRowClick={onFrameClick}
              />
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

/**
 * Frame Bar Item Component
 */
interface FrameBarItemProps {
  distribution: KGFrameDistribution;
  total: number;
  showEntityCount: boolean;
  onClick?: () => void;
}

function FrameBarItem({ distribution, total, showEntityCount, onClick }: FrameBarItemProps) {
  const percentage = total > 0 ? (distribution.count / total) * 100 : 0;

  return (
    <div
      className={`p-3 rounded-lg cursor-pointer transition-all hover:scale-[1.01] ${getNarrativeBgColor(
        distribution.frame_type
      )}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`font-medium capitalize ${getNarrativeColor(distribution.frame_type)}`}>
            {distribution.frame_type}
          </span>
          <Badge variant="secondary" className="text-xs">
            {distribution.count.toLocaleString()}
          </Badge>
        </div>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {showEntityCount && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {distribution.entity_count}
            </span>
          )}
          <span className="font-medium">{percentage.toFixed(1)}%</span>
        </div>
      </div>
      <Progress value={percentage} className="h-3" />
      <div className="mt-1 text-xs text-muted-foreground">
        Avg Confidence: {(distribution.avg_confidence * 100).toFixed(1)}%
      </div>
    </div>
  );
}

/**
 * Table View Component
 */
interface FrameDistributionTableProps {
  distribution: KGFrameDistribution[];
  total: number;
  showEntityCount: boolean;
  onRowClick?: (frameType: NarrativeType) => void;
}

function FrameDistributionTable({
  distribution,
  total,
  showEntityCount,
  onRowClick,
}: FrameDistributionTableProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-2 text-left font-medium">Frame Type</th>
            <th className="px-4 py-2 text-right font-medium">Count</th>
            <th className="px-4 py-2 text-right font-medium">Percentage</th>
            <th className="px-4 py-2 text-right font-medium">Avg Confidence</th>
            {showEntityCount && (
              <th className="px-4 py-2 text-right font-medium">Entities</th>
            )}
          </tr>
        </thead>
        <tbody>
          {distribution.map((item, index) => {
            const percentage = total > 0 ? (item.count / total) * 100 : 0;
            return (
              <tr
                key={item.frame_type}
                className={`border-t cursor-pointer hover:bg-muted/30 ${
                  index % 2 === 0 ? 'bg-background' : 'bg-muted/10'
                }`}
                onClick={() => onRowClick?.(item.frame_type)}
              >
                <td className="px-4 py-3">
                  <span className={`capitalize font-medium ${getNarrativeColor(item.frame_type)}`}>
                    {item.frame_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {item.count.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {percentage.toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {(item.avg_confidence * 100).toFixed(1)}%
                </td>
                {showEntityCount && (
                  <td className="px-4 py-3 text-right font-mono">
                    {item.entity_count}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Compact version for dashboards
 */
export function CompactFrameDistribution({
  days = 7,
  onFrameClick,
  className = '',
}: {
  days?: number;
  onFrameClick?: (frameType: NarrativeType) => void;
  className?: string;
}) {
  const { data, isLoading } = useRecentFrameDistribution(days);

  const sortedDistribution = useMemo(() => {
    if (!data) return [];
    return [...data.distribution].sort((a, b) => b.count - a.count).slice(0, 5);
  }, [data]);

  const total = useMemo(() => {
    return data?.distribution.reduce((sum, d) => sum + d.count, 0) ?? 0;
  }, [data]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Frame Distribution
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {sortedDistribution.length > 0 ? (
          <div className="space-y-2">
            {sortedDistribution.map((item) => {
              const percentage = total > 0 ? (item.count / total) * 100 : 0;
              return (
                <div
                  key={item.frame_type}
                  className="flex items-center gap-2 cursor-pointer hover:opacity-80"
                  onClick={() => onFrameClick?.(item.frame_type)}
                >
                  <span
                    className={`text-xs capitalize w-20 truncate ${getNarrativeColor(
                      item.frame_type
                    )}`}
                  >
                    {item.frame_type}
                  </span>
                  <Progress value={percentage} className="h-2 flex-1" />
                  <span className="text-xs text-muted-foreground w-10 text-right">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            No distribution data
          </p>
        )}
      </CardContent>
    </Card>
  );
}
