/**
 * GraphQualityReport - Graph Quality Metrics Display
 *
 * Shows knowledge graph quality metrics and recommendations
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Network,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  RefreshCw,
} from 'lucide-react';
import { useGraphQuality } from '../api';
import type { GraphQualityReport as GraphQualityReportType } from '../types/osint.types';

interface GraphQualityReportProps {
  className?: string;
}

export function GraphQualityReport({ className }: GraphQualityReportProps) {
  const { data, isLoading, error, refetch } = useGraphQuality();

  if (isLoading) {
    return <GraphQualityReportSkeleton />;
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load graph quality report</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* Overview Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Graph Quality Report
            </CardTitle>
            <CardDescription>
              Last updated: {new Date(data.last_updated).toLocaleString()}
            </CardDescription>
          </div>
          <button
            onClick={() => refetch()}
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Nodes"
              value={data.total_nodes.toLocaleString()}
              icon={<Network className="h-4 w-4" />}
            />
            <MetricCard
              label="Edges"
              value={data.total_edges.toLocaleString()}
              icon={<Network className="h-4 w-4" />}
            />
            <MetricCard
              label="Orphan Nodes"
              value={data.orphan_nodes.toLocaleString()}
              icon={
                data.orphan_nodes > 0 ? (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )
              }
              status={data.orphan_nodes > 100 ? 'warning' : 'normal'}
            />
            <MetricCard
              label="Duplicate Rate"
              value={`${(data.duplicate_rate * 100).toFixed(1)}%`}
              icon={
                data.duplicate_rate > 0.05 ? (
                  <TrendingDown className="h-4 w-4 text-yellow-500" />
                ) : (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                )
              }
              status={data.duplicate_rate > 0.1 ? 'warning' : 'normal'}
            />
          </div>
        </CardContent>
      </Card>

      {/* Scores Card */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <ScoreBar
              label="Connectivity"
              score={data.connectivity_score}
              description="How well-connected nodes are in the graph"
            />
            <ScoreBar
              label="Completeness"
              score={data.completeness_score}
              description="How complete entity data is across the graph"
            />
            <ScoreBar
              label="Freshness"
              score={data.freshness_score}
              description="How up-to-date the graph data is"
            />
          </div>
        </CardContent>
      </Card>

      {/* Breakdown Card */}
      {data.breakdown && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">By Entity Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(data.breakdown.by_entity_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{type.replace(/_/g, ' ')}</span>
                    <Badge variant="secondary">{count.toLocaleString()}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">By Relationship Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(data.breakdown.by_relationship_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{type.replace(/_/g, ' ')}</span>
                    <Badge variant="secondary">{count.toLocaleString()}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recommendations Card */}
      {data.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {data.recommendations.map((rec, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm text-muted-foreground"
                >
                  <span className="text-yellow-500 mt-0.5">-</span>
                  {rec}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  status?: 'normal' | 'warning' | 'error';
}

function MetricCard({ label, value, icon, status = 'normal' }: MetricCardProps) {
  const statusClasses = {
    normal: '',
    warning: 'border-yellow-500/50',
    error: 'border-red-500/50',
  };

  return (
    <div className={`rounded-lg border p-4 ${statusClasses[status]}`}>
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

interface ScoreBarProps {
  label: string;
  score: number;
  description: string;
}

function ScoreBar({ label, score, description }: ScoreBarProps) {
  const percentage = Math.round(score * 100);
  const getColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium">{label}</span>
        <span className={`text-sm font-bold ${percentage >= 60 ? 'text-green-500' : 'text-yellow-500'}`}>
          {percentage}%
        </span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${getColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  );
}

function GraphQualityReportSkeleton() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-lg border p-4">
                <Skeleton className="h-4 w-16 mb-2" />
                <Skeleton className="h-8 w-24" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-2 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default GraphQualityReport;
