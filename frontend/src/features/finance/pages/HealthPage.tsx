import { Activity } from 'lucide-react';

export function HealthPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Activity className="w-8 h-8 text-[#00D4FF]" />
          <div>
            <h1 className="text-3xl font-bold">System Health</h1>
            <p className="text-gray-400 mt-1">FMP Service monitoring and performance metrics</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 bg-green-500/20 border border-green-500/30 rounded px-4 py-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm font-medium text-green-400">All Systems Operational</span>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="space-y-6">
        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#1A1F2E] border border-green-500/30 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-gray-400">FMP API</span>
              <span className="text-xs text-green-400 font-medium">✅ HEALTHY</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">99.8%</div>
            <div className="text-xs text-gray-500">Uptime</div>
          </div>

          <div className="bg-[#1A1F2E] border border-green-500/30 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-gray-400">Rate Limiter</span>
              <span className="text-xs text-green-400 font-medium">✅ HEALTHY</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">248/300</div>
            <div className="text-xs text-gray-500">Available Tokens</div>
          </div>

          <div className="bg-[#1A1F2E] border border-green-500/30 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-gray-400">Database</span>
              <span className="text-xs text-green-400 font-medium">✅ HEALTHY</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">12ms</div>
            <div className="text-xs text-gray-500">Avg Query Time</div>
          </div>
        </div>

        {/* Worker Status */}
        <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
          <h2 className="text-lg font-bold mb-4">Worker Status</h2>
          <div className="space-y-3">
            {[
              { name: 'Tier 1 Worker', symbols: '50/50', duration: '1.2s' },
              { name: 'Tier 2 Worker', symbols: '100/100', duration: '5.3s' },
              { name: 'Tier 3 Worker', symbols: '237/237', duration: '3.1s' },
            ].map((worker) => (
              <div key={worker.name} className="flex items-center justify-between bg-[#0B0E11] border border-gray-700 rounded p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="font-medium">{worker.name}</span>
                </div>
                <div className="flex items-center space-x-6 text-sm">
                  <span className="text-gray-400">{worker.symbols} symbols</span>
                  <span className="text-gray-400">{worker.duration}</span>
                  <span className="text-green-400 font-medium">Running</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* API Calls Graph Placeholder */}
        <div className="bg-[#1A1F2E] border border-gray-700 rounded-lg p-6">
          <h2 className="text-lg font-bold mb-4">API Calls (Last 24h)</h2>
          <div className="bg-[#0B0E11] border border-gray-700 rounded p-6">
            <div className="h-48 flex items-end justify-around space-x-1">
              {Array.from({ length: 24 }).map((_, i) => {
                const height = Math.random() * 80 + 20;
                return (
                  <div
                    key={i}
                    className="w-4 bg-gradient-to-t from-[#00D4FF]/30 to-[#00D4FF]/60 rounded-t"
                    style={{ height: `${height}%` }}
                  ></div>
                );
              })}
            </div>
            <div className="text-xs text-gray-500 mt-4 text-center">API Calls Over Time</div>
          </div>
        </div>
      </div>
    </div>
  );
}
