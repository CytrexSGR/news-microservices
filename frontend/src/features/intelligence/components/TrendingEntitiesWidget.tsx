/**
 * TrendingEntitiesWidget - Trending entities list with sparklines
 *
 * Shows top persons, organizations, and locations from recent events
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import { User, Building2, MapPin, TrendingUp, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useTrendingEntities, useSubcategories } from '../api/useTrendingEntities';

interface TrendingEntitiesWidgetProps {
  hours?: number;
  limit?: number;
}

export function TrendingEntitiesWidget({ hours = 4, limit = 50 }: TrendingEntitiesWidgetProps) {
  const { persons, organizations, locations, totalEvents, isLoading, error, refetch } = useTrendingEntities(hours, limit);
  const { data: subcategories, isLoading: isLoadingSubcategories } = useSubcategories();

  const renderEntityList = (
    entities: [string, number][],
    icon: React.ReactNode,
    emptyMessage: string
  ) => {
    if (entities.length === 0) {
      return (
        <div className="text-center py-6 text-muted-foreground">
          {emptyMessage}
        </div>
      );
    }

    const maxCount = entities.length > 0 ? entities[0][1] : 1;

    return (
      <div className="space-y-2">
        {entities.map(([name, count], idx) => (
          <div
            key={name}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent transition-colors"
          >
            <span className="text-sm font-medium text-muted-foreground w-6">
              #{idx + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {icon}
                <span className="font-medium truncate">{name}</span>
              </div>
              {/* Mini sparkline bar */}
              <div className="mt-1 w-full bg-secondary rounded-full h-1">
                <div
                  className="bg-primary h-1 rounded-full transition-all"
                  style={{ width: `${(count / maxCount) * 100}%` }}
                />
              </div>
            </div>
            <Badge variant="secondary" className="ml-2">
              {count}
            </Badge>
          </div>
        ))}
      </div>
    );
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trending Entities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-destructive">
            Failed to load trending data
            <Button variant="link" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Trending Entities
          </CardTitle>
          <CardDescription>
            From {totalEvents} events in the last {hours} hours
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-4 w-6" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-5 w-12" />
              </div>
            ))}
          </div>
        ) : (
          <Tabs defaultValue="persons" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="persons" className="text-xs">
                <User className="h-3 w-3 mr-1" />
                People
              </TabsTrigger>
              <TabsTrigger value="organizations" className="text-xs">
                <Building2 className="h-3 w-3 mr-1" />
                Orgs
              </TabsTrigger>
              <TabsTrigger value="locations" className="text-xs">
                <MapPin className="h-3 w-3 mr-1" />
                Places
              </TabsTrigger>
            </TabsList>

            <TabsContent value="persons" className="mt-4">
              {renderEntityList(
                persons,
                <User className="h-4 w-4 text-blue-500" />,
                'No persons found in recent events'
              )}
            </TabsContent>

            <TabsContent value="organizations" className="mt-4">
              {renderEntityList(
                organizations,
                <Building2 className="h-4 w-4 text-purple-500" />,
                'No organizations found in recent events'
              )}
            </TabsContent>

            <TabsContent value="locations" className="mt-4">
              {renderEntityList(
                locations,
                <MapPin className="h-4 w-4 text-green-500" />,
                'No locations found in recent events'
              )}
            </TabsContent>
          </Tabs>
        )}

        {/* Subcategories */}
        {!isLoadingSubcategories && subcategories && (
          <div className="mt-6 pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Top Topics by Category</h4>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(subcategories).map(([category, topics]) => (
                <div key={category}>
                  <p className="text-xs text-muted-foreground uppercase mb-2">{category}</p>
                  <div className="space-y-1">
                    {topics.slice(0, 2).map((topic) => (
                      <div key={topic.name} className="text-sm flex items-center justify-between">
                        <span className="truncate">{topic.name}</span>
                        <span className="text-xs text-muted-foreground ml-1">
                          {topic.event_count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
