import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Activity, TrendingUp } from 'lucide-react'

// Live Operations Components
import { IndexStatsCard } from '@/features/admin/search-service/components/cards/IndexStatsCard'
import { CacheStatsCard } from '@/features/admin/search-service/components/cards/CacheStatsCard'
import { CeleryStatsCard } from '@/features/admin/search-service/components/cards/CeleryStatsCard'

// Query Statistics Components
import { QueryPerformanceCard } from '@/features/admin/search-service/components/performance/QueryPerformanceCard'
import { TopQueriesTable } from '@/features/admin/search-service/components/performance/TopQueriesTable'

// Hooks
import { useIndexStats } from '@/features/admin/search-service/hooks/useIndexStats'
import { useCacheStats } from '@/features/admin/search-service/hooks/useCacheStats'
import { useCeleryStats } from '@/features/admin/search-service/hooks/useCeleryStats'
import { useQueryStats } from '@/features/admin/search-service/hooks/useQueryStats'
import { usePerformanceStats } from '@/features/admin/search-service/hooks/usePerformanceStats'

export function SearchServiceAdminPage() {
  const [activeTab, setActiveTab] = useState('operations')

  // Live Operations data (auto-refresh every 10s)
  const { data: indexStats, isLoading: indexLoading, error: indexError } = useIndexStats(10000)
  const { data: cacheStats, isLoading: cacheLoading, error: cacheError } = useCacheStats(10000)
  const { data: celeryStats, isLoading: celeryLoading, error: celeryError } = useCeleryStats(10000)

  // Query Statistics data (auto-refresh every 30s for less frequent updates)
  const { data: queryStats, isLoading: queryLoading, error: queryError } = useQueryStats(30000)
  const { data: performanceStats, isLoading: perfLoading, error: perfError } = usePerformanceStats(30000)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search Service</h1>
        <p className="text-muted-foreground">
          Monitor search index, cache performance, query statistics, and worker health
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations" className="gap-2">
            <Activity className="h-4 w-4" />
            Live Operations
          </TabsTrigger>
          <TabsTrigger value="queries" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Query Statistics
          </TabsTrigger>
        </TabsList>

        {/* Live Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Index Stats - independent loading */}
            {indexLoading ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-muted-foreground">Loading index stats...</p>
              </div>
            ) : indexError ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-destructive">Index stats error: {indexError.message}</p>
              </div>
            ) : indexStats ? (
              <IndexStatsCard stats={indexStats} />
            ) : null}

            {/* Cache Stats - independent loading */}
            {cacheLoading ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-muted-foreground">Loading cache stats...</p>
              </div>
            ) : cacheError ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-destructive">Cache stats error: {cacheError.message}</p>
              </div>
            ) : cacheStats ? (
              <CacheStatsCard stats={cacheStats} />
            ) : null}

            {/* Celery Stats - independent loading */}
            {celeryLoading ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-muted-foreground">Loading worker stats...</p>
              </div>
            ) : celeryError ? (
              <div className="rounded-lg border bg-card p-6">
                <p className="text-destructive">Worker stats error: {celeryError.message}</p>
              </div>
            ) : celeryStats ? (
              <CeleryStatsCard stats={celeryStats} />
            ) : null}
          </div>
        </TabsContent>

        {/* Query Statistics Tab */}
        <TabsContent value="queries" className="space-y-4">
          {(queryLoading || perfLoading) ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading query statistics...
            </div>
          ) : (queryError || perfError) ? (
            <div className="text-center py-8 text-destructive">
              Failed to load query statistics: {(queryError || perfError)?.message}
            </div>
          ) : queryStats && performanceStats ? (
            <div className="grid gap-4 md:grid-cols-2">
              <QueryPerformanceCard stats={performanceStats} />
              <TopQueriesTable queries={queryStats.top_queries} />
            </div>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  )
}
