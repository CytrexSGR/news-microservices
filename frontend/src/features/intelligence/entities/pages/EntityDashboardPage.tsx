/**
 * EntityDashboardPage - Stats dashboard page
 *
 * Overview dashboard with key metrics and statistics.
 */
import { ArrowLeft, RefreshCw, Database, Link2, Zap, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { CanonStatsCard } from '../components/CanonStatsCard';
import { EntityClustersTable } from '../components/EntityClustersTable';
import { EntityHistoryTimeline } from '../components/EntityHistoryTimeline';
import { useCanonStats } from '../api/useCanonStats';
import type { EntityCluster } from '../types/entities.types';

interface EntityDashboardPageProps {
  onEntitySelect?: (entity: EntityCluster) => void;
  showBackButton?: boolean;
}

function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  isLoading,
}: {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ElementType;
  trend?: { value: number; label: string };
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div
            className={`flex items-center text-xs mt-1 ${
              trend.value >= 0 ? 'text-green-500' : 'text-red-500'
            }`}
          >
            <TrendingUp className="h-3 w-3 mr-1" />
            {trend.value >= 0 ? '+' : ''}
            {trend.value}% {trend.label}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function EntityDashboardPage({
  onEntitySelect,
  showBackButton,
}: EntityDashboardPageProps) {
  const navigate = useNavigate();
  const { data: stats, isLoading, refetch, isRefetching } = useCanonStats();

  const handleEntityClick = (entity: EntityCluster) => {
    if (onEntitySelect) {
      onEntitySelect(entity);
    } else {
      navigate(
        `/intelligence/entities/${encodeURIComponent(entity.canonical_name)}?type=${entity.entity_type}`
      );
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {showBackButton && (
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Database className="h-8 w-8" />
              Entity Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">
              Canonicalization metrics and entity management overview
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isRefetching}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Canonical Entities"
          value={stats?.total_canonical_entities.toLocaleString() ?? '-'}
          description="Total unique entities"
          icon={Database}
          isLoading={isLoading}
        />
        <MetricCard
          title="Total Aliases"
          value={stats?.total_aliases.toLocaleString() ?? '-'}
          description="Known entity variants"
          icon={Link2}
          isLoading={isLoading}
        />
        <MetricCard
          title="Wikidata Coverage"
          value={`${stats?.wikidata_coverage_percent.toFixed(1) ?? '-'}%`}
          description={`${stats?.wikidata_linked ?? 0} entities linked`}
          icon={Link2}
          isLoading={isLoading}
        />
        <MetricCard
          title="Deduplication Ratio"
          value={`${stats?.deduplication_ratio.toFixed(2) ?? '-'}x`}
          description="Aliases per entity"
          icon={Zap}
          isLoading={isLoading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Top Entities & History */}
        <div className="lg:col-span-2 space-y-6">
          <EntityClustersTable onEntityClick={handleEntityClick} />
          <EntityHistoryTimeline limit={10} />
        </div>

        {/* Right Column - Detailed Stats */}
        <div className="lg:col-span-1">
          <CanonStatsCard />
        </div>
      </div>
    </div>
  );
}
