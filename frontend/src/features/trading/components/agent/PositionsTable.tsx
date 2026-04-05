import { ArrowUp, ArrowDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { AgentPosition } from '../../hooks/useAgentControl'

interface PositionsTableProps {
  positions: AgentPosition[] | undefined
  isLoading: boolean
}

export function PositionsTable({ positions, isLoading }: PositionsTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Open Positions</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const list = positions ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Open Positions</span>
          <Badge variant="secondary">{list.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {list.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No open positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4">Symbol</th>
                  <th className="pb-2 pr-4">Direction</th>
                  <th className="pb-2 pr-4 text-right">Entry</th>
                  <th className="pb-2 pr-4 text-right">Current</th>
                  <th className="pb-2 pr-4 text-right">PnL</th>
                  <th className="pb-2 pr-4 text-right">PnL %</th>
                  <th className="pb-2 pr-4 text-right">Size $</th>
                  <th className="pb-2 pr-4 text-center">Leverage</th>
                  <th className="pb-2 pr-4 text-right">SL</th>
                  <th className="pb-2 pr-4 text-right">TP</th>
                  <th className="pb-2 text-center">Trailing</th>
                </tr>
              </thead>
              <tbody>
                {list.map((pos) => {
                  const pnlPct = pos.pnl_pct ?? (pos.entry_price > 0
                    ? ((pos.current_price - pos.entry_price) / pos.entry_price * 100 * (pos.direction === 'SHORT' ? -1 : 1))
                    : 0)
                  const pnlPositive = (pos.unrealized_pnl ?? 0) >= 0

                  return (
                    <tr key={pos.symbol} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-2 pr-4 font-medium">{pos.symbol}</td>
                      <td className="py-2 pr-4">
                        <Badge variant={pos.direction === 'LONG' ? 'default' : 'destructive'} className="gap-1">
                          {pos.direction === 'LONG' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {pos.direction}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4 text-right font-mono">{formatPrice(pos.entry_price)}</td>
                      <td className="py-2 pr-4 text-right font-mono">{formatPrice(pos.current_price)}</td>
                      <td className={`py-2 pr-4 text-right font-mono ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {pnlPositive ? '+' : ''}{(pos.unrealized_pnl ?? 0).toFixed(2)}$
                      </td>
                      <td className={`py-2 pr-4 text-right font-mono ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {pnlPositive ? '+' : ''}{pnlPct.toFixed(2)}%
                      </td>
                      <td className="py-2 pr-4 text-right font-mono text-muted-foreground">
                        {pos.size_usd ? `$${pos.size_usd.toFixed(2)}` : '-'}
                      </td>
                      <td className="py-2 pr-4 text-center font-mono">
                        {pos.leverage && pos.leverage > 1 ? (
                          <Badge variant="secondary" className="text-xs">{pos.leverage}x</Badge>
                        ) : (
                          <span className="text-muted-foreground">1x</span>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-right font-mono text-muted-foreground">{formatPrice(pos.stop_loss)}</td>
                      <td className="py-2 pr-4 text-right font-mono text-muted-foreground">{formatPrice(pos.take_profit)}</td>
                      <td className="py-2 text-center">
                        {pos.trailing_activated ? (
                          <Badge variant="default" className="text-xs">ON</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function formatPrice(price: number | undefined): string {
  if (price == null || price === 0) return '-'
  if (price >= 1000) return price.toFixed(2)
  if (price >= 1) return price.toFixed(4)
  return price.toFixed(6)
}
