import { EnrichmentStatsCard } from './EnrichmentStatsCard'
import { EnrichmentCandidateList } from './EnrichmentCandidateList'
import { EnrichmentToolPanel } from './EnrichmentToolPanel'
import { useEnrichmentStats, useEnrichmentWorkflow } from '../../hooks/useEnrichment'

export function EnrichmentDashboard() {
  // Fetch stats (auto-refresh every 60s)
  const { data: stats, isLoading: statsLoading } = useEnrichmentStats(60000)

  // Enrichment workflow state
  const {
    candidates,
    selectedCandidate,
    toolResult,
    analyze,
    setSelectedCandidate,
    executeTool,
    applySuggestion,
    isAnalyzing,
    isExecuting,
    isApplying
  } = useEnrichmentWorkflow()

  return (
    <div className="space-y-4">
      {/* Stats Overview */}
      <EnrichmentStatsCard stats={stats || null} isLoading={statsLoading} />

      {/* Workflow Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Left: Candidate List */}
        <EnrichmentCandidateList
          candidates={candidates}
          isLoading={isAnalyzing}
          onSelectCandidate={setSelectedCandidate}
          selectedCandidate={selectedCandidate}
          onAnalyze={analyze}
        />

        {/* Right: Tool Execution */}
        <EnrichmentToolPanel
          candidate={selectedCandidate}
          onExecuteTool={executeTool}
          toolResult={toolResult}
          isExecuting={isExecuting}
          onApplySuggestion={applySuggestion}
          isApplying={isApplying}
        />
      </div>

      {/* Usage Instructions */}
      <div className="text-xs text-muted-foreground p-4 bg-muted/30 rounded-lg">
        <div className="font-medium mb-2">Workflow:</div>
        <ol className="list-decimal list-inside space-y-1">
          <li>Click "Analyze" to find NOT_APPLICABLE relationships that occur frequently</li>
          <li>Select a candidate entity pair from the list</li>
          <li>Choose a tool (Wikipedia, Research, etc.) and execute it</li>
          <li>Review the relationship suggestions with confidence scores</li>
          <li>Click "Apply" on the best suggestion to enrich the Knowledge Graph</li>
        </ol>
      </div>
    </div>
  )
}
