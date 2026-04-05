/**
 * CanonStatsCard - Stats dashboard card
 *
 * Displays canonicalization statistics including entity counts,
 * coverage metrics, and cost savings.
 */
import {
  Database,
  Link2,
  Percent,
  TrendingUp,
  DollarSign,
  Clock,
  Zap,
  Users,
  Building2,
  MapPin,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import { useCanonStats } from '../api/useCanonStats';
import type { EntityType } from '../types/entities.types';

interface CanonStatsCardProps {
  className?: string;
  refetchInterval?: number;
}

const EntityTypeIcon = ({ type }: { type: EntityType }) => {
  switch (type) {
    case 'PERSON':
      return <Users className="h-4 w-4 text-blue-500" />;
    case 'ORGANIZATION':
      return <Building2 className="h-4 w-4 text-purple-500" />;
    case 'LOCATION':
      return <MapPin className="h-4 w-4 text-green-500" />;
    case 'EVENT':
      return <Calendar className="h-4 w-4 text-orange-500" />;
    default:
      return <Database className="h-4 w-4 text-gray-500" />;
  }
};

export function CanonStatsCard({ className, refetchInterval = 60000 }: CanonStatsCardProps) {
  const { data: stats, isLoading, isError, error } = useCanonStats({ refetchInterval });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Canonicalization Stats
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Canonicalization Stats
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-destructive/10 rounded-lg text-destructive text-sm">
            Failed to load stats: {error?.message}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) return null;

  const entityTypes = Object.entries(stats.entity_type_distribution || {})
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Canonicalization Stats
        </CardTitle>
        <CardDescription>Entity deduplication and Wikidata coverage</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Core Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Database className="h-4 w-4" />
              Canonical Entities
            </div>
            <div className="text-2xl font-bold">{stats.total_canonical_entities.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Link2 className="h-4 w-4" />
              Total Aliases
            </div>
            <div className="text-2xl font-bold">{stats.total_aliases.toLocaleString()}</div>
          </div>
        </div>

        {/* Wikidata Coverage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Percent className="h-4 w-4" />
              Wikidata Coverage
            </span>
            <span className="font-medium">{stats.wikidata_coverage_percent.toFixed(1)}%</span>
          </div>
          <Progress value={stats.wikidata_coverage_percent} className="h-2" />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{stats.wikidata_linked} linked</span>
            <span>{stats.entities_without_qid} missing</span>
          </div>
        </div>

        {/* Deduplication Ratio */}
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <span className="text-sm">Deduplication Ratio</span>
          </div>
          <span className="font-bold text-green-600">{stats.deduplication_ratio.toFixed(2)}x</span>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-3">
          {stats.cache_hit_rate !== null && (
            <div className="p-3 bg-muted rounded-lg space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground text-xs">
                <Zap className="h-3 w-3" />
                Cache Hit Rate
              </div>
              <div className="font-bold">{stats.cache_hit_rate.toFixed(1)}%</div>
            </div>
          )}
          {stats.avg_cache_hit_time_ms !== null && (
            <div className="p-3 bg-muted rounded-lg space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground text-xs">
                <Clock className="h-3 w-3" />
                Avg Response
              </div>
              <div className="font-bold">{stats.avg_cache_hit_time_ms.toFixed(1)}ms</div>
            </div>
          )}
        </div>

        {/* Cost Savings */}
        <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-700">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm font-medium">Estimated Monthly Savings</span>
            </div>
            <span className="font-bold text-green-700">
              ${stats.estimated_cost_savings_monthly.toFixed(2)}
            </span>
          </div>
          <p className="text-xs text-green-600/80 mt-1">
            {stats.total_api_calls_saved.toLocaleString()} API calls saved
          </p>
        </div>

        {/* Entity Type Distribution */}
        {entityTypes.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Entity Types</h4>
            <div className="space-y-2">
              {entityTypes.slice(0, 5).map(([type, count]) => {
                const percentage =
                  (count / stats.total_canonical_entities) * 100;
                return (
                  <div key={type} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <EntityTypeIcon type={type as EntityType} />
                        <span>{type}</span>
                      </div>
                      <span className="text-muted-foreground">{count}</span>
                    </div>
                    <Progress value={percentage} className="h-1" />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Source Breakdown */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Source Breakdown</h4>
          <div className="grid grid-cols-5 gap-2 text-center">
            {Object.entries(stats.source_breakdown || {}).map(([source, count]) => (
              <div key={source} className="p-2 bg-muted rounded">
                <div className="font-bold">{count}</div>
                <div className="text-xs text-muted-foreground capitalize">{source}</div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
