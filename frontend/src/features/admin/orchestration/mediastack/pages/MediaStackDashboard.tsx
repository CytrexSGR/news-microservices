import React from 'react';
import { Link } from 'react-router-dom';
import { MediaStackHealthStatus } from '../components/MediaStackHealthStatus';
import { MediaStackUsagePanel } from '../components/MediaStackUsagePanel';
import { MediaStackNewsList } from '../components/MediaStackNewsList';

/**
 * MediaStack Dashboard
 *
 * Main overview page for the MediaStack news integration.
 * Displays API health, usage statistics, and recent news articles.
 */
export const MediaStackDashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">MediaStack Dashboard</h1>
          <p className="text-gray-600">
            News aggregation from MediaStack API
          </p>
        </div>
        <Link
          to="/admin/orchestration/mediastack/search"
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Advanced Search
        </Link>
      </div>

      {/* Status Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MediaStackHealthStatus />
        <MediaStackUsagePanel />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <QuickStatCard
          title="Categories"
          value="7"
          description="Available news categories"
          icon="folder"
        />
        <QuickStatCard
          title="Countries"
          value="50+"
          description="Supported countries"
          icon="globe"
        />
        <QuickStatCard
          title="Languages"
          value="13+"
          description="Supported languages"
          icon="language"
        />
        <QuickStatCard
          title="Sources"
          value="7500+"
          description="News sources worldwide"
          icon="newspaper"
        />
      </div>

      {/* Recent News */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Recent News</h2>
          <Link
            to="/admin/orchestration/mediastack/search"
            className="text-blue-500 hover:text-blue-600 text-sm"
          >
            View All
          </Link>
        </div>
        <MediaStackNewsList
          showFilters={false}
          pageSize={6}
          initialParams={{
            countries: ['de', 'us'],
            sort: 'published_desc',
          }}
        />
      </div>
    </div>
  );
};

/**
 * Quick Stat Card Component
 */
interface QuickStatCardProps {
  title: string;
  value: string;
  description: string;
  icon: 'folder' | 'globe' | 'language' | 'newspaper';
}

const QuickStatCard: React.FC<QuickStatCardProps> = ({
  title,
  value,
  description,
}) => {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-400 mt-1">{description}</p>
    </div>
  );
};

export default MediaStackDashboard;
