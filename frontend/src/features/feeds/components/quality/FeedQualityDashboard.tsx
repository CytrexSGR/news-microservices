/**
 * FeedQualityDashboard Component
 *
 * Comprehensive quality dashboard combining graph integrity,
 * entity disambiguation, and overall quality metrics.
 */
import { useMemo } from 'react';
import { useGraphIntegrity } from '../../api/useGraphIntegrity';
import { useDisambiguationQuality } from '../../api/useDisambiguationQuality';
import { calculateOverallQualityScore, getQualityStatus } from '../../types/quality';
import { GraphIntegrityPanel } from './GraphIntegrityPanel';
import { EntityQualityWidget } from './EntityQualityWidget';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  BarChart3,
} from 'lucide-react';

interface FeedQualityDashboardProps {
  className?: string;
  onReviewEntitiesClick?: () => void;
}

export function FeedQualityDashboard({
  className,
  onReviewEntitiesClick,
}: FeedQualityDashboardProps) {
  const { data: graphData, isLoading: graphLoading } = useGraphIntegrity();
  const { data: disambiguationData, isLoading: disambiguationLoading } = useDisambiguationQuality();

  // Calculate overall quality score
  const overallScore = useMemo(() => {
    if (!graphData || !disambiguationData) return null;
    return calculateOverallQualityScore(
      graphData.data_quality_score,
      disambiguationData.success_rate
    );
  }, [graphData, disambiguationData]);

  const qualityStatus = useMemo(() => {
    if (overallScore === null) return null;
    return getQualityStatus(overallScore);
  }, [overallScore]);

  // Determine trend (placeholder - would need historical data)
  const trend = useMemo(() => {
    if (overallScore === null) return 'stable';
    if (overallScore >= 85) return 'up';
    if (overallScore < 60) return 'down';
    return 'stable';
  }, [overallScore]);

  const trendConfig = {
    up: { icon: TrendingUp, color: 'text-green-500', label: 'Improving' },
    down: { icon: TrendingDown, color: 'text-red-500', label: 'Declining' },
    stable: { icon: Minus, color: 'text-gray-500', label: 'Stable' },
  };

  const TrendIcon = trendConfig[trend].icon;
  const isLoading = graphLoading || disambiguationLoading;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Overall Score Summary */}
      <Card className="p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-primary/10">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Feed Quality Overview</h2>
            <p className="text-sm text-muted-foreground">
              Combined metrics from Knowledge Graph analysis
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-24">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : overallScore !== null && qualityStatus !== null ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Overall Score */}
            <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Overall Score</span>
                <div className={cn('flex items-center gap-1', trendConfig[trend].color)}>
                  <TrendIcon className="h-4 w-4" />
                  <span className="text-xs">{trendConfig[trend].label}</span>
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">{overallScore}</span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
              <div className="mt-2">
                <span
                  className={cn(
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                    qualityStatus.color === 'green' && 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
                    qualityStatus.color === 'blue' && 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
                    qualityStatus.color === 'yellow' && 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
                    qualityStatus.color === 'red' && 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  )}
                >
                  {qualityStatus.label}
                </span>
              </div>
            </div>

            {/* Graph Quality */}
            <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-blue-500" />
                <span className="text-sm text-muted-foreground">Graph Quality</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">
                  {graphData?.data_quality_score ?? '-'}
                </span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {graphData?.total_nodes?.toLocaleString() ?? 0} nodes,{' '}
                {graphData?.total_relationships?.toLocaleString() ?? 0} relationships
              </p>
            </div>

            {/* Disambiguation Rate */}
            <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-4 w-4 text-purple-500" />
                <span className="text-sm text-muted-foreground">Disambiguation</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">
                  {disambiguationData
                    ? Math.round(disambiguationData.success_rate * 100)
                    : '-'}
                </span>
                <span className="text-sm text-muted-foreground">%</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {disambiguationData?.resolved_entities?.toLocaleString() ?? 0} resolved,{' '}
                {disambiguationData?.pending_review ?? 0} pending
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p>No quality data available</p>
          </div>
        )}
      </Card>

      {/* Detailed Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <GraphIntegrityPanel />
        <EntityQualityWidget onReviewClick={onReviewEntitiesClick} />
      </div>

      {/* Quality Tips */}
      {overallScore !== null && overallScore < 75 && (
        <Card className="p-4 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900">
          <div className="flex items-start gap-3">
            <Activity className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-800 dark:text-blue-200">
                Quality Improvement Tips
              </h4>
              <ul className="mt-2 space-y-1 text-sm text-blue-700 dark:text-blue-300">
                {graphData && graphData.orphaned_nodes > 50 && (
                  <li>
                    - Review and connect {graphData.orphaned_nodes} orphaned nodes to improve graph connectivity
                  </li>
                )}
                {graphData && graphData.broken_relationships > 10 && (
                  <li>
                    - Fix {graphData.broken_relationships} broken relationships to maintain data integrity
                  </li>
                )}
                {disambiguationData && disambiguationData.pending_review > 0 && (
                  <li>
                    - Review {disambiguationData.pending_review} pending entity disambiguations
                  </li>
                )}
                {disambiguationData && disambiguationData.success_rate < 0.85 && (
                  <li>
                    - Improve entity extraction rules to increase disambiguation success rate
                  </li>
                )}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
