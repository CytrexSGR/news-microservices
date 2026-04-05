import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Lightbulb, CheckCircle2, AlertTriangle, XCircle, TrendingUp } from 'lucide-react'
import type { FeedQualityV2Response } from '@/types/feedServiceAdmin'

interface QualityRecommendationsProps {
  quality: FeedQualityV2Response
}

type Priority = 'high' | 'medium' | 'low' | 'info'

interface Recommendation {
  priority: Priority
  title: string
  description: string
  action?: string
}

const priorityConfig = {
  high: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    badge: 'bg-red-100 text-red-800',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    badge: 'bg-yellow-100 text-yellow-800',
  },
  low: {
    icon: TrendingUp,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-800',
  },
  info: {
    icon: CheckCircle2,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    badge: 'bg-green-100 text-green-800',
  },
}

export function QualityRecommendations({ quality }: QualityRecommendationsProps) {
  const recommendations = generateRecommendations(quality)

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Lightbulb className="h-5 w-5" />
        Recommendations & Actions
      </h3>

      <div className="space-y-3">
        {recommendations.length > 0 ? (
          recommendations.map((rec, index) => {
            const config = priorityConfig[rec.priority]
            const Icon = config.icon

            return (
              <div
                key={index}
                className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor}`}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`h-5 w-5 ${config.color} mt-0.5 flex-shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">{rec.title}</span>
                      <Badge className={`text-xs ${config.badge}`}>
                        {rec.priority.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{rec.description}</p>
                    {rec.action && (
                      <div className="text-xs font-medium text-gray-700 mt-2">
                        → {rec.action}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500 opacity-50" />
            <p className="text-sm font-medium">Feed Quality is Excellent!</p>
            <p className="text-xs mt-1">No immediate actions needed. Continue monitoring.</p>
          </div>
        )}

        {/* Source Quality Recommendations from API */}
        {quality.recommendations && quality.recommendations.length > 0 && (
          <div className="mt-4 p-3 rounded-lg border bg-muted/30">
            <div className="text-xs font-medium mb-2">System Recommendations</div>
            <ul className="text-xs text-muted-foreground space-y-1">
              {quality.recommendations.map((rec, i) => (
                <li key={i}>• {rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  )
}

// Generate recommendations based on quality metrics
function generateRecommendations(quality: FeedQualityV2Response): Recommendation[] {
  const recommendations: Recommendation[] = []
  const { component_scores, quality_score, admiralty_code, red_flags, data_stats, trend } = quality

  // Critical Issues (High Priority)
  // Note: Check for null before comparing (Phase 1.1 - scores can be null)
  if (quality_score !== null && quality_score < 50) {
    recommendations.push({
      priority: 'high',
      title: 'Critical Quality Issues',
      description: `Overall quality score of ${quality_score.toFixed(1)} is below acceptable threshold`,
      action: 'Review feed configuration and consider pausing until quality improves',
    })
  }

  if (admiralty_code.code === 'F') {
    recommendations.push({
      priority: 'high',
      title: 'Unreliable Source',
      description: 'Source has failed reliability assessment (Code F)',
      action: 'Do not use for production. Consider removing or replacing this feed',
    })
  }

  // Article Quality Issues
  if (component_scores.article_quality.score !== null && component_scores.article_quality.score < 50) {
    recommendations.push({
      priority: 'high',
      title: 'Low Article Quality',
      description: `Article quality score of ${component_scores.article_quality.score.toFixed(1)} indicates poor content quality`,
      action: 'Review article analysis settings and consider enabling content enrichment',
    })
  }

  // Red Flags
  if (Object.keys(red_flags).length > 0) {
    const totalFlagged = Object.values(red_flags).reduce((sum, val) => sum + val, 0)
    recommendations.push({
      priority: 'high',
      title: 'Quality Red Flags Detected',
      description: `${Object.keys(red_flags).length} types of quality issues affecting ${totalFlagged.toFixed(0)}% of articles`,
      action: 'Review red flag details and implement quality filters',
    })
  }

  // Operational Issues
  if (component_scores.operational.score !== null && component_scores.operational.score < 70) {
    recommendations.push({
      priority: 'medium',
      title: 'Operational Reliability Issues',
      description: `Operational score of ${component_scores.operational.score.toFixed(1)} indicates fetch/reliability problems`,
      action: 'Check feed health and error logs. Consider adjusting fetch interval',
    })
  }

  if (component_scores.operational.consecutive_failures > 3) {
    recommendations.push({
      priority: 'medium',
      title: 'Recent Fetch Failures',
      description: `${component_scores.operational.consecutive_failures} consecutive failures detected`,
      action: 'Verify feed URL is still valid and accessible',
    })
  }

  // Freshness Issues
  if (component_scores.freshness_consistency.score !== null && component_scores.freshness_consistency.score < 50) {
    recommendations.push({
      priority: 'medium',
      title: 'Freshness & Consistency Issues',
      description: 'Feed is not updating frequently or consistently',
      action: 'Review fetch interval settings and verify feed is still active',
    })
  }

  // Data Coverage Issues
  if (data_stats.coverage_percentage < 50) {
    recommendations.push({
      priority: 'medium',
      title: 'Low Analysis Coverage',
      description: `Only ${data_stats.coverage_percentage.toFixed(0)}% of articles have been analyzed`,
      action: 'Enable auto-analysis for more reliable quality metrics',
    })
  }

  // Improvement Opportunities (Low Priority)
  if (quality_score !== null && quality_score >= 60 && quality_score < 75) {
    recommendations.push({
      priority: 'low',
      title: 'Quality Improvement Opportunity',
      description: 'Feed meets basic standards but has room for improvement',
      action: 'Focus on article quality improvements to reach "Reliable" (Code B) status',
    })
  }

  // Positive Trends
  if (trend === 'improving' && quality_score !== null && quality_score >= 70) {
    recommendations.push({
      priority: 'info',
      title: 'Positive Quality Trend',
      description: 'Feed quality is improving - continue current configuration',
      action: 'Monitor progress and maintain current quality standards',
    })
  }

  if (quality_score !== null && quality_score >= 85 && admiralty_code.code === 'A') {
    recommendations.push({
      priority: 'info',
      title: 'Excellent Feed Quality',
      description: 'Feed achieves top-tier reliability standards (Code A)',
      action: 'Maintain current practices. Consider as reference for other feeds',
    })
  }

  // Sort by priority
  const priorityOrder: Record<Priority, number> = { high: 0, medium: 1, low: 2, info: 3 }
  return recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])
}
