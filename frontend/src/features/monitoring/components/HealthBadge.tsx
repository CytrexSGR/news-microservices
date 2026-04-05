/**
 * HealthBadge Component
 *
 * Displays a health status indicator with optional label.
 * Color coding: green=healthy, yellow=degraded, red=unhealthy, gray=unknown.
 */

import { CheckCircle, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import type { HealthBadgeProps, HealthStatus } from '../types';

/**
 * Get styles and icon based on health status
 */
function getStatusConfig(status: HealthStatus): {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: React.ReactNode;
  label: string;
} {
  switch (status) {
    case 'healthy':
      return {
        bgColor: 'bg-green-100 dark:bg-green-950/50',
        textColor: 'text-green-700 dark:text-green-400',
        borderColor: 'border-green-300 dark:border-green-800',
        icon: <CheckCircle className="w-full h-full" />,
        label: 'Healthy',
      };
    case 'degraded':
      return {
        bgColor: 'bg-yellow-100 dark:bg-yellow-950/50',
        textColor: 'text-yellow-700 dark:text-yellow-400',
        borderColor: 'border-yellow-300 dark:border-yellow-800',
        icon: <AlertTriangle className="w-full h-full" />,
        label: 'Degraded',
      };
    case 'unhealthy':
      return {
        bgColor: 'bg-red-100 dark:bg-red-950/50',
        textColor: 'text-red-700 dark:text-red-400',
        borderColor: 'border-red-300 dark:border-red-800',
        icon: <XCircle className="w-full h-full" />,
        label: 'Unhealthy',
      };
    case 'unknown':
    default:
      return {
        bgColor: 'bg-gray-100 dark:bg-gray-900/50',
        textColor: 'text-gray-600 dark:text-gray-400',
        borderColor: 'border-gray-300 dark:border-gray-700',
        icon: <HelpCircle className="w-full h-full" />,
        label: 'Unknown',
      };
  }
}

/**
 * Get size classes based on size prop
 */
function getSizeClasses(size: 'sm' | 'md' | 'lg'): {
  iconSize: string;
  textSize: string;
  padding: string;
  gap: string;
} {
  switch (size) {
    case 'sm':
      return {
        iconSize: 'w-3 h-3',
        textSize: 'text-xs',
        padding: 'px-1.5 py-0.5',
        gap: 'gap-1',
      };
    case 'lg':
      return {
        iconSize: 'w-5 h-5',
        textSize: 'text-base',
        padding: 'px-3 py-1.5',
        gap: 'gap-2',
      };
    case 'md':
    default:
      return {
        iconSize: 'w-4 h-4',
        textSize: 'text-sm',
        padding: 'px-2 py-1',
        gap: 'gap-1.5',
      };
  }
}

export function HealthBadge({
  status,
  size = 'md',
  showLabel = true,
}: HealthBadgeProps) {
  const config = getStatusConfig(status);
  const sizeClasses = getSizeClasses(size);

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full border
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        ${sizeClasses.padding} ${sizeClasses.gap}
      `}
    >
      <span className={sizeClasses.iconSize}>{config.icon}</span>
      {showLabel && <span className={sizeClasses.textSize}>{config.label}</span>}
    </span>
  );
}
