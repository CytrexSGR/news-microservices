import { Search } from 'lucide-react';

export function SearchPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center space-x-3">
        <Search className="w-8 h-8 text-[#00D4FF]" />
        <div>
          <h1 className="text-3xl font-bold">Symbol Search & Intelligence</h1>
          <p className="text-gray-400 mt-1">Advanced search with OSINT tags and correlation analysis</p>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="space-y-6">
        {/* Search Bar */}
        <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search 387 symbols by name, symbol, or tags..."
              className="w-full bg-[#0B0E11] border border-gray-700 rounded-lg pl-12 pr-4 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-[#00D4FF] transition-colors"
              disabled
            />
          </div>
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2">
          {['Crypto', 'Forex', 'Indices', 'Commodities', 'Trending', 'Volatile', 'High Volume'].map((filter) => (
            <button
              key={filter}
              className="px-4 py-2 bg-[#1A1F2E] border border-gray-700 rounded-lg text-sm text-gray-400 hover:border-[#00D4FF] hover:text-[#00D4FF] transition-colors"
              disabled
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Features Preview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
            <div className="text-sm font-bold text-[#00D4FF] mb-3">🔍 Fuzzy Search</div>
            <p className="text-xs text-gray-400">Typo-tolerant search across symbols and names</p>
          </div>

          <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
            <div className="text-sm font-bold text-[#00D4FF] mb-3">🏷️ OSINT Tags</div>
            <p className="text-xs text-gray-400">Geopolitical, Sector, Risk Level classifications</p>
          </div>

          <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
            <div className="text-sm font-bold text-[#00D4FF] mb-3">📊 Correlation Matrix</div>
            <p className="text-xs text-gray-400">Identify related symbols and market correlations</p>
          </div>
        </div>

        {/* Search Results Placeholder */}
        <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-12 text-center">
          <Search className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-300 mb-2">Advanced Search Coming Soon</h2>
          <p className="text-gray-500">
            Search across 387 symbols with advanced filters and OSINT intelligence
          </p>
        </div>
      </div>
    </div>
  );
}
