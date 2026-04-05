/**
 * BiasPage - Bias analysis overview and history
 *
 * Shows bias analysis statistics, trends, and historical data.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RefreshCw, TrendingUp, BarChart3, AlertCircle } from 'lucide-react';
import { useBiasAnalysis, useBiasStats } from '../api/useBiasAnalysis';
import {
  BiasGauge,
  BiasBarChart,
  BiasComparisonChart,
  BiasChartSkeleton,
} from '../components/BiasChart';
import { BiasIndicatorList } from '../components/BiasIndicatorList';
import type { BiasType } from '../types/narrative.types';

interface BiasPageProps {
  className?: string;
}

export function BiasPage({ className = '' }: BiasPageProps) {
  const [days, setDays] = useState(7);
  const [biasTypeFilter, setBiasTypeFilter] = useState<BiasType | 'all'>('all');

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useBiasStats(days);
  const {
    data: analyses,
    isLoading: analysesLoading,
    refetch: refetchAnalyses,
  } = useBiasAnalysis({
    bias_type: biasTypeFilter !== 'all' ? biasTypeFilter : undefined,
    per_page: 50,
  });

  const handleRefresh = () => {
    refetchStats();
    refetchAnalyses();
  };

  const biasTypes: BiasType[] = ['political', 'ideological', 'commercial', 'emotional', 'source'];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bias Analysis</h1>
          <p className="text-muted-foreground mt-1">
            Track and analyze bias patterns across your content.
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v))}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24 hours</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="14">Last 14 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid md:grid-cols-3 gap-4">
        {statsLoading ? (
          <>
            <Skeleton className="h-[120px]" />
            <Skeleton className="h-[120px]" />
            <Skeleton className="h-[120px]" />
          </>
        ) : stats ? (
          <>
            {/* Average Bias */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Average Bias
                </CardTitle>
              </CardHeader>
              <CardContent>
                <BiasGauge
                  score={stats.avg_bias}
                  confidence={0.9}
                  size="md"
                  showLabels={false}
                />
              </CardContent>
            </Card>

            {/* Bias Distribution */}
            <Card className="md:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  {Object.entries(stats.distribution).map(([direction, count]) => (
                    <div key={direction} className="text-center">
                      <div className="text-xl font-bold">{count}</div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {direction}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <Card className="md:col-span-3">
            <CardContent className="py-8 text-center text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              No bias data available for this period.
            </CardContent>
          </Card>
        )}
      </div>

      {/* Tabs for different views */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trend">Trend</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4 space-y-4">
          {statsLoading ? (
            <BiasChartSkeleton height={300} />
          ) : stats?.distribution ? (
            <BiasComparisonChart
              data={Object.entries(stats.distribution).map(([label, count]) => ({
                label,
                score: label === 'left' ? -0.7 :
                       label === 'center-left' ? -0.3 :
                       label === 'center' ? 0 :
                       label === 'center-right' ? 0.3 : 0.7,
                count,
              }))}
              title="Bias Distribution by Direction"
              height={300}
            />
          ) : null}
        </TabsContent>

        {/* Trend Tab */}
        <TabsContent value="trend" className="mt-4 space-y-4">
          {statsLoading ? (
            <BiasChartSkeleton height={350} />
          ) : stats?.trend && stats.trend.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Bias Trend Over Time</CardTitle>
                <CardDescription>
                  Daily average bias score for the last {days} days
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  {/* In a real implementation, use a line chart here */}
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Trend chart visualization</p>
                    <p className="text-sm">{stats.trend.length} data points</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                Not enough data for trend analysis.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details" className="mt-4 space-y-4">
          {/* Type Filter */}
          <Card>
            <CardContent className="py-4">
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-muted-foreground self-center mr-2">
                  Filter by type:
                </span>
                <Button
                  variant={biasTypeFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setBiasTypeFilter('all')}
                >
                  All
                </Button>
                {biasTypes.map((type) => (
                  <Button
                    key={type}
                    variant={biasTypeFilter === type ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setBiasTypeFilter(type)}
                    className="capitalize"
                  >
                    {type}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Analyses List */}
          {analysesLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : analyses?.analyses && analyses.analyses.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Bias Analyses</CardTitle>
                <CardDescription>
                  {analyses.total} total analyses from {analyses.period_start} to{' '}
                  {analyses.period_end}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BiasIndicatorList
                  indicators={analyses.analyses.flatMap((a) => a.indicators || [])}
                  showExplanations
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No analyses found for the selected filter.
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default BiasPage;
