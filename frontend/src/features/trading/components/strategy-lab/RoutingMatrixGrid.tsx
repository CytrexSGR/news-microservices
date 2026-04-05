/**
 * RoutingMatrixGrid - Displays the strategy routing matrix as an HTML table.
 *
 * Rows = symbol groups, Columns = market regimes.
 * Each cell shows the assigned strategy name (as Badge) and its weight.
 */

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import type { StrategyPortfolio } from '../../hooks/useStrategyLab'

const REGIMES = ['TRENDING', 'MEAN_REVERSION', 'TRANSITION', 'HIGH_VOLATILITY'] as const

interface RoutingMatrixGridProps {
  portfolio: StrategyPortfolio | undefined
  isLoading: boolean
}

export default function RoutingMatrixGrid({ portfolio, isLoading }: RoutingMatrixGridProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Routing Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!portfolio || !portfolio.routing_matrix) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Routing Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No routing matrix available. The champion portfolio has not been configured yet.
          </p>
        </CardContent>
      </Card>
    )
  }

  const symbolGroups = Object.keys(portfolio.routing_matrix)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Routing Matrix
          {portfolio.version && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              v{portfolio.version}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative w-full overflow-auto">
          <table className="w-full caption-bottom text-sm">
            <thead className="[&_tr]:border-b">
              <tr className="border-b transition-colors">
                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                  Symbol Group
                </th>
                {REGIMES.map((regime) => (
                  <th
                    key={regime}
                    className="h-12 px-4 text-left align-middle font-medium text-muted-foreground"
                  >
                    {regime.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {symbolGroups.map((group) => (
                <tr key={group} className="border-b transition-colors hover:bg-muted/50">
                  <td className="p-4 align-middle font-medium">{group}</td>
                  {REGIMES.map((regime) => {
                    const cell = portfolio.routing_matrix[group]?.[regime]
                    return (
                      <td key={regime} className="p-4 align-middle">
                        {cell ? (
                          <div className="flex flex-col gap-1">
                            <Badge variant="secondary" className="w-fit">
                              {cell.strategy}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              weight: {(cell.weight * 100).toFixed(0)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">--</span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
