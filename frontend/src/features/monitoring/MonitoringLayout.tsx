/**
 * MonitoringLayout Component
 *
 * Layout wrapper for monitoring feature with sidebar navigation.
 */

import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  Activity,
  Server,
  AlertCircle,
  TrendingUp,
  HardDrive,
  ChevronLeft,
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  end?: boolean;
}

const navItems: NavItem[] = [
  {
    to: '/admin/monitoring',
    label: 'Dashboard',
    icon: <Activity className="w-4 h-4" />,
    end: true,
  },
  {
    to: '/admin/monitoring/services',
    label: 'Services',
    icon: <Server className="w-4 h-4" />,
  },
  {
    to: '/admin/monitoring/errors',
    label: 'Error Logs',
    icon: <AlertCircle className="w-4 h-4" />,
  },
  {
    to: '/admin/monitoring/performance',
    label: 'Performance',
    icon: <TrendingUp className="w-4 h-4" />,
  },
  {
    to: '/admin/monitoring/infrastructure',
    label: 'Infrastructure',
    icon: <HardDrive className="w-4 h-4" />,
  },
];

export function MonitoringLayout() {
  const location = useLocation();

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card shrink-0">
        <div className="p-4 border-b border-border">
          <NavLink
            to="/admin"
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Admin
          </NavLink>
        </div>

        <div className="p-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground mb-4">
            <Activity className="w-5 h-5 text-primary" />
            Monitoring
          </h2>

          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Quick Stats (optional) */}
        <div className="p-4 mt-auto border-t border-border">
          <div className="text-xs text-muted-foreground">
            <p>Monitoring Feature</p>
            <p className="mt-1">Admin only</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto bg-background">
        <Outlet />
      </main>
    </div>
  );
}
