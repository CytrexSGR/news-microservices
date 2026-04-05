/**
 * SearchFiltersPanel Component
 *
 * Panel for configuring search filters including date range,
 * sources, categories, sentiment, and entity types.
 */

import * as React from 'react';
import { useState, useCallback } from 'react';
import { format, subDays, subMonths, startOfDay, endOfDay } from 'date-fns';
import {
  Calendar,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  RotateCcw,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
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
import { cn } from '@/lib/utils';
import type { SearchFilters, EntityType } from '../types/search.types';

interface SearchFiltersPanelProps {
  /** Current filter values */
  filters: SearchFilters;
  /** Called when filters change */
  onChange: (filters: SearchFilters) => void;
  /** Available sources for filtering */
  availableSources?: string[];
  /** Available categories for filtering */
  availableCategories?: string[];
  /** Whether to show in compact mode */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// Predefined date ranges
const DATE_PRESETS = [
  { label: 'Today', getValue: () => ({ from: startOfDay(new Date()), to: endOfDay(new Date()) }) },
  { label: 'Yesterday', getValue: () => {
    const yesterday = subDays(new Date(), 1);
    return { from: startOfDay(yesterday), to: endOfDay(yesterday) };
  }},
  { label: 'Last 7 days', getValue: () => ({ from: subDays(new Date(), 7), to: new Date() }) },
  { label: 'Last 30 days', getValue: () => ({ from: subDays(new Date(), 30), to: new Date() }) },
  { label: 'Last 3 months', getValue: () => ({ from: subMonths(new Date(), 3), to: new Date() }) },
  { label: 'Last year', getValue: () => ({ from: subMonths(new Date(), 12), to: new Date() }) },
];

// Default categories if not provided
const DEFAULT_CATEGORIES = [
  { value: 'economy_markets', label: 'Economy & Markets' },
  { value: 'technology_science', label: 'Technology & Science' },
  { value: 'geopolitics_security', label: 'Geopolitics & Security' },
  { value: 'climate_environment_health', label: 'Climate & Environment' },
  { value: 'politics_society', label: 'Politics & Society' },
  { value: 'panorama', label: 'Panorama' },
];

// Entity types
const ENTITY_TYPES: { value: EntityType; label: string }[] = [
  { value: 'PERSON', label: 'People' },
  { value: 'ORGANIZATION', label: 'Organizations' },
  { value: 'LOCATION', label: 'Locations' },
  { value: 'GPE', label: 'Countries/Regions' },
  { value: 'EVENT', label: 'Events' },
  { value: 'PRODUCT', label: 'Products' },
  { value: 'MONEY', label: 'Money' },
  { value: 'DATE', label: 'Dates' },
];

// Sentiment options
const SENTIMENT_OPTIONS = [
  { value: 'all', label: 'All Sentiments' },
  { value: 'positive', label: 'Positive' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'negative', label: 'Negative' },
];

/**
 * Date range picker component
 */
function DateRangePicker({
  dateFrom,
  dateTo,
  onChange,
}: {
  dateFrom?: string;
  dateTo?: string;
  onChange: (from?: string, to?: string) => void;
}) {
  const [open, setOpen] = useState(false);

  const fromDate = dateFrom ? new Date(dateFrom) : undefined;
  const toDate = dateTo ? new Date(dateTo) : undefined;

  const handlePresetClick = (preset: typeof DATE_PRESETS[0]) => {
    const range = preset.getValue();
    onChange(
      format(range.from, 'yyyy-MM-dd'),
      format(range.to, 'yyyy-MM-dd')
    );
    setOpen(false);
  };

  const handleDateSelect = (date: Date | undefined, type: 'from' | 'to') => {
    if (!date) return;
    const formatted = format(date, 'yyyy-MM-dd');
    if (type === 'from') {
      onChange(formatted, dateTo);
    } else {
      onChange(dateFrom, formatted);
    }
  };

  const displayValue = () => {
    if (fromDate && toDate) {
      return `${format(fromDate, 'MMM d')} - ${format(toDate, 'MMM d, yyyy')}`;
    }
    if (fromDate) {
      return `From ${format(fromDate, 'MMM d, yyyy')}`;
    }
    if (toDate) {
      return `Until ${format(toDate, 'MMM d, yyyy')}`;
    }
    return 'Select dates';
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-full justify-start text-left font-normal',
            !dateFrom && !dateTo && 'text-muted-foreground'
          )}
        >
          <Calendar className="mr-2 h-4 w-4" />
          {displayValue()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {/* Presets */}
          <div className="border-r p-2 space-y-1">
            {DATE_PRESETS.map((preset) => (
              <Button
                key={preset.label}
                variant="ghost"
                size="sm"
                className="w-full justify-start"
                onClick={() => handlePresetClick(preset)}
              >
                {preset.label}
              </Button>
            ))}
            <Separator className="my-2" />
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-muted-foreground"
              onClick={() => {
                onChange(undefined, undefined);
                setOpen(false);
              }}
            >
              Clear dates
            </Button>
          </div>

          {/* Calendars */}
          <div className="p-3 space-y-3">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">From</Label>
              <CalendarComponent
                mode="single"
                selected={fromDate}
                onSelect={(date) => handleDateSelect(date, 'from')}
                disabled={(date) => toDate ? date > toDate : false}
              />
            </div>
            <Separator />
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">To</Label>
              <CalendarComponent
                mode="single"
                selected={toDate}
                onSelect={(date) => handleDateSelect(date, 'to')}
                disabled={(date) => fromDate ? date < fromDate : false}
              />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Multi-select checkbox group
 */
function MultiSelectGroup({
  label,
  options,
  selected,
  onChange,
  maxVisible = 5,
}: {
  label: string;
  options: Array<{ value: string; label: string }>;
  selected: string[];
  onChange: (selected: string[]) => void;
  maxVisible?: number;
}) {
  const [expanded, setExpanded] = useState(false);

  const visibleOptions = expanded ? options : options.slice(0, maxVisible);
  const hiddenCount = options.length - maxVisible;

  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{label}</Label>
        {selected.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-auto py-0.5 px-2 text-xs"
            onClick={() => onChange([])}
          >
            Clear
          </Button>
        )}
      </div>
      <div className="space-y-2">
        {visibleOptions.map((option) => (
          <label
            key={option.value}
            className="flex items-center gap-2 cursor-pointer"
          >
            <Checkbox
              checked={selected.includes(option.value)}
              onCheckedChange={() => handleToggle(option.value)}
            />
            <span className="text-sm">{option.label}</span>
          </label>
        ))}
        {hiddenCount > 0 && !expanded && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            onClick={() => setExpanded(true)}
          >
            Show {hiddenCount} more
            <ChevronDown className="ml-1 h-3 w-3" />
          </Button>
        )}
        {expanded && hiddenCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            onClick={() => setExpanded(false)}
          >
            Show less
            <ChevronUp className="ml-1 h-3 w-3" />
          </Button>
        )}
      </div>
    </div>
  );
}

export function SearchFiltersPanel({
  filters,
  onChange,
  availableSources = [],
  availableCategories,
  compact = false,
  className,
}: SearchFiltersPanelProps) {
  const [isExpanded, setIsExpanded] = useState(!compact);

  const categories = availableCategories
    ? availableCategories.map((c) => {
        const preset = DEFAULT_CATEGORIES.find((p) => p.value === c);
        return preset || { value: c, label: c };
      })
    : DEFAULT_CATEGORIES;

  const sources = availableSources.map((s) => ({ value: s, label: s }));

  // Count active filters
  const activeFilterCount =
    (filters.date_from || filters.date_to ? 1 : 0) +
    (filters.sources?.length || 0) +
    (filters.categories?.length || 0) +
    (filters.sentiment && filters.sentiment !== 'all' ? 1 : 0) +
    (filters.has_entities ? 1 : 0) +
    (filters.entity_types?.length || 0);

  const handleReset = useCallback(() => {
    onChange({});
  }, [onChange]);

  const handleDateChange = useCallback(
    (from?: string, to?: string) => {
      onChange({
        ...filters,
        date_from: from,
        date_to: to,
      });
    },
    [filters, onChange]
  );

  const handleSentimentChange = useCallback(
    (sentiment: string) => {
      onChange({
        ...filters,
        sentiment: sentiment === 'all' ? undefined : (sentiment as SearchFilters['sentiment']),
      });
    },
    [filters, onChange]
  );

  const handleSourcesChange = useCallback(
    (sources: string[]) => {
      onChange({
        ...filters,
        sources: sources.length > 0 ? sources : undefined,
      });
    },
    [filters, onChange]
  );

  const handleCategoriesChange = useCallback(
    (categories: string[]) => {
      onChange({
        ...filters,
        categories: categories.length > 0 ? categories : undefined,
      });
    },
    [filters, onChange]
  );

  const handleEntityTypesChange = useCallback(
    (types: string[]) => {
      onChange({
        ...filters,
        entity_types: types.length > 0 ? (types as EntityType[]) : undefined,
        has_entities: types.length > 0 ? true : filters.has_entities,
      });
    },
    [filters, onChange]
  );

  const handleHasEntitiesChange = useCallback(
    (checked: boolean) => {
      onChange({
        ...filters,
        has_entities: checked || undefined,
        entity_types: checked ? filters.entity_types : undefined,
      });
    },
    [filters, onChange]
  );

  if (compact) {
    return (
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="w-full justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              <span>Filters</span>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {activeFilterCount}
                </Badge>
              )}
            </div>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-4">
          <FilterContent
            filters={filters}
            categories={categories}
            sources={sources}
            activeFilterCount={activeFilterCount}
            onReset={handleReset}
            onDateChange={handleDateChange}
            onSentimentChange={handleSentimentChange}
            onSourcesChange={handleSourcesChange}
            onCategoriesChange={handleCategoriesChange}
            onEntityTypesChange={handleEntityTypesChange}
            onHasEntitiesChange={handleHasEntitiesChange}
          />
        </CollapsibleContent>
      </Collapsible>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <FilterContent
        filters={filters}
        categories={categories}
        sources={sources}
        activeFilterCount={activeFilterCount}
        onReset={handleReset}
        onDateChange={handleDateChange}
        onSentimentChange={handleSentimentChange}
        onSourcesChange={handleSourcesChange}
        onCategoriesChange={handleCategoriesChange}
        onEntityTypesChange={handleEntityTypesChange}
        onHasEntitiesChange={handleHasEntitiesChange}
      />
    </div>
  );
}

/**
 * Extracted filter content for reuse in both modes
 */
function FilterContent({
  filters,
  categories,
  sources,
  activeFilterCount,
  onReset,
  onDateChange,
  onSentimentChange,
  onSourcesChange,
  onCategoriesChange,
  onEntityTypesChange,
  onHasEntitiesChange,
}: {
  filters: SearchFilters;
  categories: Array<{ value: string; label: string }>;
  sources: Array<{ value: string; label: string }>;
  activeFilterCount: number;
  onReset: () => void;
  onDateChange: (from?: string, to?: string) => void;
  onSentimentChange: (sentiment: string) => void;
  onSourcesChange: (sources: string[]) => void;
  onCategoriesChange: (categories: string[]) => void;
  onEntityTypesChange: (types: string[]) => void;
  onHasEntitiesChange: (checked: boolean) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Header with reset */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span className="font-medium">Filters</span>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {activeFilterCount} active
            </Badge>
          )}
        </div>
        {activeFilterCount > 0 && (
          <Button variant="ghost" size="sm" onClick={onReset}>
            <RotateCcw className="mr-1 h-3 w-3" />
            Reset
          </Button>
        )}
      </div>

      {/* Date Range */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Date Range</Label>
        <DateRangePicker
          dateFrom={filters.date_from}
          dateTo={filters.date_to}
          onChange={onDateChange}
        />
      </div>

      {/* Sentiment */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Sentiment</Label>
        <Select
          value={filters.sentiment || 'all'}
          onValueChange={onSentimentChange}
        >
          <SelectTrigger>
            <SelectValue placeholder="All Sentiments" />
          </SelectTrigger>
          <SelectContent>
            {SENTIMENT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Categories */}
      <MultiSelectGroup
        label="Categories"
        options={categories}
        selected={filters.categories || []}
        onChange={onCategoriesChange}
      />

      {/* Sources */}
      {sources.length > 0 && (
        <MultiSelectGroup
          label="Sources"
          options={sources}
          selected={filters.sources || []}
          onChange={onSourcesChange}
        />
      )}

      {/* Entities */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={filters.has_entities || false}
            onCheckedChange={onHasEntitiesChange}
          />
          <span className="text-sm font-medium">Has extracted entities</span>
        </label>

        {filters.has_entities && (
          <div className="pl-6">
            <MultiSelectGroup
              label="Entity Types"
              options={ENTITY_TYPES}
              selected={filters.entity_types || []}
              onChange={onEntityTypesChange}
            />
          </div>
        )}
      </div>
    </div>
  );
}
