import { useQuery } from '@tanstack/react-query'
import { authApi, feedApi } from '@/api/axios'

// Type definitions for the Analytics Overview API response
export interface OverviewMetrics {
  total_users: number
  active_feeds: number
  total_articles: number
  articles_today: number
  average_sentiment: number
  top_sources: Array<{
    source: string
    count: number
  }>
  articles_by_day: Array<{
    date: string
    count: number
  }>
  sentiment_distribution: {
    positive: number
    neutral: number
    negative: number
  }
}

const getOverviewMetrics = async (): Promise<OverviewMetrics> => {
  // Fetch data from multiple services in parallel
  const [authStats, feedStats] = await Promise.all([
    authApi.get('/auth/stats'),
    feedApi.get('/feeds/stats')
  ])

  // Return combined data
  return {
    total_users: authStats.data.total_users,
    active_feeds: feedStats.data.active_feeds,
    total_articles: feedStats.data.total_articles,
    articles_today: feedStats.data.articles_today,
    top_sources: feedStats.data.top_sources || [],
    articles_by_day: feedStats.data.articles_by_day || [],
    // Default values for not-yet-implemented features
    average_sentiment: 0,
    sentiment_distribution: {
      positive: 0,
      neutral: 0,
      negative: 0
    }
  }
}

export const useOverviewMetrics = () => {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: getOverviewMetrics,
    staleTime: 60 * 1000, // 1 minute
  })
}
