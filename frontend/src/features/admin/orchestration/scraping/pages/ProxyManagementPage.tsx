import React from 'react';
import { ProxyListTable } from '../components/ProxyListTable';
import { useProxyStats, useBrowserStatus } from '../api';
import { Card } from '@/components/ui/Card';

/**
 * Stats Overview
 */
const StatsOverview: React.FC = () => {
  const { data: proxyStats, isLoading: proxyLoading } = useProxyStats();
  const { data: browserStatus, isLoading: browserLoading } = useBrowserStatus();

  if (proxyLoading || browserLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-24 bg-gray-100 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {/* Proxy Stats */}
      <Card>
        <div className="p-4">
          <p className="text-sm text-gray-600">Total Proxies</p>
          <p className="text-2xl font-bold">{proxyStats?.total || 0}</p>
          <p className="text-xs text-gray-500 mt-1">
            {proxyStats?.healthy || 0} healthy
          </p>
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <p className="text-sm text-gray-600">Proxy Success Rate</p>
          <p
            className={`text-2xl font-bold ${
              (proxyStats?.overall_success_rate || 0) >= 0.9
                ? 'text-green-600'
                : (proxyStats?.overall_success_rate || 0) >= 0.7
                ? 'text-yellow-600'
                : 'text-red-600'
            }`}
          >
            {((proxyStats?.overall_success_rate || 0) * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Avg {proxyStats?.avg_response_time_ms || 0}ms
          </p>
        </div>
      </Card>

      {/* Browser Stats */}
      <Card>
        <div className="p-4">
          <p className="text-sm text-gray-600">Browser Sessions</p>
          <p className="text-2xl font-bold">{browserStatus?.total_sessions || 0}</p>
          <p className="text-xs text-gray-500 mt-1">
            {browserStatus?.active_sessions || 0} active
          </p>
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <p className="text-sm text-gray-600">Browser Memory</p>
          <p className="text-2xl font-bold">
            {browserStatus?.memory_usage_mb?.toFixed(0) || 0} MB
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {browserStatus?.instances_running || 0}/{browserStatus?.max_instances || 0} instances
          </p>
        </div>
      </Card>
    </div>
  );
};

/**
 * Proxy Type Distribution
 */
const ProxyTypeDistribution: React.FC = () => {
  const { data: proxyStats } = useProxyStats();

  if (!proxyStats?.by_type) return null;

  return (
    <Card>
      <div className="p-4">
        <h3 className="font-semibold mb-3">Proxy Types</h3>
        <div className="flex gap-4">
          {Object.entries(proxyStats.by_type).map(([type, count]) => (
            <div key={type} className="flex items-center gap-2">
              <span
                className={`px-2 py-1 rounded text-xs font-medium uppercase ${
                  type === 'http'
                    ? 'bg-blue-100 text-blue-800'
                    : type === 'https'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-purple-100 text-purple-800'
                }`}
              >
                {type}
              </span>
              <span className="font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

/**
 * Proxy Management Page
 *
 * Page for managing the proxy pool.
 */
export const ProxyManagementPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Proxy Management</h1>
          <p className="text-gray-600">
            Manage proxy pool and browser instances
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      <StatsOverview />

      {/* Proxy Type Distribution */}
      <ProxyTypeDistribution />

      {/* Proxy List */}
      <ProxyListTable />
    </div>
  );
};

export default ProxyManagementPage;
