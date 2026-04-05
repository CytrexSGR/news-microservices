import { useState, useEffect, useCallback } from 'react';

interface WaveFront {
  id: string;
  pattern_type: string;
  instability: string;
  origin: { lat: number; lon: number };
  front: { lat: number; lon: number };
  velocity_kmh: number;
  heading_deg: number;
  width_km: number;
  confidence: number;
  trail: { lat: number; lon: number }[];
}

interface PatternSnapshot {
  timestamp: string;
  propagation_detected: boolean;
  dominant_instability: string;
  total_events: number;
  wave_fronts: WaveFront[];
}

const PATTERN_ICONS: Record<string, string> = {
  'wave-front': '\u2248',    // ≈
  'soliton': '\u223F',       // ∿
  'spiral': '\u0040',        // @
  'cluster-burst': '\u2600', // ☀
};

const INSTABILITY_COLORS: Record<string, string> = {
  'eckhaus': 'text-orange-400',
  'zigzag': 'text-yellow-400',
  'benjamin-feir': 'text-red-400',
  'none': 'text-gray-400',
};

function HeadingArrow({ deg }: { deg: number }) {
  return (
    <span
      className="inline-block text-lg"
      style={{ transform: `rotate(${deg}deg)`, display: 'inline-block' }}
    >
      &#8593;
    </span>
  );
}

export function PatternPanel() {
  const [snapshot, setSnapshot] = useState<PatternSnapshot | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/geospatial/patterns/snapshot');
      const data = await res.json();
      if (data.wave_fronts !== undefined) {
        setSnapshot(data);
      }
    } catch {
      // Service not ready
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (!snapshot || !snapshot.propagation_detected) return null;

  return (
    <div className="absolute bottom-4 right-4 bg-gray-900/90 backdrop-blur-sm border border-indigo-500/50 rounded-lg p-3 z-10 min-w-64 max-w-80">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-indigo-300">WAVE FRONTS</span>
        <span className="text-xs text-gray-400">{snapshot.wave_fronts.length} active</span>
      </div>

      {snapshot.dominant_instability !== 'none' && (
        <div className="text-xs text-gray-400 mb-2">
          Dominant: <span className={`font-bold ${INSTABILITY_COLORS[snapshot.dominant_instability]}`}>
            {snapshot.dominant_instability.toUpperCase()}
          </span>
        </div>
      )}

      <div className="space-y-2 max-h-48 overflow-y-auto">
        {snapshot.wave_fronts.map((wf) => (
          <div key={wf.id} className="bg-gray-800/50 rounded p-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">
                <span className="mr-1">{PATTERN_ICONS[wf.pattern_type] || '?'}</span>
                <span className="text-white font-mono text-xs">{wf.pattern_type}</span>
              </span>
              <span className="text-xs text-gray-500">
                {(wf.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex items-center gap-1">
                <HeadingArrow deg={wf.heading_deg} />
                <span className="text-xs text-cyan-400 font-mono">{wf.velocity_kmh} km/h</span>
              </div>
              {wf.instability !== 'none' && (
                <span className={`text-xs font-bold ${INSTABILITY_COLORS[wf.instability]}`}>
                  {wf.instability}
                </span>
              )}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ({wf.origin.lat.toFixed(1)}, {wf.origin.lon.toFixed(1)}) &rarr; ({wf.front.lat.toFixed(1)}, {wf.front.lon.toFixed(1)})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
