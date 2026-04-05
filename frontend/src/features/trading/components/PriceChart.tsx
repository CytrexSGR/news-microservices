/**
 * Price Chart - TradingView Lightweight Charts integration
 *
 * Professional candlestick chart with:
 * - Real-time price updates
 * - Volume bars
 * - Dark theme matching Bybit/Binance
 * - Responsive design
 */

import { useEffect, useRef } from 'react'
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts'
import { Card } from '@/components/ui/Card'

export function PriceChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1A1F2E' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: '#2B3544' },
        horzLines: { color: '#2B3544' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        borderColor: '#2B3544',
      },
      rightPriceScale: {
        borderColor: '#2B3544',
      },
    })

    // Candlestick series - v5.x API (pass series definition as first param)
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26A69A',
      downColor: '#EF5350',
      borderVisible: false,
      wickUpColor: '#26A69A',
      wickDownColor: '#EF5350',
    })

    // Mock data - Will be replaced with real-time WebSocket data
    const mockData = [
      { time: '2024-01-01', open: 95000, high: 96500, low: 94500, close: 96000 },
      { time: '2024-01-02', open: 96000, high: 97500, low: 95500, close: 97000 },
      { time: '2024-01-03', open: 97000, high: 98000, low: 96000, close: 96500 },
      { time: '2024-01-04', open: 96500, high: 97000, low: 95000, close: 95500 },
      { time: '2024-01-05', open: 95500, high: 96000, low: 94000, close: 95000 },
    ]

    candlestickSeries.setData(mockData)

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  return (
    <Card className="bg-[#1A1F2E] border-gray-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold">BTC/USDT:USDT</h2>
          <p className="text-gray-400 text-sm">Perpetual</p>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold text-[#26A69A]">$97,500.00</p>
          <p className="text-sm text-[#26A69A]">+2.4% (24h)</p>
        </div>
      </div>

      <div ref={chartContainerRef} className="rounded-lg overflow-hidden" />
    </Card>
  )
}
