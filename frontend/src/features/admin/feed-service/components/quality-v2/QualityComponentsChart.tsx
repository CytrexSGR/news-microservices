import { Card } from '@/components/ui/Card'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { Activity } from 'lucide-react'
import type { ComponentScores } from '@/types/feedServiceAdmin'

interface QualityComponentsChartProps {
  componentScores: ComponentScores
  _feedName: string
}

export function QualityComponentsChart({ componentScores, _feedName }: QualityComponentsChartProps) {
  // Transform component scores into radar chart data
  // Note: Scores can be null if insufficient data (Phase 1.1 change)
  const chartData = [
    {
      component: 'Article Quality',
      score: componentScores.article_quality.score ?? 0,
      weight: componentScores.article_quality.weight * 100,
      fullMark: 100,
      hasData: componentScores.article_quality.score !== null,
    },
    {
      component: 'Source Credibility',
      score: componentScores.source_credibility.score ?? 0,
      weight: componentScores.source_credibility.weight * 100,
      fullMark: 100,
      hasData: componentScores.source_credibility.score !== null,
    },
    {
      component: 'Operational',
      score: componentScores.operational.score ?? 0,
      weight: componentScores.operational.weight * 100,
      fullMark: 100,
      hasData: componentScores.operational.score !== null,
    },
    {
      component: 'Freshness',
      score: componentScores.freshness_consistency.score ?? 0,
      weight: componentScores.freshness_consistency.weight * 100,
      fullMark: 100,
      hasData: componentScores.freshness_consistency.score !== null,
    },
  ]

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Activity className="h-5 w-5" />
        Component Breakdown
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={chartData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="component"
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-medium text-sm">{data.component}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Score: <span className="font-semibold">
                        {data.hasData ? data.score.toFixed(1) : 'N/A'}
                      </span>/100
                      {!data.hasData && (
                        <span className="text-orange-600 ml-1">(insufficient data)</span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Weight: <span className="font-semibold">{data.weight.toFixed(0)}%</span>
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="circle"
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Component Details */}
      <div className="mt-6 space-y-3">
        <div className="text-xs font-medium text-muted-foreground mb-2">Detailed Breakdown</div>

        {/* Article Quality */}
        <ComponentDetail
          title="Article Quality (50%)"
          score={componentScores.article_quality.score}
          breakdown={componentScores.article_quality.breakdown}
        />

        {/* Source Credibility */}
        <ComponentDetail
          title="Source Credibility (20%)"
          score={componentScores.source_credibility.score}
          details={[
            { label: 'Reputation', value: componentScores.source_credibility.reputation_score },
            { label: 'Tier', value: componentScores.source_credibility.credibility_tier },
          ]}
        />

        {/* Operational */}
        <ComponentDetail
          title="Operational (20%)"
          score={componentScores.operational.score}
          details={[
            { label: 'Success Rate', value: componentScores.operational.success_rate ? `${(componentScores.operational.success_rate * 100).toFixed(1)}%` : 'N/A' },
            { label: '7d Uptime', value: componentScores.operational.uptime_7d ? `${(componentScores.operational.uptime_7d * 100).toFixed(1)}%` : 'N/A' },
            { label: '30d Uptime', value: componentScores.operational.uptime_30d ? `${(componentScores.operational.uptime_30d * 100).toFixed(1)}%` : 'N/A' },
          ]}
        />

        {/* Freshness & Consistency */}
        <ComponentDetail
          title="Freshness & Consistency (10%)"
          score={componentScores.freshness_consistency.score}
          details={[
            { label: 'Freshness', value: componentScores.freshness_consistency.freshness ? componentScores.freshness_consistency.freshness.toFixed(1) : 'N/A' },
            { label: 'Consistency', value: componentScores.freshness_consistency.consistency ? componentScores.freshness_consistency.consistency.toFixed(1) : 'N/A' },
          ]}
        />
      </div>
    </Card>
  )
}

// Helper Component
function ComponentDetail({
  title,
  score,
  breakdown,
  details,
}: {
  title: string
  score: number | null
  breakdown?: Record<string, number | null>
  details?: Array<{ label: string; value: string | number }>
}) {
  const hasScore = score !== null

  return (
    <div className="p-3 rounded-lg border bg-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{title}</span>
        <span className={`text-sm font-semibold ${!hasScore ? 'text-muted-foreground' : ''}`}>
          {hasScore ? `${score.toFixed(1)}/100` : 'N/A'}
        </span>
      </div>
      {!hasScore && (
        <div className="text-xs text-orange-600 mb-2">
          Insufficient data for this component
        </div>
      )}
      {breakdown && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          {Object.entries(breakdown).map(([key, value]) => (
            <div key={key} className="flex flex-col">
              <span className="text-muted-foreground capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <span className={`font-medium ${value === null ? 'text-muted-foreground' : ''}`}>
                {value !== null ? value.toFixed(0) : 'N/A'}
              </span>
            </div>
          ))}
        </div>
      )}
      {details && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          {details.map(({ label, value }) => (
            <div key={label} className="flex flex-col">
              <span className="text-muted-foreground">{label}</span>
              <span className="font-medium">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
