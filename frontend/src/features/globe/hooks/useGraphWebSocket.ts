import { useEffect, useRef, useCallback } from "react";
import { encode, decode } from "@msgpack/msgpack";
import { useSliceStore, type GraphSlice, type BBox } from "../store/sliceStore";

const WS_URL = `ws://${window.location.host}/ws/graph`;

export function useGraphWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[graph-ws] connected");
      const msg = encode({
        type: "subscribe",
        slice_id: "main",
        slice: {
          layers: ["flight", "vessel", "satellite"],
          max_entities: 50000,
          min_weight: 0.5,
        },
      });
      ws.send(msg);
    };

    ws.onmessage = (event) => {
      try {
        const msg = decode(new Uint8Array(event.data)) as Record<string, unknown>;
        const store = useSliceStore.getState();
        switch (msg.type) {
          case "snapshot":
            store.applySnapshot(msg.slice_id as string, msg as any);
            break;
          case "delta":
            store.applyDelta(msg.slice_id as string, msg as any);
            break;
          case "alert":
            store.addAlert(msg as any);
            break;
          case "lod":
            store.updateLOD(msg.slice_id as string, msg as any);
            break;
        }
      } catch (e) {
        console.error("[graph-ws] decode error:", e);
      }
    };

    ws.onclose = () => console.log("[graph-ws] disconnected");
    ws.onerror = (e) => console.error("[graph-ws] error:", e);

    return () => { ws.close(); wsRef.current = null; };
  }, []);

  const subscribe = useCallback((sliceId: string, slice: GraphSlice) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(encode({ type: "subscribe", slice_id: sliceId, slice }));
    }
  }, []);

  const updateViewport = useCallback((bbox: BBox) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(encode({ type: "viewport", slice_id: "main", bbox }));
    }
  }, []);

  const refine = useCallback((patch: Partial<GraphSlice>) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(encode({ type: "refine", slice_id: "main", patch }));
    }
  }, []);

  const unsubscribe = useCallback((sliceId: string) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(encode({ type: "unsubscribe", slice_id: sliceId }));
    }
  }, []);

  return { subscribe, updateViewport, refine, unsubscribe };
}
