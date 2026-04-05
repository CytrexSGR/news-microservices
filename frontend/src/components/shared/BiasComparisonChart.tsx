import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { BiasAnalysis } from '@/api/narrative';
import { Card } from '@/components/ui/Card';

interface BiasComparisonChartProps {
  biasAnalyses: BiasAnalysis[];
  height?: number;
  groupBy?: 'source' | 'perspective';
}

/**
 * BiasComparisonChart - Visualize bias scores and sentiment across sources
 *
 * Features:
 * - Horizontal bar chart with bias scores (-1 to +1)
 * - Color-coded bias labels (left, center, right)
 * - Grouped by source or perspective
 * - Shows average sentiment alongside bias
 * - Reference line at center (0)
 *
 * @param biasAnalyses - Array of bias analyses to visualize
 * @param height - Chart height in pixels (default: 400)
 * @param groupBy - Group data by 'source' or 'perspective' (default: 'source')
 */
export function BiasComparisonChart({
  biasAnalyses,
  height = 400,
  groupBy = 'source',
}: BiasComparisonChartProps) {
  // Get bias label and color
  const getBiasLabelAndColor = (
    biasScore: number
  ): { label: string; color: string } => {
    if (biasScore < -0.5) return { label: 'Left', color: '#3b82f6' }; // blue-500
    if (biasScore < -0.2) return { label: 'Center-Left', color: '#60a5fa' }; // blue-400
    if (biasScore < 0.2) return { label: 'Center', color: '#6b7280' }; // gray-500
    if (biasScore < 0.5) return { label: 'Center-Right', color: '#f87171' }; // red-400
    return { label: 'Right', color: '#ef4444' }; // red-500
  };

  // Aggregate data by groupBy field
  const chartData = useMemo(() => {
    const groups: Record<
      string,
      { biasScores: number[]; sentiments: number[]; count: number }
    > = {};

    biasAnalyses.forEach((analysis) => {
      const key =
        groupBy === 'source'
          ? analysis.source || 'Unknown'
          : analysis.perspective || 'Unknown';

      if (!groups[key]) {
        groups[key] = { biasScores: [], sentiments: [], count: 0 };
      }

      groups[key].biasScores.push(analysis.bias_score);
      groups[key].sentiments.push(analysis.sentiment);
      groups[key].count += 1;
    });

    // Calculate averages and map to chart format
    return Object.entries(groups)
      .map(([key, data]) => {
        const avgBias =
          data.biasScores.reduce((sum, s) => sum + s, 0) / data.biasScores.length;
        const avgSentiment =
          data.sentiments.reduce((sum, s) => sum + s, 0) / data.sentiments.length;
        const { label, color } = getBiasLabelAndColor(avgBias);

        return {
          name: key,
          biasScore: avgBias,
          sentiment: avgSentiment,
          biasLabel: label,
          color,
          count: data.count,
        };
      })
      .sort((a, b) => a.biasScore - b.biasScore); // Sort by bias score
  }, [biasAnalyses, groupBy]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;

      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <div className="font-semibold mb-2">{data.name}</div>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: data.color }}
              />
              <span>
                Bias: <span style={{ color: data.color }}>{data.biasLabel}</span> (
                {data.biasScore.toFixed(2)})
              </span>
            </div>
            <div>
              Sentiment:{' '}
              <span
                className={
                  data.sentiment > 0.3
                    ? 'text-green-500'
                    : data.sentiment < -0.3
                    ? 'text-red-500'
                    : 'text-gray-500'
                }
              >
                {data.sentiment.toFixed(2)}
              </span>
            </div>
            <div className="text-muted-foreground">
              Articles: {data.count}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  if (!biasAnalyses || biasAnalyses.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Bias Comparison</h3>
        <div className="text-center py-12 text-muted-foreground">
          No bias analysis data available
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Bias Comparison</h3>
        <p className="text-sm text-muted-foreground">
          Average bias score by {groupBy} • Center line at 0
        </p>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
          <XAxis
            type="number"
            domain={[-1, 1]}
            ticks={[-1, -0.5, 0, 0.5, 1]}
            stroke="#888"
          />
          <YAxis type="category" dataKey="name" stroke="#888" width={110} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} />
          <Legend
            content={() => (
              <div className="flex justify-center gap-6 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-blue-500" />
                  <span>Left</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-blue-400" />
                  <span>Center-Left</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-gray-500" />
                  <span>Center</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-400" />
                  <span>Center-Right</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500" />
                  <span>Right</span>
                </div>
              </div>
            )}
          />
          <ReferenceLine x={0} stroke="#888" strokeWidth={2} strokeDasharray="3 3" />
          <Bar dataKey="biasScore" name="Bias Score" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Bias Distribution Summary */}
      <div className="mt-6 pt-4 border-t">
        <h4 className="text-sm font-semibold mb-3">Distribution Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {['Left', 'Center-Left', 'Center', 'Center-Right', 'Right'].map((label) => {
            const count = chartData.filter((d) => d.biasLabel === label).length;
            const color = chartData.find((d) => d.biasLabel === label)?.color || '#gray';
            return (
              <div
                key={label}
                className="text-center p-3 rounded-lg"
                style={{
                  backgroundColor: `${color}15`,
                  border: `1px solid ${color}40`,
                }}
              >
                <div className="text-2xl font-bold" style={{ color }}>
                  {count}
                </div>
                <div className="text-xs text-muted-foreground mt-1">{label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sentiment vs Bias Scatter (Optional - Future Enhancement) */}
      <div className="mt-4 text-center text-xs text-muted-foreground">
        {chartData.length} {groupBy === 'source' ? 'sources' : 'perspectives'} analyzed
      </div>
    </Card>
  );
}
