/**
 * ClusterDetailsPage
 *
 * Detailed view of a specific event cluster
 */
import { useParams, useNavigate } from 'react-router-dom';
import { ClusterDetailView } from '../components/ClusterDetailView';
import { ClusterEventsTable } from '../components/ClusterEventsTable';
import type { IntelligenceEvent } from '../types/events.types';

export function ClusterDetailsPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/intelligence/events');
  };

  const handleEventClick = (event: IntelligenceEvent) => {
    // Navigate to event detail or open modal
    console.log('Event clicked:', event.id);
  };

  const handleRelatedClusterClick = (relatedClusterId: string) => {
    navigate(`/intelligence/events/clusters/${relatedClusterId}`);
  };

  if (!clusterId) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center text-muted-foreground">
          Invalid cluster ID
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <ClusterDetailView
        clusterId={clusterId}
        onBack={handleBack}
        onEventClick={handleEventClick}
        onRelatedClusterClick={handleRelatedClusterClick}
      />

      <ClusterEventsTable
        clusterId={clusterId}
        onEventClick={handleEventClick}
        pageSize={10}
      />
    </div>
  );
}
