import { Outlet, NavLink } from 'react-router-dom';
import { TrendingUp, Clock, BarChart3, Activity, Search } from 'lucide-react';

export function FinanceLayout() {
  const navItems = [
    { to: '/finance/prices', label: 'Prices', icon: TrendingUp },
    { to: '/finance/market-hours', label: 'Market Hours', icon: Clock },
    { to: '/finance/charts', label: 'Charts', icon: BarChart3 },
    { to: '/finance/health', label: 'System Health', icon: Activity },
    { to: '/finance/search', label: 'Symbol Search', icon: Search },
  ];

  return (
    <div className="min-h-screen bg-[#0B0E11] text-white">
      {/* Top Navigation Bar */}
      <header className="bg-[#151922] border-b border-gray-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-[#00D4FF]" />
              <h1 className="text-2xl font-bold font-mono">FINANCE TERMINAL</h1>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">User:</span>
              <span className="text-sm font-medium">andreas</span>
            </div>
          </div>
        </div>
      </header>

      {/* Section Navigation */}
      <nav className="bg-[#1A1F2E] border-b border-gray-700">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-6 py-4 border-b-2 transition-colors ${
                    isActive
                      ? 'border-[#00D4FF] text-[#00D4FF] bg-[#0B0E11]'
                      : 'border-transparent text-gray-400 hover:text-white hover:bg-[#151922]'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
