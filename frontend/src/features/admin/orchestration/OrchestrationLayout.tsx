import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

interface NavItem {
  label: string;
  path: string;
  icon?: string;
}

const navSections: { title: string; items: NavItem[] }[] = [
  {
    title: 'Scheduler',
    items: [
      { label: 'Dashboard', path: '/admin/orchestration/scheduler' },
      { label: 'Jobs', path: '/admin/orchestration/scheduler/jobs' },
      { label: 'Cron Jobs', path: '/admin/orchestration/scheduler/cron' },
    ],
  },
  {
    title: 'MediaStack',
    items: [
      { label: 'Dashboard', path: '/admin/orchestration/mediastack' },
      { label: 'Search News', path: '/admin/orchestration/mediastack/search' },
    ],
  },
  {
    title: 'Scraping',
    items: [
      { label: 'Dashboard', path: '/admin/orchestration/scraping' },
      { label: 'Source Profiles', path: '/admin/orchestration/scraping/sources' },
      { label: 'Queue', path: '/admin/orchestration/scraping/queue' },
      { label: 'Cache', path: '/admin/orchestration/scraping/cache' },
      { label: 'Proxies', path: '/admin/orchestration/scraping/proxies' },
      { label: 'Tools', path: '/admin/orchestration/scraping/tools' },
      { label: 'Screenshot', path: '/admin/orchestration/scraping/screenshot' },
    ],
  },
];

/**
 * Orchestration Layout
 *
 * Provides navigation sidebar for all orchestration sub-features.
 */
export const OrchestrationLayout: React.FC = () => {
  return (
    <div className="flex h-full">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-gray-50 border-r overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Orchestration</h2>

          {navSections.map((section) => (
            <div key={section.title} className="mb-6">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {section.title}
              </h3>
              <nav className="space-y-1">
                {section.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-white">
        <Outlet />
      </main>
    </div>
  );
};

export default OrchestrationLayout;
