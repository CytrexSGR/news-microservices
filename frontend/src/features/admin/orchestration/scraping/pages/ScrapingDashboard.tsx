import React from 'react';
import { ScrapingHealthCard } from '../components/ScrapingHealthCard';
import { ScrapingMetricsPanel } from '../components/ScrapingMetricsPanel';
import { QueueStatsPanel } from '../components/QueueStatsPanel';
import { CacheStatsPanel } from '../components/CacheStatsPanel';
import { DLQTable } from '../components/DLQTable';
import { useDLQStats } from '../api';

/**
 * Quick Stats Card
 */
const QuickStatCard: React.FC<{
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}> = ({ label, value, trend, trendValue }) => {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {trend && trendValue && (
        <p className={`text-xs mt-1 ${trendColors[trend]}`}>
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
        </p>
      )}
    </div>
  );
};

/**
 * Scraping Dashboard
 *
 * Main overview page for the scraping service.
 * Displays health, metrics, queue stats, cache stats, and DLQ summary.
 */
export const ScrapingDashboard: React.FC = () => {
  const { data: dlqStats } = useDLQStats();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Scraping Dashboard</h1>
          <p className="text-gray-600">
            Monitor and manage the web scraping infrastructure
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <QuickStatCard
          label="DLQ Entries"
          value={dlqStats?.total || 0}
          trend={dlqStats?.pending_retry_count ? 'down' : 'neutral'}
          trendValue={`${dlqStats?.pending_retry_count || 0} pending retry`}
        />
        <QuickStatCard
          label="Blocked Sources"
          value={dlqStats?.by_reason?.blocked || 0}
          trend="neutral"
        />
        <QuickStatCard
          label="Rate Limited"
          value={dlqStats?.by_reason?.rate_limited || 0}
          trend="neutral"
        />
        <QuickStatCard
          label="Parse Errors"
          value={dlqStats?.by_reason?.parse_error || 0}
          trend="neutral"
        />
      </div>

      {/* Health and Metrics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScrapingHealthCard />
        <ScrapingMetricsPanel />
      </div>

      {/* Queue Stats */}
      <QueueStatsPanel />

      {/* Cache Stats */}
      <CacheStatsPanel />

      {/* DLQ Summary */}
      <DLQTable pageSize={10} />
    </div>
  );
};

export default ScrapingDashboard;
