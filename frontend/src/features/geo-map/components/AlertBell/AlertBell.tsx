import { useState, useRef, useEffect } from 'react';
import { useAlertStats } from '../../hooks/useWatchlist';
import { AlertDropdown } from './AlertDropdown';

export function AlertBell() {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { data: stats } = useAlertStats();

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const totalUnread = stats?.total_unread || 0;
  const hasCritical = (stats?.critical_unread || 0) > 0;

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`relative p-2 rounded-lg transition-colors ${
          isOpen ? 'bg-slate-700' : 'hover:bg-slate-700/50'
        } ${hasCritical ? 'animate-pulse' : ''}`}
      >
        <svg
          className={`w-6 h-6 ${hasCritical ? 'text-red-400' : 'text-slate-300'}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {totalUnread > 0 && (
          <span
            className={`absolute -top-1 -right-1 min-w-[20px] h-5 px-1.5 flex items-center justify-center text-xs font-bold rounded-full ${
              hasCritical ? 'bg-red-500' : 'bg-blue-500'
            }`}
          >
            {totalUnread > 99 ? '99+' : totalUnread}
          </span>
        )}
      </button>

      {isOpen && <AlertDropdown onClose={() => setIsOpen(false)} />}
    </div>
  );
}
