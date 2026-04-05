import React from 'react';
import { Card } from '@/components/ui/Card';
import { useSourceProfile, useTestSourceProfile, useResetSourceProfileStats } from '../api';
import type { SourceStatus, ScrapingMethod } from '../types/scraping.types';

interface SourceProfileCardProps {
  domain: string;
  className?: string;
  onEdit?: () => void;
}

/**
 * Status Badge
 */
const StatusBadge: React.FC<{ status: SourceStatus }> = ({ status }) => {
  const colors: Record<SourceStatus, string> = {
    working: 'bg-green-100 text-green-800 border-green-200',
    degraded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    blocked: 'bg-red-100 text-red-800 border-red-200',
    unknown: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

/**
 * Source Profile Card
 *
 * Displays detailed information about a source profile.
 */
export const SourceProfileCard: React.FC<SourceProfileCardProps> = ({
  domain,
  className,
  onEdit,
}) => {
  const { data: profile, isLoading, error, refetch } = useSourceProfile(domain);
  const testProfile = useTestSourceProfile();
  const resetStats = useResetSourceProfileStats();

  const handleTest = async () => {
    try {
      const result = await testProfile.mutateAsync(domain);
      alert(
        result.success
          ? `Test successful!\nMethod: ${result.method_used}\nResponse time: ${result.response_time_ms}ms`
          : `Test failed: ${result.error}`
      );
      refetch();
    } catch (err) {
      console.error('Test failed:', err);
    }
  };

  const handleResetStats = async () => {
    if (!confirm('Reset statistics for this source?')) return;
    try {
      await resetStats.mutateAsync(domain);
      refetch();
    } catch (err) {
      console.error('Reset failed:', err);
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <p className="text-red-500">Failed to load profile: {error.message}</p>
        </div>
      </Card>
    );
  }

  if (!profile) return null;

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <Card className={className}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-xl font-semibold">{profile.domain}</h3>
            <div className="mt-2">
              <StatusBadge status={profile.status} />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleTest}
              disabled={testProfile.isPending}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              {testProfile.isPending ? 'Testing...' : 'Test'}
            </button>
            {onEdit && (
              <button
                onClick={onEdit}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                Edit
              </button>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Success Rate</p>
            <p
              className={`text-xl font-bold ${
                profile.success_rate >= 0.9
                  ? 'text-green-600'
                  : profile.success_rate >= 0.7
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }`}
            >
              {(profile.success_rate * 100).toFixed(1)}%
            </p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Avg Response</p>
            <p className="text-xl font-bold">{profile.avg_response_time_ms}ms</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Failures</p>
            <p className="text-xl font-bold text-red-600">{profile.failure_count}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Rate Limit</p>
            <p className="text-xl font-bold">{profile.rate_limit_rpm || 'N/A'}/min</p>
          </div>
        </div>

        {/* Configuration */}
        <div className="space-y-3 mb-6">
          <h4 className="text-sm font-medium text-gray-700">Configuration</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Method:</span>
              <span className="font-medium">{profile.scraping_method}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Requires JS:</span>
              <span className="font-medium">{profile.requires_js ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Requires Proxy:</span>
              <span className="font-medium">{profile.requires_proxy ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </div>

        {/* Custom Selectors */}
        {profile.custom_selectors && (
          <div className="space-y-3 mb-6">
            <h4 className="text-sm font-medium text-gray-700">Custom Selectors</h4>
            <div className="bg-gray-50 rounded p-3 text-sm font-mono">
              {profile.custom_selectors.title && (
                <p>
                  <span className="text-gray-500">title:</span> {profile.custom_selectors.title}
                </p>
              )}
              {profile.custom_selectors.content && (
                <p>
                  <span className="text-gray-500">content:</span> {profile.custom_selectors.content}
                </p>
              )}
              {profile.custom_selectors.author && (
                <p>
                  <span className="text-gray-500">author:</span> {profile.custom_selectors.author}
                </p>
              )}
              {profile.custom_selectors.date && (
                <p>
                  <span className="text-gray-500">date:</span> {profile.custom_selectors.date}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Notes */}
        {profile.notes && (
          <div className="space-y-2 mb-6">
            <h4 className="text-sm font-medium text-gray-700">Notes</h4>
            <p className="text-sm text-gray-600 bg-gray-50 rounded p-3">{profile.notes}</p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t text-xs text-gray-500">
          <div>
            <p>Last checked: {formatDate(profile.last_checked)}</p>
            {profile.last_success && <p>Last success: {formatDate(profile.last_success)}</p>}
          </div>
          <button
            onClick={handleResetStats}
            disabled={resetStats.isPending}
            className="text-gray-500 hover:text-gray-700"
          >
            Reset Stats
          </button>
        </div>
      </div>
    </Card>
  );
};
