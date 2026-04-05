/**
 * MarketSparkline Component - Lightweight mini-chart for price trends
 * SVG-based, no heavy chart dependencies
 */

import { useMemo } from 'react'

interface MarketSparklineProps {
  data: number[]
  width?: number
  height?: number
  color?: 'green' | 'red' | 'blue'
  strokeWidth?: number
}

export function MarketSparkline({
  data,
  width = 100,
  height = 30,
  color = 'blue',
  strokeWidth = 2,
}: MarketSparklineProps) {
  // Calculate SVG path
  const path = useMemo(() => {
    if (data.length < 2) return ''

    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1 // Avoid division by zero

    // Normalize data to fit within height
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width
      const y = height - ((value - min) / range) * height
      return { x, y }
    })

    // Build SVG path string
    const pathString = points
      .map((point, index) => {
        const command = index === 0 ? 'M' : 'L'
        return `${command} ${point.x.toFixed(2)},${point.y.toFixed(2)}`
      })
      .join(' ')

    return pathString
  }, [data, width, height])

  const strokeColor = useMemo(() => {
    const colors = {
      green: 'stroke-green-500',
      red: 'stroke-red-500',
      blue: 'stroke-blue-500',
    }
    return colors[color]
  }, [color])

  if (data.length < 2) {
    return (
      <svg width={width} height={height} className="text-muted-foreground">
        <text x={width / 2} y={height / 2} textAnchor="middle" fontSize="10" fill="currentColor">
          N/A
        </text>
      </svg>
    )
  }

  return (
    <svg width={width} height={height} className={strokeColor}>
      <path
        d={path}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
