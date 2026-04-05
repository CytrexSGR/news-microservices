import { useGlobeStore } from '../store/globeStore';
import type { GraphDomainStats } from '../types/globe.types';

const DOMAIN_COLORS: Record<string, string> = {
  flight: 'text-yellow-400',
  vessel: 'text-blue-400',
  satellite: 'text-gray-300',
};

function DomainPulse({ stats }: { stats: GraphDomainStats | null }) {
  if (!stats) return <span className="text-gray-600">--</span>;

  const pulseOpacity = Math.max(0.2, Math.min(1, stats.avg_weight));
  const color = DOMAIN_COLORS[stats.domain] || 'text-white';

  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${color.replace('text-', 'bg-')}`}
        style={{ opacity: pulseOpacity, transition: 'opacity 1s ease' }}
      />
      <div className="flex-1">
        <div className={`text-xs font-mono ${color}`}>
          {stats.domain.toUpperCase()}
        </div>
        <div className="text-[10px] text-gray-400 font-mono">
          {stats.nodes}n {stats.edges}e w={stats.avg_weight.toFixed(3)}
        </div>
      </div>
    </div>
  );
}

export function GraphPulsePanel() {
  const graphState = useGlobeStore((s) => s.graphState);

  const totalEdges = (graphState.flight?.edges || 0)
    + (graphState.vessel?.edges || 0)
    + (graphState.satellite?.edges || 0);

  return (
    <div className="absolute bottom-4 right-4 bg-black/70 backdrop-blur-sm border border-gray-700 rounded-lg p-3 z-10 w-48">
      <h4 className="text-[10px] font-bold text-gray-400 mb-2 tracking-wider">
        GRAPH PULSE
      </h4>
      <div className="space-y-2">
        <DomainPulse stats={graphState.flight} />
        <DomainPulse stats={graphState.vessel} />
        <DomainPulse stats={graphState.satellite} />
      </div>
      <div className="mt-2 pt-2 border-t border-gray-700 text-[10px] text-gray-500 font-mono">
        {totalEdges} total edges
      </div>
    </div>
  );
}
