/**
 * NarrativeClustersGrid - Display narrative clusters in a grid
 *
 * Shows clusters of related narratives with dominant frames,
 * article counts, and bias information.
 */
import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/Input';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  RefreshCw,
  Filter,
  Users,
  TrendingUp,
  Clock,
  AlertCircle,
  ChevronRight,
} from 'lucide-react';
import { useNarrativeClusters } from '../api/useNarrativeClusters';
import { BiasGauge } from './BiasChart';
import type { NarrativeCluster, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor, getBiasLabel, getBiasColor } from '../types/narrative.types';

interface NarrativeClustersGridProps {
  onClusterSelect?: (cluster: NarrativeCluster) => void;
  selectedClusterId?: string;
  columns?: 1 | 2 | 3 | 4;
  compact?: boolean;
  className?: string;
}

export function NarrativeClustersGrid({
  onClusterSelect,
  selectedClusterId,
  columns = 3,
  compact = false,
  className = '',
}: NarrativeClustersGridProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFrame, setFilterFrame] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'article_count' | 'avg_bias' | 'last_updated'>(
    'article_count'
  );

  const { data, isLoading, error, refetch } = useNarrativeClusters({
    dominant_frame: filterFrame !== 'all' ? (filterFrame as NarrativeType) : undefined,
    sort_by: sortBy,
    sort_order: 'desc',
    per_page: 50,
  });

  const filteredClusters = useMemo(() => {
    if (!data?.clusters) return [];

    return data.clusters.filter((cluster) => {
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          cluster.name.toLowerCase().includes(term) ||
          cluster.entities.some((e) => e.toLowerCase().includes(term))
        );
      }
      return true;
    });
  }, [data?.clusters, searchTerm]);

  const narrativeTypes: NarrativeType[] = [
    'conflict',
    'cooperation',
    'crisis',
    'progress',
    'decline',
    'neutral',
  ];

  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  };

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-muted-foreground">Failed to load clusters.</p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search clusters..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Frame Filter */}
            <Select value={filterFrame} onValueChange={setFilterFrame}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by frame" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Frames</SelectItem>
                {narrativeTypes.map((type) => (
                  <SelectItem key={type} value={type} className="capitalize">
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Sort */}
            <Select value={sortBy} onValueChange={(v: any) => setSortBy(v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="article_count">Article Count</SelectItem>
                <SelectItem value="avg_bias">Bias Score</SelectItem>
                <SelectItem value="last_updated">Last Updated</SelectItem>
              </SelectContent>
            </Select>

            {/* Refresh */}
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Grid */}
      {isLoading ? (
        <ClustersGridSkeleton columns={columns} />
      ) : filteredClusters.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {searchTerm
              ? `No clusters found matching "${searchTerm}"`
              : 'No narrative clusters available.'}
          </CardContent>
        </Card>
      ) : (
        <>
          <div className={`grid ${gridCols[columns]} gap-4`}>
            {filteredClusters.map((cluster) => (
              <ClusterCard
                key={cluster.id}
                cluster={cluster}
                isSelected={cluster.id === selectedClusterId}
                compact={compact}
                onClick={() => onClusterSelect?.(cluster)}
              />
            ))}
          </div>

          {/* Results count */}
          <div className="text-sm text-muted-foreground text-center">
            Showing {filteredClusters.length} of {data?.total ?? 0} clusters
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Individual Cluster Card
 */
interface ClusterCardProps {
  cluster: NarrativeCluster;
  isSelected?: boolean;
  compact?: boolean;
  onClick?: () => void;
}

function ClusterCard({
  cluster,
  isSelected = false,
  compact = false,
  onClick,
}: ClusterCardProps) {
  const biasDirection = getBiasLabel(cluster.avg_bias);
  const biasColorClass = getBiasColor(biasDirection);

  if (compact) {
    return (
      <Card
        className={`cursor-pointer transition-all hover:shadow-md ${
          isSelected ? 'ring-2 ring-primary' : ''
        } ${getNarrativeBgColor(cluster.dominant_frame)}`}
        onClick={onClick}
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-medium">{cluster.name}</h3>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={`text-xs capitalize ${getNarrativeColor(cluster.dominant_frame)}`}
                >
                  {cluster.dominant_frame}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {cluster.article_count} articles
                </span>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onClick}
    >
      <CardHeader className={`pb-2 ${getNarrativeBgColor(cluster.dominant_frame)}`}>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base">{cluster.name}</CardTitle>
            <Badge
              variant="outline"
              className={`capitalize ${getNarrativeColor(cluster.dominant_frame)}`}
            >
              {cluster.dominant_frame}
            </Badge>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 text-center">
          <div className="p-2 rounded bg-secondary/50">
            <div className="flex items-center justify-center gap-1 text-muted-foreground text-xs mb-1">
              <Users className="h-3 w-3" />
              Articles
            </div>
            <div className="text-lg font-bold">{cluster.article_count}</div>
          </div>
          <div className="p-2 rounded bg-secondary/50">
            <div className="flex items-center justify-center gap-1 text-muted-foreground text-xs mb-1">
              <TrendingUp className="h-3 w-3" />
              Bias
            </div>
            <div className={`text-lg font-bold ${biasColorClass}`}>
              {cluster.avg_bias > 0 ? '+' : ''}
              {cluster.avg_bias.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Bias Gauge */}
        <BiasGauge score={cluster.avg_bias} confidence={0.8} size="sm" />

        {/* Entities */}
        {cluster.entities.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground mb-1">Key Entities</div>
            <div className="flex flex-wrap gap-1">
              {cluster.entities.slice(0, 4).map((entity) => (
                <Badge key={entity} variant="secondary" className="text-xs">
                  {entity}
                </Badge>
              ))}
              {cluster.entities.length > 4 && (
                <Badge variant="secondary" className="text-xs">
                  +{cluster.entities.length - 4}
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Last Updated */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {new Date(cluster.last_updated).toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Loading Skeleton
 */
function ClustersGridSkeleton({
  columns = 3,
  count = 6,
}: {
  columns?: number;
  count?: number;
}) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  };

  return (
    <div className={`grid ${gridCols[columns as keyof typeof gridCols]} gap-4`}>
      {[...Array(count)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-20" />
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-16" />
              <Skeleton className="h-16" />
            </div>
            <Skeleton className="h-8" />
            <div className="flex gap-1">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * Cluster Stats Summary
 */
interface ClusterStatsSummaryProps {
  clusters: NarrativeCluster[];
  className?: string;
}

export function ClusterStatsSummary({
  clusters,
  className = '',
}: ClusterStatsSummaryProps) {
  const totalArticles = clusters.reduce((sum, c) => sum + c.article_count, 0);
  const avgBias =
    clusters.length > 0
      ? clusters.reduce((sum, c) => sum + c.avg_bias, 0) / clusters.length
      : 0;

  const frameDistribution = clusters.reduce(
    (acc, cluster) => {
      acc[cluster.dominant_frame] = (acc[cluster.dominant_frame] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card className={className}>
      <CardContent className="py-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{clusters.length}</div>
            <div className="text-xs text-muted-foreground">Total Clusters</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{totalArticles}</div>
            <div className="text-xs text-muted-foreground">Total Articles</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {avgBias > 0 ? '+' : ''}
              {avgBias.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground">Avg Bias</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {Object.keys(frameDistribution).length}
            </div>
            <div className="text-xs text-muted-foreground">Frame Types</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
