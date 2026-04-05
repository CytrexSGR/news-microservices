import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Database, TrendingUp } from 'lucide-react'
import type { IndexStatistics } from '@/types/searchServiceAdmin'

interface IndexStatsCardProps {
  stats: IndexStatistics
}

export function IndexStatsCard({ stats }: IndexStatsCardProps) {
  const getSentimentColor = (sentiment: string): 'default' | 'destructive' | 'secondary' => {
    const sentimentLower = sentiment.toLowerCase()
    if (sentimentLower === 'positive') return 'default'
    if (sentimentLower === 'negative') return 'destructive'
    return 'secondary'
  }

  const topSources = (stats.by_source || []).slice(0, 5)
  const maxSourceCount = topSources[0]?.count || 1

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Database className="h-5 w-5" />
        Index Statistics
      </h3>

      <div className="space-y-4">
        {/* Total Indexed - Prominent Display */}
        <div className="flex items-center justify-between p-4 rounded-lg border-2 border-primary/20 bg-primary/5">
          <div>
            <div className="text-2xl font-bold">{(stats?.total_indexed ?? 0).toLocaleString()}</div>
            <div className="text-sm text-muted-foreground">Total Articles Indexed</div>
          </div>
          <Database className="h-8 w-8 text-primary" />
        </div>

        {/* Index Size - Secondary Metric */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="font-medium">Index Size</div>
          <div className="text-sm font-mono">{stats?.index_size ?? 'Unknown'}</div>
        </div>

        {/* Recent 24h with Trend */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <div className="font-medium">Last 24 Hours</div>
          </div>
          <div className="text-sm font-semibold text-green-600">
            +{(stats?.recent_24h ?? 0).toLocaleString()}
          </div>
        </div>

        {/* Top 5 Sources */}
        <div className="pt-3 border-t">
          <div className="text-sm font-medium mb-3">Top Sources</div>
          <div className="space-y-2">
            {topSources.map((source, index) => {
              const percentage = (source.count / maxSourceCount) * 100
              return (
                <div key={source.source} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="truncate max-w-[200px]" title={source.source}>
                      {index + 1}. {source.source}
                    </span>
                    <span className="font-medium">{source.count.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Sentiment Distribution */}
        <div className="pt-3 border-t">
          <div className="text-sm font-medium mb-3">Sentiment Distribution</div>
          <div className="flex flex-wrap gap-2">
            {(stats.by_sentiment || []).map((sentiment) => (
              <Badge
                key={sentiment.sentiment}
                variant={getSentimentColor(sentiment.sentiment)}
                className="text-xs"
              >
                {sentiment.sentiment}: {sentiment.count.toLocaleString()}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
