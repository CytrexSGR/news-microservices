/**
 * AssetDetailPage
 *
 * Detailed view for a specific market asset with:
 * - Real-time quote information
 * - Historical price chart with time range controls
 * - Asset-specific metrics and statistics
 * - Related assets/indicators
 *
 * Accessed via: /market/asset/:assetType/:symbol
 * Example: /market/asset/indices/^GSPC
 */

import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  DollarSign,
  BarChart3,
  AlertCircle,
} from 'lucide-react'
import { getIndices, getForex, getCommodities, getCrypto } from '@/lib/api/fmpMarket'
import { useHistoricalData } from '@/features/market/hooks/useHistoricalData'
import { HistoricalChart } from '@/features/market/components/historical/HistoricalChart'
import { ChartControls } from '@/features/market/components/historical/ChartControls'
import { calculateDateRange, TIME_RANGES } from '@/features/market/components/historical/TimeRangePicker'
import type { TimeRange } from '@/features/market/components/historical/TimeRangePicker'
import type { MarketQuote, MarketCategory } from '@/features/market/types'

/**
 * Asset Detail Page Component
 *
 * @example
 * // Route: /market/asset/indices/^GSPC
 * <Route path="/market/asset/:assetType/:symbol" element={<AssetDetailPage />} />
 */
export default function AssetDetailPage() {
  const { assetType, symbol } = useParams<{ assetType: string; symbol: string }>()
  const navigate = useNavigate()

  // State for time range selection
  const [selectedRange, setSelectedRange] = useState('1y')
  const [customRange, setCustomRange] = useState<{ fromDate: string; toDate: string } | null>(null)

  // Calculate date range for historical data
  const getDateRange = () => {
    if (customRange) {
      return customRange
    }
    const range = TIME_RANGES.find((r) => r.value === selectedRange)
    return range ? calculateDateRange(range) : { fromDate: '', toDate: '' }
  }

  const { fromDate, toDate } = getDateRange()

  // Map assetType to correct API function
  const getQuotesFn = () => {
    switch (assetType) {
      case 'indices':
        return getIndices()
      case 'forex':
        return getForex()
      case 'commodities':
        return getCommodities()
      case 'crypto':
        return getCrypto()
      default:
        throw new Error(`Unknown asset type: ${assetType}`)
    }
  }

  // Fetch current quote data
  const {
    data: quoteData,
    isLoading: quoteLoading,
    error: quoteError,
  } = useQuery({
    queryKey: ['quote', assetType, symbol],
    queryFn: getQuotesFn,
    enabled: !!assetType && !!symbol,
    select: (data) => data.find((q: MarketQuote) => q.symbol === symbol),
    staleTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 60, // Refetch every minute
  })

  // Fetch historical data
  const {
    data: historicalData,
    isLoading: historyLoading,
    error: historyError,
  } = useHistoricalData({
    assetType: assetType as 'indices' | 'forex' | 'commodities' | 'crypto',
    symbol: symbol || '',
    fromDate,
    toDate,
    enabled: !!assetType && !!symbol && !!fromDate && !!toDate,
  })

  // Handle time range change
  const handleRangeChange = (range: TimeRange) => {
    setSelectedRange(range.value)
    setCustomRange(null) // Clear custom range when preset is selected
  }

  const handleCustomDateRange = (range: { fromDate: string; toDate: string }) => {
    setSelectedRange('custom')
    setCustomRange(range)
  }

  // Loading state
  if (quoteLoading) {
    return (
      <div className="container mx-auto px-4 py-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Skeleton className="h-[500px]" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-[200px]" />
            <Skeleton className="h-[200px]" />
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (quoteError || !quoteData) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Market Overview
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h2 className="text-lg font-semibold mb-2">Asset Not Found</h2>
              <p className="text-muted-foreground mb-4">
                Could not load data for {symbol} in {assetType}
              </p>
              <Button onClick={() => navigate('/markets')}>Go to Markets</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Format asset type for display
  const formatAssetType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1)
  }

  // Calculate price change color
  const changeColor = quoteData.change >= 0 ? 'text-green-600' : 'text-red-600'
  const ChangeTrendIcon = quoteData.change >= 0 ? TrendingUp : TrendingDown

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Market Overview
        </Button>
        <Badge variant="outline">{formatAssetType(assetType || '')}</Badge>
      </div>

      {/* Asset Info Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Activity className="h-6 w-6" />
                {quoteData.symbol}
              </CardTitle>
              <CardDescription className="mt-2">{quoteData.name}</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold">${quoteData.price.toFixed(2)}</div>
              <div className={`flex items-center justify-end gap-1 mt-2 text-sm ${changeColor}`}>
                <ChangeTrendIcon className="h-4 w-4" />
                <span>
                  {quoteData.change >= 0 ? '+' : ''}
                  {quoteData.change.toFixed(2)} ({quoteData.change >= 0 ? '+' : ''}
                  {quoteData.change_percent.toFixed(2)}%)
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {new Date().toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Historical Chart - Left Column (2/3 width) */}
        <div className="lg:col-span-2 space-y-4">
          <ChartControls
            selectedRange={selectedRange}
            onRangeChange={handleRangeChange}
            onCustomDateRange={handleCustomDateRange}
            showCustomDatePicker
          />

          <HistoricalChart
            data={historicalData || []}
            symbol={quoteData.symbol}
            title={`${quoteData.name} - Historical Price`}
            description={`Price trend for ${quoteData.symbol}`}
            chartType="area"
            showVolume={false}
            isLoading={historyLoading}
            error={historyError as Error | null}
            height={500}
          />
        </div>

        {/* Stats & Info - Right Column (1/3 width) */}
        <div className="space-y-4">
          {/* Price Statistics Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Price Statistics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b">
                <span className="text-sm text-muted-foreground">Current Price</span>
                <span className="font-semibold">${quoteData.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b">
                <span className="text-sm text-muted-foreground">Day Change</span>
                <span className={`font-semibold ${changeColor}`}>
                  {quoteData.change >= 0 ? '+' : ''}
                  {quoteData.change.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b">
                <span className="text-sm text-muted-foreground">Day Change %</span>
                <span className={`font-semibold ${changeColor}`}>
                  {quoteData.change >= 0 ? '+' : ''}
                  {quoteData.change_percent.toFixed(2)}%
                </span>
              </div>
              {/* Only show day_low/day_high for commodities and crypto */}
              {('day_low' in quoteData) && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Day Low</span>
                  <span className="font-semibold">${(quoteData as any).day_low.toFixed(2)}</span>
                </div>
              )}
              {('day_high' in quoteData) && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Day High</span>
                  <span className="font-semibold">${(quoteData as any).day_high.toFixed(2)}</span>
                </div>
              )}
              {/* Only show open_price for commodities and crypto */}
              {('open_price' in quoteData) && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Open</span>
                  <span className="font-semibold">${(quoteData as any).open_price.toFixed(2)}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Trading Information Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Trading Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {quoteData.volume && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Volume</span>
                  <span className="font-semibold">
                    {quoteData.volume.toLocaleString()}
                  </span>
                </div>
              )}
              {/* Only show market_cap for crypto */}
              {('market_cap' in quoteData) && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Market Cap</span>
                  <span className="font-semibold">
                    ${((quoteData as any).market_cap / 1e9).toFixed(2)}B
                  </span>
                </div>
              )}
              {/* Show bid/ask for forex */}
              {('bid' in quoteData) && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Bid</span>
                  <span className="font-semibold">${(quoteData as any).bid.toFixed(4)}</span>
                </div>
              )}
              {('ask' in quoteData) && (
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm text-muted-foreground">Ask</span>
                  <span className="font-semibold">${(quoteData as any).ask.toFixed(4)}</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Last Updated</span>
                <span className="text-xs text-muted-foreground">
                  {new Date(quoteData.timestamp).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Last Updated Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Last Updated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {new Date().toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Data refreshes every minute. Historical data updates daily.
              </p>
            </CardContent>
          </Card>

          {/* Related Links (Future) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Related Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link
                to="/markets"
                className="block text-sm text-primary hover:underline"
              >
                View All Market Data →
              </Link>
              <Link
                to="/admin/services/fmp-service"
                className="block text-sm text-primary hover:underline"
              >
                Admin Panel →
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
