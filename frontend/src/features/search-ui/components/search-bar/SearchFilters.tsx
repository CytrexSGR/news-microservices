/**
 * Search Filters Component
 *
 * Sidebar/collapsible panel for advanced search filtering
 * - Date range picker
 * - Source selection
 * - Sentiment filter
 * - Entity filter (placeholder)
 * - Active filter count badge
 */

import * as React from 'react'
import { X, Calendar as CalendarIcon, Filter } from 'lucide-react'
import { format } from 'date-fns'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { cn } from '@/lib/utils'
import type { SearchFilters as SearchFiltersType } from '../../types/search.types'

interface SearchFiltersProps {
  /** Current filter state */
  filters: SearchFiltersType
  /** Callback when filters change (partial update) */
  onFiltersChange: (filters: Partial<SearchFiltersType>) => void
  /** Number of active filters */
  activeFilterCount: number
  /** Optional: Available sources list */
  availableSources?: string[]
  /** Optional: Available categories list */
  availableCategories?: string[]
  /** Optional: Collapsed state */
  collapsed?: boolean
  /** Optional: Toggle collapsed state */
  onToggleCollapse?: () => void
  /** Optional: Custom class name */
  className?: string
}

/**
 * Calculate active filter count from filter object
 */
export function getActiveFilterCount(filters: SearchFiltersType): number {
  let count = 0
  if (filters.source) count++
  if (filters.sentiment) count++
  if (filters.date_from) count++
  if (filters.date_to) count++
  if (filters.entities && filters.entities.length > 0) count++
  return count
}

// Category display mapping
const categoryDisplayMap: Record<string, { label: string; color: string }> = {
  economy_markets: { label: 'Economy & Markets', color: 'bg-blue-500' },
  technology_science: { label: 'Technology & Science', color: 'bg-purple-500' },
  geopolitics_security: { label: 'Geopolitics & Security', color: 'bg-red-500' },
  climate_environment_health: { label: 'Climate, Environment & Health', color: 'bg-green-500' },
  politics_society: { label: 'Politics & Society', color: 'bg-orange-500' },
  panorama: { label: 'Panorama', color: 'bg-indigo-500' },
}

export function SearchFilters({
  filters,
  onFiltersChange,
  activeFilterCount,
  availableSources = [],
  availableCategories = [],
  collapsed = false,
  onToggleCollapse,
  className,
}: SearchFiltersProps) {
  const handleClearFilters = () => {
    onFiltersChange({
      source: null,
      sentiment: null,
      date_from: null,
      date_to: null,
      entities: [],
    })
  }

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      date_from: e.target.value || null,
    })
  }

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      date_to: e.target.value || null,
    })
  }

  const handleSourceChange = (value: string) => {
    const newValue = value === 'all' ? null : value
    onFiltersChange({
      source: newValue,
    })
  }

  const handleSentimentChange = (value: string) => {
    const newValue = value === 'all' ? null : value
    onFiltersChange({
      sentiment: newValue,
    })
  }

  const handleEntityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const entities = value
      .split(',')
      .map((e) => e.trim())
      .filter((e) => e.length > 0)
    onFiltersChange({
      entities: entities.length > 0 ? entities : undefined,
    })
  }

  if (collapsed) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onToggleCollapse}
        className={cn('gap-2', className)}
      >
        <Filter className="h-4 w-4" />
        Filters
        {activeFilterCount > 0 && (
          <Badge variant="secondary" className="ml-1">
            {activeFilterCount}
          </Badge>
        )}
      </Button>
    )
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Filters</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <Badge variant="secondary">{activeFilterCount}</Badge>
          )}
          {onToggleCollapse && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleCollapse}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close filters</span>
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Date Range Filter */}
        <div className="space-y-3">
          <Label className="text-sm font-semibold">Date Range</Label>
          <div className="space-y-2">
            <div>
              <Label htmlFor="date_from" className="text-xs text-muted-foreground">
                From
              </Label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="date_from"
                  type="date"
                  value={filters.date_from || ''}
                  onChange={handleDateFromChange}
                  className="pl-10"
                  max={filters.date_to || undefined}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="date_to" className="text-xs text-muted-foreground">
                To
              </Label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="date_to"
                  type="date"
                  value={filters.date_to || ''}
                  onChange={handleDateToChange}
                  className="pl-10"
                  min={filters.date_from || undefined}
                  max={format(new Date(), 'yyyy-MM-dd')}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Source Filter */}
        <div className="space-y-2">
          <Label htmlFor="source" className="text-sm font-semibold">
            Source
          </Label>
          <Select
            value={filters.source || 'all'}
            onValueChange={handleSourceChange}
          >
            <SelectTrigger id="source">
              <SelectValue placeholder="All sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sources</SelectItem>
              {availableSources.length > 0 ? (
                availableSources
                  .filter((source) => source && source.trim() !== '')
                  .map((source) => (
                    <SelectItem key={source} value={source}>
                      {source}
                    </SelectItem>
                  ))
              ) : (
                <>
                  <SelectItem value="BBC News">BBC News</SelectItem>
                  <SelectItem value="Reuters">Reuters</SelectItem>
                  <SelectItem value="Aljazeera">Aljazeera</SelectItem>
                  <SelectItem value="DW English">DW English</SelectItem>
                  <SelectItem value="CNBC">CNBC</SelectItem>
                  <SelectItem value="Ars Technica">Ars Technica</SelectItem>
                  <SelectItem value="Heise online IT">Heise online IT</SelectItem>
                  <SelectItem value="heise online news">heise online news</SelectItem>
                  <SelectItem value="Euronews">Euronews</SelectItem>
                  <SelectItem value="Channel NewsAsia">Channel NewsAsia</SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Category Filter */}
        <div className="space-y-2">
          <Label htmlFor="sentiment" className="text-sm font-semibold">
            Category
          </Label>
          <Select
            value={filters.sentiment || 'all'}
            onValueChange={handleSentimentChange}
          >
            <SelectTrigger id="sentiment">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {availableCategories.length > 0 ? (
                availableCategories
                  .filter((category) => category && category.trim() !== '')
                  .map((category) => {
                    const display = categoryDisplayMap[category] || {
                      label: category,
                      color: 'bg-gray-500',
                    }
                    return (
                      <SelectItem key={category} value={category}>
                        <span className="flex items-center gap-2">
                          <span className={`h-2 w-2 rounded-full ${display.color}`} />
                          {display.label}
                        </span>
                      </SelectItem>
                    )
                  })
              ) : (
                <>
                  <SelectItem value="economy_markets">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-blue-500" />
                      Economy & Markets
                    </span>
                  </SelectItem>
                  <SelectItem value="technology_science">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-purple-500" />
                      Technology & Science
                    </span>
                  </SelectItem>
                  <SelectItem value="geopolitics_security">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-red-500" />
                      Geopolitics & Security
                    </span>
                  </SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Entity Filter (Placeholder for future) */}
        <div className="space-y-2 opacity-60">
          <Label htmlFor="entities" className="text-sm font-semibold">
            Entities
            <Badge variant="outline" className="ml-2 text-xs">
              Coming Soon
            </Badge>
          </Label>
          <Input
            id="entities"
            placeholder="e.g., Apple, Microsoft, Google"
            value={filters.entities?.join(', ') || ''}
            onChange={handleEntityChange}
            disabled
            className="disabled:cursor-not-allowed"
          />
          <p className="text-xs text-muted-foreground">
            Filter by mentioned entities (comma-separated)
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            onClick={handleClearFilters}
            disabled={activeFilterCount === 0}
            className="flex-1"
          >
            Clear All
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
