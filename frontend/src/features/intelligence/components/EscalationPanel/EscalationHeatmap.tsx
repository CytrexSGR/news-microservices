// frontend/src/features/intelligence/components/EscalationPanel/EscalationHeatmap.tsx
import type { RegionHeatmap } from "../../types/escalation";

interface EscalationHeatmapProps {
  heatmap: RegionHeatmap[];
}

export function EscalationHeatmap({ heatmap }: EscalationHeatmapProps) {
  const getHeatColor = (score: number): string => {
    if (score >= 0.8) return "bg-gray-900 text-white";
    if (score >= 0.6) return "bg-red-500 text-white";
    if (score >= 0.4) return "bg-orange-400 text-white";
    if (score >= 0.2) return "bg-yellow-300 text-gray-900";
    return "bg-green-200 text-gray-900";
  };

  const formatScore = (score: number): string => {
    return (score * 100).toFixed(0);
  };

  if (heatmap.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Escalation by Region</h3>
        <p className="text-sm text-muted-foreground/70 text-center py-4">
          No escalation data available
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-4">Escalation by Region</h3>

      {/* Header */}
      <div className="grid grid-cols-4 gap-2 mb-2 text-xs text-muted-foreground">
        <div>Region</div>
        <div className="text-center">Geo</div>
        <div className="text-center">Mil</div>
        <div className="text-center">Econ</div>
      </div>

      {/* Rows */}
      <div className="space-y-1">
        {heatmap.map((row) => (
          <div key={row.region} className="grid grid-cols-4 gap-2 items-center">
            <div className="text-sm font-medium text-foreground truncate">
              {row.region}
            </div>
            <div className={`text-center rounded px-2 py-1 text-xs ${getHeatColor(row.geopolitical)}`}>
              {formatScore(row.geopolitical)}
            </div>
            <div className={`text-center rounded px-2 py-1 text-xs ${getHeatColor(row.military)}`}>
              {formatScore(row.military)}
            </div>
            <div className={`text-center rounded px-2 py-1 text-xs ${getHeatColor(row.economic)}`}>
              {formatScore(row.economic)}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <span>Low</span>
        <div className="flex gap-0.5">
          <div className="w-4 h-3 bg-green-200 dark:bg-green-800 rounded-sm" />
          <div className="w-4 h-3 bg-yellow-300 dark:bg-yellow-700 rounded-sm" />
          <div className="w-4 h-3 bg-orange-400 dark:bg-orange-600 rounded-sm" />
          <div className="w-4 h-3 bg-red-500 rounded-sm" />
          <div className="w-4 h-3 bg-gray-900 dark:bg-gray-100 rounded-sm" />
        </div>
        <span>Critical</span>
      </div>
    </div>
  );
}
