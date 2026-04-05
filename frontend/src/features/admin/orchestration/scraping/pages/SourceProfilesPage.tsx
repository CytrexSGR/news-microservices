import React, { useState } from 'react';
import { SourceProfilesTable } from '../components/SourceProfilesTable';
import { SourceProfileForm } from '../components/SourceProfileForm';
import { SourceProfileCard } from '../components/SourceProfileCard';
import { useSourcesStats } from '../api';
import type { SourceProfile, SourceStatus, ScrapingMethod } from '../types/scraping.types';

/**
 * Stats Card
 */
const StatsCard: React.FC<{ label: string; value: number; color?: string }> = ({
  label,
  value,
  color = 'text-gray-900',
}) => (
  <div className="bg-white rounded-lg border p-4">
    <p className="text-sm text-gray-600">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
  </div>
);

/**
 * Source Profiles Page
 *
 * Management page for source profiles with create/edit functionality.
 */
export const SourceProfilesPage: React.FC = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingProfile, setEditingProfile] = useState<SourceProfile | null>(null);
  const [viewingDomain, setViewingDomain] = useState<string | null>(null);

  const { data: stats, refetch: refetchStats } = useSourcesStats();

  const handleEdit = (profile: SourceProfile) => {
    setEditingProfile(profile);
    setShowCreateForm(false);
    setViewingDomain(null);
  };

  const handleFormSuccess = () => {
    setShowCreateForm(false);
    setEditingProfile(null);
    refetchStats();
  };

  const handleFormCancel = () => {
    setShowCreateForm(false);
    setEditingProfile(null);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Source Profiles</h1>
          <p className="text-gray-600">
            Manage scraping configurations for different domains
          </p>
        </div>
        <button
          onClick={() => {
            setShowCreateForm(true);
            setEditingProfile(null);
            setViewingDomain(null);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Add Profile
        </button>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <StatsCard label="Total Sources" value={stats.total} />
          <StatsCard
            label="Working"
            value={stats.by_status.working || 0}
            color="text-green-600"
          />
          <StatsCard
            label="Degraded"
            value={stats.by_status.degraded || 0}
            color="text-yellow-600"
          />
          <StatsCard
            label="Blocked"
            value={stats.by_status.blocked || 0}
            color="text-red-600"
          />
          <StatsCard
            label="Avg Success Rate"
            value={Math.round(stats.avg_success_rate * 100)}
            color={stats.avg_success_rate >= 0.9 ? 'text-green-600' : 'text-yellow-600'}
          />
          <StatsCard label="Recently Checked" value={stats.recently_checked} />
        </div>
      )}

      {/* Method Distribution */}
      {stats && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">By Scraping Method</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.by_method).map(([method, count]) => (
              <span
                key={method}
                className="px-3 py-1 bg-gray-100 rounded-full text-sm"
              >
                {method}: <span className="font-medium">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table (2/3 width) */}
        <div className="lg:col-span-2">
          <SourceProfilesTable
            pageSize={15}
            onEdit={handleEdit}
          />
        </div>

        {/* Side Panel (1/3 width) */}
        <div>
          {showCreateForm ? (
            <SourceProfileForm
              onSuccess={handleFormSuccess}
              onCancel={handleFormCancel}
            />
          ) : editingProfile ? (
            <SourceProfileForm
              profile={editingProfile}
              onSuccess={handleFormSuccess}
              onCancel={handleFormCancel}
            />
          ) : viewingDomain ? (
            <SourceProfileCard
              domain={viewingDomain}
              onEdit={() => {
                // Will trigger handleEdit when profile is loaded
              }}
            />
          ) : (
            <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
              <p>Select a profile to view details</p>
              <p className="text-sm mt-2">
                or click "Add Profile" to create a new one
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SourceProfilesPage;
