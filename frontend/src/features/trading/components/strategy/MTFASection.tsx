/**
 * MTFASection Component
 *
 * Displays Multi-Timeframe Analysis configuration:
 * - Configured timeframes with weights
 * - Divergence thresholds
 * - Primary vs confirmation timeframes
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Layers, Clock, AlertTriangle } from 'lucide-react'

interface TimeframeConfig {
  id: string
  weight: number
  divergence_threshold?: number
}

interface MTFAConfig {
  timeframes?: TimeframeConfig[]
  primary_timeframe?: string
}

interface MTFASectionProps {
  mtfa?: MTFAConfig
}

const timeframeLabels: Record<string, string> = {
  '1m': '1 Minute',
  '5m': '5 Minutes',
  '15m': '15 Minutes',
  '30m': '30 Minutes',
  '1h': '1 Hour',
  '4h': '4 Hours',
  '1d': '1 Day',
  '1w': '1 Week',
  '1M': '1 Month',
}

export function MTFASection({ mtfa }: MTFASectionProps) {
  const timeframes = mtfa?.timeframes || []
  const primaryTimeframe = mtfa?.primary_timeframe || timeframes[0]?.id

  if (timeframes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Multi-Timeframe Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No MTFA configuration defined</p>
        </CardContent>
      </Card>
    )
  }

  // Calculate total weight for validation display
  const totalWeight = timeframes.reduce((sum, tf) => sum + (tf.weight || 0), 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Layers className="h-4 w-4" />
          Multi-Timeframe Analysis ({timeframes.length} timeframes)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Timeframe List */}
        <div className="space-y-3">
          {timeframes.map((tf) => {
            const isPrimary = tf.id === primaryTimeframe
            const weightPercent = (tf.weight || 0) * 100
            const divergencePercent = (tf.divergence_threshold || 0) * 100

            return (
              <div
                key={tf.id}
                className="border rounded-lg p-3 space-y-2"
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium text-sm">
                      {timeframeLabels[tf.id] || tf.id}
                    </span>
                    {isPrimary && (
                      <Badge variant="default" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs font-mono">
                    {tf.id}
                  </Badge>
                </div>

                {/* Weight */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Weight</span>
                    <span className="font-medium">{weightPercent.toFixed(0)}%</span>
                  </div>
                  <Progress value={weightPercent} className="h-1.5" />
                </div>

                {/* Divergence Threshold */}
                {tf.divergence_threshold !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      Divergence Threshold
                    </span>
                    <span className="font-medium">{divergencePercent.toFixed(0)}%</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Summary */}
        <div className="p-3 bg-muted rounded-lg">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Total Weight</span>
            <span className={`font-medium ${Math.abs(totalWeight - 1) > 0.01 ? 'text-amber-500' : 'text-green-500'}`}>
              {(totalWeight * 100).toFixed(0)}%
              {Math.abs(totalWeight - 1) > 0.01 && ' (should be 100%)'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
