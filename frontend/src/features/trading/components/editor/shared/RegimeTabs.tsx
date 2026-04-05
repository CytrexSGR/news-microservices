/**
 * RegimeTabs Component
 *
 * Reusable regime tabs for Entry Logic, Exit Logic, and Risk Management editors
 * Provides uniform tab navigation across TREND, CONSOLIDATION, HIGH_VOLATILITY regimes
 */

import { ReactNode } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { RegimeType } from '@/types/strategy'

interface RegimeTabsProps {
  /** List of regimes to show tabs for */
  regimes: RegimeType[]
  /** Default active regime */
  defaultRegime?: RegimeType
  /** Render function for tab content */
  renderContent: (regime: RegimeType) => ReactNode
  /** Optional CSS class for the tabs container */
  className?: string
}

/**
 * Color mapping for visual distinction between regimes
 */
const regimeColors: Record<RegimeType, string> = {
  TREND: 'data-[state=active]:border-green-500 data-[state=active]:text-green-600',
  CONSOLIDATION: 'data-[state=active]:border-blue-500 data-[state=active]:text-blue-600',
  HIGH_VOLATILITY: 'data-[state=active]:border-orange-500 data-[state=active]:text-orange-600',
}

export function RegimeTabs({
  regimes,
  defaultRegime,
  renderContent,
  className,
}: RegimeTabsProps) {
  const defaultValue = defaultRegime || regimes[0]

  return (
    <Tabs defaultValue={defaultValue} className={className}>
      <TabsList className="grid w-full grid-cols-3 mb-6">
        {regimes.map((regime) => (
          <TabsTrigger
            key={regime}
            value={regime}
            className={`text-xs font-medium ${regimeColors[regime]}`}
          >
            {regime}
          </TabsTrigger>
        ))}
      </TabsList>

      {regimes.map((regime) => (
        <TabsContent key={regime} value={regime} className="space-y-6">
          {renderContent(regime)}
        </TabsContent>
      ))}
    </Tabs>
  )
}
