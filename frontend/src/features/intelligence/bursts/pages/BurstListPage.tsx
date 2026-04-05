// frontend/src/features/intelligence/bursts/pages/BurstListPage.tsx

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  RefreshCw,
  Clock,
  TrendingUp,
  Filter,
  X,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { useBursts, useBurstStats } from '../api/useBursts';
import type { BurstListParams, BurstAlert, BurstCategory, BurstSeverity } from '../types';
import { BURST_CATEGORY_LABELS, SEVERITY_COLORS } from '../types';

// =============================================================================
// Constants
// =============================================================================

const CATEGORIES: BurstCategory[] = [
  'conflict',
  'finance',
  'politics',
  'humanitarian',
  'security',
  'technology',
  'other',
  'crypto',
];

const CATEGORY_COLORS: Record<BurstCategory, string> = {
  conflict: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  finance: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  politics: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  humanitarian: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  security: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  technology: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  other: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
  crypto: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

const TIME_WINDOWS = [
  { value: 6, label: '6h' },
  { value: 24, label: '24h' },
  { value: 48, label: '48h' },
  { value: 168, label: '7d' },
];

const SEVERITIES: BurstSeverity[] = ['low', 'medium', 'high', 'critical'];

// =============================================================================
// Main Component
// =============================================================================

export function BurstListPage() {
  const [params, setParams] = useState<BurstListParams>({
    hours: 24,
    limit: 50,
    offset: 0,
  });

  // Fetch bursts
  const { data, isLoading, refetch } = useBursts(params);
  const { data: statsData } = useBurstStats();

  // Handlers
  const handleCategoryClick = (category: BurstCategory) => {
    setParams(prev => ({
      ...prev,
      category: prev.category === category ? undefined : category,
      offset: 0,
    }));
  };

  const handleSeverityClick = (severity: BurstSeverity) => {
    setParams(prev => ({
      ...prev,
      severity: prev.severity === severity ? undefined : severity,
      offset: 0,
    }));
  };

  const handleTimeWindowChange = (hours: number) => {
    setParams(prev => ({ ...prev, hours, offset: 0 }));
  };

  const clearFilters = () => {
    setParams({ hours: 24, limit: 50, offset: 0 });
  };

  const hasFilters = params.category || params.severity;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Zap className="h-6 w-6 text-yellow-500" />
            Burst Detection
          </h1>
          <p className="text-muted-foreground">
            Real-time breaking news detection and alerts
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      {statsData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="py-4">
              <div className="text-2xl font-bold">{statsData.total_bursts_24h}</div>
              <div className="text-sm text-muted-foreground">Last 24h</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="text-2xl font-bold">{statsData.total_bursts_7d}</div>
              <div className="text-sm text-muted-foreground">Last 7 days</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="text-2xl font-bold">{statsData.avg_velocity.toFixed(1)}</div>
              <div className="text-sm text-muted-foreground">Avg Velocity</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="text-2xl font-bold text-red-600">
                {statsData.by_severity.critical || 0}
              </div>
              <div className="text-sm text-muted-foreground">Critical Alerts</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Category Matrix */}
          <div>
            <div className="text-sm font-medium mb-2">Category</div>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(cat => (
                <Button
                  key={cat}
                  variant={params.category === cat ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleCategoryClick(cat)}
                  className={params.category === cat ? '' : CATEGORY_COLORS[cat]}
                >
                  {BURST_CATEGORY_LABELS[cat]}
                </Button>
              ))}
            </div>
          </div>

          {/* Severity */}
          <div>
            <div className="text-sm font-medium mb-2">Severity</div>
            <div className="flex flex-wrap gap-2">
              {SEVERITIES.map(sev => (
                <Button
                  key={sev}
                  variant={params.severity === sev ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleSeverityClick(sev)}
                  className={params.severity === sev ? '' : SEVERITY_COLORS[sev]}
                >
                  {sev.charAt(0).toUpperCase() + sev.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {/* Time Window and Mode */}
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div className="flex gap-1">
                {TIME_WINDOWS.map(tw => (
                  <Button
                    key={tw.value}
                    variant={params.hours === tw.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleTimeWindowChange(tw.value)}
                  >
                    {tw.label}
                  </Button>
                ))}
              </div>
            </div>

            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear Filters
              </Button>
            )}
          </div>

          {/* Active Filter Display */}
          {hasFilters && (
            <div className="text-sm text-muted-foreground">
              Active filter:{' '}
              {params.category && (
                <Badge variant="secondary" className="mx-1">
                  {BURST_CATEGORY_LABELS[params.category]}
                </Badge>
              )}
              {params.severity && (
                <Badge variant="secondary" className="mx-1">
                  {params.severity}
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Header */}
      {!isLoading && (
        <div className="text-sm text-muted-foreground">
          Showing {data?.items.length || 0} of {data?.total || 0} bursts
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading bursts...</p>
        </div>
      )}

      {/* Burst List */}
      {!isLoading && data && data.items.length > 0 && (
        <div className="space-y-3">
          {data.items.map(burst => (
            <BurstCard key={burst.id} burst={burst} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && data && data.items.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Zap className="h-12 w-12 mx-auto text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No Bursts Detected</h3>
            <p className="text-muted-foreground">
              {hasFilters
                ? 'No bursts match the current filters'
                : 'No burst activity in the selected time window'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {data && data.has_more && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => setParams(prev => ({ ...prev, offset: (prev.offset || 0) + (prev.limit || 50) }))}
          >
            Load More
          </Button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Burst Card Component
// =============================================================================

interface BurstCardProps {
  burst: BurstAlert;
}

function BurstCard({ burst }: BurstCardProps) {
  const detectedAt = new Date(burst.detected_at);
  const timeAgo = getTimeAgo(detectedAt);

  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={SEVERITY_COLORS[burst.severity]}>
                {burst.severity}
              </Badge>
              {burst.category && (
                <Badge variant="outline" className={CATEGORY_COLORS[burst.category as BurstCategory]}>
                  {BURST_CATEGORY_LABELS[burst.category as BurstCategory]}
                </Badge>
              )}
            </div>

            <h3 className="font-medium mb-1">
              {burst.title || `Cluster ${burst.cluster_id.slice(0, 8)}...`}
            </h3>

            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4" />
                {burst.velocity} articles in {burst.window_minutes}min
              </span>
              {burst.growth_rate && (
                <span>Growth: {burst.growth_rate.toFixed(1)}x</span>
              )}
              {burst.tension_score && (
                <span>Tension: {burst.tension_score.toFixed(1)}</span>
              )}
              <span>Detected: {timeAgo}</span>
            </div>

            {/* Article time range */}
            {(burst.first_article_at || burst.last_article_at) && (
              <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>
                  Articles: {formatDateRange(burst.first_article_at, burst.last_article_at)}
                </span>
              </div>
            )}

            {burst.top_entities && burst.top_entities.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {burst.top_entities.slice(0, 5).map((entity, i) => (
                  <Badge key={i} variant="outline" className="text-xs">
                    {typeof entity === 'string' ? entity : entity.name || entity.text || 'Unknown'}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <Link to={`/intelligence/events/clusters/${burst.cluster_id}`}>
              <Button variant="outline" size="sm">
                View Cluster
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function formatDateRange(first?: string, last?: string): string {
  if (!first && !last) return 'Unknown';

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (first && last) {
    const firstDate = new Date(first);
    const lastDate = new Date(last);
    const sameDay = firstDate.toDateString() === lastDate.toDateString();

    if (sameDay) {
      // Same day - show date once with time range
      const dateStr = firstDate.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
      const firstTime = firstDate.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
      const lastTime = lastDate.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
      return `${dateStr} ${firstTime} – ${lastTime}`;
    }
    return `${formatDate(first)} – ${formatDate(last)}`;
  }

  return formatDate(first || last!);
}

export default BurstListPage;
