/**
 * IndicatorsSection Component
 *
 * Displays multi-timeframe indicators in a table:
 * - Indicator ID (e.g., "1h_RSI_14")
 * - Type (RSI, EMA, MACD, etc.)
 * - Timeframe (1m, 5m, 1h, etc.)
 * - Parameters (JSON display)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { IndicatorDefinition } from '@/types/strategy'

interface IndicatorsSectionProps {
  indicators: IndicatorDefinition[]
}

export function IndicatorsSection({ indicators }: IndicatorsSectionProps) {
  if (indicators.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Indicators</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No indicators defined</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Indicators ({indicators.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Timeframe</TableHead>
              <TableHead>Parameters</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {indicators.map((indicator) => (
              <TableRow key={indicator.id}>
                <TableCell className="font-mono text-xs">{indicator.id}</TableCell>
                <TableCell>
                  <Badge variant="outline">{indicator.type}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="text-xs">
                    {indicator.timeframe}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {JSON.stringify(indicator.params)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
