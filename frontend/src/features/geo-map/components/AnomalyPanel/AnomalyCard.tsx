// frontend/src/features/geo-map/components/AnomalyPanel/AnomalyCard.tsx

interface AnomalyData {
  entity: string;
  entity_type: string;
  current_count: number;
  baseline_avg: number;
  deviation_factor: number;
  is_anomaly: boolean;
  trend: string;
  category_breakdown: Record<string, number>;
}

interface AnomalyCardProps {
  anomaly: AnomalyData;
  isHighlighted?: boolean;
  onClick?: () => void;
}

const TREND_COLORS: Record<string, string> = {
  spike: 'bg-red-500',
  elevated: 'bg-orange-500',
  normal: 'bg-green-500',
  low: 'bg-blue-500',
};

const TREND_ICONS: Record<string, string> = {
  spike: '📈',
  elevated: '↗️',
  normal: '➡️',
  low: '📉',
};

export function AnomalyCard({ anomaly, isHighlighted, onClick }: AnomalyCardProps) {
  const changePercent = ((anomaly.current_count / anomaly.baseline_avg) - 1) * 100;

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg cursor-pointer transition-all ${
        isHighlighted
          ? 'ring-2 ring-orange-500 bg-slate-700'
          : anomaly.is_anomaly
            ? 'bg-red-900/30 border border-red-700/50 hover:bg-red-900/40'
            : 'bg-slate-800/50 hover:bg-slate-800/70'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{TREND_ICONS[anomaly.trend]}</span>
          <span className="font-semibold">{anomaly.entity}</span>
        </div>
        <span className={`px-2 py-0.5 text-xs rounded ${TREND_COLORS[anomaly.trend]}`}>
          {anomaly.trend.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-sm mb-3">
        <div>
          <div className="text-slate-400 text-xs">Current</div>
          <div className="font-bold text-lg">{anomaly.current_count}</div>
        </div>
        <div>
          <div className="text-slate-400 text-xs">Baseline</div>
          <div className="font-medium">{anomaly.baseline_avg.toFixed(1)}/day</div>
        </div>
        <div>
          <div className="text-slate-400 text-xs">Change</div>
          <div className={`font-bold ${changePercent > 0 ? 'text-red-400' : 'text-green-400'}`}>
            {changePercent > 0 ? '+' : ''}{changePercent.toFixed(0)}%
          </div>
        </div>
      </div>

      <div className="flex gap-1 text-xs">
        {Object.entries(anomaly.category_breakdown).map(([cat, count]) => (
          count > 0 && (
            <span key={cat} className="px-2 py-0.5 bg-slate-700 rounded">
              {cat}: {count}
            </span>
          )
        ))}
      </div>

      {anomaly.is_anomaly && (
        <div className="mt-2 text-xs text-red-400">
          {anomaly.deviation_factor.toFixed(1)} std above baseline
        </div>
      )}
    </div>
  );
}
