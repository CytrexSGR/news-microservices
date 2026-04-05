import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

interface NavItem {
  label: string;
  path: string;
}

const navSections: { title: string; items: NavItem[] }[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', path: '/intelligence/dashboard' },
    ],
  },
  {
    title: 'Content Analysis',
    items: [
      { label: 'Analyze Article', path: '/intelligence/analysis' },
      { label: 'Entity Extraction', path: '/intelligence/analysis/entities' },
    ],
  },
  {
    title: 'Entity Canonicalization',
    items: [
      { label: 'Single Entity', path: '/intelligence/entities' },
      { label: 'Clusters', path: '/intelligence/entities/clusters' },
      { label: 'Batch Processing', path: '/intelligence/entities/batch' },
      { label: 'Dashboard', path: '/intelligence/entities/dashboard' },
    ],
  },
  {
    title: 'OSINT',
    items: [
      { label: 'Dashboard', path: '/intelligence/osint' },
      { label: 'Pattern Detection', path: '/intelligence/osint/patterns' },
      { label: 'Graph Quality', path: '/intelligence/osint/quality' },
      { label: 'Templates', path: '/intelligence/osint/templates' },
      { label: 'Instances', path: '/intelligence/osint/instances' },
      { label: 'Alerts', path: '/intelligence/osint/alerts' },
    ],
  },
  {
    title: 'Events',
    items: [
      { label: 'Clusters', path: '/intelligence/events' },
      { label: 'Latest Events', path: '/intelligence/events/latest' },
      { label: 'Subcategories', path: '/intelligence/events/subcategories' },
      { label: 'Risk History', path: '/intelligence/events/risk' },
    ],
  },
  {
    title: 'Narrative Analysis',
    items: [
      { label: 'Dashboard', path: '/intelligence/narrative' },
      { label: 'Analyze Text', path: '/intelligence/narrative/analyze' },
      { label: 'Frames', path: '/intelligence/narrative/frames' },
      { label: 'Bias Analysis', path: '/intelligence/narrative/bias' },
      { label: 'Clusters', path: '/intelligence/narrative/clusters' },
    ],
  },
];

/**
 * Intelligence Layout
 *
 * Provides navigation sidebar for the Intelligence CORE feature.
 */
export const IntelligenceLayout: React.FC = () => {
  return (
    <div className="flex h-full">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-gray-50 border-r overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-bold text-gray-800 mb-1">Intelligence</h2>
          <p className="text-xs text-gray-500 mb-4">AI-Powered Analysis</p>

          {navSections.map((section) => (
            <div key={section.title} className="mb-5">
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
                          ? 'bg-indigo-100 text-indigo-700'
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

export default IntelligenceLayout;
