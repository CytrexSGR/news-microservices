import { ArrowUp, ArrowDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { ShadowTradesResponse } from '../../hooks/useAgentControl'

interface TradeHistoryProps {
  data: ShadowTradesResponse | undefined
  isLoading: boolean
}

export function TradeHistory({ data, isLoading }: TradeHistoryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Trade History</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const trades = data?.shadow_trades ?? []
  const list = trades.slice().sort((a, b) => {
    const ta = a.exit_time ?? a.entry_time ?? ''
    const tb = b.exit_time ?? b.entry_time ?? ''
    return tb.localeCompare(ta)
  })

  const totalPnl = list.reduce((sum, t) => sum + (t.pnl ?? 0), 0)
  const winCount = data?.would_have_won ?? list.filter(t => (t.pnl ?? 0) > 0).length
  const winRate = list.length > 0 ? (winCount / list.length * 100) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Trade History</span>
          <div className="flex gap-2 text-sm font-normal">
            <Badge variant="secondary">{list.length} trades</Badge>
            <Badge variant={winRate >= 50 ? 'default' : 'destructive'}>{winRate.toFixed(0)}% WR</Badge>
            <Badge variant={totalPnl >= 0 ? 'default' : 'destructive'}>
              {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)}$
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {list.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No closed trades yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4">Time</th>
                  <th className="pb-2 pr-4">Symbol</th>
                  <th className="pb-2 pr-4">Direction</th>
                  <th className="pb-2 pr-4 text-right">Entry</th>
                  <th className="pb-2 pr-4 text-right">Exit</th>
                  <th className="pb-2 pr-4 text-right">PnL</th>
                  <th className="pb-2 pr-4 text-right">PnL %</th>
                  <th className="pb-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {list.map((trade) => {
                  const pnlPositive = (trade.pnl ?? 0) >= 0
                  return (
                    <tr key={trade.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-2 pr-4 text-muted-foreground whitespace-nowrap">
                        {formatTime(trade.exit_time ?? trade.entry_time)}
                      </td>
                      <td className="py-2 pr-4 font-medium">{trade.symbol}</td>
                      <td className="py-2 pr-4">
                        <Badge variant={trade.direction === 'LONG' ? 'default' : 'destructive'} className="gap-1">
                          {trade.direction === 'LONG' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {trade.direction}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4 text-right font-mono">{trade.entry_price?.toFixed(2)}</td>
                      <td className="py-2 pr-4 text-right font-mono">{trade.exit_price?.toFixed(2)}</td>
                      <td className={`py-2 pr-4 text-right font-mono ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {pnlPositive ? '+' : ''}{(trade.pnl ?? 0).toFixed(2)}$
                      </td>
                      <td className={`py-2 pr-4 text-right font-mono ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {pnlPositive ? '+' : ''}{(trade.pnl_pct ?? 0).toFixed(2)}%
                      </td>
                      <td className="py-2 text-muted-foreground text-xs">
                        {trade.exit_reason ?? '-'}
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

function formatTime(iso: string | undefined): string {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString('de-DE', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}
