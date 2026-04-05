/**
 * Metric Card - Financial metric display component
 *
 * Displays key trading metrics with:
 * - Icon
 * - Value
 * - Change indicator (up/down/neutral)
 * - Trend-based coloring
 */

import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
}

export function MetricCard({ title, value, change, trend, icon }: MetricCardProps) {
  const trendColors = {
    up: 'text-[#26A69A] bg-[#26A69A]/10',
    down: 'text-[#EF5350] bg-[#EF5350]/10',
    neutral: 'text-gray-400 bg-gray-400/10',
  }

  const valueColors = {
    up: 'text-[#26A69A]',
    down: 'text-[#EF5350]',
    neutral: 'text-white',
  }

  return (
    <Card className="bg-[#1A1F2E] border-gray-800 p-6 hover:bg-[#1F2937] transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-400 text-sm font-medium mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', valueColors[trend])}>
            {value}
          </p>
          <Badge
            variant="outline"
            className={cn('text-xs font-normal', trendColors[trend])}
          >
            {change}
          </Badge>
        </div>

        <div className={cn(
          'p-3 rounded-lg',
          trendColors[trend]
        )}>
          {icon}
        </div>
      </div>
    </Card>
  )
}
