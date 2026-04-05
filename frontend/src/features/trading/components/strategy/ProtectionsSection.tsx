/**
 * ProtectionsSection Component
 *
 * Displays global protection guards:
 * - StoplossGuard: Prevent trading after X stoplosses
 * - MaxDrawdown: Halt trading if drawdown exceeds threshold
 * - LowProfitPairs: Lock pairs with low profit
 * - CooldownPeriod: Force cooldown after losing streaks
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Shield, AlertOctagon, TrendingDown, Clock, Ban } from 'lucide-react'

interface Protection {
  id?: string
  type: string
  method?: string
  enabled?: boolean
  config?: {
    stop_duration_candles?: number
    trade_limit?: number
    required_profit?: number
    max_allowed_drawdown?: number
    lookback_period_candles?: number
  }
  // Direct properties (alternative format)
  stop_duration_candles?: number
  trade_limit?: number
  required_profit?: number
  max_allowed_drawdown?: number
  lookback_period_candles?: number
  stop_duration?: number
  only_per_pair?: boolean
  only_per_side?: boolean
  description?: string
}

interface ProtectionsSectionProps {
  protections?: Protection[]
}

const protectionIcons: Record<string, typeof Shield> = {
  StoplossGuard: AlertOctagon,
  MaxDrawdown: TrendingDown,
  LowProfitPairs: Ban,
  CooldownPeriod: Clock,
}

const protectionDescriptions: Record<string, string> = {
  StoplossGuard: 'Halts trading after consecutive stop losses',
  MaxDrawdown: 'Stops trading when drawdown exceeds threshold',
  LowProfitPairs: 'Locks underperforming trading pairs',
  CooldownPeriod: 'Enforces cooldown after losing trades',
}

export function ProtectionsSection({ protections = [] }: ProtectionsSectionProps) {
  if (protections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Protection Guards
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No protection guards configured</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Protection Guards ({protections.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {protections.map((protection, idx) => {
          const type = protection.type || protection.method || 'Unknown'
          const Icon = protectionIcons[type] || Shield
          const isEnabled = protection.enabled !== false

          // Get config values (support both nested and flat formats)
          const config = protection.config || protection
          const stopDuration = config.stop_duration_candles ?? protection.stop_duration_candles
          const tradeLimit = config.trade_limit ?? protection.trade_limit
          const requiredProfit = config.required_profit ?? protection.required_profit
          const maxDrawdown = config.max_allowed_drawdown ?? protection.max_allowed_drawdown
          const lookbackPeriod = config.lookback_period_candles ?? protection.lookback_period_candles

          return (
            <div
              key={protection.id || idx}
              className={`border rounded-lg p-3 space-y-2 ${
                !isEnabled ? 'opacity-50' : ''
              }`}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-amber-500" />
                  <span className="font-medium text-sm">{type}</span>
                </div>
                <Badge variant={isEnabled ? 'default' : 'secondary'} className="text-xs">
                  {isEnabled ? 'Active' : 'Disabled'}
                </Badge>
              </div>

              {/* Description */}
              <p className="text-xs text-muted-foreground">
                {protection.description || protectionDescriptions[type] || 'Protection mechanism'}
              </p>

              {/* Config Details */}
              <div className="grid grid-cols-2 gap-2 pt-1">
                {stopDuration !== undefined && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Stop Duration:</span>
                    <span className="ml-1 font-medium">{stopDuration} candles</span>
                  </div>
                )}

                {tradeLimit !== undefined && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Trade Limit:</span>
                    <span className="ml-1 font-medium">{tradeLimit}</span>
                  </div>
                )}

                {maxDrawdown !== undefined && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Max Drawdown:</span>
                    <span className="ml-1 font-medium">{(maxDrawdown * 100).toFixed(0)}%</span>
                  </div>
                )}

                {lookbackPeriod !== undefined && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Lookback:</span>
                    <span className="ml-1 font-medium">{lookbackPeriod} candles</span>
                  </div>
                )}

                {requiredProfit !== undefined && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Required Profit:</span>
                    <span className="ml-1 font-medium">{(requiredProfit * 100).toFixed(1)}%</span>
                  </div>
                )}

                {protection.only_per_pair && (
                  <div className="text-xs">
                    <Badge variant="outline" className="text-xs">Per Pair</Badge>
                  </div>
                )}

                {protection.only_per_side && (
                  <div className="text-xs">
                    <Badge variant="outline" className="text-xs">Per Side</Badge>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
