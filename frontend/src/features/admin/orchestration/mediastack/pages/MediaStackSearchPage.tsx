import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { MediaStackNewsList } from '../components/MediaStackNewsList';
import { MediaStackHealthStatus } from '../components/MediaStackHealthStatus';
import { useMediaStackSources } from '../api';
import type { MediaStackNewsParams } from '../types/mediastack.types';

/**
 * Saved Search Interface
 */
interface SavedSearch {
  id: string;
  name: string;
  params: MediaStackNewsParams;
  createdAt: string;
}

/**
 * MediaStack Search Page
 *
 * Full-featured search interface for MediaStack news articles.
 * Includes advanced filters, saved searches, and source browsing.
 */
export const MediaStackSearchPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'sources' | 'saved'>('search');
  const [savedSearches] = useState<SavedSearch[]>([
    {
      id: '1',
      name: 'German Tech News',
      params: {
        countries: ['de'],
        categories: ['technology'],
        languages: ['de'],
      },
      createdAt: new Date().toISOString(),
    },
    {
      id: '2',
      name: 'US Business Headlines',
      params: {
        countries: ['us'],
        categories: ['business'],
        sort: 'published_desc',
      },
      createdAt: new Date().toISOString(),
    },
  ]);
  const [activeSearch, setActiveSearch] = useState<MediaStackNewsParams>({});

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link
            to="/admin/orchestration/mediastack"
            className="text-gray-500 hover:text-gray-700"
          >
            &larr; Back
          </Link>
          <div>
            <h1 className="text-2xl font-bold">MediaStack Search</h1>
            <p className="text-gray-600">
              Search and filter news from around the world
            </p>
          </div>
        </div>
        <MediaStackHealthStatus compact />
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          <TabButton
            active={activeTab === 'search'}
            onClick={() => setActiveTab('search')}
          >
            Search News
          </TabButton>
          <TabButton
            active={activeTab === 'sources'}
            onClick={() => setActiveTab('sources')}
          >
            Browse Sources
          </TabButton>
          <TabButton
            active={activeTab === 'saved'}
            onClick={() => setActiveTab('saved')}
          >
            Saved Searches ({savedSearches.length})
          </TabButton>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'search' && (
        <MediaStackNewsList
          showFilters={true}
          pageSize={20}
          initialParams={activeSearch}
        />
      )}

      {activeTab === 'sources' && <SourcesBrowser />}

      {activeTab === 'saved' && (
        <SavedSearchesList
          searches={savedSearches}
          onApply={(params) => {
            setActiveSearch(params);
            setActiveTab('search');
          }}
        />
      )}
    </div>
  );
};

/**
 * Tab Button Component
 */
interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`pb-3 px-1 border-b-2 transition-colors ${
      active
        ? 'border-blue-500 text-blue-600 font-medium'
        : 'border-transparent text-gray-500 hover:text-gray-700'
    }`}
  >
    {children}
  </button>
);

/**
 * Sources Browser Component
 */
const SourcesBrowser: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  const { data, isLoading, error } = useMediaStackSources({
    search: search || undefined,
    countries: selectedCountry ? [selectedCountry] : undefined,
    categories: selectedCategory ? [selectedCategory] : undefined,
    limit: 50,
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Sources
            </label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Country
            </label>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Countries</option>
              <option value="de">Germany</option>
              <option value="us">United States</option>
              <option value="gb">United Kingdom</option>
              <option value="fr">France</option>
              <option value="nl">Netherlands</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Categories</option>
              <option value="general">General</option>
              <option value="business">Business</option>
              <option value="technology">Technology</option>
              <option value="science">Science</option>
              <option value="health">Health</option>
              <option value="sports">Sports</option>
              <option value="entertainment">Entertainment</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Sources List */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <Card className="p-6 text-center">
          <p className="text-red-600">Failed to load sources: {error.message}</p>
        </Card>
      )}

      {data && (
        <>
          <p className="text-sm text-gray-600">
            Showing {data.data.length} of {data.pagination.total} sources
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.data.map((source) => (
              <Card key={source.id} className="p-4 hover:shadow-md transition-shadow">
                <h3 className="font-semibold text-gray-900">{source.name}</h3>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-500 hover:underline truncate block"
                >
                  {source.url}
                </a>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                    {source.country.toUpperCase()}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                    {source.category}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                    {source.language.toUpperCase()}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

/**
 * Saved Searches List Component
 */
interface SavedSearchesListProps {
  searches: SavedSearch[];
  onApply: (params: MediaStackNewsParams) => void;
}

const SavedSearchesList: React.FC<SavedSearchesListProps> = ({ searches, onApply }) => {
  if (searches.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-500">No saved searches yet.</p>
        <p className="text-sm text-gray-400 mt-1">
          Save your frequently used search configurations for quick access.
        </p>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {searches.map((search) => (
        <Card key={search.id} className="p-4">
          <h3 className="font-semibold text-gray-900 mb-2">{search.name}</h3>
          <div className="space-y-1 text-sm text-gray-600 mb-3">
            {search.params.countries && (
              <p>Countries: {search.params.countries.join(', ').toUpperCase()}</p>
            )}
            {search.params.categories && (
              <p>Categories: {search.params.categories.join(', ')}</p>
            )}
            {search.params.languages && (
              <p>Languages: {search.params.languages.join(', ').toUpperCase()}</p>
            )}
            {search.params.keywords && (
              <p>Keywords: {search.params.keywords}</p>
            )}
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-400">
              Created: {new Date(search.createdAt).toLocaleDateString()}
            </span>
            <button
              onClick={() => onApply(search.params)}
              className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              Apply
            </button>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default MediaStackSearchPage;
