import { Card } from '@/components/ui/Card'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { PieChart as PieChartIcon } from 'lucide-react'
import type { FeedQualityV2Response } from '@/types/feedServiceAdmin'

interface QualityDistributionChartProps {
  quality: FeedQualityV2Response
}

const COLORS = {
  premium: '#10b981',           // green-500
  high_quality: '#3b82f6',      // blue-500
  moderate_quality: '#f59e0b',  // amber-500
  low_quality: '#f97316',       // orange-500
  very_low_quality: '#ef4444',  // red-500
}

const LABELS = {
  premium: 'Premium (90-100)',
  high_quality: 'High Quality (75-89)',
  moderate_quality: 'Moderate (60-74)',
  low_quality: 'Low Quality (40-59)',
  very_low_quality: 'Very Low (0-39)',
}

export function QualityDistributionChart({ quality }: QualityDistributionChartProps) {
  const distribution = quality.quality_distribution

  // Transform distribution into chart data (only include non-zero values)
  const chartData = Object.entries(distribution)
    .filter(([_, value]) => value > 0)
    .map(([key, value]) => ({
      name: LABELS[key as keyof typeof LABELS],
      value: value * 100, // Convert to percentage
      count: Math.round((value * quality.data_stats.articles_analyzed)),
      color: COLORS[key as keyof typeof COLORS],
    }))

  const hasData = chartData.length > 0

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <PieChartIcon className="h-5 w-5" />
        Article Quality Distribution
      </h3>

      {hasData ? (
        <>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name: _name, value }) => `${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload[0]) {
                    const data = payload[0].payload
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-medium text-sm">{data.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          <span className="font-semibold">{data.count}</span> articles
                        </p>
                        <p className="text-xs text-muted-foreground">
                          <span className="font-semibold">{data.value.toFixed(1)}%</span> of analyzed
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                wrapperStyle={{ fontSize: '11px' }}
                iconType="circle"
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Detailed Stats */}
          <div className="mt-4 space-y-2">
            <div className="text-xs font-medium text-muted-foreground mb-2">
              Detailed Distribution
            </div>
            {chartData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between p-2 rounded border"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs font-medium">{item.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-xs font-semibold">{item.count} articles</div>
                  <div className="text-xs text-muted-foreground">{item.value.toFixed(1)}%</div>
                </div>
              </div>
            ))}
          </div>

          {/* Quality Insights */}
          <div className="mt-4 p-3 rounded-lg bg-muted/50 border">
            <div className="text-xs font-medium mb-1">Quality Insights</div>
            <div className="text-xs text-muted-foreground space-y-1">
              {getQualityInsights(distribution, quality.data_stats.articles_analyzed).map(
                (insight, i) => (
                  <p key={i}>• {insight}</p>
                )
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          <PieChartIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No quality data available</p>
          <p className="text-xs mt-1">Articles need analysis before distribution can be shown</p>
        </div>
      )}
    </Card>
  )
}

// Helper to generate insights
function getQualityInsights(
  distribution: Record<string, number>,
  totalArticles: number
): string[] {
  const insights: string[] = []
  const premium = distribution.premium || 0
  const high = distribution.high_quality || 0
  const moderate = distribution.moderate_quality || 0
  const low = distribution.low_quality || 0
  const veryLow = distribution.very_low_quality || 0

  const premiumCount = Math.round(premium * totalArticles)
  const _highCount = Math.round(high * totalArticles)
  const lowCount = Math.round((low + veryLow) * totalArticles)

  if (premiumCount > 0) {
    insights.push(`${premiumCount} premium quality articles (90+ score)`)
  }

  if ((premium + high) > 0.5) {
    insights.push('Majority of articles are high quality (75+)')
  } else if ((premium + high + moderate) > 0.7) {
    insights.push('Most articles meet moderate quality standards (60+)')
  }

  if (lowCount > totalArticles * 0.3) {
    insights.push(`${lowCount} articles need quality improvement (<60 score)`)
  }

  if (veryLow > 0.1) {
    insights.push(`${Math.round(veryLow * 100)}% very low quality - immediate attention needed`)
  }

  if (insights.length === 0) {
    insights.push('Quality distribution is balanced across categories')
  }

  return insights
}
