import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, TrendingUp, Database, Percent } from 'lucide-react'
import type { EnrichmentStats } from '@/api/knowledgeGraphEnrichment'

interface EnrichmentStatsCardProps {
  stats: EnrichmentStats | null
  isLoading: boolean
}

export function EnrichmentStatsCard({ stats, isLoading }: EnrichmentStatsCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Enrichment Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading enrichment statistics...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Enrichment Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load enrichment statistics
          </div>
        </CardContent>
      </Card>
    )
  }

  const percentageColor =
    stats.percentage_needs_enrichment >= 60 ? 'destructive' :
    stats.percentage_needs_enrichment >= 40 ? 'secondary' : 'default'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Enrichment Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-muted-foreground mb-1">Total Relationships</div>
            <div className="text-2xl font-bold">{stats.total_relationships.toLocaleString()}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground mb-1">Enrichment Potential</div>
            <Badge variant={percentageColor} className="text-base px-3 py-1">
              {stats.percentage_needs_enrichment.toFixed(1)}%
            </Badge>
          </div>
        </div>

        {/* Breakdown */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-600" />
              <span className="text-sm">NOT_APPLICABLE</span>
            </div>
            <div className="text-sm font-medium">{stats.total_not_applicable.toLocaleString()}</div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-yellow-600" />
              <span className="text-sm">RELATED_TO (generic)</span>
            </div>
            <div className="text-sm font-medium">{stats.total_related_to.toLocaleString()}</div>
          </div>
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2">
              <Percent className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium">Total Needs Enrichment</span>
            </div>
            <div className="text-sm font-bold">{stats.enrichment_potential.toLocaleString()}</div>
          </div>
        </div>

        {/* Top Patterns */}
        {stats.top_entity_type_patterns.length > 0 && (
          <div className="pt-4 border-t space-y-2">
            <div className="text-sm font-medium mb-3">Top Patterns Needing Enrichment</div>
            <div className="space-y-1">
              {stats.top_entity_type_patterns.slice(0, 5).map((pattern, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs p-2 bg-muted/30 rounded"
                >
                  <span className="font-mono text-muted-foreground">{pattern.pattern}</span>
                  <Badge variant="outline" className="text-xs">
                    {pattern.count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
