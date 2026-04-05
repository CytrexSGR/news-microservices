/**
 * SourceList Component
 *
 * Displays a filterable, searchable list of sources.
 */

import { useState, useMemo } from 'react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Search, Plus, RefreshCw, Filter, X } from 'lucide-react'
import { SourceCard } from './SourceCard'
import { useSources } from '../hooks'
import type { Source, SourceFilters, CredibilityTier, SourceStatus } from '@/types/source'

interface SourceListProps {
  onSourceSelect?: (source: Source) => void
  onCreateSource?: () => void
  onEditSource?: (source: Source) => void
  onAssessSource?: (source: Source) => void
  onManageFeeds?: (source: Source) => void
}

export function SourceList({
  onSourceSelect,
  onCreateSource,
  onEditSource,
  onAssessSource,
  onManageFeeds,
}: SourceListProps) {
  const [filters, setFilters] = useState<SourceFilters>({
    limit: 50,
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const { data, isLoading, error, refetch } = useSources({
    ...filters,
    search: searchTerm || undefined,
    refetchInterval: 60000, // Refresh every minute
  })

  const sources = data?.sources ?? []

  // Filter sources client-side for instant search feedback
  const filteredSources = useMemo(() => {
    if (!searchTerm) return sources
    const term = searchTerm.toLowerCase()
    return sources.filter(
      (s) =>
        s.domain.toLowerCase().includes(term) ||
        s.canonical_name.toLowerCase().includes(term) ||
        s.organization_name?.toLowerCase().includes(term)
    )
  }, [sources, searchTerm])

  const clearFilters = () => {
    setFilters({ limit: 50 })
    setSearchTerm('')
  }

  const hasActiveFilters =
    filters.status ||
    filters.credibility_tier ||
    filters.country ||
    filters.category ||
    searchTerm

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            Sources
            <span className="text-sm font-normal text-muted-foreground">
              ({filteredSources.length})
            </span>
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            {onCreateSource && (
              <Button size="sm" onClick={onCreateSource}>
                <Plus className="h-4 w-4 mr-1" />
                Add Source
              </Button>
            )}
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="flex items-center gap-2 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by domain, name, or organization..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant={showFilters ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-1" />
            Filters
            {hasActiveFilters && (
              <span className="ml-1 bg-primary text-primary-foreground rounded-full w-5 h-5 text-xs flex items-center justify-center">
                !
              </span>
            )}
          </Button>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>

        {/* Filter Row */}
        {showFilters && (
          <div className="flex items-center gap-2 mt-3 flex-wrap">
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  status: value === 'all' ? undefined : (value as SourceStatus),
                })
              }
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.credibility_tier || 'all'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  credibility_tier:
                    value === 'all' ? undefined : (value as CredibilityTier),
                })
              }
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Credibility" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="tier_1">Tier 1 (Highly Credible)</SelectItem>
                <SelectItem value="tier_2">Tier 2 (Generally Credible)</SelectItem>
                <SelectItem value="tier_3">Tier 3 (Use with Caution)</SelectItem>
                <SelectItem value="unknown">Not Assessed</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.country || 'all'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  country: value === 'all' ? undefined : value,
                })
              }
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                <SelectItem value="DE">Germany</SelectItem>
                <SelectItem value="US">USA</SelectItem>
                <SelectItem value="GB">UK</SelectItem>
                <SelectItem value="FR">France</SelectItem>
                <SelectItem value="CH">Switzerland</SelectItem>
                <SelectItem value="AT">Austria</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.category || 'all'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  category: value === 'all' ? undefined : value,
                })
              }
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="technology">Technology</SelectItem>
                <SelectItem value="business">Business</SelectItem>
                <SelectItem value="science">Science</SelectItem>
                <SelectItem value="politics">Politics</SelectItem>
                <SelectItem value="finance">Finance</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {isLoading && sources.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
            <p>Loading sources...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-destructive">
            <p>Failed to load sources</p>
            <p className="text-sm mt-1">{error.message}</p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-4">
              Retry
            </Button>
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No sources found</p>
            {hasActiveFilters && (
              <Button variant="link" onClick={clearFilters} className="mt-2">
                Clear filters
              </Button>
            )}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {filteredSources.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                onSelect={onSourceSelect}
                onEdit={onEditSource}
                onAssess={onAssessSource}
                onManageFeeds={onManageFeeds}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
