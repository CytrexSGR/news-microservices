// frontend/src/features/intelligence/components/EscalationPanel/FinancePanel.tsx
import type { FinanceIndicators } from "../../types/escalation";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface FinancePanelProps {
  finance: FinanceIndicators;
}

export function FinancePanel({ finance }: FinancePanelProps) {
  const formatValue = (value: number | null, decimals = 2): string => {
    if (value === null || value === undefined) return "N/A";
    return value.toFixed(decimals);
  };

  const getTrendIcon = (value: number | null) => {
    if (value === null) return <Minus className="w-4 h-4 text-gray-400" />;
    if (value > 0.05) return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (value < -0.05) return <TrendingDown className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const indicators = [
    {
      label: "VIX",
      value: finance.vix,
      change: finance.vixChange,
      description: "Fear index",
      format: (v: number | null) => formatValue(v, 1),
    },
    {
      label: "DXY Signal",
      value: finance.dxy,
      description: "Dollar strength",
      format: (v: number | null) => formatValue(v, 2),
    },
    {
      label: "Yield Curve",
      value: finance.yieldSpread,
      description: "10Y-2Y spread",
      format: (v: number | null) => formatValue(v, 2),
    },
    {
      label: "Carry Trade",
      value: finance.carryTrade,
      description: "Risk appetite",
      format: (v: number | null) => formatValue(v, 2),
    },
  ];

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-4">Financial Indicators</h3>

      <div className="grid grid-cols-2 gap-4">
        {indicators.map((ind) => (
          <div key={ind.label} className="flex flex-col">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{ind.label}</span>
              {getTrendIcon(ind.value)}
            </div>
            <span className="text-lg font-semibold text-foreground">
              {ind.format(ind.value)}
            </span>
            <span className="text-xs text-muted-foreground/70">{ind.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
