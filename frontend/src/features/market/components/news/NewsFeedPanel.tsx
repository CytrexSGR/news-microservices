/**
 * NewsFeedPanel Component - Display financial news and calendar events
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Newspaper, Calendar, ExternalLink } from 'lucide-react'
import { useGeneralNews, useEarningsCalendar } from '@/features/market/hooks/useMarketNews'
import { formatDistanceToNow } from 'date-fns'

export function NewsFeedPanel() {
  // Fetch news and events
  const { data: news, isLoading: newsLoading } = useGeneralNews({ page: 0, size: 10 })
  const { data: earnings, isLoading: earningsLoading } = useEarningsCalendar({ limit: 20 })

  // Filter upcoming earnings (next 7 days)
  const upcomingEarnings = earnings
    ?.filter((e) => new Date(e.reportDate) > new Date())
    .sort((a, b) => new Date(a.reportDate).getTime() - new Date(b.reportDate).getTime())
    .slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Latest News */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5" />
            Latest Financial News
          </CardTitle>
        </CardHeader>
        <CardContent>
          {newsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="p-4 rounded-lg border border-border animate-pulse">
                  <div className="h-5 w-3/4 bg-muted rounded mb-2"></div>
                  <div className="h-4 w-full bg-muted rounded"></div>
                </div>
              ))}
            </div>
          ) : news && news.length > 0 ? (
            <div className="space-y-3">
              {news.map((article, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-xs">
                          {article.source}
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
                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(article.publishedAt), { addSuffix: true })}
                      </p>
                    </div>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No news available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upcoming Earnings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Upcoming Earnings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {earningsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="p-4 rounded-lg border border-border animate-pulse">
                  <div className="h-4 w-1/2 bg-muted rounded mb-2"></div>
                  <div className="h-3 w-full bg-muted rounded"></div>
                </div>
              ))}
            </div>
          ) : upcomingEarnings && upcomingEarnings.length > 0 ? (
            <div className="space-y-3">
              {upcomingEarnings.map((event, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{event.symbol}</span>
                        <Badge variant="outline" className="text-xs">
                          {event.time === 'bmo' ? 'Before Market' : 'After Market'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{event.companyName}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(event.reportDate).toLocaleDateString()}
                      </p>
                    </div>
                    {event.epsEstimate && (
                      <div className="text-right text-sm">
                        <div className="text-muted-foreground">EPS Est.</div>
                        <div className="font-medium">${event.epsEstimate.toFixed(2)}</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No upcoming earnings
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
