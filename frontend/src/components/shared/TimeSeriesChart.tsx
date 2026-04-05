import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { useTheme } from '@/components/ThemeProvider'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface TimeSeriesChartProps {
  data: any[]
  dataKey: string
  title: string
  xAxisKey?: string
  isLoading?: boolean
}

export function TimeSeriesChart({
  data,
  dataKey,
  title,
  xAxisKey = 'date',
  isLoading = false,
}: TimeSeriesChartProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  const chartColors = {
    stroke: isDark ? '#60a5fa' : '#3b82f6',
    fill: isDark ? 'rgba(96, 165, 250, 0.2)' : 'rgba(59, 130, 246, 0.2)',
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColors.stroke} stopOpacity={0.8} />
                <stop offset="95%" stopColor={chartColors.stroke} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis
              dataKey={xAxisKey}
              stroke={chartColors.text}
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke={chartColors.text}
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#1f2937' : '#ffffff',
                border: `1px solid ${chartColors.grid}`,
                borderRadius: '6px',
                color: isDark ? '#f3f4f6' : '#111827',
              }}
              labelStyle={{
                color: isDark ? '#f3f4f6' : '#111827',
              }}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={chartColors.stroke}
              fillOpacity={1}
              fill="url(#colorValue)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
