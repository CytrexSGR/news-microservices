import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ReferenceDot, ResponsiveContainer } from 'recharts';

interface Trade {
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  direction: 'long' | 'short';
}

interface TradeTimelineProps {
  trades: Trade[];
  priceData: Array<{ timestamp: string; close: number }>;
}

export const TradeTimeline: React.FC<TradeTimelineProps> = ({ trades, priceData }) => {
  // Prepare chart data with trade markers
  const chartData = priceData.map(point => ({
    timestamp: point.timestamp,
    price: point.close,
    trade: trades.find(t =>
      t.entry_time === point.timestamp || t.exit_time === point.timestamp
    )
  }));

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Trade Timeline ({trades.length} trades)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <YAxis domain={['auto', 'auto']} />
            <Tooltip
              labelFormatter={(value) => new Date(value).toLocaleString()}
              formatter={(value: number) => value.toFixed(2)}
            />
            <Legend />

            <Line
              type="monotone"
              dataKey="price"
              stroke="#8884d8"
              dot={false}
              name="Price"
            />

            {/* Entry points (green dots) */}
            {trades.map((trade, idx) => {
              const entryPoint = chartData.find(d => d.timestamp === trade.entry_time);
              if (!entryPoint) return null;

              return (
                <ReferenceDot
                  key={`entry-${idx}`}
                  x={trade.entry_time}
                  y={trade.entry_price}
                  r={6}
                  fill="green"
                  stroke="none"
                />
              );
            })}

            {/* Exit points (red/green based on profit) */}
            {trades.map((trade, idx) => {
              const exitPoint = chartData.find(d => d.timestamp === trade.exit_time);
              if (!exitPoint) return null;

              return (
                <ReferenceDot
                  key={`exit-${idx}`}
                  x={trade.exit_time}
                  y={trade.exit_price}
                  r={6}
                  fill={trade.pnl > 0 ? 'green' : 'red'}
                  stroke="none"
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 flex gap-2 flex-wrap">
          {trades.map((trade, idx) => (
            <Badge
              key={idx}
              variant={trade.pnl > 0 ? 'default' : 'destructive'}
              className="text-xs"
            >
              {trade.direction.toUpperCase()} {trade.pnl_pct.toFixed(2)}%
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
