import { Users, FileText, TrendingUp, Activity } from 'lucide-react'
import { StatCard } from '@/components/shared/StatCard'
import { TimeSeriesChart } from '@/components/shared/TimeSeriesChart'
import { useOverviewMetrics } from '@/features/overview/api/getOverviewMetrics'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

export function HomePage() {
  const { data, isLoading, isError, error } = useOverviewMetrics()

  if (isError) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Dashboard Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'An unknown error occurred.'}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Please check if the Analytics service is running.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">System Overview</h2>
        <p className="text-muted-foreground">
          Live metrics and analytics from your news system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Users"
          value={data?.total_users ?? 0}
          icon={<Users className="h-4 w-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Active Feeds"
          value={data?.active_feeds ?? 0}
          icon={<Activity className="h-4 w-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Total Articles"
          value={data?.total_articles ?? 0}
          icon={<FileText className="h-4 w-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Articles Today"
          value={data?.articles_today ?? 0}
          icon={<TrendingUp className="h-4 w-4" />}
          isLoading={isLoading}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        <TimeSeriesChart
          title="Articles per Day"
          data={data?.articles_by_day ?? []}
          dataKey="count"
          xAxisKey="date"
          isLoading={isLoading}
        />

        <Card>
          <CardHeader>
            <CardTitle>Top Sources</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-8 w-full animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {data?.top_sources?.slice(0, 5).map((source, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{source.source}</span>
                    <span className="text-sm text-muted-foreground">{source.count} articles</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
