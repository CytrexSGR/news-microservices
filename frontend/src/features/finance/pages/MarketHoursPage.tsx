import { Clock } from 'lucide-react';

export function MarketHoursPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center space-x-3">
        <Clock className="w-8 h-8 text-[#00D4FF]" />
        <div>
          <h1 className="text-3xl font-bold">Market Hours Status</h1>
          <p className="text-gray-400 mt-1">Global Market Intelligence & API Savings</p>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-12 text-center">
        <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-300 mb-2">Market Hours Dashboard Coming Soon</h2>
        <p className="text-gray-500 mb-8">
          Real-time market status for Crypto, Forex, Indices, and Commodities
        </p>

        {/* Preview of market status cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <div className="bg-[#0B0E11] border border-green-500/30 rounded p-4">
            <div className="text-xl font-bold text-green-400 mb-2">✅ CRYPTO</div>
            <div className="text-sm text-gray-400">24/7 Open</div>
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-xl font-bold text-gray-400 mb-2">⏸️ FOREX</div>
            <div className="text-sm text-gray-400">Weekends Closed</div>
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-xl font-bold text-gray-400 mb-2">⏸️ INDICES</div>
            <div className="text-sm text-gray-400">9:30-16:00 ET</div>
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-xl font-bold text-gray-400 mb-2">⏸️ COMMODITIES</div>
            <div className="text-sm text-gray-400">8:20-13:30 ET</div>
          </div>
        </div>

        <div className="mt-8 bg-[#0B0E11] border border-[#00D4FF]/30 rounded p-6 max-w-lg mx-auto">
          <div className="text-3xl font-bold text-[#00D4FF] mb-2">5.2M+</div>
          <div className="text-sm text-gray-400">API Calls Saved Annually</div>
        </div>
      </div>
    </div>
  );
}
