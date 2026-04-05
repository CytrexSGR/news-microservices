/**
 * SubcategoriesPage
 *
 * Subcategories breakdown view
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { SubcategoriesPanel } from '../components/SubcategoriesPanel';
import { EventClustersGrid } from '../components/EventClustersGrid';
import type { Subcategory, EventCluster } from '../types/events.types';

export function SubcategoriesPage() {
  const [selectedSubcategory, setSelectedSubcategory] = useState<Subcategory | null>(null);

  const handleSubcategoryClick = (subcategory: Subcategory) => {
    setSelectedSubcategory(subcategory);
  };

  const handleClusterClick = (cluster: EventCluster) => {
    // Navigate to cluster detail
    console.log('Cluster clicked:', cluster.id);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Event Subcategories</h1>
          <p className="text-muted-foreground">
            Explore events organized by subcategory
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Subcategories Panel */}
        <div className="lg:col-span-1">
          <SubcategoriesPanel
            onSubcategoryClick={handleSubcategoryClick}
          />
        </div>

        {/* Selected Subcategory Content */}
        <div className="lg:col-span-2">
          {selectedSubcategory ? (
            <Card>
              <CardHeader>
                <CardTitle>{selectedSubcategory.name}</CardTitle>
                <CardDescription>
                  {selectedSubcategory.count} events | Parent: {selectedSubcategory.parent_category}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EventClustersGrid
                  onClusterClick={handleClusterClick}
                  pageSize={6}
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-muted-foreground">
                  <p className="text-lg mb-2">Select a subcategory</p>
                  <p className="text-sm">
                    Choose a subcategory from the left panel to view related event clusters
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
