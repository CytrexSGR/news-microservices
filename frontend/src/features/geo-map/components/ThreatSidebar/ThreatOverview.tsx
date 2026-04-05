/**
 * ThreatOverview Component
 *
 * Displays threat level statistics and regional breakdown
 */

import type { SecurityOverview } from '../../types/security.types';

interface ThreatOverviewProps {
  overview: SecurityOverview;
}

export function ThreatOverview({ overview }: ThreatOverviewProps) {
  const stats = [
    {
      label: 'Critical',
      value: overview.critical_count,
      color: 'bg-red-500',
      textColor: 'text-red-400',
    },
    {
      label: 'High',
      value: overview.high_count,
      color: 'bg-orange-500',
      textColor: 'text-orange-400',
    },
    {
      label: 'Medium',
      value: overview.medium_count,
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
    },
  ];

  const totalHighPriority = overview.critical_count + overview.high_count;
  const percentHighPriority =
    overview.total_events > 0
      ? Math.round((totalHighPriority / overview.total_events) * 100)
      : 0;

  return (
    <div className="space-y-4">
      {/* Main Stats */}
      <div className="bg-slate-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-300">Threat Summary</h3>
          <span className="text-xs text-slate-500">
            {percentHighPriority}% high priority
          </span>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-3 gap-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-slate-700/50 rounded-lg p-3 text-center"
            >
              <div className={`text-2xl font-bold ${stat.textColor}`}>
                {stat.value.toLocaleString()}
              </div>
              <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex h-2 rounded-full overflow-hidden bg-slate-700">
            <div
              className="bg-red-500 transition-all"
              style={{
                width: `${
                  overview.total_events > 0
                    ? (overview.critical_count / overview.total_events) * 100
                    : 0
                }%`,
              }}
            />
            <div
              className="bg-orange-500 transition-all"
              style={{
                width: `${
                  overview.total_events > 0
                    ? (overview.high_count / overview.total_events) * 100
                    : 0
                }%`,
              }}
            />
            <div
              className="bg-yellow-500 transition-all"
              style={{
                width: `${
                  overview.total_events > 0
                    ? (overview.medium_count / overview.total_events) * 100
                    : 0
                }%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Regional Breakdown */}
      <div className="bg-slate-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">By Region</h3>
        <div className="space-y-2">
          {Object.entries(overview.by_region)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 6)
            .map(([region, count]) => {
              const percentage =
                overview.total_events > 0
                  ? Math.round((count / overview.total_events) * 100)
                  : 0;

              return (
                <div key={region} className="flex items-center gap-2">
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">{region}</span>
                      <span className="text-slate-500">{count.toLocaleString()}</span>
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}
