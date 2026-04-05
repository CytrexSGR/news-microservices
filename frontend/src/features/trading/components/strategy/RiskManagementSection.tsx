/**
 * RiskManagementSection Component
 *
 * Displays risk management rules:
 * - Position sizing formula (SymPy expression)
 * - Max position size percentage
 * - Max leverage
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import type { RiskManagement } from '@/types/strategy'

interface RiskManagementSectionProps {
  riskManagement: RiskManagement
}

export function RiskManagementSection({ riskManagement }: RiskManagementSectionProps) {
  const hasContent =
    riskManagement.position_size_formula ||
    riskManagement.max_position_size_pct !== undefined ||
    riskManagement.max_leverage !== undefined

  if (!hasContent) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Risk Management</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No risk management rules defined</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Risk Management</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {riskManagement.position_size_formula && (
          <div>
            <span className="text-sm font-medium">Position Sizing Formula:</span>
            <code className="block text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
              {riskManagement.position_size_formula}
            </code>
          </div>
        )}

        {riskManagement.max_position_size_pct !== undefined && (
          <div className="text-sm">
            <span className="font-medium">Max Position Size:</span>
            <span className="ml-2">
              {(riskManagement.max_position_size_pct * 100).toFixed(1)}% of account balance
            </span>
          </div>
        )}

        {riskManagement.max_leverage !== undefined && (
          <div className="text-sm">
            <span className="font-medium">Max Leverage:</span>
            <span className="ml-2">{riskManagement.max_leverage}x</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
