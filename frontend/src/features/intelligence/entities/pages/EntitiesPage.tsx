/**
 * EntitiesPage - Single entity canonicalization page
 *
 * Main page for canonicalizing individual entities.
 */
import { useState } from 'react';
import { Sparkles, History, BarChart3 } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { EntityCanonForm } from '../components/EntityCanonForm';
import { EntityClustersTable } from '../components/EntityClustersTable';
import { EntityHistoryTimeline } from '../components/EntityHistoryTimeline';
import { CanonStatsCard } from '../components/CanonStatsCard';
import type { CanonicalEntity, EntityCluster } from '../types/entities.types';

interface EntitiesPageProps {
  onEntitySelect?: (entity: EntityCluster) => void;
}

export function EntitiesPage({ onEntitySelect }: EntitiesPageProps) {
  const [lastResult, setLastResult] = useState<CanonicalEntity | null>(null);

  const handleSuccess = (result: CanonicalEntity) => {
    setLastResult(result);
  };

  const handleEntityClick = (entity: EntityCluster) => {
    onEntitySelect?.(entity);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Sparkles className="h-8 w-8" />
          Entity Canonicalization
        </h1>
        <p className="text-muted-foreground mt-1">
          Resolve entity names to their canonical forms with Wikidata linking
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Canonicalization Form */}
        <div className="lg:col-span-1">
          <EntityCanonForm onSuccess={handleSuccess} />
        </div>

        {/* Right Column - Stats & History */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="clusters" className="space-y-4">
            <TabsList>
              <TabsTrigger value="clusters" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Top Entities
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                Merge History
              </TabsTrigger>
              <TabsTrigger value="stats" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Statistics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="clusters">
              <EntityClustersTable onEntityClick={handleEntityClick} />
            </TabsContent>

            <TabsContent value="history">
              <EntityHistoryTimeline limit={20} />
            </TabsContent>

            <TabsContent value="stats">
              <CanonStatsCard />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
