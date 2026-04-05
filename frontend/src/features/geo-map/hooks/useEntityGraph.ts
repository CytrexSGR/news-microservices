// frontend/src/features/geo-map/hooks/useEntityGraph.ts

import { useQuery } from '@tanstack/react-query';

interface EntityNode {
  id: string;
  name: string;
  type: string;
  threat_score: number | null;
  mention_count: number;
  countries: string[];
}

interface EntityEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  evidence: string | null;
}

interface EntityGraphResponse {
  nodes: EntityNode[];
  edges: EntityEdge[];
  total_nodes: number;
  total_edges: number;
}

const getApiBase = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:8115/api/v1/geo/security`;
};

export function useEntityGraph(country?: string, limit = 50) {
  return useQuery<EntityGraphResponse>({
    queryKey: ['security', 'entity-graph', country, limit],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (country) params.append('country', country);

      const response = await fetch(`${getApiBase()}/entity-graph?${params}`);
      if (!response.ok) throw new Error('Failed to fetch entity graph');
      return response.json();
    },
    staleTime: 120_000,
  });
}

export type { EntityNode, EntityEdge, EntityGraphResponse };
