import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp } from 'lucide-react'
import type { FeedStats } from '@/types/feedServiceAdmin'

interface QualityOverviewCardProps {
  stats: FeedStats
}

export function QualityOverviewCard({ stats }: QualityOverviewCardProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5" />
        Top Sources by Articles
      </h3>

      <div className="space-y-4">
        {/* Top Sources */}
        {stats.top_sources && stats.top_sources.length > 0 ? (
          <div className="space-y-1.5">
            {stats.top_sources.map((source, i) => (
              <div
                key={source.source}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                    #{i + 1}
                  </div>
                  <span className="text-sm font-medium truncate">{source.source}</span>
                </div>
                <Badge variant="outline" className="text-xs">
                  {source.count.toLocaleString()} articles
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No source data available</p>
          </div>
        )}
      </div>
    </Card>
  )
}
