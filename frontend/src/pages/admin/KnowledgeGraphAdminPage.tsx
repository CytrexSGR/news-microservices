import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Activity, BarChart3, Network, Sparkles, GitMerge, TrendingUp } from 'lucide-react'

// Live Operations Components
import { ServiceHealthCard } from '@/features/admin/knowledge-graph/components/live-operations/ServiceHealthCard'
import { GraphStatsCard } from '@/features/admin/knowledge-graph/components/live-operations/GraphStatsCard'
import { Neo4jHealthCard } from '@/features/admin/knowledge-graph/components/live-operations/Neo4jHealthCard'
import { RabbitMQHealthCard } from '@/features/admin/knowledge-graph/components/live-operations/RabbitMQHealthCard'

// Analytics Components (Phase 2)
import { TopEntitiesCard } from '@/features/admin/knowledge-graph/components/analytics/TopEntitiesCard'
import { GrowthHistoryChart } from '@/features/admin/knowledge-graph/components/analytics/GrowthHistoryChart'
import { RelationshipStatsCard } from '@/features/admin/knowledge-graph/components/analytics/RelationshipStatsCard'
import { CanonicalizationStatsCard } from '@/features/admin/knowledge-graph/components/analytics/CanonicalizationStatsCard'
import { EntityMergeHistory } from '@/features/admin/knowledge-graph/components/analytics/EntityMergeHistory'
import { DisambiguationQuality } from '@/features/admin/knowledge-graph/components/analytics/DisambiguationQuality'
import { EntityTypeTrends } from '@/features/admin/knowledge-graph/components/analytics/EntityTypeTrends'
import { CrossArticleCoverage } from '@/features/admin/knowledge-graph/components/analytics/CrossArticleCoverage'
import { BatchReprocessing } from '@/features/admin/knowledge-graph/components/analytics/BatchReprocessing'
import { DataQualityCard } from '@/features/admin/knowledge-graph/components/analytics/DataQualityCard'
import { NotApplicableTrendCard } from '@/features/admin/knowledge-graph/components/analytics/NotApplicableTrendCard'
import { RelationshipQualityBreakdown } from '@/features/admin/knowledge-graph/components/analytics/RelationshipQualityBreakdown'

// Enrichment Components (Phase 2)
import { EnrichmentDashboard } from '@/features/admin/knowledge-graph/components/enrichment/EnrichmentDashboard'

// Hooks
import { useServiceHealth } from '@/features/admin/knowledge-graph/hooks/useServiceHealth'
import { useBasicHealth } from '@/features/admin/knowledge-graph/hooks/useBasicHealth'
import { useNeo4jHealth } from '@/features/admin/knowledge-graph/hooks/useNeo4jHealth'
import { useRabbitMQHealth } from '@/features/admin/knowledge-graph/hooks/useRabbitMQHealth'
import { useGraphStats } from '@/features/admin/knowledge-graph/hooks/useGraphStats'
import { useTopEntities } from '@/features/admin/knowledge-graph/hooks/useTopEntities'
import { useGrowthHistory } from '@/features/admin/knowledge-graph/hooks/useGrowthHistory'
import { useRelationshipStats } from '@/features/admin/knowledge-graph/hooks/useRelationshipStats'
import { useCanonicalizationStats } from '@/features/admin/knowledge-graph/hooks/useCanonicalizationStats'
import { useCrossArticleCoverage } from '@/features/admin/knowledge-graph/hooks/useCrossArticleCoverage'

export function KnowledgeGraphAdminPage() {
  const [activeTab, setActiveTab] = useState('operations')
  const [statisticsSubTab, setStatisticsSubTab] = useState('graph-metrics')
  const [selectedEntityType, setSelectedEntityType] = useState<string | undefined>(undefined)

  // Live Operations data (auto-refresh every 10s)
  const { data: serviceHealth, isLoading: serviceHealthLoading, error: serviceHealthError } = useServiceHealth(10000)
  const { data: basicHealth, isLoading: basicHealthLoading } = useBasicHealth(10000)
  const { data: neo4jHealth, isLoading: neo4jHealthLoading } = useNeo4jHealth(10000)
  const { data: rabbitmqHealth, isLoading: rabbitmqHealthLoading } = useRabbitMQHealth(10000)

  // Graph Statistics data (auto-refresh every 30s)
  const { data: graphStats, isLoading: graphStatsLoading, error: graphStatsError } = useGraphStats(30000)

  // Analytics data (auto-refresh every 60s for Phase 2)
  const { data: topEntities, isLoading: topEntitiesLoading } = useTopEntities(10, selectedEntityType, 60000)
  const { data: growthHistory, isLoading: growthHistoryLoading } = useGrowthHistory(30, 60000)
  const { data: relationshipStats, isLoading: relationshipStatsLoading } = useRelationshipStats(60000)
  const { data: canonStats, isLoading: canonStatsLoading } = useCanonicalizationStats(60000)
  const { data: crossArticleCoverage, isLoading: crossArticleCoverageLoading } = useCrossArticleCoverage(10, 60000)

  // Extract available entity types from graph stats
  const availableEntityTypes = graphStats?.entity_types
    ? Object.keys(graphStats.entity_types).sort()
    : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Knowledge Graph Service</h1>
        <p className="text-muted-foreground">
          Monitor service health, explore graph statistics, and query entity connections
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations" className="gap-2">
            <Activity className="h-4 w-4" />
            Live Operations
          </TabsTrigger>
          <TabsTrigger value="statistics" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Statistics & Analytics
          </TabsTrigger>
          <TabsTrigger value="enrichment" className="gap-2">
            <Sparkles className="h-4 w-4" />
            Manual Enrichment
          </TabsTrigger>
          <TabsTrigger value="explorer" className="gap-2" disabled>
            <Network className="h-4 w-4" />
            Graph Explorer (Phase 3)
          </TabsTrigger>
        </TabsList>

        {/* Live Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          {serviceHealthError && (
            <div className="text-center py-8 text-destructive">
              Failed to load service health: {serviceHealthError.message}
            </div>
          )}

          {graphStatsError && (
            <div className="text-center py-8 text-destructive">
              Failed to load graph statistics: {graphStatsError.message}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <ServiceHealthCard
              health={serviceHealth || null}
              basicHealth={basicHealth || null}
              isLoading={serviceHealthLoading || basicHealthLoading}
            />
            <GraphStatsCard
              stats={graphStats || null}
              isLoading={graphStatsLoading}
            />
            <Neo4jHealthCard
              health={neo4jHealth || null}
              isLoading={neo4jHealthLoading}
            />
            <RabbitMQHealthCard
              health={rabbitmqHealth || null}
              isLoading={rabbitmqHealthLoading}
            />
          </div>
        </TabsContent>

        {/* Statistics & Analytics Tab (Phase 2) */}
        <TabsContent value="statistics" className="space-y-4">
          {/* Sub-Navigation */}
          <Tabs value={statisticsSubTab} onValueChange={setStatisticsSubTab} className="space-y-4">
            <TabsList>
              <TabsTrigger value="graph-metrics" className="gap-2">
                <Network className="h-4 w-4" />
                Graph Metrics
              </TabsTrigger>
              <TabsTrigger value="canonicalization" className="gap-2">
                <GitMerge className="h-4 w-4" />
                Canonicalization
              </TabsTrigger>
              <TabsTrigger value="trends" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                Trends
              </TabsTrigger>
            </TabsList>

            {/* Graph Metrics Sub-Tab */}
            <TabsContent value="graph-metrics" className="space-y-4">
              {/* Data Quality Score - Full Width, Prominent Position */}
              <DataQualityCard />

              {/* Relationship Quality Breakdown - Phase 3.3 - Full Width */}
              <RelationshipQualityBreakdown />

              <div className="grid gap-4 md:grid-cols-2">
                {/* Graph Overview Stats */}
                <GraphStatsCard
                  stats={graphStats || null}
                  isLoading={graphStatsLoading}
                />

                {/* Top Entities */}
                <TopEntitiesCard
                  entities={topEntities || null}
                  isLoading={topEntitiesLoading}
                  availableEntityTypes={availableEntityTypes}
                  selectedEntityType={selectedEntityType}
                  onEntityTypeChange={setSelectedEntityType}
                />

                {/* Relationship Statistics - Full Width */}
                <div className="md:col-span-2">
                  <RelationshipStatsCard
                    stats={relationshipStats || null}
                    isLoading={relationshipStatsLoading}
                  />
                </div>
              </div>
            </TabsContent>

            {/* Canonicalization Sub-Tab */}
            <TabsContent value="canonicalization" className="space-y-4">
              <div className="grid gap-4">
                {/* Batch Reprocessing - Action Card */}
                <BatchReprocessing />

                {/* Canonicalization Statistics - Full Width */}
                <CanonicalizationStatsCard
                  stats={canonStats || null}
                  isLoading={canonStatsLoading}
                />

                {/* Entity Merge History - Now connected to real backend! */}
                <EntityMergeHistory />

                {/* Disambiguation Quality - Now connected to real backend! */}
                <DisambiguationQuality />
              </div>
            </TabsContent>

            {/* Trends Sub-Tab */}
            <TabsContent value="trends" className="space-y-4">
              <div className="grid gap-4">
                {/* Growth History Chart - Full Width */}
                <GrowthHistoryChart
                  data={growthHistory || null}
                  isLoading={growthHistoryLoading}
                  days={30}
                />

                {/* NOT_APPLICABLE Trend Tracking - Phase 3.2 */}
                <NotApplicableTrendCard />

                {/* Entity Type Trends */}
                <EntityTypeTrends days={30} />

                {/* Cross-Article Coverage */}
                <CrossArticleCoverage
                  stats={crossArticleCoverage || null}
                  isLoading={crossArticleCoverageLoading}
                />
              </div>
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* Manual Enrichment Tab (Phase 2) */}
        <TabsContent value="enrichment" className="space-y-4">
          <EnrichmentDashboard />
        </TabsContent>

        {/* Graph Explorer Tab (Phase 3) */}
        <TabsContent value="explorer" className="space-y-4">
          <div className="text-center py-8 text-muted-foreground">
            Graph Explorer will be implemented in Phase 3
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
