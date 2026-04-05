/**
 * MacroIndicatorsPage
 *
 * List and detail view of macroeconomic indicators with:
 * - List of available indicators
 * - Click to view detailed historical data
 * - Chart controls for time range selection
 * - Statistical summaries
 *
 * Accessed via: /market/macro-indicators
 */

import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { ArrowLeft, BarChart3 } from 'lucide-react'
import { useMacroIndicatorsList, useMacroIndicatorDetail } from '@/features/market/hooks/useMacroIndicators'
import { MacroIndicatorList } from '@/features/market/components/macros/MacroIndicatorList'
import { MacroDetailView } from '@/features/market/components/macros/MacroDetailView'
import type { MacroDataPoint } from '@/features/market/components/macros/MacroDetailView'

/**
 * Macro Indicators Page Component
 *
 * @example
 * // Route: /market/macro-indicators
 * // Route: /market/macro-indicators?indicator=GDP
 * <Route path="/market/macro-indicators" element={<MacroIndicatorsPage />} />
 */
export default function MacroIndicatorsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Get selected indicator from URL params
  const selectedIndicator = searchParams.get('indicator')

  // Date range state for detail view (default: last 5 years)
  const [fromDate, setFromDate] = useState(() => {
    const date = new Date()
    date.setFullYear(date.getFullYear() - 5)
    return date.toISOString().split('T')[0]
  })
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0])

  // Fetch indicators list
  const {
    data: indicatorsList,
    isLoading: listLoading,
    error: listError,
  } = useMacroIndicatorsList()

  // Fetch detail data if indicator is selected
  const {
    data: detailData,
    isLoading: detailLoading,
    error: detailError,
  } = useMacroIndicatorDetail({
    indicatorName: selectedIndicator || '',
    fromDate,
    toDate,
    enabled: !!selectedIndicator,
  })

  // Handle indicator selection
  const handleIndicatorSelect = (indicatorName: string) => {
    setSearchParams({ indicator: indicatorName })
  }

  // Handle back to list
  const handleBackToList = () => {
    setSearchParams({})
  }

  // Handle time range change
  const handleTimeRangeChange = (newFromDate: string, newToDate: string) => {
    setFromDate(newFromDate)
    setToDate(newToDate)
  }

  // Get indicator metadata from list
  const getIndicatorMetadata = (name: string) => {
    if (!indicatorsList) return null
    return indicatorsList.find((ind: any) => ind.name === name)
  }

  const selectedMetadata = selectedIndicator ? getIndicatorMetadata(selectedIndicator) : null

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {selectedIndicator && (
            <Button variant="ghost" onClick={handleBackToList}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to List
            </Button>
          )}
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BarChart3 className="h-8 w-8" />
              {selectedIndicator
                ? formatIndicatorName(selectedIndicator)
                : 'Macroeconomic Indicators'}
            </h1>
            {selectedIndicator && selectedMetadata && (
              <p className="text-muted-foreground mt-1">{selectedMetadata.description}</p>
            )}
          </div>
        </div>
        <Button variant="outline" onClick={() => navigate('/markets')}>
          Markets
        </Button>
      </div>

      {/* Content */}
      {!selectedIndicator ? (
        // List View
        <div>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Available Indicators</CardTitle>
              <CardDescription>
                Select an indicator to view its historical trend and detailed statistics
              </CardDescription>
            </CardHeader>
          </Card>

          {listLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-48" />
              ))}
            </div>
          ) : listError ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12 text-destructive">
                  <p>Error loading indicators: {(listError as Error).message}</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <MacroIndicatorList
              indicators={indicatorsList || []}
              onIndicatorClick={handleIndicatorSelect}
            />
          )}
        </div>
      ) : (
        // Detail View
        <MacroDetailView
          indicatorName={selectedIndicator}
          data={(detailData as MacroDataPoint[]) || []}
          unit={selectedMetadata?.unit}
          description={selectedMetadata?.description}
          isLoading={detailLoading}
          error={detailError as Error | null}
          onTimeRangeChange={handleTimeRangeChange}
        />
      )}

      {/* Info Footer */}
      {!selectedIndicator && !listLoading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>About Macroeconomic Indicators:</strong> These indicators provide insights
                into economic health, policy decisions, and market trends.
              </p>
              <p>
                Data is sourced from the FMP Service and updated regularly. Historical data may vary
                by indicator availability.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

/**
 * Format indicator name for display
 */
function formatIndicatorName(name: string): string {
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}
