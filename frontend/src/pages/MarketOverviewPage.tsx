/**
 * MarketOverviewPage - Consolidated market data dashboard
 * Displays real-time quotes for indices, forex, commodities, crypto + news & events
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { BarChart3, DollarSign, Coins, Bitcoin, Newspaper, Activity } from 'lucide-react'
import { useMarketData } from '@/features/market/hooks/useMarketData'
import { MarketSummary } from '@/features/market/components/summary/MarketSummary'
import { IndicesTab } from '@/features/market/components/quotes/IndicesTab'
import { ForexTab } from '@/features/market/components/quotes/ForexTab'
import { CommoditiesTab } from '@/features/market/components/quotes/CommoditiesTab'
import { CryptoTab } from '@/features/market/components/quotes/CryptoTab'
import { NewsTabsPanel } from '@/features/market/components/news/NewsTabsPanel'

export function MarketOverviewPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const navigate = useNavigate()

  // Fetch all market data
  const {
    indices,
    forex,
    commodities,
    crypto,
    allQuotes,
    isLoading,
    loading,
    error,
    lastFetchedAt,
  } = useMarketData()

  // Handle quote click - navigate to AssetDetailPage
  const handleQuoteClick = (quote: any) => {
    // Map category to assetType for URL
    const assetTypeMap = {
      index: 'indices',
      forex: 'forex',
      commodity: 'commodities',
      crypto: 'crypto',
    }
    const assetType = assetTypeMap[quote.category as keyof typeof assetTypeMap] || quote.category
    navigate(`/market/asset/${assetType}/${encodeURIComponent(quote.symbol)}`)
  }

  // Format last fetch time as relative time (e.g., "30 seconds ago")
  const getLastUpdateText = () => {
    if (!lastFetchedAt) return 'Unknown'

    const now = Date.now()
    const secondsAgo = Math.floor((now - lastFetchedAt) / 1000)

    if (secondsAgo < 60) {
      return secondsAgo <= 5 ? 'Just now' : `${secondsAgo} seconds ago`
    }

    const minutesAgo = Math.floor(secondsAgo / 60)
    if (minutesAgo < 60) {
      return `${minutesAgo} minute${minutesAgo > 1 ? 's' : ''} ago`
    }

    const hoursAgo = Math.floor(minutesAgo / 60)
    return `${hoursAgo} hour${hoursAgo > 1 ? 's' : ''} ago`
  }

  const lastUpdate = getLastUpdateText()

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <div
          className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Market Data</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Failed to load market data'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Market Overview</h1>
          <p className="text-muted-foreground mt-1">
            Real-time quotes, news, and calendar events
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-2">
          <Activity className="h-3 w-3 animate-pulse text-green-500" />
          <span>Last updated: {lastUpdate}</span>
        </Badge>
      </div>

      {/* Tabs Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 lg:w-auto">
          <TabsTrigger value="overview" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="indices" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Indices</span>
            {indices.length > 0 && (
              <Badge variant="secondary" className="ml-1 hidden lg:inline">
                {indices.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="forex" className="gap-2">
            <DollarSign className="h-4 w-4" />
            <span className="hidden sm:inline">Forex</span>
            {forex.length > 0 && (
              <Badge variant="secondary" className="ml-1 hidden lg:inline">
                {forex.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="commodities" className="gap-2">
            <Coins className="h-4 w-4" />
            <span className="hidden sm:inline">Commodities</span>
            {commodities.length > 0 && (
              <Badge variant="secondary" className="ml-1 hidden lg:inline">
                {commodities.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="crypto" className="gap-2">
            <Bitcoin className="h-4 w-4" />
            <span className="hidden sm:inline">Crypto</span>
            {crypto.length > 0 && (
              <Badge variant="secondary" className="ml-1 hidden lg:inline">
                {crypto.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="news" className="gap-2">
            <Newspaper className="h-4 w-4" />
            <span className="hidden sm:inline">News</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="p-6">
                  <div className="space-y-3">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <MarketSummary allQuotes={allQuotes} onQuoteClick={handleQuoteClick} />
          )}
        </TabsContent>

        {/* Indices Tab */}
        <TabsContent value="indices">
          <IndicesTab
            indices={indices}
            isLoading={loading.indices}
            onQuoteClick={handleQuoteClick}
          />
        </TabsContent>

        {/* Forex Tab */}
        <TabsContent value="forex">
          <ForexTab
            forex={forex}
            isLoading={loading.forex}
            onQuoteClick={handleQuoteClick}
          />
        </TabsContent>

        {/* Commodities Tab */}
        <TabsContent value="commodities">
          <CommoditiesTab
            commodities={commodities}
            isLoading={loading.commodities}
            onQuoteClick={handleQuoteClick}
          />
        </TabsContent>

        {/* Crypto Tab */}
        <TabsContent value="crypto">
          <CryptoTab
            crypto={crypto}
            isLoading={loading.crypto}
            onQuoteClick={handleQuoteClick}
          />
        </TabsContent>

        {/* News & Events Tab */}
        <TabsContent value="news">
          <NewsTabsPanel />
        </TabsContent>
      </Tabs>
    </div>
  )
}
