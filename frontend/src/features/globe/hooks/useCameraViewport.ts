import { useEffect, useRef } from "react";
import { Math as CesiumMath } from "cesium";
import type { Viewer } from "cesium";
import type { BBox } from "../store/sliceStore";

export function useCameraViewport(
  viewer: Viewer | null,
  onViewportChange: (bbox: BBox) => void,
  debounceMs: number = 300,
) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!viewer) return;

    const handler = () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        const rect = viewer.camera.computeViewRectangle();
        if (!rect) return;
        const bbox: BBox = {
          lat_min: CesiumMath.toDegrees(rect.south),
          lat_max: CesiumMath.toDegrees(rect.north),
          lon_min: CesiumMath.toDegrees(rect.west),
          lon_max: CesiumMath.toDegrees(rect.east),
        };
        onViewportChange(bbox);
      }, debounceMs);
    };

    const removeListener = viewer.camera.changed.addEventListener(handler);

    return () => {
      removeListener();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [viewer, onViewportChange, debounceMs]);
}
