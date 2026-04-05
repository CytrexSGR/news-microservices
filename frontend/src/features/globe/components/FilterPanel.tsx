import { useCallback, useState } from "react";
import { useSliceStore } from "../store/sliceStore";
import { useGraphWebSocket } from "../hooks/useGraphWebSocket";

const LAYERS = ["flight", "vessel", "satellite"] as const;

const REGIONS: Record<string, { lat_min: number; lat_max: number; lon_min: number; lon_max: number } | null> = {
  "Global": null,
  "Persischer Golf": { lat_min: 22, lat_max: 32, lon_min: 44, lon_max: 62 },
  "Ostsee": { lat_min: 53, lat_max: 66, lon_min: 10, lon_max: 30 },
  "Suedchinesisches Meer": { lat_min: 0, lat_max: 25, lon_min: 100, lon_max: 122 },
  "Mittelmeer": { lat_min: 30, lat_max: 46, lon_min: -6, lon_max: 36 },
  "Naher Osten": { lat_min: 12, lat_max: 42, lon_min: 25, lon_max: 65 },
};

export function FilterPanel() {
  const { subscribe, refine } = useGraphWebSocket();
  const [activeLayers, setActiveLayers] = useState<Set<string>>(new Set(LAYERS));
  const alertCount = useSliceStore((s) => s.alertCount);
  const activeSliceId = useSliceStore((s) => s.activeSliceId);
  const slice = useSliceStore((s) => s.slices.get(s.activeSliceId));
  const shown = slice?.nodes.size ?? 0;
  const total = slice?.totalMatching ?? 0;

  const handleLayerToggle = useCallback((layer: string, checked: boolean) => {
    setActiveLayers(prev => {
      const next = new Set(prev);
      if (checked) next.add(layer);
      else next.delete(layer);
      subscribe("main", { layers: [...next] });
      return next;
    });
  }, [subscribe]);

  const handleRegion = useCallback((regionName: string) => {
    const bbox = REGIONS[regionName];
    if (bbox) {
      refine({ bbox });
    } else {
      refine({ bbox: null });
    }
  }, [refine]);

  return (
    <div style={{
      position: "absolute", top: 10, left: 10, zIndex: 1000,
      background: "rgba(0,0,0,0.85)", color: "#0f0", padding: "12px",
      borderRadius: "4px", fontFamily: "monospace", fontSize: "12px",
      minWidth: "220px", border: "1px solid #0f03",
    }}>
      <div style={{ marginBottom: "8px", fontWeight: "bold", borderBottom: "1px solid #0f03", paddingBottom: "4px" }}>
        OBSERVER FILTER
      </div>

      <div style={{ marginBottom: "8px" }}>
        {LAYERS.map((l) => (
          <label key={l} style={{ display: "block", cursor: "pointer", padding: "2px 0" }}>
            <input
              type="checkbox"
              checked={activeLayers.has(l)}
              onChange={(e) => handleLayerToggle(l, e.target.checked)}
              style={{ marginRight: "6px" }}
            />
            {l}
          </label>
        ))}
      </div>

      <div style={{ marginBottom: "8px" }}>
        <select
          onChange={(e) => handleRegion(e.target.value)}
          style={{ width: "100%", background: "#111", color: "#0f0", border: "1px solid #0f0", padding: "4px" }}
        >
          {Object.keys(REGIONS).map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <div style={{ borderTop: "1px solid #0f03", paddingTop: "6px" }}>
        <div>Entities: {shown.toLocaleString()} / {total.toLocaleString()}</div>
        <div>Alerts: {alertCount}</div>
      </div>
    </div>
  );
}
