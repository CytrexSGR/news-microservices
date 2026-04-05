import { useGeoMapStore } from '../store/geoMapStore';
import { useCategories } from '../hooks/useGeoData';
import type { GeoFilters } from '../types/geo.types';

interface Category {
  id: string;
  name: string;
  icon: string;
  total_count: number;
  count_24h: number;
  count_7d: number;
}

export function MapControls() {
  const {
    viewMode,
    setViewMode,
    filters,
    setFilters,
    selectedCountry,
    setSelectedCountry,
    securityViewEnabled,
    setSecurityViewEnabled,
    securityMinPriority,
    setSecurityMinPriority,
  } = useGeoMapStore();
  const { data: categories, isLoading: categoriesLoading } = useCategories();

  const toggleCategory = (categoryId: string) => {
    const current = filters.categories;
    const updated = current.includes(categoryId)
      ? current.filter((c) => c !== categoryId)
      : [...current, categoryId];
    setFilters({ categories: updated });
  };

  const clearCategories = () => {
    setFilters({ categories: [] });
  };

  return (
    <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2">
      {/* Security View Toggle */}
      <button
        onClick={() => setSecurityViewEnabled(!securityViewEnabled)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-md text-sm font-medium transition-all ${
          securityViewEnabled
            ? 'bg-slate-800 text-white border-2 border-red-500'
            : 'bg-white text-gray-700 hover:bg-gray-50'
        }`}
      >
        <span className="text-lg">{securityViewEnabled ? '🛡️' : '🗺️'}</span>
        <span>{securityViewEnabled ? 'Security View' : 'Normal View'}</span>
        {securityViewEnabled && (
          <span className="ml-1 px-1.5 py-0.5 bg-red-500 text-white text-xs rounded">
            ON
          </span>
        )}
      </button>

      {/* Security Priority Filter (only when security view is enabled) */}
      {securityViewEnabled && (
        <div className="bg-slate-800 text-white rounded-lg shadow-md p-2">
          <label className="block text-xs text-slate-400 mb-1">Min Priority</label>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min={1}
              max={10}
              value={securityMinPriority}
              onChange={(e) => setSecurityMinPriority(Number(e.target.value))}
              className="flex-1 h-1.5 bg-slate-600 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-sm font-bold w-6 text-center">
              {securityMinPriority}
            </span>
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>Low</span>
            <span>Critical</span>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      <div className="bg-white rounded-lg shadow-md p-2 flex gap-1">
        <button
          onClick={() => setViewMode('countries')}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            viewMode === 'countries'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Countries
        </button>
        <button
          onClick={() => setViewMode('heatmap')}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            viewMode === 'heatmap'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Heatmap
        </button>
      </div>

      {/* Time Range */}
      <div className="bg-white rounded-lg shadow-md p-2">
        <label className="block text-xs text-gray-500 mb-1">Time Range</label>
        <select
          value={filters.timeRange}
          onChange={(e) => setFilters({ timeRange: e.target.value as GeoFilters['timeRange'] })}
          className="w-full text-sm border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="today">Today</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      {/* Category Filter */}
      <div className="bg-white rounded-lg shadow-md p-2 max-h-64 overflow-y-auto">
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs text-gray-500">Categories</label>
          {filters.categories.length > 0 && (
            <button
              onClick={clearCategories}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Clear
            </button>
          )}
        </div>
        {categoriesLoading ? (
          <div className="text-xs text-gray-400">Loading...</div>
        ) : (
          <div className="flex flex-col gap-1">
            {(categories as Category[] | undefined)?.map((cat) => (
              <label
                key={cat.id}
                className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 rounded px-1 py-0.5"
              >
                <input
                  type="checkbox"
                  checked={filters.categories.includes(cat.id)}
                  onChange={() => toggleCategory(cat.id)}
                  className="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="flex-1 truncate">{cat.name}</span>
                <span className="text-xs text-gray-400">
                  {filters.timeRange === 'today' ? cat.count_24h :
                   filters.timeRange === '7d' ? cat.count_7d : cat.total_count}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Clear Selection */}
      {selectedCountry && (
        <button
          onClick={() => setSelectedCountry(null)}
          className="bg-white rounded-lg shadow-md p-2 text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Clear Selection
        </button>
      )}
    </div>
  );
}
