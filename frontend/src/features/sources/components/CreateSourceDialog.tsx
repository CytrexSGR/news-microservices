/**
 * CreateSourceDialog Component
 *
 * Dialog for creating a new source with essential fields.
 * Advanced options are collapsed by default.
 */

import { useState } from 'react'
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
import { Textarea } from '@/components/ui/Textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Switch } from '@/components/ui/Switch'
import { ChevronDown, Loader2 } from 'lucide-react'
import { useCreateSource } from '../hooks'
import type { CreateSourceRequest, PaywallType } from '@/types/source'

interface CreateSourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: (sourceId: string) => void
}

const CATEGORIES = [
  'General News',
  'Technology',
  'Business',
  'Science',
  'Politics',
  'Finance',
  'Sports',
  'Entertainment',
  'Health',
  'World News',
]

const COUNTRIES = [
  { code: 'DE', name: 'Germany' },
  { code: 'US', name: 'USA' },
  { code: 'GB', name: 'UK' },
  { code: 'FR', name: 'France' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'AT', name: 'Austria' },
  { code: 'AU', name: 'Australia' },
  { code: 'CA', name: 'Canada' },
]

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'de', name: 'German' },
  { code: 'fr', name: 'French' },
  { code: 'es', name: 'Spanish' },
]

const SCRAPE_METHODS = [
  'newspaper4k',
  'trafilatura',
  'readability',
  'beautifulsoup',
  'selenium',
]

export function CreateSourceDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateSourceDialogProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [formData, setFormData] = useState<CreateSourceRequest>({
    domain: '',
    canonical_name: '',
    organization_name: '',
    description: '',
    homepage_url: '',
    category: '',
    country: '',
    language: 'en',
    scrape_method: 'newspaper4k',
    paywall_type: 'none',
    rate_limit_per_minute: 10,
    requires_stealth: false,
    requires_proxy: false,
  })

  const createSource = useCreateSource()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Auto-generate homepage_url from domain if not provided
    const request = {
      ...formData,
      homepage_url: formData.homepage_url || `https://${formData.domain}`,
    }

    createSource.mutate(request, {
      onSuccess: (source) => {
        onOpenChange(false)
        resetForm()
        onSuccess?.(source.id)
      },
    })
  }

  const resetForm = () => {
    setFormData({
      domain: '',
      canonical_name: '',
      organization_name: '',
      description: '',
      homepage_url: '',
      category: '',
      country: '',
      language: 'en',
      scrape_method: 'newspaper4k',
      paywall_type: 'none',
      rate_limit_per_minute: 10,
      requires_stealth: false,
      requires_proxy: false,
    })
    setShowAdvanced(false)
  }

  const handleDomainChange = (domain: string) => {
    setFormData((prev) => ({
      ...prev,
      domain,
      // Auto-fill canonical_name from domain if empty
      canonical_name: prev.canonical_name || formatDomainAsName(domain),
    }))
  }

  const formatDomainAsName = (domain: string): string => {
    // Remove common prefixes and format nicely
    return domain
      .replace(/^(www\.|news\.|rss\.)/i, '')
      .split('.')
      .slice(0, -1)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ')
  }

  const isValid = formData.domain.length > 0 && formData.canonical_name.length > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add New Source</DialogTitle>
            <DialogDescription>
              Add a new news source to the system. The source will be available for
              feed association and assessment.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Essential Fields */}
            <div className="grid gap-2">
              <Label htmlFor="domain">Domain *</Label>
              <Input
                id="domain"
                placeholder="example.com"
                value={formData.domain}
                onChange={(e) => handleDomainChange(e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground">
                The main domain of the news source (without https://)
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="canonical_name">Name *</Label>
              <Input
                id="canonical_name"
                placeholder="Example News"
                value={formData.canonical_name}
                onChange={(e) =>
                  setFormData({ ...formData, canonical_name: e.target.value })
                }
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="organization_name">Organization</Label>
              <Input
                id="organization_name"
                placeholder="Example Media Group"
                value={formData.organization_name}
                onChange={(e) =>
                  setFormData({ ...formData, organization_name: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        {cat}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="country">Country</Label>
                <Select
                  value={formData.country}
                  onValueChange={(value) =>
                    setFormData({ ...formData, country: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRIES.map((c) => (
                      <SelectItem key={c.code} value={c.code}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Brief description of the source..."
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={2}
              />
            </div>

            {/* Advanced Options */}
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full justify-between"
                >
                  Advanced Options
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      showAdvanced ? 'rotate-180' : ''
                    }`}
                  />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="language">Language</Label>
                    <Select
                      value={formData.language}
                      onValueChange={(value) =>
                        setFormData({ ...formData, language: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LANGUAGES.map((lang) => (
                          <SelectItem key={lang.code} value={lang.code}>
                            {lang.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="scrape_method">Scrape Method</Label>
                    <Select
                      value={formData.scrape_method}
                      onValueChange={(value) =>
                        setFormData({ ...formData, scrape_method: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SCRAPE_METHODS.map((method) => (
                          <SelectItem key={method} value={method}>
                            {method}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="paywall_type">Paywall Type</Label>
                    <Select
                      value={formData.paywall_type}
                      onValueChange={(value: PaywallType) =>
                        setFormData({ ...formData, paywall_type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="soft">Soft</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                        <SelectItem value="metered">Metered</SelectItem>
                        <SelectItem value="dynamic">Dynamic</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="rate_limit">Rate Limit (/min)</Label>
                    <Input
                      id="rate_limit"
                      type="number"
                      min={1}
                      max={100}
                      value={formData.rate_limit_per_minute}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rate_limit_per_minute: parseInt(e.target.value) || 10,
                        })
                      }
                    />
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="homepage_url">Homepage URL</Label>
                  <Input
                    id="homepage_url"
                    placeholder={`https://${formData.domain || 'example.com'}`}
                    value={formData.homepage_url}
                    onChange={(e) =>
                      setFormData({ ...formData, homepage_url: e.target.value })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Defaults to https://{'{domain}'} if not specified
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="requires_stealth">Requires Stealth</Label>
                    <p className="text-xs text-muted-foreground">
                      Use stealth mode for scraping
                    </p>
                  </div>
                  <Switch
                    id="requires_stealth"
                    checked={formData.requires_stealth}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, requires_stealth: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="requires_proxy">Requires Proxy</Label>
                    <p className="text-xs text-muted-foreground">
                      Route requests through proxy
                    </p>
                  </div>
                  <Switch
                    id="requires_proxy"
                    checked={formData.requires_proxy}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, requires_proxy: checked })
                    }
                  />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || createSource.isPending}>
              {createSource.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Source
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
