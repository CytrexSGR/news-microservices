import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Network, Info, TrendingUp, ExternalLink, AlertTriangle } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { CrossArticleCoverageStats } from '@/types/knowledgeGraph'

interface CrossArticleCoverageProps {
  stats: CrossArticleCoverageStats | null
  isLoading: boolean
}

export function CrossArticleCoverage({ stats, isLoading }: CrossArticleCoverageProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Cross-Article Entity Coverage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading coverage data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Mock data for demonstration (TODO: Connect to real API)
  const mockStats: CrossArticleCoverageStats = stats || {
    total_articles: 543,
    total_unique_entities: 265,
    entities_per_article_avg: 8.7,
    articles_per_entity_avg: 2.3,
    top_entities: [
      {
        entity_name: 'United States',
        entity_type: 'LOCATION',
        article_count: 127,
        coverage_percentage: 23.4,
        wikidata_id: 'Q30',
        recent_articles: [
          { title: 'US Economy Shows Growth', published_at: '2025-01-24' },
          { title: 'Policy Changes in Washington', published_at: '2025-01-23' },
        ],
      },
      {
        entity_name: 'Angela Merkel',
        entity_type: 'PERSON',
        article_count: 89,
        coverage_percentage: 16.4,
        wikidata_id: 'Q567',
        recent_articles: [
          { title: 'Former Chancellor Interview', published_at: '2025-01-24' },
          { title: 'Political Legacy Discussion', published_at: '2025-01-22' },
        ],
      },
      {
        entity_name: 'European Union',
        entity_type: 'ORGANIZATION',
        article_count: 76,
        coverage_percentage: 14.0,
        wikidata_id: 'Q458',
        recent_articles: [
          { title: 'EU Trade Agreement', published_at: '2025-01-23' },
          { title: 'Brussels Summit Results', published_at: '2025-01-21' },
        ],
      },
      {
        entity_name: 'Climate Change',
        entity_type: 'EVENT',
        article_count: 64,
        coverage_percentage: 11.8,
        wikidata_id: 'Q125928',
        recent_articles: [
          { title: 'Climate Summit Update', published_at: '2025-01-24' },
          { title: 'New Environmental Policies', published_at: '2025-01-20' },
        ],
      },
      {
        entity_name: 'China',
        entity_type: 'LOCATION',
        article_count: 58,
        coverage_percentage: 10.7,
        wikidata_id: 'Q148',
        recent_articles: [
          { title: 'Asian Markets Analysis', published_at: '2025-01-23' },
          { title: 'Trade Relations Update', published_at: '2025-01-22' },
        ],
      },
    ],
  }

  const displayStats = mockStats

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" />
          Cross-Article Entity Coverage
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Shows which entities appear across multiple articles. High coverage
                  indicates recurring themes and important topics.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ⚠️ MOCK DATA WARNING */}
        <Alert className="bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-sm text-amber-900 dark:text-amber-100">
            <strong>Mock Data:</strong> This component shows placeholder data. Backend feature
            required: Article-Entity relationships must be stored in Neo4j Knowledge Graph.
            Implementation needed in{' '}
            <code className="text-xs bg-amber-100 dark:bg-amber-900 px-1 rounded">
              knowledge-graph-service
            </code>
            {' '}to track which articles contain which entities.
          </AlertDescription>
        </Alert>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <span className="text-xs text-muted-foreground">Total Articles</span>
            </div>
            <p className="text-2xl font-bold">{displayStats.total_articles}</p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <span className="text-xs text-muted-foreground">Unique Entities</span>
            </div>
            <p className="text-2xl font-bold">{displayStats.total_unique_entities}</p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <span className="text-xs text-muted-foreground underline decoration-dotted cursor-help">
                      Entities/Article
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-sm">Average entities per article</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <p className="text-2xl font-bold">
              {displayStats.entities_per_article_avg.toFixed(1)}
            </p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <span className="text-xs text-muted-foreground underline decoration-dotted cursor-help">
                      Articles/Entity
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-sm">Average articles per entity</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <p className="text-2xl font-bold">
              {displayStats.articles_per_entity_avg.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Top Entities by Coverage */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-amber-500" />
            <span className="text-sm font-medium">Most Covered Entities</span>
          </div>

          <div className="space-y-3">
            {displayStats.top_entities.map((entity, idx) => (
              <div key={idx} className="space-y-2">
                {/* Entity Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="text-xs text-muted-foreground w-6 flex-shrink-0">
                      #{idx + 1}
                    </span>
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{entity.entity_name}</p>
                      <Badge variant="outline" className="text-xs flex-shrink-0">
                        {entity.entity_type}
                      </Badge>
                      {entity.wikidata_id && (
                        <a
                          href={`https://www.wikidata.org/wiki/${entity.wikidata_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 flex-shrink-0"
                          title={`View ${entity.entity_name} on Wikidata`}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                    <span className="text-sm font-bold">{entity.article_count}</span>
                    <span className="text-xs text-muted-foreground">articles</span>
                  </div>
                </div>

                {/* Coverage Progress Bar */}
                <div className="space-y-1 pl-8">
                  <Progress
                    value={entity.coverage_percentage}
                    className="h-2 [&>div]:bg-blue-600"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{entity.coverage_percentage.toFixed(1)}% of all articles</span>
                    {entity.recent_articles?.[0]?.published_at && (
                      <span>
                        Last: {new Date(entity.recent_articles[0].published_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Recent Articles Preview */}
                <div className="pl-8 space-y-1">
                  {(entity.recent_articles?.slice(0, 2) || []).map((article, artIdx) => (
                    <p key={artIdx} className="text-xs text-muted-foreground truncate">
                      • {article.title}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="pt-3 border-t text-center text-xs text-muted-foreground">
          Showing top 5 entities by article coverage
        </div>
      </CardContent>
    </Card>
  )
}
