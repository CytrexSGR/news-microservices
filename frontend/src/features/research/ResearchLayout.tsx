/**
 * ResearchLayout
 *
 * Layout wrapper for research feature with:
 * - Sidebar navigation
 * - Breadcrumbs
 * - Common styling
 */

import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Beaker,
  Search,
  History,
  BarChart3,
  FileText,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/research',
    label: 'Dashboard',
    icon: <Search className="h-4 w-4" />,
    end: true,
  },
  {
    to: '/research/history',
    label: 'History',
    icon: <History className="h-4 w-4" />,
  },
  {
    to: '/research/stats',
    label: 'Statistics',
    icon: <BarChart3 className="h-4 w-4" />,
  },
];

function SideNav() {
  return (
    <nav className="space-y-1">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors',
              isActive
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )
          }
        >
          {item.icon}
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export function ResearchLayout() {
  const location = useLocation();

  // Check if we're on a detail page (e.g., /research/123)
  const isDetailPage =
    location.pathname.match(/^\/research\/\d+$/) !== null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Beaker className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            Research Dashboard
          </h1>
          <p className="text-sm text-muted-foreground">
            AI-powered research with Perplexity
          </p>
        </div>
      </div>

      {/* Layout */}
      <div className="flex gap-6">
        {/* Sidebar (hidden on detail pages) */}
        {!isDetailPage && (
          <aside className="hidden md:block w-48 shrink-0">
            <SideNav />
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>

      {/* Mobile Navigation (tab bar) */}
      {!isDetailPage && (
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t border-border px-4 py-2 z-50">
          <div className="flex justify-around">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col items-center gap-1 px-3 py-2 text-xs rounded-lg transition-colors',
                    isActive
                      ? 'text-primary'
                      : 'text-muted-foreground'
                  )
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </div>
  );
}
