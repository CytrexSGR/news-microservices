import { useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';
import type { NarrativeFrame } from '@/api/narrative';
import { Card } from '@/components/ui/Card';
import { format } from 'date-fns';

interface FrameTimelineProps {
  frames: NarrativeFrame[];
  height?: number;
  selectedFrameType?: string;
  onFrameClick?: (frame: NarrativeFrame) => void;
}

/**
 * FrameTimeline - Interactive timeline visualization of narrative frames
 *
 * Features:
 * - Scatter plot with time on X-axis, frame types on Y-axis
 * - Color-coded frame types
 * - Size represents confidence (larger = more confident)
 * - Interactive tooltips with frame details
 * - Optional filtering by frame type
 *
 * @param frames - Array of narrative frames to visualize
 * @param height - Chart height in pixels (default: 400)
 * @param selectedFrameType - Optional filter to highlight specific frame type
 * @param onFrameClick - Optional callback when frame is clicked
 */
export function FrameTimeline({
  frames,
  height = 400,
  selectedFrameType,
  onFrameClick,
}: FrameTimelineProps) {
  // Frame type to Y-axis mapping
  const frameTypeToY: Record<string, number> = {
    victim: 6,
    hero: 5,
    threat: 4,
    solution: 3,
    conflict: 2,
    economic: 1,
  };

  // Frame type colors
  const frameTypeColors: Record<string, string> = {
    victim: '#ef4444', // red-500
    hero: '#22c55e', // green-500
    threat: '#f97316', // orange-500
    solution: '#3b82f6', // blue-500
    conflict: '#a855f7', // purple-500
    economic: '#eab308', // yellow-500
  };

  // Transform frames to chart data
  const chartData = useMemo(() => {
    return frames
      .map((frame) => ({
        ...frame,
        timestamp: new Date(frame.created_at).getTime(),
        y: frameTypeToY[frame.frame_type] || 0,
        // Size based on confidence (min: 50, max: 300)
        size: Math.max(50, Math.min(300, frame.confidence * 400)),
        color: frameTypeColors[frame.frame_type] || '#gray',
      }))
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [frames]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const frame = payload[0].payload as NarrativeFrame & {
        timestamp: number;
        y: number;
        size: number;
        color: string;
      };

      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg max-w-sm">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: frame.color }}
            />
            <span className="font-semibold capitalize">{frame.frame_type}</span>
          </div>
          <div className="space-y-1 text-sm text-muted-foreground">
            <div>
              <span className="font-medium">Confidence:</span>{' '}
              {(frame.confidence * 100).toFixed(0)}%
            </div>
            <div>
              <span className="font-medium">Time:</span>{' '}
              {format(new Date(frame.created_at), 'MMM dd, HH:mm')}
            </div>
            {frame.text_excerpt && (
              <div className="mt-2 pt-2 border-t">
                <span className="font-medium">Excerpt:</span>
                <p className="mt-1 text-xs line-clamp-3">{frame.text_excerpt}</p>
              </div>
            )}
            {frame.entities && Object.keys(frame.entities).length > 0 && (
              <div className="mt-2 pt-2 border-t">
                <span className="font-medium">Entities:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {Object.entries(frame.entities).slice(0, 3).map(([type, entities]) => (
                    <span
                      key={type}
                      className="px-1.5 py-0.5 bg-secondary rounded text-xs"
                    >
                      {type}: {(entities as any[]).slice(0, 2).join(', ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom Y-axis tick
  const renderYAxisTick = ({ x, y, payload }: any) => {
    const frameType = Object.keys(frameTypeToY).find(
      (key) => frameTypeToY[key] === payload.value
    );
    const color = frameType ? frameTypeColors[frameType] : '#gray';

    return (
      <g transform={`translate(${x},${y})`}>
        <text
          x={0}
          y={0}
          dy={4}
          textAnchor="end"
          fill={selectedFrameType === frameType ? color : '#888'}
          fontSize={12}
          fontWeight={selectedFrameType === frameType ? 'bold' : 'normal'}
          className="capitalize"
        >
          {frameType || ''}
        </text>
      </g>
    );
  };

  // Custom X-axis tick (format timestamps)
  const renderXAxisTick = ({ x, y, payload }: any) => {
    return (
      <g transform={`translate(${x},${y})`}>
        <text x={0} y={0} dy={16} textAnchor="middle" fill="#888" fontSize={11}>
          {format(new Date(payload.value), 'MMM dd')}
        </text>
      </g>
    );
  };

  if (!frames || frames.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Frame Timeline</h3>
        <div className="text-center py-12 text-muted-foreground">
          No frames available to visualize
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Frame Timeline</h3>
        <p className="text-sm text-muted-foreground">
          {frames.length} frames over time • Size indicates confidence
        </p>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 20, left: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
          <XAxis
            type="number"
            dataKey="timestamp"
            name="Time"
            domain={['dataMin', 'dataMax']}
            tick={renderXAxisTick}
            stroke="#888"
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Frame Type"
            domain={[0, 7]}
            ticks={[1, 2, 3, 4, 5, 6]}
            tick={renderYAxisTick}
            stroke="#888"
          />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <Legend
            verticalAlign="top"
            height={36}
            content={() => (
              <div className="flex justify-center gap-4 mb-2">
                {Object.entries(frameTypeColors).map(([type, color]) => (
                  <div
                    key={type}
                    className="flex items-center gap-1.5"
                    style={{
                      opacity: selectedFrameType && selectedFrameType !== type ? 0.3 : 1,
                    }}
                  >
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs capitalize text-muted-foreground">{type}</span>
                  </div>
                ))}
              </div>
            )}
          />
          <Scatter
            data={chartData}
            fill="#8884d8"
            onClick={onFrameClick ? (data: any) => onFrameClick(data) : undefined}
            style={{ cursor: onFrameClick ? 'pointer' : 'default' }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                fillOpacity={
                  selectedFrameType && selectedFrameType !== entry.frame_type ? 0.2 : 0.8
                }
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Frame Type Counts */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {Object.entries(
          frames.reduce((acc, frame) => {
            acc[frame.frame_type] = (acc[frame.frame_type] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        )
          .sort(([, a], [, b]) => b - a)
          .map(([type, count]) => (
            <div
              key={type}
              className="px-3 py-1.5 rounded-lg text-sm"
              style={{
                backgroundColor: `${frameTypeColors[type]}15`,
                border: `1px solid ${frameTypeColors[type]}40`,
                color: frameTypeColors[type],
                opacity: selectedFrameType && selectedFrameType !== type ? 0.5 : 1,
              }}
            >
              <span className="capitalize font-medium">{type}</span>
              <span className="ml-1.5 opacity-75">({count})</span>
            </div>
          ))}
      </div>
    </Card>
  );
}
