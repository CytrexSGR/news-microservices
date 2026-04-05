/**
 * MetadataEditor Component
 *
 * Edits basic strategy information:
 * - Name, Version, Description
 * - Author, Tags
 * - Is Public toggle
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Textarea } from '@/components/ui/Textarea'
import { Switch } from '@/components/ui/Switch'
import type { Strategy } from '@/types/strategy'

interface MetadataEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

export function MetadataEditor({ strategy, onChange }: MetadataEditorProps) {
  const handleChange = (field: string, value: any) => {
    if (onChange) {
      onChange(field, value)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Basic Information</CardTitle>
        <CardDescription>
          Configure strategy name, version, and visibility settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Name */}
        <div className="space-y-2">
          <Label htmlFor="name">
            Strategy Name
            <span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="name"
            value={strategy.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="e.g., Adaptive Momentum Strategy"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            A descriptive name for your trading strategy
          </p>
        </div>

        {/* Version */}
        <div className="space-y-2">
          <Label htmlFor="version">
            Version
            <span className="text-destructive ml-1">*</span>
          </Label>
          <Input
            id="version"
            value={strategy.version}
            onChange={(e) => handleChange('version', e.target.value)}
            placeholder="1.0.0"
            className="max-w-xs"
          />
          <p className="text-xs text-muted-foreground">
            Semantic version (e.g., 1.0.0, 2.1.3)
          </p>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={strategy.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Describe your strategy's approach, goals, and key characteristics..."
            rows={4}
            className="resize-none"
          />
          <p className="text-xs text-muted-foreground">
            Optional: Provide details about your strategy for documentation
          </p>
        </div>

        {/* Author */}
        <div className="space-y-2">
          <Label htmlFor="author">Author</Label>
          <Input
            id="author"
            value={strategy.author || 'andreas'}
            onChange={(e) => handleChange('author', e.target.value)}
            placeholder="andreas"
            className="max-w-md"
            disabled
          />
          <p className="text-xs text-muted-foreground">
            Strategy creator (automatically set to current user)
          </p>
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <Label htmlFor="tags">Tags</Label>
          <Input
            id="tags"
            value={strategy.tags?.join(', ') || ''}
            onChange={(e) => handleChange('tags', e.target.value.split(',').map(t => t.trim()))}
            placeholder="trend-following, momentum, futures"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            Comma-separated tags for categorization (e.g., trend-following, momentum)
          </p>
        </div>

        {/* Is Public */}
        <div className="flex items-center justify-between max-w-md py-4 px-4 border rounded-lg">
          <div className="space-y-0.5">
            <Label htmlFor="is-public">Public Strategy</Label>
            <p className="text-xs text-muted-foreground">
              Allow other users to view and use this strategy
            </p>
          </div>
          <Switch
            id="is-public"
            checked={strategy.is_public}
            onCheckedChange={(checked) => handleChange('is_public', checked)}
          />
        </div>

        {/* Created/Updated Metadata (Read-Only) */}
        <div className="pt-4 border-t space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Created:</span>
            <span className="font-medium">
              {new Date(strategy.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
          {strategy.updated_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last Updated:</span>
              <span className="font-medium">
                {new Date(strategy.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
