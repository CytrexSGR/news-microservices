import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Target,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  TrendingUp,
} from 'lucide-react'
import { useDisambiguationQuality } from '../../hooks/useDisambiguationQuality'
import type { DisambiguationQualityResponse } from '@/types/knowledgeGraph'

/**
 * Transform backend response to component display format
 */
function transformDisambiguationData(data: DisambiguationQualityResponse) {
  // Calculate average confidence from distribution
  const totalRelationships = data.confidence_distribution.total
  const avgConfidence = totalRelationships > 0
    ? (
        data.confidence_distribution.high * 0.9 +
        data.confidence_distribution.medium * 0.65 +
        data.confidence_distribution.low * 0.35
      ) / totalRelationships
    : 0

  // Extract low confidence cases (entities with low avg confidence in variations)
  const lowConfidenceCases = data.top_ambiguous_entities
    .filter(entity => {
      const avgConf = entity.variations_detail.reduce(
        (sum, v) => sum + v.avg_confidence, 0
      ) / (entity.variations_detail.length || 1)
      return avgConf < 0.7
    })
    .slice(0, 3)
    .map(entity => ({
      entity_name: entity.name,
      entity_type: entity.type_variations[0] || 'UNKNOWN',
      confidence: entity.variations_detail.reduce(
        (sum, v) => sum + v.avg_confidence, 0
      ) / (entity.variations_detail.length || 1),
      candidates: entity.type_variations.length
    }))

  return {
    total_disambiguations: data.total_disambiguation_cases,
    successful: data.well_disambiguated_count,
    ambiguous: data.total_ambiguous_names - data.well_disambiguated_count,
    failed: 0, // Not tracked in current backend
    success_rate: data.success_rate * 100, // Convert 0-1 to percentage
    avg_confidence: avgConfidence,
    low_confidence_cases: lowConfidenceCases
  }
}

export function DisambiguationQuality() {
  const { data, isLoading, error } = useDisambiguationQuality()
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Disambiguation Quality
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading disambiguation metrics...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Disambiguation Quality
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-sm text-red-900 dark:text-red-100">
              Failed to load disambiguation metrics. Please try again later.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  const displayMetrics = transformDisambiguationData(data)
  const isHighQuality = displayMetrics.success_rate >= 90
  const hasIssues = displayMetrics.failed > 0 || displayMetrics.ambiguous > 50

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Disambiguation Quality
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Measures how accurately the system distinguishes between entities
                  with similar names (e.g., "Paris" the city vs "Paris" the person).
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span className="text-xs text-muted-foreground">Successful</span>
            </div>
            <p className="text-2xl font-bold">{displayMetrics.successful}</p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <span className="text-xs text-muted-foreground">Ambiguous</span>
            </div>
            <p className="text-2xl font-bold">{displayMetrics.ambiguous}</p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <XCircle className="h-4 w-4 text-red-600" />
              <span className="text-xs text-muted-foreground">Failed</span>
            </div>
            <p className="text-2xl font-bold">{displayMetrics.failed}</p>
          </div>

          <div>
            <div className="flex items-center justify-center gap-1 mb-1">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Avg Conf.</span>
            </div>
            <p className="text-2xl font-bold">
              {(displayMetrics.avg_confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Success Rate Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Success Rate</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold">
                {displayMetrics.success_rate.toFixed(1)}%
              </span>
              {isHighQuality && <CheckCircle2 className="h-4 w-4 text-green-600" />}
            </div>
          </div>
          <Progress
            value={displayMetrics.success_rate}
            className={`h-2 ${
              isHighQuality
                ? '[&>div]:bg-green-600'
                : displayMetrics.success_rate > 80
                ? '[&>div]:bg-yellow-600'
                : '[&>div]:bg-orange-600'
            }`}
          />
          <p className="text-xs text-muted-foreground">
            {displayMetrics.total_disambiguations} total disambiguation attempts
          </p>
        </div>

        {/* Quality Alert */}
        {hasIssues && (
          <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-sm">
              <p className="font-medium text-yellow-900 dark:text-yellow-100">
                Attention Needed
              </p>
              <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                {displayMetrics.ambiguous} ambiguous cases and {displayMetrics.failed}{' '}
                failed disambiguations require manual review.
              </p>
            </AlertDescription>
          </Alert>
        )}

        {/* Low Confidence Cases */}
        {displayMetrics.low_confidence_cases.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <span className="text-sm font-medium">Low Confidence Cases</span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3 w-3 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-sm">
                      Entities with multiple possible meanings that need review
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <div className="space-y-2">
              {displayMetrics.low_confidence_cases.map((case_, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium truncate">{case_.entity_name}</p>
                      <Badge variant="outline" className="text-xs flex-shrink-0">
                        {case_.entity_type}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {case_.candidates} possible candidates
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                    <span
                      className={`text-sm font-bold ${
                        case_.confidence >= 0.7
                          ? 'text-yellow-600'
                          : case_.confidence >= 0.5
                          ? 'text-orange-600'
                          : 'text-red-600'
                      }`}
                    >
                      {(case_.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="pt-3 border-t text-center text-xs text-muted-foreground">
          Disambiguation quality directly impacts knowledge graph accuracy
        </div>
      </CardContent>
    </Card>
  )
}
