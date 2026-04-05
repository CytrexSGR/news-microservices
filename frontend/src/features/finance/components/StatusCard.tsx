/**
 * StatusCard Component
 *
 * Reusable card component for displaying status information
 * Used in: Market Hours, System Health sections
 */

import type { ReactNode } from 'react';

export interface StatusCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  status?: 'success' | 'warning' | 'danger' | 'neutral';
  icon?: ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  className?: string;
}

const statusColors = {
  success: 'border-green-500/30 bg-green-500/5',
  warning: 'border-yellow-500/30 bg-yellow-500/5',
  danger: 'border-red-500/30 bg-red-500/5',
  neutral: 'border-gray-700 bg-[#1A1F2E]',
};

const statusTextColors = {
  success: 'text-green-400',
  warning: 'text-yellow-400',
  danger: 'text-red-400',
  neutral: 'text-gray-400',
};

export function StatusCard({
  title,
  value,
  subtitle,
  status = 'neutral',
  icon,
  trend,
  className = '',
}: StatusCardProps) {
  return (
    <div className={`border rounded-lg p-6 ${statusColors[status]} ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-400">{title}</span>
        {icon && <div className={statusTextColors[status]}>{icon}</div>}
      </div>

      <div className="text-2xl font-bold text-white mb-1 font-mono">{value}</div>

      {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}

      {trend && (
        <div className="mt-2 flex items-center space-x-1">
          <span
            className={`text-xs font-medium ${
              trend.direction === 'up' ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {trend.direction === 'up' ? '↑' : '↓'} {Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-gray-500">vs last period</span>
        </div>
      )}
    </div>
  );
}
