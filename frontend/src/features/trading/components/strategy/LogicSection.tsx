/**
 * LogicSection Component
 *
 * Displays entry/exit logic per regime with tabs:
 * - TREND regime logic
 * - CONSOLIDATION regime logic
 * - HIGH_VOLATILITY regime logic
 *
 * Each regime shows:
 * - Entry conditions with aggregation mode
 * - Exit rules
 * - Risk management details
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import type { RegimeType } from '@/types/strategy'

// Actual API structure (not matching TypeScript types yet)
interface ApiCondition {
  expression: string
  description?: string
  confidence?: number
}

interface ApiEntryLogic {
  conditions: ApiCondition[]
  aggregation: string
  threshold?: number
  description?: string
}

interface ApiExitRule {
  type: string
  value?: number
  offset?: number
  activation?: number
  threshold?: number
  action?: string
  description?: string
  maxBars?: number
}

interface ApiExitLogic {
  rules: ApiExitRule[]
}

interface ApiRegimeLogic {
  entry: ApiEntryLogic
  exit: ApiExitLogic
  risk?: any
}

interface LogicSectionProps {
  logic: Record<RegimeType, ApiRegimeLogic>
}

export function LogicSection({ logic }: LogicSectionProps) {
  const regimes = Object.keys(logic) as RegimeType[]

  if (regimes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Entry/Exit Logic</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No logic defined</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Entry/Exit Logic</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={regimes[0]} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            {regimes.map((regime) => (
              <TabsTrigger key={regime} value={regime} className="text-xs">
                {regime}
              </TabsTrigger>
            ))}
          </TabsList>
          {regimes.map((regime) => (
            <TabsContent key={regime} value={regime} className="mt-4">
              <RegimeLogicPanel logic={logic[regime]} />
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  )
}

/**
 * RegimeLogicPanel - Internal component for displaying regime-specific logic
 */
interface RegimeLogicPanelProps {
  logic: ApiRegimeLogic
}

function RegimeLogicPanel({ logic }: RegimeLogicPanelProps) {
  return (
    <div className="space-y-4">
      {/* Entry Logic */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-sm font-semibold">Entry Conditions</h4>
          <Badge variant="secondary" className="text-xs">
            {logic.entry.aggregation}
          </Badge>
        </div>

        {logic.entry.conditions?.length === 0 ? (
          <p className="text-sm text-muted-foreground">No entry conditions defined</p>
        ) : (
          <ul className="space-y-1">
            {logic.entry.conditions?.map((condition, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-green-500 mt-0.5">✓</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    {condition.confidence !== undefined && (
                      <Badge variant="outline" className="text-xs">
                        confidence: {condition.confidence.toFixed(2)}
                      </Badge>
                    )}
                  </div>
                  <code className="block text-xs bg-muted px-2 py-1 rounded mt-1 overflow-x-auto">
                    {condition.expression}
                  </code>
                  {condition.description && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {condition.description}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {logic.entry.threshold && (
          <p className="text-xs text-muted-foreground mt-2">
            Minimum Threshold: {(logic.entry.threshold * 100).toFixed(0)}%
          </p>
        )}
        {logic.entry.description && (
          <p className="text-xs text-muted-foreground mt-1 italic">
            {logic.entry.description}
          </p>
        )}
      </div>

      {/* Exit Logic */}
      <div>
        <h4 className="text-sm font-semibold mb-2">Exit Rules</h4>

        {logic.exit.rules?.length === 0 ? (
          <p className="text-sm text-muted-foreground">No exit rules defined</p>
        ) : (
          <ul className="space-y-2">
            {logic.exit.rules?.map((rule, idx) => (
              <li key={idx} className="border-l-2 border-red-500 pl-3 text-sm">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {rule.type}
                  </Badge>
                  {rule.value !== undefined && (
                    <span className="text-xs">
                      {(rule.value * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                {rule.description && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {rule.description}
                  </p>
                )}
                {rule.type === 'trailing_stop' && (
                  <div className="text-xs text-muted-foreground mt-1">
                    <span>Activation: {((rule.activation || 0) * 100).toFixed(1)}%</span>
                    {' • '}
                    <span>Offset: {((rule.offset || 0) * 100).toFixed(2)}%</span>
                  </div>
                )}
                {rule.type === 'time_based' && rule.maxBars && (
                  <span className="text-xs text-muted-foreground">
                    Max {rule.maxBars} bars
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
