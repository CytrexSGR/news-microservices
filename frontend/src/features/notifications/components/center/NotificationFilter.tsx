/**
 * NotificationFilter Component
 *
 * Filter controls for notification list.
 */

import { Filter, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type {
  NotificationFilterOptions,
  NotificationStatus,
  NotificationChannel,
} from '../../types';

interface NotificationFilterProps {
  value: NotificationFilterOptions;
  onChange: (filters: NotificationFilterOptions) => void;
  className?: string;
}

const STATUS_OPTIONS: { value: NotificationStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'sent', label: 'Sent' },
  { value: 'failed', label: 'Failed' },
  { value: 'read', label: 'Read' },
  { value: 'archived', label: 'Archived' },
];

const CHANNEL_OPTIONS: { value: NotificationChannel | 'all'; label: string }[] = [
  { value: 'all', label: 'All Channels' },
  { value: 'email', label: 'Email' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'push', label: 'Push' },
];

const DATE_RANGE_OPTIONS: { value: string; label: string }[] = [
  { value: 'all', label: 'All Time' },
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
];

export function NotificationFilter({
  value,
  onChange,
  className,
}: NotificationFilterProps) {
  const hasFilters =
    value.status !== 'all' ||
    value.channel !== 'all' ||
    value.dateRange !== 'all';

  const activeFiltersCount = [
    value.status !== 'all',
    value.channel !== 'all',
    value.dateRange !== 'all',
  ].filter(Boolean).length;

  const handleReset = () => {
    onChange({
      status: 'all',
      channel: 'all',
      dateRange: 'all',
    });
  };

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        <Filter className="h-4 w-4" />
        <span className="hidden sm:inline">Filters</span>
        {activeFiltersCount > 0 && (
          <Badge variant="secondary" className="h-5 px-1.5 text-xs">
            {activeFiltersCount}
          </Badge>
        )}
      </div>

      {/* Status filter */}
      <Select
        value={value.status}
        onValueChange={(status) =>
          onChange({ ...value, status: status as NotificationStatus | 'all' })
        }
      >
        <SelectTrigger className="w-[140px] h-8">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Channel filter */}
      <Select
        value={value.channel}
        onValueChange={(channel) =>
          onChange({ ...value, channel: channel as NotificationChannel | 'all' })
        }
      >
        <SelectTrigger className="w-[140px] h-8">
          <SelectValue placeholder="Channel" />
        </SelectTrigger>
        <SelectContent>
          {CHANNEL_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Date range filter */}
      <Select
        value={value.dateRange}
        onValueChange={(dateRange) =>
          onChange({
            ...value,
            dateRange: dateRange as 'all' | 'today' | 'week' | 'month' | 'custom',
          })
        }
      >
        <SelectTrigger className="w-[140px] h-8">
          <SelectValue placeholder="Date Range" />
        </SelectTrigger>
        <SelectContent>
          {DATE_RANGE_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Reset button */}
      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          className="h-8 px-2"
        >
          <X className="h-4 w-4 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
}
