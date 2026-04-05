// frontend/src/features/geo-map/components/EntityGraph/EntityGraph.tsx

import { useEffect, useRef, useState } from 'react';
import { useEntityGraph } from '../../hooks/useEntityGraph';
import type { EntityNode } from '../../hooks/useEntityGraph';
import { useGeoMapStore } from '../../store/geoMapStore';

const TYPE_COLORS: Record<string, string> = {
  PERSON: '#ef4444',
  ORG: '#3b82f6',
  GPE: '#22c55e',
  NORP: '#f59e0b',
  FAC: '#8b5cf6',
  EVENT: '#ec4899',
  UNKNOWN: '#64748b',
};

interface EntityGraphProps {
  selectedCountry?: string;
}

export function EntityGraph({ selectedCountry }: EntityGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<EntityNode | null>(null);
  const { data, isLoading, error } = useEntityGraph(selectedCountry, 40);
  const { highlightedCountries, setHighlightedCountries, setHighlightedEntity, highlightedEntity } = useGeoMapStore();

  const handleNodeSelect = (node: EntityNode) => {
    setSelectedNode(node);
    setHighlightedEntity(node.name);

    // Highlight countries associated with this entity
    if (node.countries && node.countries.length > 0) {
      setHighlightedCountries(node.countries);
    }
  };

  const clearEntityHighlight = () => {
    setSelectedNode(null);
    setHighlightedEntity(null);
    setHighlightedCountries([]);
  };

  useEffect(() => {
    if (!data || !containerRef.current) return;

    // Simple force-directed layout using vanilla JS
    // For production, use D3.js force simulation
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 400;

    // Clear previous content
    container.innerHTML = '';

    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', String(width));
    svg.setAttribute('height', String(height));
    svg.style.backgroundColor = '#1e293b';
    svg.style.borderRadius = '8px';
    container.appendChild(svg);

    // Position nodes in a circle
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2.5;

    const nodePositions: Record<string, { x: number; y: number }> = {};
    data.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / data.nodes.length;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    // Draw edges
    data.edges.forEach((edge) => {
      const sourcePos = nodePositions[edge.source];
      const targetPos = nodePositions[edge.target];
      if (!sourcePos || !targetPos) return;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', String(sourcePos.x));
      line.setAttribute('y1', String(sourcePos.y));
      line.setAttribute('x2', String(targetPos.x));
      line.setAttribute('y2', String(targetPos.y));
      line.setAttribute('stroke', '#475569');
      line.setAttribute('stroke-width', String(Math.max(1, edge.weight * 2)));
      line.setAttribute('opacity', '0.5');
      svg.appendChild(line);
    });

    // Draw nodes
    data.nodes.forEach((node) => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      const nodeSize = 8 + Math.min(node.mention_count * 2, 16);
      const color = TYPE_COLORS[node.type] || TYPE_COLORS.UNKNOWN;

      // Node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', String(pos.x));
      circle.setAttribute('cy', String(pos.y));
      circle.setAttribute('r', String(nodeSize));
      circle.setAttribute('fill', color);
      circle.setAttribute('stroke', '#fff');
      circle.setAttribute('stroke-width', '2');
      circle.style.cursor = 'pointer';
      circle.onclick = () => handleNodeSelect(node);
      svg.appendChild(circle);

      // Node label (only for larger nodes)
      if (node.mention_count >= 3) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', String(pos.x));
        text.setAttribute('y', String(pos.y + nodeSize + 12));
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#94a3b8');
        text.setAttribute('font-size', '10');
        text.textContent = node.name.length > 12 ? node.name.slice(0, 12) + '...' : node.name;
        svg.appendChild(text);
      }
    });
  }, [data]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <span>🕸️</span> Entity Network
      </h3>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-xs">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </span>
        ))}
      </div>

      {/* Graph Container */}
      {isLoading ? (
        <div className="h-96 flex items-center justify-center bg-slate-800 rounded-lg">
          <span className="text-slate-400">Loading graph...</span>
        </div>
      ) : error ? (
        <div className="h-96 flex items-center justify-center bg-slate-800 rounded-lg">
          <span className="text-red-400">Failed to load entity graph</span>
        </div>
      ) : (
        <div ref={containerRef} className="w-full" />
      )}

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="p-3 bg-slate-800 rounded-lg ring-2 ring-orange-500/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: TYPE_COLORS[selectedNode.type] }}
              />
              <span className="font-semibold">{selectedNode.name}</span>
              <span className="text-xs text-slate-400">({selectedNode.type})</span>
            </div>
            <button
              onClick={clearEntityHighlight}
              className="text-xs text-slate-400 hover:text-white transition-colors"
            >
              Clear
            </button>
          </div>
          <div className="text-sm text-slate-300">
            <p>Mentions: {selectedNode.mention_count}</p>
            {selectedNode.threat_score && (
              <p>Threat Score: {selectedNode.threat_score.toFixed(1)}</p>
            )}
            {selectedNode.countries.length > 0 && (
              <p className="text-orange-400">
                Highlighted on map: {selectedNode.countries.join(', ')}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      {data && (
        <div className="text-xs text-slate-500 text-center">
          {data.total_nodes} entities {data.total_edges > 0 && `• ${data.total_edges} relationships`}
        </div>
      )}
    </div>
  );
}
