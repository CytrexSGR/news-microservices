import React, { useState, useMemo } from 'react';
import { Card } from '@/components/ui/Card';
import { useMediaStackNews } from '../api';
import { MediaStackNewsCard } from './MediaStackNewsCard';
import {
  MEDIASTACK_CATEGORIES,
  MEDIASTACK_COUNTRIES,
  MEDIASTACK_LANGUAGES,
  type MediaStackNewsParams,
} from '../types/mediastack.types';

/**
 * Props for MediaStackNewsList
 */
interface MediaStackNewsListProps {
  initialParams?: MediaStackNewsParams;
  showFilters?: boolean;
  pageSize?: number;
  className?: string;
}

/**
 * MediaStack News List
 *
 * Displays a list of news articles with optional search and filtering.
 */
export const MediaStackNewsList: React.FC<MediaStackNewsListProps> = ({
  initialParams = {},
  showFilters = true,
  pageSize = 20,
  className,
}) => {
  // Filter state
  const [keywords, setKeywords] = useState(initialParams.keywords || '');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    initialParams.categories || []
  );
  const [selectedCountries, setSelectedCountries] = useState<string[]>(
    initialParams.countries || []
  );
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(
    initialParams.languages || []
  );
  const [sortOrder, setSortOrder] = useState<'published_desc' | 'published_asc' | 'popularity'>(
    initialParams.sort || 'published_desc'
  );
  const [offset, setOffset] = useState(0);

  // Build query params
  const queryParams = useMemo<MediaStackNewsParams>(
    () => ({
      keywords: keywords || undefined,
      categories: selectedCategories.length > 0 ? selectedCategories : undefined,
      countries: selectedCountries.length > 0 ? selectedCountries : undefined,
      languages: selectedLanguages.length > 0 ? selectedLanguages : undefined,
      sort: sortOrder,
      limit: pageSize,
      offset,
    }),
    [keywords, selectedCategories, selectedCountries, selectedLanguages, sortOrder, pageSize, offset]
  );

  // Fetch news
  const { data, isLoading, error, refetch, isRefetching } = useMediaStackNews(queryParams);

  // Toggle functions for multi-select
  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
    setOffset(0);
  };

  const toggleCountry = (country: string) => {
    setSelectedCountries((prev) =>
      prev.includes(country) ? prev.filter((c) => c !== country) : [...prev, country]
    );
    setOffset(0);
  };

  const toggleLanguage = (language: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(language) ? prev.filter((l) => l !== language) : [...prev, language]
    );
    setOffset(0);
  };

  // Pagination
  const totalPages = data?.pagination ? Math.ceil(data.pagination.total / pageSize) : 1;
  const currentPage = Math.floor(offset / pageSize) + 1;

  const handlePrevPage = () => {
    if (offset >= pageSize) {
      setOffset(offset - pageSize);
    }
  };

  const handleNextPage = () => {
    if (data?.pagination && offset + pageSize < data.pagination.total) {
      setOffset(offset + pageSize);
    }
  };

  return (
    <div className={className}>
      {/* Filters */}
      {showFilters && (
        <Card className="p-4 mb-6">
          <div className="space-y-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Keywords
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={keywords}
                  onChange={(e) => {
                    setKeywords(e.target.value);
                    setOffset(0);
                  }}
                  placeholder="Enter keywords..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => refetch()}
                  disabled={isRefetching}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                >
                  {isRefetching ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Categories */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categories
              </label>
              <div className="flex flex-wrap gap-2">
                {MEDIASTACK_CATEGORIES.map((category) => (
                  <button
                    key={category}
                    onClick={() => toggleCategory(category)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedCategories.includes(category)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Countries */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Countries
              </label>
              <div className="flex flex-wrap gap-2">
                {MEDIASTACK_COUNTRIES.map((country) => (
                  <button
                    key={country}
                    onClick={() => toggleCountry(country)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedCountries.includes(country)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {country.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Languages */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Languages
              </label>
              <div className="flex flex-wrap gap-2">
                {MEDIASTACK_LANGUAGES.map((language) => (
                  <button
                    key={language}
                    onClick={() => toggleLanguage(language)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedLanguages.includes(language)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {language.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={sortOrder}
                onChange={(e) => {
                  setSortOrder(e.target.value as typeof sortOrder);
                  setOffset(0);
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="published_desc">Newest First</option>
                <option value="published_asc">Oldest First</option>
                <option value="popularity">Popularity</option>
              </select>
            </div>
          </div>
        </Card>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="animate-pulse space-y-3">
                <div className="h-32 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <Card className="p-6 text-center">
          <p className="text-red-600 mb-4">Failed to load news: {error.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Retry
          </button>
        </Card>
      )}

      {/* Results */}
      {data && (
        <>
          {/* Results count */}
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-gray-600">
              Showing {data.data.length} of {data.pagination.total.toLocaleString()} articles
            </p>
            {isRefetching && (
              <span className="text-sm text-blue-600">Refreshing...</span>
            )}
          </div>

          {/* Articles grid */}
          {data.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.data.map((article, index) => (
                <MediaStackNewsCard
                  key={`${article.url}-${index}`}
                  article={article}
                />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <p className="text-gray-500">No articles found. Try adjusting your filters.</p>
            </Card>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-6">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MediaStackNewsList;
