import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { GitBranch, Percent, AlertCircle, CheckCircle, ChevronDown, ChevronRight, ArrowRight } from 'lucide-react'
import type { RelationshipStats } from '@/types/knowledgeGraph'

interface RelationshipStatsCardProps {
  stats: RelationshipStats | null
  isLoading: boolean
}

export function RelationshipStatsCard({ stats, isLoading }: RelationshipStatsCardProps) {
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set())

  const toggleExpand = (type: string) => {
    const newSet = new Set(expandedTypes)
    if (newSet.has(type)) {
      newSet.delete(type)
    } else {
      newSet.add(type)
    }
    setExpandedTypes(newSet)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Relationship Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading relationship insights...
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
            <GitBranch className="h-5 w-5" />
            Relationship Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load relationship insights
          </div>
        </CardContent>
      </Card>
    )
  }

  // Get top 6 relationship types for overview
  const topRelationships = stats.relationship_types.slice(0, 6)
  const qualityBadgeColor =
    stats.quality_insights.avg_confidence_overall >= 0.8 ? 'default' :
    stats.quality_insights.avg_confidence_overall >= 0.6 ? 'secondary' : 'destructive'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Relationship Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Quality Overview */}
        <div className="pb-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-sm text-muted-foreground">Total Relationships</div>
              <div className="text-2xl font-bold">{stats.total_relationships.toLocaleString()}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground mb-1">Overall Quality</div>
              <Badge variant={qualityBadgeColor} className="text-base px-3 py-1">
                {(stats.quality_insights.avg_confidence_overall * 100).toFixed(0)}%
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3 text-green-600" />
              <span>{stats.quality_insights.high_quality_count} high quality types</span>
            </div>
            {stats.quality_insights.needs_review_count > 0 && (
              <div className="flex items-center gap-1 text-orange-600">
                <AlertCircle className="h-3 w-3" />
                <span>{stats.quality_insights.needs_review_count} need review</span>
              </div>
            )}
          </div>
        </div>

        {/* Warnings */}
        {stats.warnings.length > 0 && (
          <div className="space-y-2">
            {stats.warnings.map((warning, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 p-2 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900"
              >
                <AlertCircle className="h-4 w-4 text-orange-600 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-orange-900 dark:text-orange-200">
                  {warning.message}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Top Relationship Types with Examples */}
        <div className="space-y-2">
          <div className="text-sm font-medium mb-3">Top Relationship Types</div>
          {topRelationships.map((rel) => {
            const isExpanded = expandedTypes.has(rel.type)
            const hasExamples = rel.examples && rel.examples.length > 0
            const barWidth = `${Math.min(rel.percentage, 100)}%`
            const qualityColor =
              rel.quality === 'high' ? 'text-green-600' :
              rel.quality === 'medium' ? 'text-yellow-600' : 'text-red-600'

            return (
              <div key={rel.type} className="space-y-1 pb-2 border-b last:border-0">
                {/* Type Header - Clickable */}
                <div
                  className={`flex items-center justify-between text-sm ${hasExamples ? 'cursor-pointer hover:bg-muted/50 -mx-1 px-1 py-1 rounded' : ''}`}
                  onClick={() => hasExamples && toggleExpand(rel.type)}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {hasExamples && (
                      isExpanded ? <ChevronDown className="h-3 w-3 flex-shrink-0" /> : <ChevronRight className="h-3 w-3 flex-shrink-0" />
                    )}
                    <span className="font-medium truncate">{rel.type}</span>
                    <Badge variant="secondary" className="text-xs">
                      {rel.count.toLocaleString()}
                    </Badge>
                    <div title={`${rel.quality} quality`}>
                      <CheckCircle className={`h-3 w-3 ${qualityColor} flex-shrink-0`} />
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Percent className="h-3 w-3" />
                    <span>{rel.percentage.toFixed(1)}%</span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: barWidth }}
                  />
                </div>

                {/* Confidence & Mentions */}
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Confidence: {(rel.avg_confidence * 100).toFixed(0)}%</span>
                  <span>{rel.total_mentions.toLocaleString()} mentions</span>
                </div>

                {/* Expanded Examples */}
                {isExpanded && hasExamples && (
                  <div className="mt-2 ml-5 space-y-1 pt-2 border-t">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Examples:</div>
                    {rel.examples.map((ex, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs p-1.5 bg-muted/50 rounded">
                        <Badge variant="outline" className="text-xs px-1.5 py-0">
                          {ex.source_type}
                        </Badge>
                        <span className="font-medium truncate flex-1">{ex.source}</span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="font-medium truncate flex-1">{ex.target}</span>
                        <Badge variant="outline" className="text-xs px-1.5 py-0">
                          {ex.target_type}
                        </Badge>
                        <span className="text-muted-foreground">({ex.mentions}x)</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {/* Show remaining types count */}
          {stats.relationship_types.length > 6 && (
            <div className="pt-1 text-xs text-center text-muted-foreground">
              +{stats.relationship_types.length - 6} more relationship types
            </div>
          )}
        </div>

        {/* Entity-Type Patterns */}
        {stats.patterns && stats.patterns.length > 0 && (
          <div className="pt-4 border-t space-y-2">
            <div className="text-sm font-medium mb-2">Common Patterns</div>
            <div className="space-y-1">
              {stats.patterns.slice(0, 5).map((pattern, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs p-2 bg-muted/30 rounded"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {pattern.source_type}
                    </Badge>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="text-muted-foreground font-mono text-xs">
                      {pattern.relationship_type}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <Badge variant="outline" className="text-xs">
                      {pattern.target_type}
                    </Badge>
                  </div>
                  <span className="text-muted-foreground font-medium">
                    {pattern.count}×
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
