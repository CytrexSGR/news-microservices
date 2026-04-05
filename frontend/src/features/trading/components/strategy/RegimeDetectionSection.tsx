/**
 * RegimeDetectionSection Component
 *
 * Displays regime detection configuration:
 * - Detection provider (threshold, freqai, hmm)
 * - Provider-specific configuration
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { RegimeDetectionConfig } from '@/types/strategy'

interface RegimeDetectionSectionProps {
  config: RegimeDetectionConfig
}

export function RegimeDetectionSection({ config }: RegimeDetectionSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Regime Detection</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>
            <span className="text-sm font-medium">Provider:</span>
            <Badge variant="outline" className="ml-2">
              {config.provider}
            </Badge>
          </div>
          <div>
            <span className="text-sm font-medium">Configuration:</span>
            <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
              {JSON.stringify(config.config, null, 2)}
            </pre>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
