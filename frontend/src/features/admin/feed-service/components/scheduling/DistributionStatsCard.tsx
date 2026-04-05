import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { BarChart3, AlertCircle, CheckCircle2, TrendingUp } from 'lucide-react'
import { useDistributionStats } from '@/features/admin/feed-service/hooks/useScheduling'

interface DistributionStatsCardProps {
  autoRefresh?: boolean
}

export function DistributionStatsCard({ autoRefresh = false }: DistributionStatsCardProps) {
  const { data, isLoading, error } = useDistributionStats(autoRefresh ? 30000 : undefined)

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-muted-foreground">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm">Lade Verteilungsstatistiken...</p>
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

  // Determine quality status based on distribution score
  const getQualityStatus = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', icon: CheckCircle2, label: 'Exzellent' }
    if (score >= 60) return { color: 'text-blue-600', icon: TrendingUp, label: 'Gut' }
    if (score >= 40) return { color: 'text-yellow-600', icon: AlertCircle, label: 'Akzeptabel' }
    return { color: 'text-destructive', icon: AlertCircle, label: 'Schlecht' }
  }

  const qualityStatus = getQualityStatus(data.distribution_score)
  const QualityIcon = qualityStatus.icon

  // Get progress bar color
  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-600'
    if (score >= 60) return 'bg-blue-600'
    if (score >= 40) return 'bg-yellow-600'
    return 'bg-destructive'
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Verteilungs-Qualität
          </h3>
          <p className="text-sm text-muted-foreground">Aktuelle Zeitplan-Effizienz</p>
        </div>

        {/* Distribution Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Verteilungs-Score</span>
            <div className="flex items-center gap-2">
              <QualityIcon className={`h-4 w-4 ${qualityStatus.color}`} />
              <span className={`text-sm font-semibold ${qualityStatus.color}`}>
                {qualityStatus.label}
              </span>
            </div>
          </div>
          <div className="relative h-3 bg-secondary rounded-full overflow-hidden">
            <div
              className={`h-full ${getProgressColor(data.distribution_score)} transition-all duration-500`}
              style={{ width: `${data.distribution_score}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0</span>
            <span className="font-semibold">{data.distribution_score.toFixed(1)}/100</span>
            <span>100</span>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Aktive Feeds</div>
            <div className="text-xl font-bold">{data.total_active_feeds || 0}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Max Gleichzeitig</div>
            <div className="text-xl font-bold">{data.max_concurrent_feeds || 0}</div>
          </div>
          {data.avg_feeds_per_slot !== undefined && (
            <div className="p-3 rounded-lg border bg-card col-span-2">
              <div className="text-xs text-muted-foreground mb-1">Ø Feeds pro Zeitfenster</div>
              <div className="text-xl font-bold">{data.avg_feeds_per_slot.toFixed(2)}</div>
            </div>
          )}
        </div>

        {/* Interval Distribution */}
        {data.intervals && Object.keys(data.intervals).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Verteilung nach Intervall</h4>
            <div className="space-y-1.5">
              {Object.entries(data.intervals)
                .sort(([a], [b]) => parseInt(a) - parseInt(b))
                .map(([interval, stats]) => (
                  <div key={interval} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{interval} min</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {stats.count} Feeds
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Ø {stats.avg_concurrent.toFixed(1)} gleichzeitig
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Recommendation */}
        {data.recommendation && (
          <div className="p-3 rounded-lg bg-muted/50 border">
            <p className="text-sm">
              <strong className="text-foreground">Empfehlung:</strong>{' '}
              <span className="text-muted-foreground">{data.recommendation}</span>
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
