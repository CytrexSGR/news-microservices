/**
 * SubcategoriesPanel Component
 *
 * Displays subcategories breakdown for intelligence events
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  FolderTree,
  RefreshCw,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSubcategories } from '../api/useSubcategories';
import { CompactRiskBadge } from './RiskBadge';
import type { EventCategory, Subcategory } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor } from '../types/events.types';

interface SubcategoriesPanelProps {
  onSubcategoryClick?: (subcategory: Subcategory) => void;
  parentCategory?: EventCategory;
  className?: string;
}

export function SubcategoriesPanel({
  onSubcategoryClick,
  parentCategory,
  className,
}: SubcategoriesPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState<EventCategory | undefined>(parentCategory);

  const { data, isLoading, error, refetch } = useSubcategories({
    parent_category: selectedCategory,
  });

  const categories: EventCategory[] = ['breaking', 'developing', 'trend', 'recurring', 'anomaly'];

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center gap-3 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load subcategories</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group subcategories by parent category
  const groupedSubcategories = data?.subcategories.reduce((acc, sub) => {
    if (!acc[sub.parent_category]) {
      acc[sub.parent_category] = [];
    }
    acc[sub.parent_category].push(sub);
    return acc;
  }, {} as Record<EventCategory, Subcategory[]>) || {};

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FolderTree className="h-5 w-5" />
              Subcategories
            </CardTitle>
            <CardDescription>
              {data?.total || 0} subcategories across all event types
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Category filter */}
        <div className="flex flex-wrap gap-2 mt-4">
          <Button
            variant={!selectedCategory ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory(undefined)}
          >
            All
          </Button>
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                'capitalize',
                selectedCategory === cat && getCategoryBgColor(cat)
              )}
            >
              {cat}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : Object.keys(groupedSubcategories).length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No subcategories found
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedSubcategories).map(([category, subs]) => (
              <div key={category}>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      'capitalize',
                      getCategoryBgColor(category as EventCategory),
                      getCategoryColor(category as EventCategory)
                    )}
                  >
                    {category}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    ({subs.length} subcategories)
                  </span>
                </h4>

                <div className="space-y-2">
                  {subs.map((sub) => (
                    <div
                      key={sub.name}
                      className={cn(
                        'flex items-center justify-between p-3 rounded-lg border',
                        'hover:bg-accent/50 transition-colors',
                        onSubcategoryClick && 'cursor-pointer'
                      )}
                      onClick={() => onSubcategoryClick?.(sub)}
                    >
                      <div className="flex items-center gap-3">
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{sub.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {sub.count} events
                          </p>
                        </div>
                      </div>
                      <CompactRiskBadge score={sub.avg_risk} size="sm" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
