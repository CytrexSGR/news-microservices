import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import {
  useSourceProfiles,
  useDeleteSourceProfile,
  useTestSourceProfile,
} from '../api';
import type { SourceProfile, SourceStatus, ScrapingMethod } from '../types/scraping.types';

interface SourceProfilesTableProps {
  className?: string;
  pageSize?: number;
  onEdit?: (profile: SourceProfile) => void;
}

/**
 * Status Badge
 */
const StatusBadge: React.FC<{ status: SourceStatus }> = ({ status }) => {
  const colors: Record<SourceStatus, string> = {
    working: 'bg-green-100 text-green-800',
    degraded: 'bg-yellow-100 text-yellow-800',
    blocked: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

/**
 * Method Badge
 */
const MethodBadge: React.FC<{ method: ScrapingMethod }> = ({ method }) => {
  const colors: Record<ScrapingMethod, string> = {
    httpx: 'bg-blue-100 text-blue-800',
    playwright: 'bg-purple-100 text-purple-800',
    newspaper4k: 'bg-orange-100 text-orange-800',
    trafilatura: 'bg-teal-100 text-teal-800',
    auto: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[method]}`}>
      {method}
    </span>
  );
};

/**
 * Source Profiles Table
 *
 * Displays a paginated table of source profiles with actions.
 */
export const SourceProfilesTable: React.FC<SourceProfilesTableProps> = ({
  className,
  pageSize = 20,
  onEdit,
}) => {
  const [statusFilter, setStatusFilter] = useState<SourceStatus | undefined>();
  const [page, setPage] = useState(0);

  const { data, isLoading, error, refetch, isRefetching } = useSourceProfiles({
    status: statusFilter,
    limit: pageSize,
    offset: page * pageSize,
  });

  const deleteProfile = useDeleteSourceProfile();
  const testProfile = useTestSourceProfile();

  const handleDelete = async (domain: string) => {
    if (!confirm(`Delete profile for ${domain}?`)) return;
    try {
      await deleteProfile.mutateAsync(domain);
    } catch (err) {
      console.error('Failed to delete profile:', err);
    }
  };

  const handleTest = async (domain: string) => {
    try {
      const result = await testProfile.mutateAsync(domain);
      alert(
        result.success
          ? `Test successful! Response time: ${result.response_time_ms}ms`
          : `Test failed: ${result.error}`
      );
    } catch (err) {
      console.error('Failed to test profile:', err);
    }
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  const statusOptions: (SourceStatus | 'all')[] = ['all', 'working', 'degraded', 'blocked', 'unknown'];

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Source Profiles</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load profiles: {error.message}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Source Profiles</h3>
          <div className="flex gap-2">
            <select
              value={statusFilter || 'all'}
              onChange={(e) => {
                const val = e.target.value;
                setStatusFilter(val === 'all' ? undefined : (val as SourceStatus));
                setPage(0);
              }}
              className="px-3 py-1 border rounded text-sm"
            >
              {statusOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt === 'all' ? 'All Status' : opt.charAt(0).toUpperCase() + opt.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            >
              {isRefetching ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : data?.sources.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No source profiles found</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">Domain</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Method</th>
                    <th className="px-3 py-2 text-left">Success Rate</th>
                    <th className="px-3 py-2 text-left">Avg Response</th>
                    <th className="px-3 py-2 text-left">Last Checked</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data?.sources.map((profile) => (
                    <tr key={profile.domain} className="hover:bg-gray-50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{profile.domain}</span>
                          {profile.requires_js && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-1 rounded">JS</span>
                          )}
                          {profile.requires_proxy && (
                            <span className="text-xs bg-orange-100 text-orange-700 px-1 rounded">Proxy</span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge status={profile.status} />
                      </td>
                      <td className="px-3 py-2">
                        <MethodBadge method={profile.scraping_method} />
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={
                            profile.success_rate >= 0.9
                              ? 'text-green-600'
                              : profile.success_rate >= 0.7
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }
                        >
                          {(profile.success_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {profile.avg_response_time_ms}ms
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-500">
                        {formatDate(profile.last_checked)}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleTest(profile.domain)}
                            disabled={testProfile.isPending}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                          >
                            Test
                          </button>
                          {onEdit && (
                            <button
                              onClick={() => onEdit(profile)}
                              className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                            >
                              Edit
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(profile.domain)}
                            disabled={deleteProfile.isPending}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t">
              <p className="text-sm text-gray-600">
                Showing {page * pageSize + 1}-
                {Math.min((page + 1) * pageSize, data?.total || 0)} of {data?.total || 0}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data || (page + 1) * pageSize >= data.total}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </Card>
  );
};
