/**
 * CategorySettings Component
 *
 * Category-specific notification settings.
 */

import { useState } from 'react';
import {
  Newspaper,
  Bell,
  AlertTriangle,
  TrendingUp,
  Search,
  FileText,
  Settings2,
} from 'lucide-react';
import { Switch } from '@/components/ui/Switch';
import { Label } from '@/components/ui/Label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { useNotificationPreferences, useUpdateNotificationPreferences } from '../../api';
import type { NotificationEventType } from '../../types';

interface CategorySettingsProps {
  className?: string;
}

interface CategoryConfig {
  id: string;
  label: string;
  description: string;
  icon: typeof Newspaper;
  eventTypes: NotificationEventType[];
}

const CATEGORIES: CategoryConfig[] = [
  {
    id: 'articles',
    label: 'Articles',
    description: 'New articles, analysis completion, and high-priority content',
    icon: Newspaper,
    eventTypes: ['article.new', 'article.analysis_complete', 'article.high_priority'],
  },
  {
    id: 'feeds',
    label: 'Feeds',
    description: 'Feed updates, errors, and health warnings',
    icon: Bell,
    eventTypes: ['feed.new_items', 'feed.error', 'feed.health_warning'],
  },
  {
    id: 'osint',
    label: 'OSINT Alerts',
    description: 'Intelligence alerts and report notifications',
    icon: AlertTriangle,
    eventTypes: ['osint.alert', 'osint.report_ready'],
  },
  {
    id: 'research',
    label: 'Research',
    description: 'Research completion and error notifications',
    icon: Search,
    eventTypes: ['research.complete', 'research.error'],
  },
  {
    id: 'system',
    label: 'System',
    description: 'Maintenance windows and system alerts',
    icon: Settings2,
    eventTypes: ['system.maintenance', 'system.alert'],
  },
];

const PRIORITY_OPTIONS = [
  { value: 'all', label: 'All Priorities' },
  { value: 'normal', label: 'Normal and above' },
  { value: 'high', label: 'High and above' },
  { value: 'critical', label: 'Critical only' },
];

export function CategorySettings({ className }: CategorySettingsProps) {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Notification Categories</CardTitle>
          <CardDescription>Configure which types of notifications you receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg border animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded bg-muted" />
                <div className="space-y-1.5">
                  <div className="h-4 w-24 bg-muted rounded" />
                  <div className="h-3 w-40 bg-muted rounded" />
                </div>
              </div>
              <div className="h-5 w-10 rounded-full bg-muted" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const getCategoryEnabled = (categoryId: string): boolean => {
    const filters = preferences?.filters || {};
    const categories = filters.categories || [];
    const category = categories.find((c) => c.category === categoryId);
    return category?.enabled ?? true; // Default to enabled
  };

  const getCategoryPriority = (categoryId: string): string => {
    const filters = preferences?.filters || {};
    const categories = filters.categories || [];
    const category = categories.find((c) => c.category === categoryId);
    return category?.priority_threshold || 'all';
  };

  const handleCategoryToggle = (categoryId: string, enabled: boolean) => {
    const filters = preferences?.filters || {};
    const categories = filters.categories || [];

    const updatedCategories = categories.filter((c) => c.category !== categoryId);
    updatedCategories.push({
      category: categoryId,
      enabled,
      priority_threshold: getCategoryPriority(categoryId) as any,
    });

    updatePreferences.mutate({
      filters: {
        ...filters,
        categories: updatedCategories,
      },
    });
  };

  const handlePriorityChange = (categoryId: string, priority: string) => {
    const filters = preferences?.filters || {};
    const categories = filters.categories || [];

    const updatedCategories = categories.filter((c) => c.category !== categoryId);
    updatedCategories.push({
      category: categoryId,
      enabled: getCategoryEnabled(categoryId),
      priority_threshold: priority as any,
    });

    updatePreferences.mutate({
      filters: {
        ...filters,
        categories: updatedCategories,
      },
    });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Notification Categories</CardTitle>
        <CardDescription>Configure which types of notifications you receive</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {CATEGORIES.map(({ id, label, description, icon: Icon, eventTypes }) => {
          const enabled = getCategoryEnabled(id);
          const priority = getCategoryPriority(id);
          const isExpanded = expandedCategory === id;

          return (
            <Collapsible
              key={id}
              open={isExpanded}
              onOpenChange={(open) => setExpandedCategory(open ? id : null)}
            >
              <div
                className={cn(
                  'rounded-lg border transition-colors',
                  enabled ? 'border-border' : 'border-border/50 opacity-75'
                )}
              >
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'h-8 w-8 rounded flex items-center justify-center',
                        enabled ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <Label className="text-sm font-medium">{label}</Label>
                      <p className="text-xs text-muted-foreground">{description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-7 px-2">
                        <Settings2 className="h-3.5 w-3.5" />
                      </Button>
                    </CollapsibleTrigger>
                    <Switch
                      checked={enabled}
                      onCheckedChange={(checked) => handleCategoryToggle(id, checked)}
                    />
                  </div>
                </div>

                <CollapsibleContent>
                  <div className="px-3 pb-3 space-y-3 border-t pt-3 bg-muted/30">
                    {/* Priority filter */}
                    <div className="flex items-center justify-between">
                      <Label className="text-sm">Minimum Priority</Label>
                      <Select
                        value={priority}
                        onValueChange={(value) => handlePriorityChange(id, value)}
                      >
                        <SelectTrigger className="w-[160px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PRIORITY_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Event types info */}
                    <div>
                      <Label className="text-sm text-muted-foreground">Includes events:</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {eventTypes.map((event) => (
                          <span
                            key={event}
                            className="text-xs px-2 py-0.5 rounded-full bg-muted"
                          >
                            {event}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          );
        })}
      </CardContent>
    </Card>
  );
}
