import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Zap, Eye, Check, AlertCircle, RefreshCw } from 'lucide-react'
import { useOptimizeSchedule } from '@/features/admin/feed-service/hooks/useScheduling'
import type { OptimizationResult } from '@/types/feedServiceAdmin'

export function OptimizationControlCard() {
  const [previewResult, setPreviewResult] = useState<OptimizationResult | null>(null)
  const optimizeMutation = useOptimizeSchedule()

  const handlePreview = async () => {
    setPreviewResult(null)
    const result = await optimizeMutation.mutateAsync(false)
    setPreviewResult(result)
  }

  const handleApply = async () => {
    if (previewResult) {
      await optimizeMutation.mutateAsync(true)
      setPreviewResult(null)
    }
  }

  const handleOptimizeAndApply = async () => {
    await optimizeMutation.mutateAsync(true)
    setPreviewResult(null)
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Zeitplan-Optimierung
          </h3>
          <p className="text-sm text-muted-foreground">
            Intelligente Verteilung der Feed-Abrufe zur Ressourcen-Optimierung
          </p>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handlePreview}
            disabled={optimizeMutation.isPending}
            variant="outline"
            className="flex-1"
          >
            {optimizeMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Eye className="mr-2 h-4 w-4" />
            )}
            Vorschau
          </Button>
          <Button
            onClick={handleOptimizeAndApply}
            disabled={optimizeMutation.isPending}
            variant="default"
            className="flex-1"
          >
            {optimizeMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Zap className="mr-2 h-4 w-4" />
            )}
            Auto-Optimieren
          </Button>
        </div>

        {/* Preview Results */}
        {previewResult && (
          <div className="space-y-4 animate-in fade-in-50 duration-500">
            {/* Summary Banner */}
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-primary">Optimierungsvorschau</span>
                <Badge variant="secondary">
                  {previewResult.improvement_percentage.toFixed(1)}% Verbesserung
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{previewResult.message}</p>
            </div>

            {/* Before/After Comparison */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-lg border bg-card">
                <div className="text-xs text-muted-foreground mb-2 uppercase tracking-wide">
                  Vorher
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Max Gleichzeitig</span>
                    <span className="text-xl font-bold text-destructive">
                      {previewResult.before.max_concurrent}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Score</span>
                    <span className="text-sm font-semibold">
                      {previewResult.before.distribution_score.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border bg-primary/5 border-primary/20">
                <div className="text-xs text-primary mb-2 uppercase tracking-wide font-semibold">
                  Nachher
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Max Gleichzeitig</span>
                    <span className="text-xl font-bold text-green-600">
                      {previewResult.after.max_concurrent}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Score</span>
                    <span className="text-sm font-semibold text-primary">
                      {previewResult.after.distribution_score.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg border bg-card text-center">
                <div className="text-xs text-muted-foreground mb-1">Feeds Analysiert</div>
                <div className="text-lg font-bold">{previewResult.feeds_analyzed}</div>
              </div>
              <div className="p-3 rounded-lg border bg-card text-center">
                <div className="text-xs text-muted-foreground mb-1">Feeds Angepasst</div>
                <div className="text-lg font-bold text-primary">
                  {previewResult.feeds_optimized}
                </div>
              </div>
            </div>

            {/* Preview Table (if available) */}
            {previewResult.preview && previewResult.preview.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Änderungen ({previewResult.preview.length} Feeds)
                </h4>
                <div className="max-h-64 overflow-y-auto border rounded-lg">
                  <table className="w-full text-sm">
                    <thead className="bg-muted sticky top-0">
                      <tr>
                        <th className="text-left p-2">Feed</th>
                        <th className="text-center p-2">Alt</th>
                        <th className="text-center p-2">Neu</th>
                        <th className="text-center p-2">Δ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewResult.preview.map((change) => (
                        <tr key={change.feed_id} className="border-t hover:bg-muted/50">
                          <td className="p-2 truncate max-w-[150px]" title={change.feed_name}>
                            {change.feed_name}
                          </td>
                          <td className="p-2 text-center text-muted-foreground">
                            {change.old_offset}m
                          </td>
                          <td className="p-2 text-center font-medium text-primary">
                            {change.new_offset}m
                          </td>
                          <td className="p-2 text-center text-xs">
                            {change.new_offset > change.old_offset ? '+' : ''}
                            {change.new_offset - change.old_offset}m
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Apply Button */}
            <Button
              onClick={handleApply}
              disabled={optimizeMutation.isPending}
              variant="default"
              className="w-full"
              size="lg"
            >
              {optimizeMutation.isPending ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Wende Optimierung an...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Jetzt Anwenden
                </>
              )}
            </Button>
          </div>
        )}

        {/* Help Text */}
        {!previewResult && (
          <div className="p-3 rounded-lg bg-muted/50 border">
            <p className="text-xs text-muted-foreground">
              <strong className="text-foreground">Tipp:</strong> Klicke auf "Vorschau" um die
              geplanten Änderungen zu sehen, bevor du sie anwendest. "Auto-Optimieren" führt die
              Optimierung sofort aus.
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
