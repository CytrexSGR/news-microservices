import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Clock, AlertCircle } from 'lucide-react'
import { useSchedulingConflicts } from '@/features/admin/feed-service/hooks/useScheduling'
import { parseISO } from 'date-fns'

interface ConflictsCardProps {
  autoRefresh?: boolean
}

export function ConflictsCard({ autoRefresh = false }: ConflictsCardProps) {
  const { data, isLoading, error } = useSchedulingConflicts(autoRefresh ? 30000 : undefined)

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-muted-foreground">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm">Suche nach Konflikten...</p>
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

  const hasConflicts = data.conflicts_detected > 0

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Scheduling-Konflikte
          </h3>
          <p className="text-sm text-muted-foreground">
            Erkennung von Feed-Clustern zur gleichen Zeit
          </p>
        </div>

        {/* Status Banner */}
        <div
          className={`p-4 rounded-lg border ${
            hasConflicts
              ? 'bg-destructive/5 border-destructive/20'
              : 'bg-green-500/5 border-green-500/20'
          }`}
        >
          <div className="flex items-center gap-3">
            {hasConflicts ? (
              <AlertTriangle className="h-6 w-6 text-destructive flex-shrink-0" />
            ) : (
              <Clock className="h-6 w-6 text-green-600 flex-shrink-0" />
            )}
            <div>
              <div className={`font-semibold ${hasConflicts ? 'text-destructive' : 'text-green-600'}`}>
                {hasConflicts
                  ? `${data.conflicts_detected} Konflikt${data.conflicts_detected !== 1 ? 'e' : ''} erkannt`
                  : 'Keine Konflikte erkannt'}
              </div>
              <div className="text-sm text-muted-foreground">
                {hasConflicts
                  ? `${data.total_affected_feeds} Feeds betroffen`
                  : 'Feed-Verteilung ist optimal'}
              </div>
            </div>
          </div>
        </div>

        {/* Conflicts List */}
        {hasConflicts && data.clusters.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Erkannte Cluster</h4>
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {data.clusters.map((conflict, idx) => {
                const time = parseISO(conflict.time_window)

                return (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-destructive/20 bg-destructive/5"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-destructive" />
                        <span className="font-medium">
                          {time.toLocaleTimeString('de-DE', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <Badge variant="destructive">{conflict.feed_count} Feeds</Badge>
                    </div>

                    {/* Feed List */}
                    <div className="space-y-1 mt-2">
                      {conflict.feeds.map((feed) => (
                        <div
                          key={feed.id}
                          className="text-xs p-1.5 rounded bg-background/50 flex items-center justify-between"
                        >
                          <span className="truncate" title={feed.name}>
                            {feed.name}
                          </span>
                          <span className="text-muted-foreground ml-2">
                            {parseISO(feed.next_fetch_at).toLocaleTimeString('de-DE', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations && data.recommendations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Empfehlungen
            </h4>
            <div className="space-y-1.5">
              {data.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <span className="text-primary mt-0.5">•</span>
                  <span className="text-muted-foreground">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info when no conflicts */}
        {!hasConflicts && (
          <div className="p-3 rounded-lg bg-muted/50 border">
            <p className="text-sm text-muted-foreground">
              Alle Feeds sind gut verteilt. Die automatische Optimierung funktioniert korrekt.
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
