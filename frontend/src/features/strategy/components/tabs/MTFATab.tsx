/**
 * MTFATab Component
 *
 * Displays Multi-Timeframe Analysis configuration including
 * timeframe weights and divergence thresholds.
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Layers, Clock, AlertTriangle } from 'lucide-react';
import type { StrategyDefinition } from '../../types';

interface MTFATabProps {
  definition: StrategyDefinition;
}

interface MTFATimeframe {
  id: string;
  weight?: number;
  divergence_threshold?: number;
}

export function MTFATab({ definition }: MTFATabProps) {
  const mtfa = (definition as any).mtfa;
  const execution = definition.execution;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Multi-Timeframe Analysis (MTFA)
          </CardTitle>
          <CardDescription>
            Configure how different timeframes influence trading decisions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Info Banner */}
          <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-sm">
              <strong>Purpose:</strong> Higher timeframes provide context and confirmation
              for trades on the primary timeframe. Divergence thresholds detect conflicting
              signals across timeframes.
            </p>
          </div>

          {/* Timeframe Configuration */}
          {mtfa?.timeframes && mtfa.timeframes.length > 0 ? (
            <div className="space-y-4">
              {mtfa.timeframes.map((tf: MTFATimeframe) => {
                const isPrimary =
                  tf.id === execution?.timeframe || tf.id === mtfa?.primary_timeframe;
                const weightPercent = (tf.weight || 0) * 100;
                const divergencePercent = (tf.divergence_threshold || 0) * 100;

                return (
                  <div key={tf.id} className="border rounded-lg p-4 space-y-3">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold">
                          {tf.id === '1h'
                            ? '1 Hour'
                            : tf.id === '4h'
                            ? '4 Hours'
                            : tf.id === '1d'
                            ? '1 Day'
                            : tf.id}
                        </span>
                        {isPrimary && <Badge variant="default">Primary</Badge>}
                      </div>
                      <Badge variant="outline" className="font-mono">
                        {tf.id}
                      </Badge>
                    </div>

                    {/* Weight */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Weight</span>
                        <span className="font-medium">{weightPercent.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${weightPercent}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Influence of this timeframe on final decision
                      </p>
                    </div>

                    {/* Divergence Threshold */}
                    {tf.divergence_threshold !== undefined && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            Divergence Threshold
                          </span>
                          <span className="font-medium">{divergencePercent.toFixed(0)}%</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Maximum allowed divergence before blocking trade (0% = strict, 50% =
                          lenient)
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Summary */}
              <div className="p-3 bg-muted rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Total Weight</span>
                  {(() => {
                    const totalWeight = mtfa.timeframes.reduce(
                      (sum: number, tf: MTFATimeframe) => sum + (tf.weight || 0),
                      0
                    );
                    const isValid = Math.abs(totalWeight - 1) <= 0.01;
                    return (
                      <span
                        className={`font-medium ${
                          isValid ? 'text-green-500' : 'text-amber-500'
                        }`}
                      >
                        {(totalWeight * 100).toFixed(0)}%
                        {!isValid && ' (should be 100%)'}
                      </span>
                    );
                  })()}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Layers className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No MTFA configuration defined</p>
              <p className="text-xs mt-1">
                Multi-timeframe analysis uses default settings
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
