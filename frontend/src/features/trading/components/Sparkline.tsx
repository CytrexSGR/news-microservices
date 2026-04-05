/**
 * Sparkline Component
 *
 * Mini line chart for displaying 24h indicator trends
 */

import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  color = '#3b82f6',
  height = 40
}) => {
  // Convert array to chart data format
  const chartData = data.map((value, index) => ({
    index,
    value,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
