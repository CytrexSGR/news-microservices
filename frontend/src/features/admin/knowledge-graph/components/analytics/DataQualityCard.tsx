import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Shield, TrendingUp, AlertTriangle, CheckCircle2, XCircle, Info } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Progress } from '@/components/ui/progress'
import { useDetailedGraphStats } from '../../hooks/useDetailedGraphStats'

/**
 * DataQualityCard Component
 *
 * Displays comprehensive data quality metrics from DetailedGraphStats endpoint:
 * - Overall quality score (0-100)
 * - Relationship quality breakdown (high/medium/low confidence)
 * - Data completeness (Wikidata coverage, NOT_APPLICABLE ratio, orphaned entities)
 * - Quality insights and recommendations
 */
export function DataQualityCard() {
  const { data, isLoading, error } = useDetailedGraphStats({
    refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Data Quality Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading quality metrics...</p>
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
            <Shield className="h-5 w-5" />
            Data Quality Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-sm text-red-900 dark:text-red-100">
              Failed to load quality metrics. Please try again later.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  // Calculate quality tier
  const getQualityTier = (score: number) => {
    if (score >= 90) return { label: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900' }
    if (score >= 75) return { label: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900' }
    if (score >= 60) return { label: 'Fair', color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900' }
    return { label: 'Needs Attention', color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900' }
  }

  const qualityTier = getQualityTier(data.quality_score)

  // Extract metrics
  const totalNodes = data.graph_size.total_nodes
  const totalRelationships = data.graph_size.total_relationships
  const highConfRatio = data.relationship_quality.high_confidence_ratio * 100
  const mediumConfRatio = data.relationship_quality.medium_confidence_ratio * 100
  const lowConfRatio = data.relationship_quality.low_confidence_ratio * 100
  const wikidataCoverage = data.data_completeness.wikidata_coverage_ratio * 100
  const notApplicableRatio = data.data_completeness.not_applicable_ratio * 100
  const orphanedEntities = data.data_completeness.orphaned_entities_count

  // Quality insights
  const insights = []
  if (highConfRatio >= 60) {
    insights.push({ type: 'success', message: `${highConfRatio.toFixed(1)}% high-confidence relationships` })
  }
  if (wikidataCoverage >= 70) {
    insights.push({ type: 'success', message: `${wikidataCoverage.toFixed(1)}% Wikidata coverage` })
  }
  if (notApplicableRatio > 20) {
    insights.push({ type: 'warning', message: `${notApplicableRatio.toFixed(1)}% NOT_APPLICABLE relationships need review` })
  }
  if (orphanedEntities > 100) {
    insights.push({ type: 'warning', message: `${orphanedEntities.toLocaleString()} orphaned entities detected` })
  }
  if (lowConfRatio > 15) {
    insights.push({ type: 'warning', message: `${lowConfRatio.toFixed(1)}% low-confidence relationships` })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Data Quality Score
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Composite quality score based on relationship confidence (50%),
                  NOT_APPLICABLE ratio (30%), and Wikidata coverage (20%).
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Quality Score */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-2">
            <span className="text-5xl font-bold">{data.quality_score.toFixed(1)}</span>
            <div className="text-left">
              <Badge className={`${qualityTier.bgColor} ${qualityTier.color} border-none`}>
                {qualityTier.label}
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">out of 100</p>
            </div>
          </div>
          <Progress
            value={data.quality_score}
            className={`h-3 ${
              data.quality_score >= 90
                ? '[&>div]:bg-green-600'
                : data.quality_score >= 75
                ? '[&>div]:bg-blue-600'
                : data.quality_score >= 60
                ? '[&>div]:bg-yellow-600'
                : '[&>div]:bg-red-600'
            }`}
          />
        </div>

        {/* Graph Size Overview */}
        <div className="grid grid-cols-2 gap-4 text-center pt-4 border-t">
          <div>
            <p className="text-2xl font-bold">{totalNodes.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Total Entities</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{totalRelationships.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Relationships</p>
          </div>
        </div>

        {/* Relationship Quality Breakdown */}
        <div className="space-y-2 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span>High Confidence</span>
            </div>
            <span className="font-bold">{highConfRatio.toFixed(1)}%</span>
          </div>
          <Progress value={highConfRatio} className="h-2 [&>div]:bg-green-600" />

          <div className="flex items-center justify-between text-sm mt-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span>Medium Confidence</span>
            </div>
            <span className="font-bold">{mediumConfRatio.toFixed(1)}%</span>
          </div>
          <Progress value={mediumConfRatio} className="h-2 [&>div]:bg-blue-600" />

          <div className="flex items-center justify-between text-sm mt-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <span>Low Confidence</span>
            </div>
            <span className="font-bold">{lowConfRatio.toFixed(1)}%</span>
          </div>
          <Progress value={lowConfRatio} className="h-2 [&>div]:bg-orange-600" />
        </div>

        {/* Data Completeness */}
        <div className="space-y-3 pt-4 border-t">
          <p className="text-sm font-medium">Data Completeness</p>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Wikidata Coverage</span>
            <span className="font-bold">{wikidataCoverage.toFixed(1)}%</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">NOT_APPLICABLE</span>
            <span className={`font-bold ${notApplicableRatio > 20 ? 'text-orange-600' : ''}`}>
              {notApplicableRatio.toFixed(1)}%
            </span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Orphaned Entities</span>
            <span className={`font-bold ${orphanedEntities > 100 ? 'text-orange-600' : ''}`}>
              {orphanedEntities.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Quality Insights */}
        {insights.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <p className="text-sm font-medium mb-3">Quality Insights</p>
            {insights.map((insight, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 text-sm"
              >
                {insight.type === 'success' ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-orange-600 flex-shrink-0 mt-0.5" />
                )}
                <span className={insight.type === 'success' ? 'text-green-700 dark:text-green-300' : 'text-orange-700 dark:text-orange-300'}>
                  {insight.message}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Query Time */}
        <div className="pt-3 border-t text-center text-xs text-muted-foreground">
          Query time: {data.query_time_ms.toFixed(0)}ms
        </div>
      </CardContent>
    </Card>
  )
}
