/**
 * ResearchStatsPage
 *
 * Comprehensive research usage statistics:
 * - Period selection
 * - Multiple timeframe comparison
 * - Detailed breakdowns
 */

import { useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { ResearchStatsPanel } from '../components/ResearchStatsPanel';
import { UsageStatsCard } from '../components/UsageStatsCard';

type Period = 7 | 30 | 90 | 365;

export function ResearchStatsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<Period>(30);

  const periods: { value: Period; label: string }[] = [
    { value: 7, label: 'Last 7 days' },
    { value: 30, label: 'Last 30 days' },
    { value: 90, label: 'Last 90 days' },
    { value: 365, label: 'Last year' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <BarChart3 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-foreground">
              Research Statistics
            </h1>
            <p className="text-sm text-muted-foreground">
              Usage analytics and cost breakdown
            </p>
          </div>
        </div>

        {/* Period Selector */}
        <div className="flex items-center gap-2">
          {periods.map((period) => (
            <button
              key={period.value}
              onClick={() => setSelectedPeriod(period.value)}
              className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                selectedPeriod === period.value
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-card border-border text-muted-foreground hover:border-primary/50'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Stats Panel */}
      <ResearchStatsPanel days={selectedPeriod} />

      {/* Comparison Cards */}
      <div>
        <h2 className="text-lg font-medium text-foreground mb-4">
          Quick Comparison
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          <UsageStatsCard days={7} />
          <UsageStatsCard days={30} />
          <UsageStatsCard days={90} />
        </div>
      </div>
    </div>
  );
}
