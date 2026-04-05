import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { Decision } from '../../hooks/useAgentControl'

interface DecisionLogProps {
  decisions: Decision[] | undefined
  isLoading: boolean
}

const decisionColors: Record<string, string> = {
  entry: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  exit: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  skip: 'bg-muted text-muted-foreground',
  override: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
}

export function DecisionLog({ decisions, isLoading }: DecisionLogProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Decision Log</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-14 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const list = (decisions ?? []).slice().sort((a, b) =>
    (b.timestamp ?? '').localeCompare(a.timestamp ?? '')
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Decision Log (24h)</span>
          <Badge variant="secondary">{list.length} decisions</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {list.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No decisions recorded</p>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {list.map((d, i) => (
              <div key={`${d.timestamp}-${d.symbol}-${i}`} className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50">
                <div className="flex-shrink-0 pt-0.5">
                  <Badge className={decisionColors[d.decision] ?? decisionColors.skip}>
                    {d.decision.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">{d.symbol}</span>
                    {d.confidence > 0 && (
                      <span className="text-xs text-muted-foreground">
                        {(d.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                    {d.executed && (
                      <Badge variant="outline" className="text-xs">executed</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {typeof d.reason === 'string' ? d.reason : JSON.stringify(d.reason)}
                  </p>
                </div>
                <div className="flex-shrink-0 text-xs text-muted-foreground whitespace-nowrap">
                  {formatTime(d.timestamp)}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function formatTime(iso: string | undefined): string {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso
  }
}
