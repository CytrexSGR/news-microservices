import { useState } from 'react';
import { useGlobeStore } from '../store/globeStore';
import type { GlobeViewMode, DataLayerType } from '../types/globe.types';
import type { EdgeLayerType } from '../store/globeStore';

const VIEW_MODES: { value: GlobeViewMode; label: string }[] = [
  { value: 'standard', label: 'Standard' },
  { value: 'nvg', label: 'NVG' },
  { value: 'flir', label: 'FLIR' },
  { value: 'threat', label: 'Threat' },
];

const LAYER_LABELS: Record<DataLayerType, string> = {
  'news-events': 'News Events',
  flights: 'Flights',
  vessels: 'Vessels',
  satellites: 'Satellites',
  earthquakes: 'Earthquakes',
  gdelt: 'GDELT',
  anomalies: 'DCA Anomalies',
};

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-sm font-medium py-1 hover:text-primary transition-colors"
      >
        <span>{title}</span>
        <span className="text-xs opacity-60">{open ? '\u25B2' : '\u25BC'}</span>
      </button>
      {open && <div className="pt-1 pb-2">{children}</div>}
    </div>
  );
}

export function GlobeControls() {
  const { viewMode, setViewMode, layers, toggleLayer, edgeLayers, toggleEdgeLayer } =
    useGlobeStore();

  const activeEdgeCount = edgeLayers.filter((l) => l.visible).length;

  return (
    <div className="absolute top-4 right-4 bg-background/80 backdrop-blur-sm border rounded-lg p-3 space-y-1 w-56 z-10 max-h-[80vh] overflow-y-auto">
      <Section title="View Mode" defaultOpen>
        <div className="flex flex-wrap gap-1">
          {VIEW_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setViewMode(m.value)}
              className={`px-2 py-1 text-xs rounded ${
                viewMode === m.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </Section>

      <Section title="Data Layers" defaultOpen>
        <div className="space-y-1">
          {layers.map((layer) => (
            <label
              key={layer.type}
              className="flex items-center gap-2 text-xs cursor-pointer"
            >
              <input
                type="checkbox"
                checked={layer.visible}
                onChange={() => toggleLayer(layer.type)}
                className="rounded"
              />
              {LAYER_LABELS[layer.type]}
            </label>
          ))}
        </div>
      </Section>

      <Section title={`Graph Edges${activeEdgeCount > 0 ? ` (${activeEdgeCount})` : ''}`}>
        <div className="space-y-1">
          {edgeLayers.map((edge) => (
            <label
              key={edge.type}
              className="flex items-center gap-2 text-xs cursor-pointer"
            >
              <input
                type="checkbox"
                checked={edge.visible}
                onChange={() => toggleEdgeLayer(edge.type)}
                className="rounded"
              />
              <span
                className="inline-block w-2 h-2 rounded-full mr-1"
                style={{ backgroundColor: edge.color }}
              />
              {edge.label}
            </label>
          ))}
        </div>
      </Section>
    </div>
  );
}
