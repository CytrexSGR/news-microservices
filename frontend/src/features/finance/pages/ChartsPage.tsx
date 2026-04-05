import { BarChart3 } from 'lucide-react';

export function ChartsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center space-x-3">
        <BarChart3 className="w-8 h-8 text-[#00D4FF]" />
        <div>
          <h1 className="text-3xl font-bold">Professional Charts</h1>
          <p className="text-gray-400 mt-1">TradingView-style candlestick charts with technical indicators</p>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-12 text-center">
        <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-300 mb-2">Professional Charting Coming Soon</h2>
        <p className="text-gray-500 mb-8">
          Advanced candlestick charts with multiple timeframes and technical indicators
        </p>

        {/* Features Preview */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4 text-left">
            <div className="text-sm font-bold text-[#00D4FF] mb-2">Timeframes</div>
            <div className="text-xs text-gray-400">1min • 5min • 15min • 1h • 1d</div>
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4 text-left">
            <div className="text-sm font-bold text-[#00D4FF] mb-2">Indicators</div>
            <div className="text-xs text-gray-400">MA • RSI • MACD • Bollinger</div>
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4 text-left">
            <div className="text-sm font-bold text-[#00D4FF] mb-2">Features</div>
            <div className="text-xs text-gray-400">Zoom • Pan • Compare • Export</div>
          </div>
        </div>

        {/* Mock chart visualization */}
        <div className="mt-8 bg-[#0B0E11] border border-gray-700 rounded p-6 max-w-4xl mx-auto">
          <div className="h-64 flex items-end justify-around space-x-1">
            {[60, 45, 70, 55, 80, 75, 85, 90, 65, 70, 75, 80, 85, 75, 70, 65, 70, 75, 80, 85].map((height, i) => (
              <div
                key={i}
                className="w-4 bg-gradient-to-t from-[#00D4FF]/20 to-[#00D4FF]/50 rounded-t"
                style={{ height: `${height}%` }}
              ></div>
            ))}
          </div>
          <div className="text-xs text-gray-500 mt-4">Candlestick Chart Visualization</div>
        </div>
      </div>
    </div>
  );
}
