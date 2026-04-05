import { TrendingUp, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface TierStats {
  tier1_actual: number;
  tier2_actual: number;
  tier3_actual: number;
  total_actual: number;
  tier1_synced: boolean;
  tier2_synced: boolean;
  tier3_synced: boolean;
}

export function PricesPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['tier-statistics'],
    queryFn: async () => {
      const response = await axios.get<TierStats>('/api/v1/admin/tiers/statistics');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const totalSymbols = stats?.total_actual ?? 0;
  const tier1 = stats?.tier1_actual ?? 0;
  const tier2 = stats?.tier2_actual ?? 0;
  const tier3 = stats?.tier3_actual ?? 0;
  const allSynced = stats?.tier1_synced && stats?.tier2_synced && stats?.tier3_synced;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <TrendingUp className="w-8 h-8 text-[#00D4FF]" />
          <div>
            <h1 className="text-3xl font-bold">Real-time Prices</h1>
            <p className="text-gray-400 mt-1">
              {isLoading ? 'Loading...' : `${totalSymbols} symbols across Crypto, Forex, Indices, Commodities`}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {allSynced ? (
            <>
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">LIVE</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-yellow-500">Limited</span>
            </>
          )}
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-12 text-center">
        <TrendingUp className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-300 mb-2">Real-time Prices Coming Soon</h2>
        <p className="text-gray-500">
          This section will display live market data for {totalSymbols > 0 ? `all ${totalSymbols} symbols` : 'available symbols'}
        </p>
        <div className="mt-8 grid grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-2xl font-bold text-[#00D4FF]">{isLoading ? '...' : tier1}</div>
            <div className="text-sm text-gray-400">Tier 1 Symbols</div>
            {stats && !stats.tier1_synced && (
              <div className="text-xs text-yellow-500 mt-1">Not synced</div>
            )}
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-2xl font-bold text-[#00D4FF]">{isLoading ? '...' : tier2}</div>
            <div className="text-sm text-gray-400">Tier 2 Symbols</div>
            {stats && !stats.tier2_synced && (
              <div className="text-xs text-yellow-500 mt-1">Not synced</div>
            )}
          </div>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-4">
            <div className="text-2xl font-bold text-[#00D4FF]">{isLoading ? '...' : tier3}</div>
            <div className="text-sm text-gray-400">Tier 3 Symbols</div>
            {stats && !stats.tier3_synced && (
              <div className="text-xs text-yellow-500 mt-1">Not synced</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
