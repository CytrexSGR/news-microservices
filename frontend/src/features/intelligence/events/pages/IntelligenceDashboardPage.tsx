/**
 * IntelligenceDashboardPage
 *
 * Main intelligence dashboard with overview metrics
 */
import { useNavigate } from 'react-router-dom';
import { IntelligenceDashboard } from '../components/IntelligenceDashboard';
import type { EventCluster, IntelligenceEvent } from '../types/events.types';

export function IntelligenceDashboardPage() {
  const navigate = useNavigate();

  const handleClusterClick = (cluster: EventCluster) => {
    navigate(`/intelligence/events/clusters/${cluster.id}`);
  };

  const handleEventClick = (event: IntelligenceEvent) => {
    // Navigate to event detail or open in modal
    console.log('Event clicked:', event.id);
  };

  return (
    <div className="container mx-auto py-6">
      <IntelligenceDashboard
        onClusterClick={handleClusterClick}
        onEventClick={handleEventClick}
      />
    </div>
  );
}
