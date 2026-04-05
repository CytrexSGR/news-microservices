import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  getEnrichmentStats,
  analyzeForEnrichment,
  executeEnrichmentTool,
  applyEnrichment,
  type EnrichmentStats,
  type EnrichmentAnalysisResult,
  type EnrichmentCandidate,
  type ToolExecutionResult
} from '@/api/knowledgeGraphEnrichment'

export function useEnrichmentStats(refetchInterval?: number) {
  return useQuery<EnrichmentStats>({
    queryKey: ['enrichment', 'stats'],
    queryFn: getEnrichmentStats,
    refetchInterval
  })
}

export function useEnrichmentWorkflow() {
  const queryClient = useQueryClient()
  const [candidates, setCandidates] = useState<EnrichmentCandidate[] | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<EnrichmentCandidate | null>(null)
  const [toolResult, setToolResult] = useState<ToolExecutionResult | null>(null)

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: (params: { limit: number; min_occurrence: number }) =>
      analyzeForEnrichment({
        analysis_type: 'not_applicable_relationships',
        ...params
      }),
    onSuccess: (data: EnrichmentAnalysisResult) => {
      setCandidates(data.candidates)
      setSelectedCandidate(null)
      setToolResult(null)
      toast.success(`Found ${data.candidates.length} enrichment candidates`)
    },
    onError: (error: Error) => {
      toast.error(`Analysis failed: ${error.message}`)
    }
  })

  // Execute tool mutation
  const executeToolMutation = useMutation({
    mutationFn: (params: {
      tool: string
      entity1: string
      entity2: string
      language: string
    }) => executeEnrichmentTool(params),
    onSuccess: (data: ToolExecutionResult) => {
      setToolResult(data)
      if (data.success) {
        if (data.suggestions && data.suggestions.length > 0) {
          toast.success(`Found ${data.suggestions.length} relationship suggestions`)
        } else {
          toast('No suggestions found', { icon: 'ℹ️' })
        }
      } else {
        toast.error(`Tool execution failed: ${data.error || 'Unknown error'}`)
      }
    },
    onError: (error: Error) => {
      toast.error(`Tool execution failed: ${error.message}`)
    }
  })

  // Apply enrichment mutation
  const applyEnrichmentMutation = useMutation({
    mutationFn: (params: {
      entity1: string
      entity2: string
      new_relationship_type: string
      confidence: number
      evidence: string
      source: string
    }) => applyEnrichment(params),
    onSuccess: (data) => {
      toast.success(`Successfully updated ${data.updated_count} relationships`)

      // Invalidate stats to refresh
      queryClient.invalidateQueries({ queryKey: ['enrichment', 'stats'] })

      // Remove the enriched candidate from the list
      if (selectedCandidate) {
        setCandidates(prev =>
          prev ? prev.filter(c =>
            c.entity1 !== selectedCandidate.entity1 ||
            c.entity2 !== selectedCandidate.entity2
          ) : null
        )
        setSelectedCandidate(null)
        setToolResult(null)
      }
    },
    onError: (error: Error) => {
      toast.error(`Apply enrichment failed: ${error.message}`)
    }
  })

  const analyze = useCallback((limit: number, minOccurrence: number) => {
    analyzeMutation.mutate({ limit, min_occurrence: minOccurrence })
  }, [analyzeMutation])

  const executeTool = useCallback(async (tool: string, language: string) => {
    if (!selectedCandidate) {
      toast.error('No candidate selected')
      return
    }

    await executeToolMutation.mutateAsync({
      tool,
      entity1: selectedCandidate.entity1,
      entity2: selectedCandidate.entity2,
      language
    })
  }, [selectedCandidate, executeToolMutation])

  const applySuggestion = useCallback((suggestion: {
    relationship_type: string
    confidence: number
    evidence: string
    source: string
  }) => {
    if (!selectedCandidate) {
      toast.error('No candidate selected')
      return
    }

    applyEnrichmentMutation.mutate({
      entity1: selectedCandidate.entity1,
      entity2: selectedCandidate.entity2,
      new_relationship_type: suggestion.relationship_type,
      confidence: suggestion.confidence,
      evidence: suggestion.evidence,
      source: suggestion.source
    })
  }, [selectedCandidate, applyEnrichmentMutation])

  return {
    // State
    candidates,
    selectedCandidate,
    toolResult,

    // Actions
    analyze,
    setSelectedCandidate,
    executeTool,
    applySuggestion,

    // Loading states
    isAnalyzing: analyzeMutation.isPending,
    isExecuting: executeToolMutation.isPending,
    isApplying: applyEnrichmentMutation.isPending
  }
}
