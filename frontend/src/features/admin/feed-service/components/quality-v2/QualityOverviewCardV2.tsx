import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Shield, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react'
import type { FeedQualityV2Response } from '@/types/feedServiceAdmin'

interface QualityOverviewCardV2Props {
  quality: FeedQualityV2Response
}

const admiraltyColors = {
  green: 'bg-green-100 text-green-800 border-green-300',
  blue: 'bg-blue-100 text-blue-800 border-blue-300',
  yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  orange: 'bg-orange-100 text-orange-800 border-orange-300',
  red: 'bg-red-100 text-red-800 border-red-300',
  gray: 'bg-gray-100 text-gray-800 border-gray-300',
}

const confidenceColors = {
  high: 'bg-green-50 text-green-700 border-green-200',
  medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  low: 'bg-orange-50 text-orange-700 border-orange-200',
}

const TrendIcon = ({ trend }: { trend: string }) => {
  if (trend === 'improving') return <TrendingUp className="h-4 w-4 text-green-600" />
  if (trend === 'declining') return <TrendingDown className="h-4 w-4 text-red-600" />
  return <Minus className="h-4 w-4 text-gray-600" />
}

export function QualityOverviewCardV2({ quality }: QualityOverviewCardV2Props) {
  const _admiraltyColorClass =
    admiraltyColors[quality.admiralty_code.color as keyof typeof admiraltyColors] ||
    admiraltyColors.gray
  const confidenceColorClass =
    confidenceColors[quality.confidence as keyof typeof confidenceColors] ||
    confidenceColors.medium

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Feed Quality V2
          </h3>
          <p className="text-sm text-muted-foreground mt-1">{quality.feed_name}</p>
        </div>
        <Badge className={`text-xs border ${confidenceColorClass}`}>
          {quality.confidence} confidence
        </Badge>
      </div>

      {/* Admiralty Code Display */}
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg border-2 ${admiraltyColorClass}">
          <div>
            <div className="text-3xl font-bold">{quality.admiralty_code.code}</div>
            <div className="text-sm font-medium mt-1">{quality.admiralty_code.label}</div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">
              {quality.quality_score !== null ? quality.quality_score.toFixed(1) : 'N/A'}
            </div>
            <div className="text-sm text-muted-foreground">Quality Score</div>
            {quality.quality_score === null && (
              <div className="text-xs text-orange-600 mt-1">Insufficient data</div>
            )}
          </div>
        </div>

        {/* Trend and Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg border bg-card">
            <div className="flex items-center gap-2 mb-1">
              <TrendIcon trend={quality.trend} />
              <span className="text-xs font-medium uppercase">{quality.trend}</span>
            </div>
            <div className="text-xs text-muted-foreground">Trend</div>
          </div>

          <div className="p-3 rounded-lg border bg-card">
            <div className="text-lg font-semibold">
              {quality.data_stats.articles_analyzed}
            </div>
            <div className="text-xs text-muted-foreground">
              Articles Analyzed ({quality.data_stats.coverage_percentage.toFixed(0)}%)
            </div>
          </div>
        </div>

        {/* Component Scores Preview */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Component Breakdown</div>
          <div className="space-y-1.5">
            <ScoreBar
              label="Article Quality"
              score={quality.component_scores.article_quality.score}
              weight={quality.component_scores.article_quality.weight}
            />
            <ScoreBar
              label="Source Credibility"
              score={quality.component_scores.source_credibility.score}
              weight={quality.component_scores.source_credibility.weight}
            />
            <ScoreBar
              label="Operational"
              score={quality.component_scores.operational.score}
              weight={quality.component_scores.operational.weight}
            />
            <ScoreBar
              label="Freshness"
              score={quality.component_scores.freshness_consistency.score}
              weight={quality.component_scores.freshness_consistency.weight}
            />
          </div>
        </div>

        {/* Red Flags (if any) */}
        {Object.keys(quality.red_flags).length > 0 && (
          <div className="p-3 rounded-lg border-l-4 border-red-500 bg-red-50">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
              <div className="text-sm text-red-900">
                <div className="font-medium mb-1">Quality Issues Detected</div>
                <ul className="list-disc list-inside text-xs space-y-0.5">
                  {Object.entries(quality.red_flags).map(([key, value]) => (
                    <li key={key}>
                      {key}: {value}% of articles affected
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

// Helper Component for Score Bars
function ScoreBar({ label, score, weight }: { label: string; score: number | null; weight: number }) {
  const hasScore = score !== null
  const percentage = hasScore ? (score / 100) * 100 : 0
  const color = !hasScore
    ? 'bg-gray-300'
    : score >= 80
      ? 'bg-green-500'
      : score >= 60
        ? 'bg-blue-500'
        : score >= 40
          ? 'bg-yellow-500'
          : 'bg-red-500'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium">
          {label} ({(weight * 100).toFixed(0)}%)
        </span>
        <span className={`text-muted-foreground ${!hasScore ? 'text-orange-600' : ''}`}>
          {hasScore ? `${score.toFixed(1)}/100` : 'N/A (insufficient data)'}
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
