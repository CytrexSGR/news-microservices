import { useQuery } from '@tanstack/react-query'
import { getCrossArticleCoverage } from '@/lib/api/knowledgeGraphAdmin'

export function useCrossArticleCoverage(topLimit: number = 10, refetchInterval: number = 60000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'cross-article-coverage', topLimit],
    queryFn: () => getCrossArticleCoverage(topLimit),
    refetchInterval, // Auto-refresh every 60 seconds
    staleTime: 30000,
  })
}
