/**
 * CategoryBreakdown Component
 *
 * Displays event distribution by security category
 */

import { CATEGORY_ICONS } from '../../types/security.types';

interface CategoryBreakdownProps {
  byCategory: Record<string, number>;
}

const CATEGORY_COLORS: Record<string, string> = {
  CONFLICT: 'bg-red-500',
  SECURITY: 'bg-orange-500',
  HUMANITARIAN: 'bg-blue-500',
  POLITICS: 'bg-purple-500',
};

const CATEGORY_TEXT_COLORS: Record<string, string> = {
  CONFLICT: 'text-red-400',
  SECURITY: 'text-orange-400',
  HUMANITARIAN: 'text-blue-400',
  POLITICS: 'text-purple-400',
};

export function CategoryBreakdown({ byCategory }: CategoryBreakdownProps) {
  const total = Object.values(byCategory).reduce((sum, count) => sum + count, 0);

  if (total === 0) {
    return null;
  }

  const categories = Object.entries(byCategory)
    .filter(([cat]) => ['CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS'].includes(cat))
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">By Category</h3>

      {/* Visual Bar */}
      <div className="flex h-3 rounded-full overflow-hidden mb-4">
        {categories.map(([category, count]) => (
          <div
            key={category}
            className={`${CATEGORY_COLORS[category] || 'bg-slate-600'} transition-all`}
            style={{ width: `${(count / total) * 100}%` }}
            title={`${category}: ${count}`}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2">
        {categories.map(([category, count]) => {
          const percentage = Math.round((count / total) * 100);
          const icon = CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS] || '📄';
          const textColor = CATEGORY_TEXT_COLORS[category] || 'text-slate-400';

          return (
            <div
              key={category}
              className="flex items-center gap-2 p-2 bg-slate-700/30 rounded"
            >
              <span className="text-lg">{icon}</span>
              <div className="flex-1 min-w-0">
                <div className={`text-xs font-medium ${textColor}`}>
                  {category}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-sm font-bold text-white">
                    {count.toLocaleString()}
                  </span>
                  <span className="text-xs text-slate-500">({percentage}%)</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
