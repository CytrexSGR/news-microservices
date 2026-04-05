import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { useScheduleTimeline } from '@/features/admin/feed-service/hooks/useScheduling'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { de } from 'date-fns/locale'

interface ScheduleTimelineCardProps {
  hours?: number
  autoRefresh?: boolean
}

export function ScheduleTimelineCard({ hours = 24, autoRefresh = false }: ScheduleTimelineCardProps) {
  const { data, isLoading, error } = useScheduleTimeline(hours, autoRefresh ? 30000 : undefined)

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-muted-foreground">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm">Lade Zeitplan...</p>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-destructive">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">Fehler beim Laden: {error.message}</p>
        </div>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  // Convert timeline object to sorted array
  const timelineSlots = Object.entries(data.timeline)
    .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
    .slice(0, 20) // Show only next 20 slots for performance

  // Get color based on feed count in slot
  const getSlotColor = (count: number) => {
    if (count >= 7) return 'bg-destructive/10 border-destructive'
    if (count >= 5) return 'bg-orange-500/10 border-orange-500'
    if (count >= 3) return 'bg-yellow-500/10 border-yellow-500'
    return 'bg-primary/10 border-primary'
  }

  const getSlotIcon = (count: number) => {
    if (count >= 7) return <AlertCircle className="h-4 w-4 text-destructive" />
    if (count >= 5) return <TrendingUp className="h-4 w-4 text-orange-500" />
    return <Clock className="h-4 w-4 text-primary" />
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Zeitplan-Übersicht
          </h3>
          <p className="text-sm text-muted-foreground">
            Nächste {hours} Stunden • {data.total_feeds} Feeds geplant
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border bg-card text-center">
            <div className="text-sm text-muted-foreground mb-1">Gesamt</div>
            <div className="text-2xl font-bold">{data.total_feeds}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card text-center">
            <div className="text-sm text-muted-foreground mb-1">Max Gleichzeitig</div>
            <div className="text-2xl font-bold">{data.max_concurrent_feeds}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card text-center">
            <div className="text-sm text-muted-foreground mb-1">Ø pro Slot</div>
            <div className="text-2xl font-bold">{data.avg_feeds_per_slot}</div>
          </div>
        </div>

        {/* Timeline Slots */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {timelineSlots.map(([timestamp, feeds]) => {
            const time = parseISO(timestamp)
            const feedCount = feeds.length

            return (
              <div
                key={timestamp}
                className={`p-3 rounded-lg border ${getSlotColor(feedCount)} transition-colors`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getSlotIcon(feedCount)}
                    <span className="font-medium">
                      {time.toLocaleTimeString('de-DE', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({formatDistanceToNow(time, { addSuffix: true, locale: de })})
                    </span>
                  </div>
                  <Badge variant={feedCount >= 7 ? 'destructive' : 'secondary'}>
                    {feedCount} Feed{feedCount !== 1 ? 's' : ''}
                  </Badge>
                </div>

                {/* Feed List */}
                <div className="grid grid-cols-2 gap-1 mt-2">
                  {feeds.map((feed) => (
                    <div
                      key={feed.id}
                      className="text-xs p-1.5 rounded bg-background/50 truncate"
                      title={feed.name}
                    >
                      {feed.name}
                      <span className="text-muted-foreground ml-1">
                        ({feed.fetch_interval}min)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer Info */}
        {timelineSlots.length >= 20 && (
          <p className="text-xs text-muted-foreground text-center">
            Zeige nur die ersten 20 Zeitfenster
          </p>
        )}
      </div>
    </Card>
  )
}
