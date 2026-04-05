/**
 * EarningsCalendarTable Component
 * Table view of earnings with sorting and filtering
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Calendar,
  Filter,
} from 'lucide-react';
import { useEarningsCalendar } from '../../api/useEarningsCalendar';
import type { EarningsEvent, EarningsCalendarFilters } from '../../types/earnings.types';
import { formatEarningsTime, getEarningsTimeColor } from '../../types/earnings.types';

interface EarningsCalendarTableProps {
  filters?: EarningsCalendarFilters;
  onEventClick?: (event: EarningsEvent) => void;
  className?: string;
}

type SortField = 'date' | 'symbol' | 'company_name' | 'time' | 'eps_estimated' | 'revenue_estimated';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

function formatCurrency(value: number | null, scale: 'M' | 'B' = 'M'): string {
  if (value === null) return '-';
  const divisor = scale === 'B' ? 1e9 : 1e6;
  const formatted = (value / divisor).toFixed(2);
  return `$${formatted}${scale}`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function EarningsCalendarTable({
  filters: initialFilters,
  onEventClick,
  className,
}: EarningsCalendarTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'date',
    direction: 'asc',
  });
  const [dateRange, setDateRange] = useState<{ from: string; to: string }>({
    from: initialFilters?.from || new Date().toISOString().split('T')[0],
    to:
      initialFilters?.to ||
      new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  });

  const { data: events, isLoading, error } = useEarningsCalendar({
    ...initialFilters,
    from: dateRange.from,
    to: dateRange.to,
  });

  const filteredAndSortedEvents = useMemo(() => {
    if (!events) return [];

    let result = [...events];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.symbol.toLowerCase().includes(query) ||
          e.company_name.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    result.sort((a, b) => {
      const direction = sortConfig.direction === 'asc' ? 1 : -1;

      switch (sortConfig.field) {
        case 'date':
          return direction * a.date.localeCompare(b.date);
        case 'symbol':
          return direction * a.symbol.localeCompare(b.symbol);
        case 'company_name':
          return direction * a.company_name.localeCompare(b.company_name);
        case 'time':
          return direction * a.time.localeCompare(b.time);
        case 'eps_estimated':
          return direction * ((a.eps_estimated || 0) - (b.eps_estimated || 0));
        case 'revenue_estimated':
          return direction * ((a.revenue_estimated || 0) - (b.revenue_estimated || 0));
        default:
          return 0;
      }
    });

    return result;
  }, [events, searchQuery, sortConfig]);

  const handleSort = (field: SortField) => {
    setSortConfig((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortConfig.field !== field) {
      return <ArrowUpDown className="h-4 w-4 text-muted-foreground" />;
    }
    return sortConfig.direction === 'asc' ? (
      <ArrowUp className="h-4 w-4" />
    ) : (
      <ArrowDown className="h-4 w-4" />
    );
  };

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load earnings data
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Earnings Calendar
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Date Range Filters */}
            <div className="flex items-center gap-1">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Input
                type="date"
                value={dateRange.from}
                onChange={(e) => setDateRange((prev) => ({ ...prev, from: e.target.value }))}
                className="w-[130px] h-8 text-xs"
              />
              <span className="text-muted-foreground">to</span>
              <Input
                type="date"
                value={dateRange.to}
                onChange={(e) => setDateRange((prev) => ({ ...prev, to: e.target.value }))}
                className="w-[130px] h-8 text-xs"
              />
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search symbol or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 w-[200px] h-8"
              />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center gap-1">
                    Date
                    <SortIcon field="date" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('symbol')}
                >
                  <div className="flex items-center gap-1">
                    Symbol
                    <SortIcon field="symbol" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('company_name')}
                >
                  <div className="flex items-center gap-1">
                    Company
                    <SortIcon field="company_name" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('time')}
                >
                  <div className="flex items-center gap-1">
                    Time
                    <SortIcon field="time" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50 text-right"
                  onClick={() => handleSort('eps_estimated')}
                >
                  <div className="flex items-center justify-end gap-1">
                    EPS Est.
                    <SortIcon field="eps_estimated" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50 text-right"
                  onClick={() => handleSort('revenue_estimated')}
                >
                  <div className="flex items-center justify-end gap-1">
                    Rev Est.
                    <SortIcon field="revenue_estimated" />
                  </div>
                </TableHead>
                <TableHead className="text-right">Quarter</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredAndSortedEvents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No earnings events found
                  </TableCell>
                </TableRow>
              ) : (
                filteredAndSortedEvents.map((event) => (
                  <TableRow
                    key={`${event.symbol}-${event.date}`}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => onEventClick?.(event)}
                  >
                    <TableCell className="font-medium">{formatDate(event.date)}</TableCell>
                    <TableCell>
                      <span className="font-semibold text-primary">{event.symbol}</span>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {event.company_name}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs ${getEarningsTimeColor(event.time)}`}
                      >
                        {formatEarningsTime(event.time)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {event.eps_estimated !== null ? `$${event.eps_estimated.toFixed(2)}` : '-'}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(event.revenue_estimated, 'B')}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {event.fiscal_quarter} {event.fiscal_year}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary */}
        {!isLoading && filteredAndSortedEvents.length > 0 && (
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredAndSortedEvents.length} earnings events
            {searchQuery && ` matching "${searchQuery}"`}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default EarningsCalendarTable;
