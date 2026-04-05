/**
 * EventsPage
 *
 * Event clusters overview page
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { EventClustersGrid } from '../components/EventClustersGrid';
import type { EventCluster } from '../types/events.types';

export function EventsPage() {
  const navigate = useNavigate();

  const handleClusterClick = (cluster: EventCluster) => {
    navigate(`/intelligence/events/clusters/${cluster.id}`);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Intelligence Events</h1>
          <p className="text-muted-foreground">
            Monitor and analyze event clusters across intelligence sources
          </p>
        </div>
      </div>

      <EventClustersGrid
        onClusterClick={handleClusterClick}
        pageSize={12}
      />
    </div>
  );
}
