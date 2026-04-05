import { useState, useEffect, useCallback } from 'react';

interface TDASnapshot {
  timestamp: string;
  betti_0: number;
  betti_1: number;
  persistence_entropy: number;
  max_persistence: number;
  csd_autocorr: number;
  csd_variance: number;
  feigenbaum_ratio: number;
  tipping_score: number;
  n_events: number;
}

function ScoreBar({ value, max = 1, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full h-2 bg-gray-700 rounded overflow-hidden">
      <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function TDAPanel() {
  const [snapshot, setSnapshot] = useState<TDASnapshot | null>(null);
  const [history, setHistory] = useState<TDASnapshot[]>([]);
  const [expanded, setExpanded] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [snapRes, histRes] = await Promise.all([
        fetch('/api/geospatial/tda/snapshot'),
        fetch('/api/geospatial/tda/history?n=20'),
      ]);
      const snapData = await snapRes.json();
      if (snapData.tipping_score !== undefined) {
        setSnapshot(snapData);
      }
      const histData = await histRes.json();
      if (Array.isArray(histData)) {
        setHistory(histData);
      }
    } catch {
      // Service might not be available yet
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (!snapshot) return null;

  const tippingColor =
    snapshot.tipping_score > 0.8
      ? 'bg-red-500'
      : snapshot.tipping_score > 0.5
        ? 'bg-yellow-500'
        : 'bg-green-500';

  const tippingText =
    snapshot.tipping_score > 0.8
      ? 'CRITICAL'
      : snapshot.tipping_score > 0.65
        ? 'WARNING'
        : snapshot.tipping_score > 0.4
          ? 'ELEVATED'
          : 'NOMINAL';

  return (
    <div className="absolute top-4 left-64 bg-gray-900/90 backdrop-blur-sm border border-gray-600 rounded-lg p-3 z-10 min-w-56">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-xs font-bold text-gray-300 mb-2"
      >
        <span>TDA KIPPPUNKT</span>
        <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${tippingColor}`}>
          {tippingText}
        </span>
      </button>

      {/* Tipping score bar */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Tipping Score</span>
          <span className="font-mono">{snapshot.tipping_score.toFixed(3)}</span>
        </div>
        <ScoreBar value={snapshot.tipping_score} color={tippingColor} />
      </div>

      {expanded && (
        <>
          {/* Betti numbers */}
          <div className="grid grid-cols-2 gap-2 mb-2">
            <div className="text-center">
              <div className="text-lg font-bold text-blue-400 font-mono">{snapshot.betti_0}</div>
              <div className="text-xs text-gray-500">&#946;&#8320; Components</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-purple-400 font-mono">{snapshot.betti_1}</div>
              <div className="text-xs text-gray-500">&#946;&#8321; Loops</div>
            </div>
          </div>

          {/* CSD Indicators */}
          <div className="space-y-1 mb-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Autocorrelation</span>
              <span className="font-mono text-cyan-400">{snapshot.csd_autocorr.toFixed(4)}</span>
            </div>
            <ScoreBar value={Math.max(0, snapshot.csd_autocorr)} color="bg-cyan-500" />

            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Variance</span>
              <span className="font-mono text-amber-400">{snapshot.csd_variance.toFixed(2)}</span>
            </div>
            <ScoreBar value={snapshot.csd_variance} max={50} color="bg-amber-500" />

            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Feigenbaum</span>
              <span className="font-mono text-pink-400">{snapshot.feigenbaum_ratio.toFixed(4)}</span>
            </div>
            <ScoreBar value={snapshot.feigenbaum_ratio} color="bg-pink-500" />
          </div>

          {/* Persistence */}
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Persistence Entropy</span>
            <span className="font-mono">{snapshot.persistence_entropy.toFixed(3)}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Max Persistence</span>
            <span className="font-mono">{snapshot.max_persistence.toFixed(1)} km</span>
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Events in Window</span>
            <span className="font-mono">{snapshot.n_events}</span>
          </div>

          {/* Mini sparkline from history */}
          {history.length > 1 && (
            <div className="mt-2 pt-2 border-t border-gray-700">
              <div className="text-xs text-gray-500 mb-1">Score History</div>
              <div className="flex items-end gap-px h-8">
                {history.map((h, i) => {
                  const height = Math.max(2, h.tipping_score * 32);
                  const barColor =
                    h.tipping_score > 0.8
                      ? 'bg-red-500'
                      : h.tipping_score > 0.5
                        ? 'bg-yellow-500'
                        : 'bg-green-500';
                  return (
                    <div
                      key={i}
                      className={`flex-1 ${barColor} rounded-t opacity-80`}
                      style={{ height: `${height}px` }}
                      title={`${h.tipping_score.toFixed(3)} @ ${new Date(h.timestamp).toLocaleTimeString()}`}
                    />
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
