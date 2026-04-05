/**
 * QuietHoursSettings Component
 *
 * Configure quiet hours when notifications are suppressed.
 */

import { Moon, AlertCircle, Clock } from 'lucide-react';
import { Switch } from '@/components/ui/Switch';
import { Label } from '@/components/ui/Label';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useNotificationPreferences, useUpdateQuietHours } from '../../api';
import type { DayOfWeek } from '../../types';

interface QuietHoursSettingsProps {
  className?: string;
}

const DAYS: { value: DayOfWeek; label: string; short: string }[] = [
  { value: 'monday', label: 'Monday', short: 'Mon' },
  { value: 'tuesday', label: 'Tuesday', short: 'Tue' },
  { value: 'wednesday', label: 'Wednesday', short: 'Wed' },
  { value: 'thursday', label: 'Thursday', short: 'Thu' },
  { value: 'friday', label: 'Friday', short: 'Fri' },
  { value: 'saturday', label: 'Saturday', short: 'Sat' },
  { value: 'sunday', label: 'Sunday', short: 'Sun' },
];

const TIMEZONES = [
  { value: 'Europe/Berlin', label: 'Europe/Berlin (CET/CEST)' },
  { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
  { value: 'America/New_York', label: 'America/New_York (EST/EDT)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST)' },
  { value: 'UTC', label: 'UTC' },
];

export function QuietHoursSettings({ className }: QuietHoursSettingsProps) {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updateQuietHours = useUpdateQuietHours();

  const quietHours = preferences?.quiet_hours || {
    enabled: false,
    start_time: '22:00',
    end_time: '08:00',
    timezone: 'Europe/Berlin',
    days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] as DayOfWeek[],
    allow_critical: true,
  };

  const handleToggle = (enabled: boolean) => {
    updateQuietHours.mutate({
      ...quietHours,
      enabled,
    });
  };

  const handleTimeChange = (field: 'start_time' | 'end_time', value: string) => {
    updateQuietHours.mutate({
      ...quietHours,
      [field]: value,
    });
  };

  const handleTimezoneChange = (timezone: string) => {
    updateQuietHours.mutate({
      ...quietHours,
      timezone,
    });
  };

  const handleDayToggle = (day: DayOfWeek) => {
    const currentDays = quietHours.days || [];
    const updatedDays = currentDays.includes(day)
      ? currentDays.filter((d) => d !== day)
      : [...currentDays, day];

    updateQuietHours.mutate({
      ...quietHours,
      days: updatedDays,
    });
  };

  const handleCriticalToggle = (allow: boolean) => {
    updateQuietHours.mutate({
      ...quietHours,
      allow_critical: allow,
    });
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            Quiet Hours
          </CardTitle>
          <CardDescription>
            Set times when notifications will be suppressed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 animate-pulse">
            <div className="h-10 bg-muted rounded" />
            <div className="h-24 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Moon className="h-5 w-5" />
              Quiet Hours
            </CardTitle>
            <CardDescription className="mt-1">
              Set times when notifications will be suppressed
            </CardDescription>
          </div>
          <Switch
            checked={quietHours.enabled}
            onCheckedChange={handleToggle}
            disabled={updateQuietHours.isPending}
          />
        </div>
      </CardHeader>

      <CardContent
        className={cn(
          'space-y-6 transition-opacity',
          !quietHours.enabled && 'opacity-50 pointer-events-none'
        )}
      >
        {/* Time range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="start-time" className="text-sm flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              Start Time
            </Label>
            <Input
              id="start-time"
              type="time"
              value={quietHours.start_time}
              onChange={(e) => handleTimeChange('start_time', e.target.value)}
              className="mt-1.5"
            />
          </div>
          <div>
            <Label htmlFor="end-time" className="text-sm flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              End Time
            </Label>
            <Input
              id="end-time"
              type="time"
              value={quietHours.end_time}
              onChange={(e) => handleTimeChange('end_time', e.target.value)}
              className="mt-1.5"
            />
          </div>
        </div>

        {/* Timezone */}
        <div>
          <Label htmlFor="timezone" className="text-sm">
            Timezone
          </Label>
          <Select value={quietHours.timezone} onValueChange={handleTimezoneChange}>
            <SelectTrigger id="timezone" className="mt-1.5">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIMEZONES.map((tz) => (
                <SelectItem key={tz.value} value={tz.value}>
                  {tz.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Days of the week */}
        <div>
          <Label className="text-sm">Active Days</Label>
          <div className="flex gap-2 mt-2 flex-wrap">
            {DAYS.map(({ value, short }) => {
              const isActive = (quietHours.days || []).includes(value);
              return (
                <button
                  key={value}
                  onClick={() => handleDayToggle(value)}
                  className={cn(
                    'h-10 w-10 rounded-full text-sm font-medium transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80 text-muted-foreground'
                  )}
                >
                  {short}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Select the days when quiet hours should be active
          </p>
        </div>

        {/* Critical notifications */}
        <div className="flex items-center justify-between p-3 rounded-lg border bg-amber-50/50 dark:bg-amber-900/10">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <Label htmlFor="allow-critical" className="text-sm font-medium">
                Allow Critical Notifications
              </Label>
              <p className="text-xs text-muted-foreground mt-0.5">
                Critical alerts will still be delivered during quiet hours
              </p>
            </div>
          </div>
          <Switch
            id="allow-critical"
            checked={quietHours.allow_critical}
            onCheckedChange={handleCriticalToggle}
          />
        </div>

        {/* Summary */}
        {quietHours.enabled && (
          <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
            <strong>Active schedule:</strong> Notifications will be muted from{' '}
            <span className="font-medium text-foreground">{quietHours.start_time}</span>
            {' to '}
            <span className="font-medium text-foreground">{quietHours.end_time}</span>
            {' '}({quietHours.timezone}) on{' '}
            <span className="font-medium text-foreground">
              {(quietHours.days || []).length === 7
                ? 'all days'
                : (quietHours.days || []).length === 5 &&
                  ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].every((d) =>
                    (quietHours.days || []).includes(d as DayOfWeek)
                  )
                ? 'weekdays'
                : (quietHours.days || []).map((d) => d.slice(0, 3)).join(', ')}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
