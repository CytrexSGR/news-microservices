/**
 * MTFAEditor Component
 *
 * Multi-Timeframe Analysis configuration
 * Manages timeframe weights and divergence thresholds
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/badge'
import type { Strategy } from '@/types/strategy'

interface MTFAEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

const timeframes = [
  { id: '1h', label: '1 Hour', description: 'Primary trading timeframe', removable: false },
  { id: '4h', label: '4 Hour', description: 'Confirmation timeframe', removable: true },
  { id: '1d', label: '1 Day', description: 'Macro trend filter', removable: true },
]

export function MTFAEditor({ strategy, onChange }: MTFAEditorProps) {
  const mtfaConfig = strategy.definition?.mtfa || {
    timeframes: timeframes.map((tf) => ({
      id: tf.id,
      weight: tf.id === '1h' ? 0.6 : 0.2,
      divergence_threshold: 0.1,
    })),
  }

  const handleWeightChange = (timeframeId: string, weight: number) => {
    onChange?.(`mtfa.timeframes.${timeframeId}.weight`, weight)
  }

  const handleDivergenceChange = (timeframeId: string, threshold: number) => {
    onChange?.(`mtfa.timeframes.${timeframeId}.divergence_threshold`, threshold)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Multi-Timeframe Analysis (MTFA)</CardTitle>
        <CardDescription>
          Configure how different timeframes influence trading decisions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Info */}
        <div className="p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Purpose:</strong> Higher timeframes provide context and confirmation for trades on
            the primary timeframe. Divergence thresholds detect conflicting signals across timeframes.
          </p>
        </div>

        {/* Timeframe Configurations */}
        <div className="space-y-6">
          {timeframes.map((timeframe) => {
            const tfConfig = mtfaConfig.timeframes?.find((tf: any) => tf.id === timeframe.id) || {
              id: timeframe.id,
              weight: timeframe.id === '1h' ? 0.6 : 0.2,
              divergence_threshold: 0.1,
            }

            return (
              <div key={timeframe.id} className="border rounded-lg p-4 space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{timeframe.label}</h4>
                      {!timeframe.removable && (
                        <Badge variant="default" className="text-xs">
                          Primary
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{timeframe.description}</p>
                  </div>
                </div>

                {/* Weight */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={`${timeframe.id}-weight`}>Weight</Label>
                    <span className="text-sm font-medium">
                      {((tfConfig.weight || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    id={`${timeframe.id}-weight`}
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={tfConfig.weight || 0}
                    onChange={(e) => handleWeightChange(timeframe.id, Number(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">
                    Influence of this timeframe on final decision (higher = more important)
                  </p>
                </div>

                {/* Divergence Threshold */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={`${timeframe.id}-divergence`}>Divergence Threshold</Label>
                    <span className="text-sm font-medium">
                      {((tfConfig.divergence_threshold || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    id={`${timeframe.id}-divergence`}
                    type="range"
                    min="0"
                    max="0.5"
                    step="0.05"
                    value={tfConfig.divergence_threshold || 0}
                    onChange={(e) => handleDivergenceChange(timeframe.id, Number(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum allowed divergence before blocking trade (0 = strict, 0.5 = lenient)
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary */}
        <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
          <p className="font-medium">Total Weights:</p>
          <div className="flex items-center gap-3">
            {timeframes.map((tf) => {
              const tfConfig = mtfaConfig.timeframes?.find((t: any) => t.id === tf.id)
              return (
                <span key={tf.id}>
                  {tf.label}: {((tfConfig?.weight || 0) * 100).toFixed(0)}%
                </span>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
