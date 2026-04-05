import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Rss, FileText, TrendingUp, TrendingDown } from 'lucide-react'
import type { FeedStats } from '@/types/feedServiceAdmin'

interface FeedStatsCardProps {
  stats: FeedStats
}

export function FeedStatsCard({ stats }: FeedStatsCardProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Rss className="h-5 w-5" />
        Feed Statistics
      </h3>

      <div className="mb-4">
        {/* Active Feeds */}
        <div className="p-4 rounded-lg border bg-primary/5">
          <div className="text-sm text-muted-foreground mb-1">Active Feeds</div>
          <div className="text-3xl font-bold">{stats.active_feeds}</div>
          <div className="text-xs text-muted-foreground mt-1">
            currently fetching
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {/* Total Articles */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Total Articles</div>
              <div className="text-sm text-muted-foreground">
                All time
              </div>
            </div>
          </div>
          <Badge variant="outline" className="text-lg font-semibold">
            {stats.total_articles.toLocaleString()}
          </Badge>
        </div>

        {/* Articles Today */}
        <div className="flex items-center justify-between p-3 rounded-lg border bg-primary/5">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-4 w-4 text-primary" />
            <div>
              <div className="font-medium">Articles Today</div>
              <div className="text-sm text-muted-foreground">
                Last 24 hours
              </div>
            </div>
          </div>
          <Badge className="text-lg font-semibold">
            {stats.articles_today.toLocaleString()}
          </Badge>
        </div>

        {/* 7-Day Trend */}
        {stats.articles_by_day && stats.articles_by_day.length > 1 && (
          <div className="p-3 rounded-lg border">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
              <div className="font-medium">7-Day Trend</div>
            </div>
            <div className="flex items-end gap-1 h-12">
              {stats.articles_by_day.slice(0, 7).map((day, i) => {
                const maxCount = Math.max(...stats.articles_by_day.map(d => d.count))
                const height = maxCount > 0 ? (day.count / maxCount) * 100 : 0
                return (
                  <div
                    key={i}
                    className="flex-1 bg-primary/20 rounded-t hover:bg-primary/40 transition-colors"
                    style={{ height: `${height}%` }}
                    title={`${day.date}: ${day.count} articles`}
                  />
                )
              })}
            </div>
            <div className="text-xs text-muted-foreground mt-1 text-center">
              Last 7 days
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
