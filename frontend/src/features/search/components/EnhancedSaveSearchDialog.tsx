/**
 * EnhancedSaveSearchDialog Component
 *
 * Dialog to save the current search with optional scheduling
 * and alert configuration.
 */

import * as React from 'react';
import { useState, useCallback } from 'react';
import {
  Bookmark,
  Bell,
  Clock,
  Loader2,
  ChevronDown,
  ChevronUp,
  Calendar,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { useSaveSearch } from '../api/useSaveSearch';
import type { SearchFilters, ScheduleFrequency, SavedSearchCreate } from '../types/search.types';

interface EnhancedSaveSearchDialogProps {
  /** Current search query */
  query: string;
  /** Current active filters */
  filters: SearchFilters;
  /** Trigger element */
  trigger?: React.ReactNode;
  /** Called after successful save */
  onSaved?: (savedSearchId: string) => void;
  /** Whether dialog is open (controlled) */
  open?: boolean;
  /** Called when open state changes */
  onOpenChange?: (open: boolean) => void;
}

// Schedule frequency options
const SCHEDULE_OPTIONS: Array<{
  value: ScheduleFrequency;
  label: string;
  description: string;
  cron: string;
}> = [
  {
    value: 'hourly',
    label: 'Every Hour',
    description: 'Run every hour',
    cron: '0 * * * *',
  },
  {
    value: 'daily',
    label: 'Daily',
    description: 'Run once per day',
    cron: '0 9 * * *',
  },
  {
    value: 'weekly',
    label: 'Weekly',
    description: 'Run once per week',
    cron: '0 9 * * 1',
  },
];

// Hour options for scheduling
const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => ({
  value: i.toString(),
  label: `${i.toString().padStart(2, '0')}:00`,
}));

// Day options for weekly scheduling
const DAY_OPTIONS = [
  { value: '0', label: 'Sunday' },
  { value: '1', label: 'Monday' },
  { value: '2', label: 'Tuesday' },
  { value: '3', label: 'Wednesday' },
  { value: '4', label: 'Thursday' },
  { value: '5', label: 'Friday' },
  { value: '6', label: 'Saturday' },
];

export function EnhancedSaveSearchDialog({
  query,
  filters,
  trigger,
  onSaved,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: EnhancedSaveSearchDialogProps) {
  // Dialog state (controlled or uncontrolled)
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;
  const setOpen = isControlled ? controlledOnOpenChange! : setUncontrolledOpen;

  // Form state
  const [name, setName] = useState('');
  const [enableSchedule, setEnableSchedule] = useState(false);
  const [scheduleFrequency, setScheduleFrequency] = useState<ScheduleFrequency>('daily');
  const [scheduleHour, setScheduleHour] = useState('9');
  const [scheduleDay, setScheduleDay] = useState('1');
  const [enableAlerts, setEnableAlerts] = useState(false);
  const [alertThreshold, setAlertThreshold] = useState(5);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { mutate: saveSearch, isPending } = useSaveSearch();

  // Count active filters
  const activeFilterCount = Object.values(filters).filter(
    (v) => v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0 : true)
  ).length;

  // Can save if has query or filters
  const canSave = query.trim().length > 0 || activeFilterCount > 0;

  // Generate cron expression
  const getCronExpression = useCallback((): string => {
    switch (scheduleFrequency) {
      case 'hourly':
        return '0 * * * *';
      case 'daily':
        return `0 ${scheduleHour} * * *`;
      case 'weekly':
        return `0 ${scheduleHour} * * ${scheduleDay}`;
      default:
        return '0 9 * * *';
    }
  }, [scheduleFrequency, scheduleHour, scheduleDay]);

  // Handle save
  const handleSave = useCallback(() => {
    if (!name.trim()) {
      toast.error('Please enter a name for your search');
      return;
    }

    const searchData: SavedSearchCreate = {
      name: name.trim(),
      query: query || '',
      filters: activeFilterCount > 0 ? filters : undefined,
      is_scheduled: enableSchedule,
      schedule_cron: enableSchedule ? getCronExpression() : undefined,
      alert_enabled: enableAlerts,
      alert_threshold: enableAlerts ? alertThreshold : undefined,
    };

    saveSearch(searchData, {
      onSuccess: (saved) => {
        setOpen(false);
        resetForm();
        onSaved?.(saved.id);
      },
    });
  }, [
    name,
    query,
    filters,
    activeFilterCount,
    enableSchedule,
    enableAlerts,
    alertThreshold,
    getCronExpression,
    saveSearch,
    setOpen,
    onSaved,
  ]);

  // Reset form
  const resetForm = useCallback(() => {
    setName('');
    setEnableSchedule(false);
    setScheduleFrequency('daily');
    setScheduleHour('9');
    setScheduleDay('1');
    setEnableAlerts(false);
    setAlertThreshold(5);
    setShowAdvanced(false);
  }, []);

  // Handle dialog open change
  const handleOpenChange = useCallback(
    (newOpen: boolean) => {
      if (!newOpen) {
        resetForm();
      }
      setOpen(newOpen);
    },
    [setOpen, resetForm]
  );

  // Get schedule description
  const getScheduleDescription = (): string => {
    switch (scheduleFrequency) {
      case 'hourly':
        return 'Runs every hour at :00';
      case 'daily':
        return `Runs daily at ${HOUR_OPTIONS[parseInt(scheduleHour)].label}`;
      case 'weekly':
        return `Runs every ${DAY_OPTIONS[parseInt(scheduleDay)].label} at ${HOUR_OPTIONS[parseInt(scheduleHour)].label}`;
      default:
        return '';
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" disabled={!canSave} className="gap-2">
            <Bookmark className="h-4 w-4" />
            Save Search
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bookmark className="h-5 w-5" />
            Save Search
          </DialogTitle>
          <DialogDescription>
            Save this search to quickly access it later. Optionally schedule it to run
            automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Name Input */}
          <div className="space-y-2">
            <Label htmlFor="search-name">Name *</Label>
            <Input
              id="search-name"
              placeholder="e.g., AI Technology News"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isPending}
              autoFocus
            />
          </div>

          {/* Current Search Summary */}
          <div className="space-y-2">
            <Label className="text-sm text-muted-foreground">Search Configuration</Label>
            <div className="rounded-lg border p-3 bg-muted/30 space-y-2">
              {query && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Query:</span>
                  <code className="text-sm bg-muted px-1.5 py-0.5 rounded">
                    {query}
                  </code>
                </div>
              )}
              {activeFilterCount > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-muted-foreground">Filters:</span>
                  <Badge variant="secondary" className="text-xs">
                    {activeFilterCount} active
                  </Badge>
                </div>
              )}
              {!query && activeFilterCount === 0 && (
                <p className="text-sm text-muted-foreground italic">
                  No query or filters configured
                </p>
              )}
            </div>
          </div>

          <Separator />

          {/* Schedule Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <Label htmlFor="enable-schedule" className="font-medium cursor-pointer">
                  Schedule Automatic Runs
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Run this search automatically on a schedule
              </p>
            </div>
            <Switch
              id="enable-schedule"
              checked={enableSchedule}
              onCheckedChange={setEnableSchedule}
              disabled={isPending}
            />
          </div>

          {/* Schedule Configuration */}
          {enableSchedule && (
            <div className="space-y-4 pl-6 border-l-2 border-primary/20">
              {/* Frequency */}
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Select
                  value={scheduleFrequency}
                  onValueChange={(v) => setScheduleFrequency(v as ScheduleFrequency)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SCHEDULE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Time Configuration */}
              {scheduleFrequency !== 'hourly' && (
                <div className="grid grid-cols-2 gap-4">
                  {scheduleFrequency === 'weekly' && (
                    <div className="space-y-2">
                      <Label>Day</Label>
                      <Select value={scheduleDay} onValueChange={setScheduleDay}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {DAY_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label>Time</Label>
                    <Select value={scheduleHour} onValueChange={setScheduleHour}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {HOUR_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {/* Schedule Summary */}
              <Alert>
                <Calendar className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  {getScheduleDescription()}
                </AlertDescription>
              </Alert>
            </div>
          )}

          <Separator />

          {/* Alerts Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-muted-foreground" />
                <Label htmlFor="enable-alerts" className="font-medium cursor-pointer">
                  Enable Alerts
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Get notified when new results are found
              </p>
            </div>
            <Switch
              id="enable-alerts"
              checked={enableAlerts}
              onCheckedChange={setEnableAlerts}
              disabled={isPending}
            />
          </div>

          {/* Alert Configuration */}
          {enableAlerts && (
            <div className="space-y-4 pl-6 border-l-2 border-primary/20">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Alert Threshold</Label>
                  <span className="text-sm font-medium tabular-nums">
                    {alertThreshold} results
                  </span>
                </div>
                <Slider
                  value={[alertThreshold]}
                  onValueChange={([v]) => setAlertThreshold(v)}
                  min={1}
                  max={50}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">
                  Alert when at least {alertThreshold} new results are found
                </p>
              </div>
            </div>
          )}

          {/* Advanced Options */}
          <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="w-full justify-between">
                Advanced Options
                {showAdvanced ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-4 space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  Advanced alert configuration (email, webhook, cooldown) can be set after
                  saving in the Alerts Settings page.
                </AlertDescription>
              </Alert>
            </CollapsibleContent>
          </Collapsible>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isPending || !name.trim()}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Bookmark className="mr-2 h-4 w-4" />
                Save Search
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
