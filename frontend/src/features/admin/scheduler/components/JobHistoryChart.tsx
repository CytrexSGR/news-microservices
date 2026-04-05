/**
 * JobHistoryChart Component
 *
 * Displays execution time history as a simple bar chart
 */

import { useMemo } from 'react';

interface ExecutionData {
  timestamp: string;
  duration: number; // milliseconds
  success: boolean;
}

interface JobHistoryChartProps {
  history: ExecutionData[];
  height?: number;
}

export function JobHistoryChart({ history, height = 100 }: JobHistoryChartProps) {
  const chartData = useMemo(() => {
    if (history.length === 0) return { bars: [], maxDuration: 0 };

    const maxDuration = Math.max(...history.map((h) => h.duration));

    const bars = history.map((item) => ({
      ...item,
      heightPercent: (item.duration / maxDuration) * 100,
      time: new Date(item.timestamp),
    }));

    // Sort by timestamp ascending (oldest first, newest last)
    bars.sort((a, b) => a.time.getTime() - b.time.getTime());

    return { bars, maxDuration };
  }, [history]);

  if (history.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground text-sm"
        style={{ height }}
      >
        No execution history
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        className="flex items-end gap-1"
        style={{ height }}
      >
        {chartData.bars.map((bar, idx) => (
          <div
            key={idx}
            className="relative flex-1 group"
            style={{ height: '100%' }}
          >
            <div
              className={`absolute bottom-0 left-0 right-0 rounded-t transition-all ${
                bar.success
                  ? 'bg-green-500 hover:bg-green-400'
                  : 'bg-red-500 hover:bg-red-400'
              }`}
              style={{ height: `${bar.heightPercent}%`, minHeight: '2px' }}
            />
            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
              <div className="bg-popover text-popover-foreground text-xs rounded-md px-2 py-1 shadow-lg border whitespace-nowrap">
                <div className="font-medium">
                  {(bar.duration / 1000).toFixed(2)}s
                </div>
                <div className="text-muted-foreground">
                  {bar.time.toLocaleTimeString()}
                </div>
                <div className={bar.success ? 'text-green-500' : 'text-red-500'}>
                  {bar.success ? 'Success' : 'Failed'}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>
          {chartData.bars.length > 0
            ? chartData.bars[0].time.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            : ''}
        </span>
        <span>
          Max: {(chartData.maxDuration / 1000).toFixed(1)}s
        </span>
        <span>
          {chartData.bars.length > 0
            ? chartData.bars[chartData.bars.length - 1].time.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            : ''}
        </span>
      </div>
    </div>
  );
}
