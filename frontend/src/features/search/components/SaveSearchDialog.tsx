/**
 * SaveSearchDialog Component
 *
 * Modal dialog to save the current search query and filters.
 * Features:
 * - Name input with validation
 * - Shows current query and active filters
 * - Notification toggle for new results
 * - Loading state during save
 */

import * as React from 'react'
import { useState } from 'react'
import { Bookmark, Bell, BellOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Switch } from '@/components/ui/Switch'
import { Badge } from '@/components/ui/badge'
import { useCreateSavedSearch } from '../api/useSavedSearches'
import type { SavedSearchFilters } from '../types/savedSearch'

interface SaveSearchDialogProps {
  /** Current search query */
  query: string
  /** Current active filters */
  filters: {
    source?: string | null
    sentiment?: string | null
    date_from?: string | null
    date_to?: string | null
  }
  /** Trigger element (optional, defaults to save button) */
  trigger?: React.ReactNode
  /** Called after successful save */
  onSaved?: () => void
}

export function SaveSearchDialog({
  query,
  filters,
  trigger,
  onSaved,
}: SaveSearchDialogProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [notifications, setNotifications] = useState(false)

  const { mutate: createSearch, isPending } = useCreateSavedSearch()

  // Count active filters
  const activeFilterCount =
    (filters.source ? 1 : 0) +
    (filters.sentiment ? 1 : 0) +
    (filters.date_from ? 1 : 0) +
    (filters.date_to ? 1 : 0)

  // Disable save if no query and no filters
  const canSave = query.trim().length > 0 || activeFilterCount > 0

  const handleSave = () => {
    if (!name.trim()) {
      toast.error('Please enter a name for your saved search')
      return
    }

    // Convert filters to API format (arrays for source/sentiment)
    const apiFilters: SavedSearchFilters = {
      source: filters.source ? [filters.source] : null,
      sentiment: filters.sentiment ? [filters.sentiment] : null,
      date_from: filters.date_from || null,
      date_to: filters.date_to || null,
    }

    createSearch(
      {
        name: name.trim(),
        query: query || '',
        filters: activeFilterCount > 0 ? apiFilters : null,
        notifications_enabled: notifications,
      },
      {
        onSuccess: (saved) => {
          toast.success(`Saved search "${saved.name}" created`)
          setOpen(false)
          setName('')
          setNotifications(false)
          onSaved?.()
        },
        onError: (error: Error) => {
          toast.error(error.message || 'Failed to save search')
        },
      }
    )
  }

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen)
    if (!newOpen) {
      // Reset form when closing
      setName('')
      setNotifications(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button
            variant="outline"
            size="sm"
            disabled={!canSave}
            className="gap-2"
          >
            <Bookmark className="h-4 w-4" />
            Save Search
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bookmark className="h-5 w-5" />
            Save Search
          </DialogTitle>
          <DialogDescription>
            Save this search to quickly run it again later.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Search Name */}
          <div className="space-y-2">
            <Label htmlFor="search-name">Name</Label>
            <Input
              id="search-name"
              placeholder="e.g., AI Technology News"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isPending}
              autoFocus
            />
          </div>

          {/* Current Query */}
          {query && (
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Query</Label>
              <div className="p-3 rounded-md bg-muted text-sm font-mono">
                {query}
              </div>
            </div>
          )}

          {/* Active Filters */}
          {activeFilterCount > 0 && (
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Filters</Label>
              <div className="flex flex-wrap gap-2">
                {filters.source && (
                  <Badge variant="secondary">Source: {filters.source}</Badge>
                )}
                {filters.sentiment && (
                  <Badge variant="secondary">
                    Category: {filters.sentiment}
                  </Badge>
                )}
                {filters.date_from && (
                  <Badge variant="secondary">From: {filters.date_from}</Badge>
                )}
                {filters.date_to && (
                  <Badge variant="secondary">To: {filters.date_to}</Badge>
                )}
              </div>
            </div>
          )}

          {/* Notifications Toggle */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                {notifications ? (
                  <Bell className="h-4 w-4 text-primary" />
                ) : (
                  <BellOff className="h-4 w-4 text-muted-foreground" />
                )}
                <Label
                  htmlFor="notifications"
                  className="text-sm font-medium cursor-pointer"
                >
                  Enable Notifications
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Get notified when new articles match this search.
              </p>
            </div>
            <Switch
              id="notifications"
              checked={notifications}
              onCheckedChange={setNotifications}
              disabled={isPending}
            />
          </div>
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
  )
}
