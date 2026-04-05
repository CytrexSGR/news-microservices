/**
 * NewsTabsPanel Component - Categorized financial news with tabs
 * Displays General, Stock, Forex, and Crypto news in separate tabs
 */

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Newspaper, TrendingUp, DollarSign, Bitcoin, ExternalLink, Handshake } from 'lucide-react'
import {
  useLiveGeneralNews,
  useLiveStockNews,
  useLiveForexNews,
  useLiveCryptoNews,
  useLiveMergersAcquisitions,
} from '@/features/market/hooks/useMarketNews'
import { formatDistanceToNow } from 'date-fns'
import type { FMPNews } from '@/features/market/types/market.types'

interface NewsItemProps {
  article: FMPNews
}

function NewsItem({ article }: NewsItemProps) {
  // Handle both DB format (published_at, source, content) and Live API format (publishedDate, site, text)
  const source = article.source || (article as any).site || 'Unknown'
  const content = article.content || (article as any).text
  const publishedDate = article.publishedAt || (article as any).publishedDate

  return (
    <div className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {source}
            </Badge>
            {article.sentiment && (
              <Badge
                variant="outline"
                className={
                  article.sentiment === 'positive'
                    ? 'bg-green-500/10 text-green-600 border-green-500/20'
                    : article.sentiment === 'negative'
                    ? 'bg-red-500/10 text-red-600 border-red-500/20'
                    : 'bg-muted'
                }
              >
                {article.sentiment}
              </Badge>
            )}
            {article.symbols && article.symbols.length > 0 && (
              <div className="flex gap-1">
                {article.symbols.slice(0, 3).map((symbol) => (
                  <Badge key={symbol} variant="secondary" className="text-xs">
                    {symbol}
                  </Badge>
                ))}
                {article.symbols.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{article.symbols.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </div>
          <h4 className="font-semibold text-sm line-clamp-2">{article.title}</h4>
          {content && (
            <p className="text-xs text-muted-foreground line-clamp-2">{content}</p>
          )}
          <p className="text-xs text-muted-foreground">
            {publishedDate
              ? formatDistanceToNow(new Date(publishedDate), { addSuffix: true })
              : 'Recently'}
          </p>
        </div>
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline flex-shrink-0"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>
    </div>
  )
}

interface MAItemProps {
  item: any // M&A data has different structure than FMPNews
}

function MAItem({ item }: MAItemProps) {
  return (
    <div className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-600 border-blue-500/20">
              SEC Filing
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {item.symbol}
            </Badge>
            {item.targetedSymbol && (
              <Badge variant="secondary" className="text-xs">
                → {item.targetedSymbol}
              </Badge>
            )}
          </div>
          <h4 className="font-semibold text-sm">
            {item.companyName} acquiring {item.targetedCompanyName}
          </h4>
          <p className="text-xs text-muted-foreground">
            Transaction Date: {new Date(item.transactionDate).toLocaleDateString()}
          </p>
          <p className="text-xs text-muted-foreground">
            Filed: {formatDistanceToNow(new Date(item.acceptedDate), { addSuffix: true })}
          </p>
        </div>
        {item.link && (
          <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline flex-shrink-0"
            title="View SEC Filing"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>
    </div>
  )
}

interface NewsListProps {
  news?: FMPNews[]
  isLoading: boolean
  category: string
}

function NewsList({ news, isLoading, category }: NewsListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border border-border animate-pulse">
            <div className="h-5 w-3/4 bg-muted rounded mb-2"></div>
            <div className="h-4 w-full bg-muted rounded mb-2"></div>
            <div className="h-3 w-1/2 bg-muted rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!news || news.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Newspaper className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p>No {category} news available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {news.map((article, index) => (
        <NewsItem key={index} article={article} />
      ))}
    </div>
  )
}

interface MAListProps {
  data?: any[]
  isLoading: boolean
}

function MAList({ data, isLoading }: MAListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border border-border animate-pulse">
            <div className="h-5 w-3/4 bg-muted rounded mb-2"></div>
            <div className="h-4 w-full bg-muted rounded mb-2"></div>
            <div className="h-3 w-1/2 bg-muted rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Handshake className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p>No M&A activity available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <MAItem key={index} item={item} />
      ))}
    </div>
  )
}

export function NewsTabsPanel() {
  const [activeTab, setActiveTab] = useState('general')

  // Fetch news for all categories
  const { data: generalNews, isLoading: generalLoading } = useLiveGeneralNews(0, 20)
  const { data: stockNews, isLoading: stockLoading } = useLiveStockNews(0, 20)
  const { data: forexNews, isLoading: forexLoading } = useLiveForexNews(0, 20)
  const { data: cryptoNews, isLoading: cryptoLoading } = useLiveCryptoNews(0, 20)
  const { data: maNews, isLoading: maLoading } = useLiveMergersAcquisitions(0, 20)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5" />
          Financial News
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 md:grid-cols-5">
            <TabsTrigger value="general" className="flex items-center gap-2">
              <Newspaper className="h-4 w-4" />
              <span className="hidden sm:inline">General</span>
            </TabsTrigger>
            <TabsTrigger value="stock" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              <span className="hidden sm:inline">Stock</span>
            </TabsTrigger>
            <TabsTrigger value="forex" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              <span className="hidden sm:inline">Forex</span>
            </TabsTrigger>
            <TabsTrigger value="crypto" className="flex items-center gap-2">
              <Bitcoin className="h-4 w-4" />
              <span className="hidden sm:inline">Crypto</span>
            </TabsTrigger>
            <TabsTrigger value="ma" className="flex items-center gap-2">
              <Handshake className="h-4 w-4" />
              <span className="hidden sm:inline">M&A</span>
            </TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="general" className="mt-0">
              <div className="mb-3">
                <p className="text-sm text-muted-foreground">
                  Latest financial news from various sources
                </p>
              </div>
              <NewsList news={generalNews} isLoading={generalLoading} category="general" />
            </TabsContent>

            <TabsContent value="stock" className="mt-0">
              <div className="mb-3">
                <p className="text-sm text-muted-foreground">
                  Stock market news with ticker symbols and market insights
                </p>
              </div>
              <NewsList news={stockNews} isLoading={stockLoading} category="stock" />
            </TabsContent>

            <TabsContent value="forex" className="mt-0">
              <div className="mb-3">
                <p className="text-sm text-muted-foreground">
                  Foreign exchange market news and currency pair updates
                </p>
              </div>
              <NewsList news={forexNews} isLoading={forexLoading} category="forex" />
            </TabsContent>

            <TabsContent value="crypto" className="mt-0">
              <div className="mb-3">
                <p className="text-sm text-muted-foreground">
                  Cryptocurrency market news for Bitcoin, Ethereum, and other digital assets
                </p>
              </div>
              <NewsList news={cryptoNews} isLoading={cryptoLoading} category="crypto" />
            </TabsContent>

            <TabsContent value="ma" className="mt-0">
              <div className="mb-3">
                <p className="text-sm text-muted-foreground">
                  Mergers, acquisitions, takeovers, and corporate consolidation news from SEC filings
                </p>
              </div>
              <MAList data={maNews} isLoading={maLoading} />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  )
}
