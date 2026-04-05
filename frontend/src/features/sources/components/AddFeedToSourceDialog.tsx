/**
 * AddFeedToSourceDialog Component
 *
 * Dialog for adding a new feed to an existing source.
 * Supports multiple provider types (RSS, MediaStack, etc.)
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { Switch } from '@/components/ui/Switch'
import { Badge } from '@/components/ui/badge'
import { Loader2, Globe } from 'lucide-react'
import { useAddSourceFeed } from '../hooks'
import type { Source, ProviderType, AddSourceFeedRequest } from '@/types/source'

interface AddFeedToSourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  source: Source | null
  onSuccess?: () => void
}

const PROVIDER_TYPES: { value: ProviderType; label: string; description: string }[] = [
  {
    value: 'rss',
    label: 'RSS Feed',
    description: 'Standard RSS/Atom feed URL',
  },
  {
    value: 'mediastack',
    label: 'MediaStack',
    description: 'MediaStack API source keyword',
  },
  {
    value: 'newsapi',
    label: 'NewsAPI',
    description: 'NewsAPI source identifier',
  },
  {
    value: 'gdelt',
    label: 'GDELT',
    description: 'GDELT data source',
  },
  {
    value: 'custom_api',
    label: 'Custom API',
    description: 'Custom API endpoint',
  },
]

const FEED_CATEGORIES = [
  'general',
  'technology',
  'business',
  'science',
  'politics',
  'finance',
  'sports',
  'entertainment',
  'health',
]

export function AddFeedToSourceDialog({
  open,
  onOpenChange,
  source,
  onSuccess,
}: AddFeedToSourceDialogProps) {
  const [formData, setFormData] = useState<AddSourceFeedRequest>({
    name: '',
    url: '',
    provider_type: 'rss',
    provider_config: {},
    category: 'general',
    is_active: true,
    fetch_interval_minutes: 60,
  })

  const addFeed = useAddSourceFeed(source?.id ?? '')

  // Reset form when source changes
  useEffect(() => {
    if (source) {
      setFormData((prev) => ({
        ...prev,
        name: `${source.canonical_name} Feed`,
        category: source.category?.toLowerCase() || 'general',
      }))
    }
  }, [source])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!source) return

    addFeed.mutate(formData, {
      onSuccess: () => {
        onOpenChange(false)
        resetForm()
        onSuccess?.()
      },
    })
  }

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      provider_type: 'rss',
      provider_config: {},
      category: 'general',
      is_active: true,
      fetch_interval_minutes: 60,
    })
  }

  const handleProviderChange = (providerType: ProviderType) => {
    setFormData({
      ...formData,
      provider_type: providerType,
      url: '', // Reset URL when provider changes
      provider_config: {}, // Reset config
    })
  }

  const getUrlPlaceholder = (): string => {
    switch (formData.provider_type) {
      case 'rss':
        return 'https://example.com/feed.xml'
      case 'mediastack':
        return 'source_keyword (e.g., bbc-news)'
      case 'newsapi':
        return 'source_id (e.g., bbc-news)'
      case 'gdelt':
        return 'gdelt_query'
      case 'custom_api':
        return 'https://api.example.com/news'
      default:
        return 'Feed URL or identifier'
    }
  }

  const getUrlLabel = (): string => {
    switch (formData.provider_type) {
      case 'rss':
        return 'Feed URL'
      case 'mediastack':
      case 'newsapi':
        return 'Source Identifier'
      case 'gdelt':
        return 'GDELT Query'
      case 'custom_api':
        return 'API Endpoint'
      default:
        return 'URL / Identifier'
    }
  }

  const isValid = formData.name.length > 0 && formData.url.length > 0

  if (!source) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add Feed to Source</DialogTitle>
            <DialogDescription className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              <span>{source.canonical_name}</span>
              <Badge variant="outline">{source.domain}</Badge>
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="provider_type">Provider Type</Label>
              <Select
                value={formData.provider_type}
                onValueChange={(value: ProviderType) => handleProviderChange(value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PROVIDER_TYPES.map((provider) => (
                    <SelectItem key={provider.value} value={provider.value}>
                      <div className="flex flex-col">
                        <span>{provider.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {PROVIDER_TYPES.find((p) => p.value === formData.provider_type)?.description}
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="name">Feed Name *</Label>
              <Input
                id="name"
                placeholder="Main RSS Feed"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="url">{getUrlLabel()} *</Label>
              <Input
                id="url"
                placeholder={getUrlPlaceholder()}
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({ ...formData, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FEED_CATEGORIES.map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="fetch_interval">Fetch Interval (min)</Label>
                <Input
                  id="fetch_interval"
                  type="number"
                  min={5}
                  max={1440}
                  value={formData.fetch_interval_minutes}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      fetch_interval_minutes: parseInt(e.target.value) || 60,
                    })
                  }
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="is_active">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Enable automatic fetching
                </p>
              </div>
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked })
                }
              />
            </div>

            {/* Provider-specific config fields */}
            {formData.provider_type === 'mediastack' && (
              <div className="grid gap-2 p-3 bg-muted/50 rounded-lg">
                <Label className="text-xs text-muted-foreground">MediaStack Options</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="countries (e.g., de,us)"
                    value={(formData.provider_config as Record<string, string>).countries || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        provider_config: {
                          ...formData.provider_config,
                          countries: e.target.value,
                        },
                      })
                    }
                  />
                  <Input
                    placeholder="languages (e.g., en,de)"
                    value={(formData.provider_config as Record<string, string>).languages || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        provider_config: {
                          ...formData.provider_config,
                          languages: e.target.value,
                        },
                      })
                    }
                  />
                </div>
              </div>
            )}

            {formData.provider_type === 'custom_api' && (
              <div className="grid gap-2 p-3 bg-muted/50 rounded-lg">
                <Label className="text-xs text-muted-foreground">Custom API Options</Label>
                <Input
                  placeholder="API Key (optional)"
                  type="password"
                  value={(formData.provider_config as Record<string, string>).api_key || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      provider_config: {
                        ...formData.provider_config,
                        api_key: e.target.value,
                      },
                    })
                  }
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || addFeed.isPending}>
              {addFeed.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Add Feed
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
