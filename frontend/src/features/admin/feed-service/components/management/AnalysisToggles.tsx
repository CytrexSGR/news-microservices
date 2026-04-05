import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Settings, Info } from 'lucide-react'
import type { FeedResponse } from '@/types/feedServiceAdmin'

interface AnalysisTogglesProps {
  feeds: FeedResponse[]
}

export function AnalysisToggles({ feeds }: AnalysisTogglesProps) {
  // Calculate how many feeds have each analysis enabled
  const analysisStats = {
    category: feeds.filter((f) => f.enable_category_analysis).length,
    finance: feeds.filter((f) => f.enable_finance_sentiment).length,
    geopolitical: feeds.filter((f) => f.enable_geopolitical_sentiment).length,
    bias: feeds.filter((f) => f.enable_bias).length,
    conflict: feeds.filter((f) => f.enable_conflict).length,
    osint: feeds.filter((f) => f.enable_osint_analysis).length,
    summary: feeds.filter((f) => f.enable_summary).length,
    entity: feeds.filter((f) => f.enable_entity_extraction).length,
    topic: feeds.filter((f) => f.enable_topic_classification).length,
  }

  const totalFeeds = feeds.length

  const getPercentage = (count: number) => {
    return totalFeeds > 0 ? ((count / totalFeeds) * 100).toFixed(0) : '0'
  }

  const analysisTypes = [
    {
      key: 'category',
      label: 'Category Analysis',
      description: 'Automatically categorize articles',
      count: analysisStats.category,
    },
    {
      key: 'summary',
      label: 'Summary Generation',
      description: 'Generate article summaries',
      count: analysisStats.summary,
    },
    {
      key: 'entity',
      label: 'Entity Extraction',
      description: 'Extract named entities from content',
      count: analysisStats.entity,
    },
    {
      key: 'topic',
      label: 'Topic Classification',
      description: 'Classify articles by topic',
      count: analysisStats.topic,
    },
    {
      key: 'finance',
      label: 'Finance Sentiment',
      description: 'Analyze financial sentiment',
      count: analysisStats.finance,
    },
    {
      key: 'geopolitical',
      label: 'Geopolitical Sentiment',
      description: 'Analyze geopolitical implications',
      count: analysisStats.geopolitical,
    },
    {
      key: 'bias',
      label: 'Bias Detection',
      description: 'Detect bias and editorial slant',
      count: analysisStats.bias,
    },
    {
      key: 'conflict',
      label: 'Conflict Event Analysis',
      description: 'Analyze conflict and violence events',
      count: analysisStats.conflict,
    },
    {
      key: 'osint',
      label: 'OSINT Analysis',
      description: 'Open-source intelligence analysis',
      count: analysisStats.osint,
    },
  ]

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Settings className="h-5 w-5" />
        Analysis Features Overview
      </h3>

      <div className="space-y-3">
        {/* Info Banner */}
        <div className="p-3 rounded-lg border bg-blue-50 dark:bg-blue-950/20 flex items-start gap-2">
          <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            These settings show how many feeds have each analysis feature enabled. To modify
            settings for individual feeds, use the Feed List table or Feed Detail pages.
          </div>
        </div>

        {/* Analysis Type List */}
        <div className="space-y-2">
          {analysisTypes.map((analysis) => (
            <div
              key={analysis.key}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div className="flex-1">
                <div className="font-medium">{analysis.label}</div>
                <div className="text-sm text-muted-foreground">{analysis.description}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {analysis.count} / {totalFeeds}
                </span>
                <Badge variant={analysis.count > 0 ? 'default' : 'outline'}>
                  {getPercentage(analysis.count)}%
                </Badge>
              </div>
            </div>
          ))}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-3 pt-3 border-t">
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Most Common</div>
            <div className="text-lg font-bold">
              {analysisTypes.reduce((max, curr) =>
                curr.count > max.count ? curr : max
              ).label}
            </div>
          </div>
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Least Common</div>
            <div className="text-lg font-bold">
              {analysisTypes.reduce((min, curr) =>
                curr.count < min.count ? curr : min
              ).label}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
