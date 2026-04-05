import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Activity, Search, Settings, Sliders, Shield, Clock, Globe } from 'lucide-react'

// Live Operations Components
import { ServiceHealthCard } from '@/features/admin/feed-service/components/live-operations/ServiceHealthCard'
import { SchedulerStatusCard } from '@/features/admin/feed-service/components/live-operations/SchedulerStatusCard'
import { FeedStatsCard } from '@/features/admin/feed-service/components/live-operations/FeedStatsCard'
import { QualityOverviewCard } from '@/features/admin/feed-service/components/live-operations/QualityOverviewCard'

// Feed Explorer Components
import { FeedListTable } from '@/features/admin/feed-service/components/feed-explorer/FeedListTable'
import { FeedHealthChart } from '@/features/admin/feed-service/components/feed-explorer/FeedHealthChart'
import { RecentItemsTable } from '@/features/admin/feed-service/components/feed-explorer/RecentItemsTable'
import { AssessmentHistorySection } from '@/features/admin/feed-service/components/feed-explorer/AssessmentHistorySection'

// Management Components
import { BulkFetchControl } from '@/features/admin/feed-service/components/management/BulkFetchControl'
import { CategoryManagement } from '@/features/admin/feed-service/components/management/CategoryManagement'
import { AnalysisToggles } from '@/features/admin/feed-service/components/management/AnalysisToggles'

// Scheduling Components
import {
  ScheduleTimelineCard,
  DistributionStatsCard,
  OptimizationControlCard,
  ConflictsCard,
} from '@/features/admin/feed-service/components/scheduling'

// Quality V2 Components
import {
  QualityOverviewCardV2,
  QualityComponentsChart,
  QualityDistributionChart,
  QualityRecommendations,
  QualityFeedListTable,
} from '@/features/admin/feed-service/components/quality-v2'

// Configuration Components
import { AdmiraltyCodeConfig } from '@/features/feeds/components/AdmiraltyCodeConfig'
import { CategoryWeightsConfig } from '@/features/feeds/components/CategoryWeightsConfig'

// Source Management Components
import {
  SourceList,
  SourceDetailPanel,
  CreateSourceDialog,
  AddFeedToSourceDialog,
} from '@/features/sources/components'
import type { Source } from '@/types/source'

// Hooks
import { useServiceHealth } from '@/features/admin/feed-service/hooks/useServiceHealth'
import { useFeedStats } from '@/features/admin/feed-service/hooks/useFeedStats'
import { useFeedList } from '@/features/admin/feed-service/hooks/useFeedList'
import { useRecentItems } from '@/features/admin/feed-service/hooks/useRecentItems'
import { useFeedQualityV2 } from '@/features/admin/feed-service/hooks/useFeedQualityV2'
import { useFeedQualityOverview } from '@/features/admin/feed-service/hooks/useFeedQualityOverview'

export function FeedServiceAdminPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') || 'operations'
  const [activeTab, setActiveTab] = useState(tabParam)
  const [selectedFeedId, setSelectedFeedId] = useState<string>('')

  // Source Management State
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)
  const [showCreateSourceDialog, setShowCreateSourceDialog] = useState(false)
  const [showAddFeedDialog, setShowAddFeedDialog] = useState(false)
  const [sourceForFeed, setSourceForFeed] = useState<Source | null>(null)

  // Sync activeTab with URL parameter
  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab && tab !== activeTab) {
      setActiveTab(tab)
    }
  }, [searchParams, activeTab])

  // Handle tab changes - update both state and URL
  const handleTabChange = (newTab: string) => {
    setActiveTab(newTab)
    setSearchParams({ tab: newTab })
  }

  // Debug: Log when selectedFeedId changes
  console.log('🟢 Current selectedFeedId:', selectedFeedId)

  // Live Operations data (auto-refresh every 10s)
  const { data: serviceHealth, isLoading: healthLoading, error: healthError } = useServiceHealth(10000)
  const { data: feedStats, isLoading: statsLoading, error: statsError } = useFeedStats(10000)

  // Feed Explorer data
  const { data: feedList, isLoading: feedsLoading } = useFeedList({ limit: 1000 })
  const { data: recentItems, isLoading: itemsLoading } = useRecentItems(20)

  // Quality V2 data
  const {
    data: qualityV2,
    isLoading: qualityLoading,
    error: qualityError,
  } = useFeedQualityV2(selectedFeedId, 30, !!selectedFeedId)

  // Debug: Log quality data state
  console.log('🟣 Quality V2 State:', {
    selectedFeedId,
    qualityLoading,
    qualityError: qualityError?.message,
    hasQualityData: !!qualityV2,
  })

  // Quality V2 Overview data
  const {
    data: qualityOverview,
    isLoading: overviewLoading,
    error: overviewError,
  } = useFeedQualityOverview()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Feed Service</h1>
        <p className="text-muted-foreground">
          Monitor service health, manage feeds, and control bulk operations
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations" className="gap-2">
            <Activity className="h-4 w-4" />
            Live Operations
          </TabsTrigger>
          <TabsTrigger value="sources" className="gap-2">
            <Globe className="h-4 w-4" />
            Sources
          </TabsTrigger>
          <TabsTrigger value="explorer" className="gap-2">
            <Search className="h-4 w-4" />
            Feed Explorer
          </TabsTrigger>
          <TabsTrigger value="quality" className="gap-2">
            <Shield className="h-4 w-4" />
            Quality V2
          </TabsTrigger>
          <TabsTrigger value="scheduling" className="gap-2">
            <Clock className="h-4 w-4" />
            Scheduling
          </TabsTrigger>
          <TabsTrigger value="management" className="gap-2">
            <Settings className="h-4 w-4" />
            Management & Controls
          </TabsTrigger>
          <TabsTrigger value="configuration" className="gap-2">
            <Sliders className="h-4 w-4" />
            Configuration
          </TabsTrigger>
        </TabsList>

        {/* Live Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          {healthLoading && (
            <div className="text-center py-8 text-muted-foreground">
              Loading service health...
            </div>
          )}

          {healthError && (
            <div className="text-center py-8 text-destructive">
              Failed to load service health: {healthError.message}
            </div>
          )}

          {serviceHealth && feedStats && (
            <div className="grid gap-4 md:grid-cols-2">
              <ServiceHealthCard health={serviceHealth} />
              <SchedulerStatusCard health={serviceHealth} />
              <FeedStatsCard stats={feedStats} />
              <QualityOverviewCard stats={feedStats} />
            </div>
          )}

          {statsError && !statsLoading && (
            <div className="text-center py-4 text-destructive">
              Failed to load feed stats: {statsError.message}
            </div>
          )}
        </TabsContent>

        {/* Sources Tab */}
        <TabsContent value="sources" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className={selectedSource ? 'lg:col-span-2' : 'lg:col-span-3'}>
              <SourceList
                onSourceSelect={(source) => setSelectedSource(source)}
                onCreateSource={() => setShowCreateSourceDialog(true)}
                onEditSource={(source) => setSelectedSource(source)}
                onAssessSource={(source) => setSelectedSource(source)}
                onManageFeeds={(source) => {
                  setSourceForFeed(source)
                  setShowAddFeedDialog(true)
                }}
              />
            </div>
            {selectedSource && (
              <div className="lg:col-span-1">
                <SourceDetailPanel
                  sourceId={selectedSource.id}
                  onClose={() => setSelectedSource(null)}
                  onEdit={(source) => setSelectedSource(source)}
                  onAddFeed={(source) => {
                    setSourceForFeed(source)
                    setShowAddFeedDialog(true)
                  }}
                />
              </div>
            )}
          </div>

          {/* Source Dialogs */}
          <CreateSourceDialog
            open={showCreateSourceDialog}
            onOpenChange={setShowCreateSourceDialog}
            onSuccess={(sourceId) => {
              console.log('Created source:', sourceId)
              // Optionally select the new source
            }}
          />
          <AddFeedToSourceDialog
            open={showAddFeedDialog}
            onOpenChange={setShowAddFeedDialog}
            source={sourceForFeed}
            onSuccess={() => {
              console.log('Feed added successfully')
            }}
          />
        </TabsContent>

        {/* Feed Explorer Tab */}
        <TabsContent value="explorer" className="space-y-4">
          {feedsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading feed data...
            </div>
          ) : feedList && feedList.feeds ? (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <FeedListTable feeds={feedList.feeds} />
                </div>
                <FeedHealthChart feeds={feedList.feeds} />
                <div>
                  {itemsLoading ? (
                    <div className="text-center py-8 text-muted-foreground">
                      Loading recent items...
                    </div>
                  ) : recentItems ? (
                    <RecentItemsTable items={recentItems.items} />
                  ) : null}
                </div>
              </div>
              <AssessmentHistorySection feeds={feedList.feeds} />
            </>
          ) : (
            <div className="text-center py-8 text-destructive">
              Failed to load feed data
            </div>
          )}
        </TabsContent>

        {/* Quality V2 Tab */}
        <TabsContent value="quality" className="space-y-4">
          <div className="space-y-4">
            {/* Section 1: Feed Quality Overview Table */}
            {overviewLoading ? (
              <div className="text-center py-12 text-muted-foreground">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-sm">Loading feed quality overview...</p>
              </div>
            ) : overviewError ? (
              <div className="text-center py-12 text-destructive">
                <p className="text-sm">Failed to load quality overview</p>
                <p className="text-xs mt-1">{overviewError.message}</p>
              </div>
            ) : qualityOverview ? (
              <QualityFeedListTable
                feeds={qualityOverview}
                onFeedSelect={setSelectedFeedId}
                selectedFeedId={selectedFeedId}
              />
            ) : null}

            {/* Section 2: Detailed Quality View (shown when feed selected) */}
            {selectedFeedId && (
              <div className="space-y-4">
                {console.log('🔴 Rendering detail section, qualityLoading:', qualityLoading, 'qualityV2:', !!qualityV2)}
                {qualityLoading ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-sm">Loading detailed quality metrics...</p>
                  </div>
                ) : qualityError ? (
                  <div className="text-center py-12 text-destructive">
                    <p className="text-sm">Failed to load quality data</p>
                    <p className="text-xs mt-1">{qualityError.message}</p>
                  </div>
                ) : qualityV2 ? (
                  <>
                    {/* Overview and Components Row */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <QualityOverviewCardV2 quality={qualityV2} />
                      <QualityComponentsChart
                        componentScores={qualityV2.component_scores}
                        feedName={qualityV2.feed_name}
                      />
                    </div>

                    {/* Distribution and Recommendations Row */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <QualityDistributionChart quality={qualityV2} />
                      <QualityRecommendations quality={qualityV2} />
                    </div>
                  </>
                ) : null}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Scheduling Tab */}
        <TabsContent value="scheduling" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <ScheduleTimelineCard hours={24} autoRefresh={true} />
            <DistributionStatsCard autoRefresh={true} />
            <OptimizationControlCard />
            <ConflictsCard autoRefresh={true} />
          </div>
        </TabsContent>

        {/* Management & Controls Tab */}
        <TabsContent value="management" className="space-y-4">
          {feedsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading feed data...
            </div>
          ) : feedList && feedList.feeds ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <BulkFetchControl feeds={feedList.feeds} />
              </div>
              <CategoryManagement feeds={feedList.feeds} />
              <AnalysisToggles feeds={feedList.feeds} />
            </div>
          ) : (
            <div className="text-center py-8 text-destructive">
              Failed to load feed data
            </div>
          )}
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <AdmiraltyCodeConfig />
            <CategoryWeightsConfig />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
