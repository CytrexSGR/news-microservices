import { Activity, Pause, AlertTriangle, DollarSign, TrendingDown, Shield } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { AgentState, RiskStatus } from '../../hooks/useAgentControl'

interface AgentStatusBarProps {
  state: AgentState | undefined
  risk: RiskStatus | undefined
  isLoading: boolean
}

export function AgentStatusBar({ state, risk, isLoading }: AgentStatusBarProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const engineRunning = state && !state.paused
  const capital = state?.portfolio?.capital ?? 0
  const peakCapital = state?.portfolio?.peak_capital ?? capital
  const unrealizedPnl = state?.portfolio?.unrealized_pnl ?? 0
  const drawdown = risk?.portfolio?.drawdown_pct ?? 0
  const breakerCount = (state?.active_breakers?.length ?? 0) + (risk?.circuit_breakers?.length ?? 0)
  const tradingBlocked = risk?.trading_blocked ?? false

  return (
    <Card>
      <CardContent className="py-4">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          {/* Engine Status */}
          <div className="flex items-center gap-2">
            {engineRunning ? (
              <Activity className="h-4 w-4 text-green-500" />
            ) : (
              <Pause className="h-4 w-4 text-yellow-500" />
            )}
            <div>
              <p className="text-xs text-muted-foreground">Engine</p>
              <Badge variant={engineRunning ? 'default' : 'secondary'}>
                {engineRunning ? 'RUNNING' : 'PAUSED'}
              </Badge>
            </div>
          </div>

          {/* Tick Count */}
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Tick</p>
              <p className="text-sm font-medium">#{state?.tick_count ?? 0}</p>
            </div>
          </div>

          {/* Capital */}
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Capital</p>
              <p className="text-sm font-medium">${capital.toFixed(2)}</p>
            </div>
          </div>

          {/* Unrealized PnL */}
          <div className="flex items-center gap-2">
            <TrendingDown className={`h-4 w-4 ${unrealizedPnl >= 0 ? 'text-green-500' : 'text-red-500'}`} />
            <div>
              <p className="text-xs text-muted-foreground">Unrealized PnL</p>
              <p className={`text-sm font-medium ${unrealizedPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {unrealizedPnl >= 0 ? '+' : ''}{unrealizedPnl.toFixed(2)}$
              </p>
            </div>
          </div>

          {/* Drawdown */}
          <div className="flex items-center gap-2">
            <TrendingDown className={`h-4 w-4 ${drawdown > 5 ? 'text-red-500' : drawdown > 2 ? 'text-yellow-500' : 'text-muted-foreground'}`} />
            <div>
              <p className="text-xs text-muted-foreground">Drawdown</p>
              <p className={`text-sm font-medium ${drawdown > 5 ? 'text-red-500' : drawdown > 2 ? 'text-yellow-500' : ''}`}>
                -{drawdown.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Circuit Breakers */}
          <div className="flex items-center gap-2">
            {tradingBlocked ? (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            ) : (
              <Shield className="h-4 w-4 text-green-500" />
            )}
            <div>
              <p className="text-xs text-muted-foreground">Breakers</p>
              <Badge variant={tradingBlocked ? 'destructive' : breakerCount > 0 ? 'secondary' : 'default'}>
                {tradingBlocked ? 'BLOCKED' : breakerCount > 0 ? `${breakerCount} active` : 'OK'}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
