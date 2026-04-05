/**
 * ExecutionSection Component
 *
 * Displays execution configuration:
 * - Primary timeframe
 * - Order types (entry, exit, stoploss)
 * - Fill timeout
 * - Long/Short permissions
 * - Regime transition behavior
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Settings, ArrowUpRight, ArrowDownRight, Clock, RefreshCw } from 'lucide-react'

interface OrderTypes {
  entry?: 'limit' | 'market'
  exit?: 'limit' | 'market'
  stoploss?: 'limit' | 'market'
}

interface RegimeTransitionBehavior {
  onRegimeChange?: 'keep_position' | 'exit_position'
  updateStops?: boolean
  updateTargets?: boolean
  description?: string
}

interface ExecutionConfig {
  timeframe?: string
  canShort?: boolean
  canLong?: boolean
  orderTypes?: OrderTypes
  fillTimeout?: number
  regimeTransitionBehavior?: RegimeTransitionBehavior
}

interface ExecutionSectionProps {
  execution?: ExecutionConfig
}

export function ExecutionSection({ execution }: ExecutionSectionProps) {
  if (!execution) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Execution Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No execution settings configured</p>
        </CardContent>
      </Card>
    )
  }

  const { timeframe, canShort, canLong, orderTypes, fillTimeout, regimeTransitionBehavior } = execution

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Settings className="h-4 w-4" />
          Execution Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Primary Timeframe */}
        {timeframe && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Primary Timeframe
            </span>
            <Badge variant="default" className="font-mono">
              {timeframe}
            </Badge>
          </div>
        )}

        {/* Trading Directions */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Trading Directions</span>
          <div className="flex items-center gap-2">
            {canLong !== undefined && (
              <Badge
                variant={canLong ? 'default' : 'secondary'}
                className={`text-xs ${canLong ? 'bg-green-600' : ''}`}
              >
                <ArrowUpRight className="h-3 w-3 mr-1" />
                Long {canLong ? '✓' : '✗'}
              </Badge>
            )}
            {canShort !== undefined && (
              <Badge
                variant={canShort ? 'default' : 'secondary'}
                className={`text-xs ${canShort ? 'bg-red-600' : ''}`}
              >
                <ArrowDownRight className="h-3 w-3 mr-1" />
                Short {canShort ? '✓' : '✗'}
              </Badge>
            )}
          </div>
        </div>

        {/* Order Types */}
        {orderTypes && (
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Order Types</span>
            <div className="grid grid-cols-3 gap-2">
              {orderTypes.entry && (
                <div className="text-xs border rounded p-2 text-center">
                  <div className="text-muted-foreground">Entry</div>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {orderTypes.entry}
                  </Badge>
                </div>
              )}
              {orderTypes.exit && (
                <div className="text-xs border rounded p-2 text-center">
                  <div className="text-muted-foreground">Exit</div>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {orderTypes.exit}
                  </Badge>
                </div>
              )}
              {orderTypes.stoploss && (
                <div className="text-xs border rounded p-2 text-center">
                  <div className="text-muted-foreground">Stop Loss</div>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {orderTypes.stoploss}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Fill Timeout */}
        {fillTimeout !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Fill Timeout</span>
            <span className="text-sm font-medium">{fillTimeout} seconds</span>
          </div>
        )}

        {/* Regime Transition Behavior */}
        {regimeTransitionBehavior && (
          <div className="border-t pt-4 space-y-2">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Regime Transition Behavior
            </span>

            <div className="grid grid-cols-2 gap-2 text-xs">
              {regimeTransitionBehavior.onRegimeChange && (
                <div>
                  <span className="text-muted-foreground">On Change:</span>
                  <Badge variant="outline" className="ml-2">
                    {regimeTransitionBehavior.onRegimeChange === 'keep_position'
                      ? 'Keep Position'
                      : 'Exit Position'}
                  </Badge>
                </div>
              )}

              {regimeTransitionBehavior.updateStops !== undefined && (
                <div>
                  <span className="text-muted-foreground">Update Stops:</span>
                  <span className={`ml-2 font-medium ${regimeTransitionBehavior.updateStops ? 'text-green-500' : 'text-gray-500'}`}>
                    {regimeTransitionBehavior.updateStops ? 'Yes' : 'No'}
                  </span>
                </div>
              )}

              {regimeTransitionBehavior.updateTargets !== undefined && (
                <div>
                  <span className="text-muted-foreground">Update Targets:</span>
                  <span className={`ml-2 font-medium ${regimeTransitionBehavior.updateTargets ? 'text-green-500' : 'text-gray-500'}`}>
                    {regimeTransitionBehavior.updateTargets ? 'Yes' : 'No'}
                  </span>
                </div>
              )}
            </div>

            {regimeTransitionBehavior.description && (
              <p className="text-xs text-muted-foreground italic mt-2">
                {regimeTransitionBehavior.description}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
