/**
 * IntelligenceDashboardPage - Intelligence analysis and event monitoring dashboard
 *
 * Location: /intelligence
 * Access: Protected (authenticated users only)
 *
 * Features:
 * - Overview: Global risk index, top clusters, key metrics
 * - Events: Latest events timeline with filtering
 * - Clusters: Event clusters grouped by topic
 * - Entities: Trending persons, organizations, locations
 * - Risk: Historical risk trends and analysis
 *
 * Note: Narrative analysis moved to /intelligence/narrative
 */
import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  TrendingUp,
  AlertCircle,
  Users,
  RefreshCw,
  Shield,
  Clock,
  BarChart3,
  Layers,
  Wrench,
} from 'lucide-react';

// Intelligence feature components
import { useIntelligenceOverview } from '@/features/intelligence/api/useIntelligenceOverview';
import { RiskScoreCard, CompactRiskBadge } from '@/features/intelligence/components/RiskScoreCard';
import { EventClustersPanel } from '@/features/intelligence/components/EventClustersPanel';
import { TrendingEntitiesWidget } from '@/features/intelligence/components/TrendingEntitiesWidget';
import { EventTimeline } from '@/features/intelligence/components/EventTimeline';
import { RiskHistoryChart } from '@/features/intelligence/components/RiskHistoryChart';
import { EventDetectionPanel } from '@/features/intelligence/components/EventDetectionPanel';
import { RiskCalculationPanel } from '@/features/intelligence/components/RiskCalculationPanel';
import { EscalationPanel } from '@/features/intelligence/components/EscalationPanel';
import { StatCard } from '@/components/shared/StatCard';

export function IntelligenceDashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<number>(7);

  // Intelligence API data
  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview,
  } = useIntelligenceOverview();

  // Refresh intelligence data
  const handleRefresh = () => {
    refetchOverview();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Intelligence Dashboard</h1>
          <p className="text-muted-foreground">
            Event monitoring, risk analysis, and narrative tracking
          </p>
        </div>
        <div className="flex gap-2">
          {/* Period Selector */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg bg-background text-foreground"
          >
            <option value={1}>Last 24h</option>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {overviewError && (
        <Card className="p-4 bg-destructive/10 border-destructive">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>Failed to load intelligence data. Please try again.</p>
          </div>
        </Card>
      )}

      {/* Escalation Panel - Intelligence Interpretation Layer */}
      <div className="mb-6">
        <EscalationPanel
          onClusterClick={(clusterId) => {
            // Navigate to cluster detail view
            window.location.href = `/intelligence/clusters/${clusterId}`;
          }}
        />
      </div>

      {/* Overview Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <RiskScoreCard
          score={overview?.global_risk_index ?? 0}
          label="Global Risk Index"
          isLoading={isLoadingOverview}
        />
        <StatCard
          title="Active Clusters"
          value={overview?.total_clusters ?? 0}
          icon={<Layers className="h-4 w-4" />}
          isLoading={isLoadingOverview}
        />
        <StatCard
          title="Events (7 days)"
          value={overview?.total_events ?? 0}
          icon={<Activity className="h-4 w-4" />}
          isLoading={isLoadingOverview}
        />
        <StatCard
          title="Top Regions"
          value={overview?.top_regions?.[0]?.name ?? '-'}
          icon={<TrendingUp className="h-4 w-4" />}
          change={overview?.top_regions?.[0] ? `${overview.top_regions[0].event_count} events` : undefined}
          isLoading={isLoadingOverview}
        />
      </div>

      {/* Risk Category Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RiskScoreCard
          score={overview?.geo_risk ?? 0}
          label="Geopolitical Risk"
          isLoading={isLoadingOverview}
        />
        <RiskScoreCard
          score={overview?.finance_risk ?? 0}
          label="Financial Risk"
          isLoading={isLoadingOverview}
        />
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex flex-wrap">
          <TabsTrigger value="overview" className="flex items-center gap-1">
            <Shield className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="events" className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            Events
          </TabsTrigger>
          <TabsTrigger value="clusters" className="flex items-center gap-1">
            <Layers className="h-4 w-4" />
            Clusters
          </TabsTrigger>
          <TabsTrigger value="entities" className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            Entities
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            Risk
          </TabsTrigger>
          <TabsTrigger value="tools" className="flex items-center gap-1">
            <Wrench className="h-4 w-4" />
            Tools
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Clusters */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Top Risk Clusters</h3>
              {isLoadingOverview ? (
                <div className="text-center py-8 text-muted-foreground">Loading...</div>
              ) : overview?.top_clusters && overview.top_clusters.length > 0 ? (
                <div className="space-y-3">
                  {overview.top_clusters.map((cluster) => (
                    <div
                      key={cluster.id}
                      className="p-3 border rounded-lg hover:bg-accent transition-colors"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium line-clamp-1">{cluster.name}</h4>
                        <CompactRiskBadge score={cluster.risk_score} size="sm" />
                      </div>
                      <div className="flex gap-3 text-sm text-muted-foreground">
                        <span>{cluster.event_count} events</span>
                        {cluster.category && (
                          <span className="capitalize">{cluster.category}</span>
                        )}
                      </div>
                      {cluster.keywords.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {cluster.keywords.slice(0, 3).map((keyword) => (
                            <span
                              key={keyword}
                              className="px-2 py-0.5 text-xs bg-secondary rounded-full"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No clusters available
                </div>
              )}
            </Card>

            {/* Top Regions */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Top Active Regions</h3>
              {isLoadingOverview ? (
                <div className="text-center py-8 text-muted-foreground">Loading...</div>
              ) : overview?.top_regions && overview.top_regions.length > 0 ? (
                <div className="space-y-3">
                  {overview.top_regions.map((region, idx) => (
                    <div
                      key={region.name}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-bold text-muted-foreground">
                          #{idx + 1}
                        </span>
                        <div>
                          <h4 className="font-medium">{region.name}</h4>
                          <p className="text-sm text-muted-foreground">
                            {region.event_count} events
                          </p>
                        </div>
                      </div>
                      <CompactRiskBadge score={region.risk_score} size="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No region data available
                </div>
              )}
            </Card>
          </div>

          {/* Quick Trending Entities */}
          <TrendingEntitiesWidget hours={4} limit={30} />
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <EventTimeline hours={24} limit={50} />
        </TabsContent>

        {/* Clusters Tab */}
        <TabsContent value="clusters" className="space-y-4">
          <EventClustersPanel sortBy="risk_score" />
        </TabsContent>

        {/* Entities Tab */}
        <TabsContent value="entities" className="space-y-4">
          <TrendingEntitiesWidget hours={24} limit={100} />
        </TabsContent>

        {/* Risk Tab */}
        <TabsContent value="risk" className="space-y-4">
          <RiskHistoryChart days={selectedPeriod} height={300} />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <RiskScoreCard
              score={overview?.global_risk_index ?? 0}
              label="Global Risk"
              isLoading={isLoadingOverview}
            />
            <RiskScoreCard
              score={overview?.geo_risk ?? 0}
              label="Geopolitical Risk"
              isLoading={isLoadingOverview}
            />
            <RiskScoreCard
              score={overview?.finance_risk ?? 0}
              label="Financial Risk"
              isLoading={isLoadingOverview}
            />
          </div>
        </TabsContent>

        {/* Tools Tab - Event Detection & Risk Calculation */}
        <TabsContent value="tools" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <EventDetectionPanel />
            <RiskCalculationPanel />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
