/**
 * PatternsPage - Pattern Detection Page
 *
 * Page for running pattern detection analysis
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Network } from 'lucide-react';
import { PatternDetectionPanel } from '../components/PatternDetectionPanel';
import type { DetectedPattern } from '../types/osint.types';

export function PatternsPage() {
  const [selectedPattern, setSelectedPattern] = useState<DetectedPattern | null>(null);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/intelligence/osint"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6" />
            Pattern Detection
          </h1>
          <p className="text-muted-foreground">
            Analyze entities and relationships to detect intelligence patterns
          </p>
        </div>
      </div>

      {/* Pattern Detection Panel */}
      <PatternDetectionPanel onPatternSelect={setSelectedPattern} />

      {/* Selected Pattern Detail */}
      {selectedPattern && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="bg-card rounded-lg border shadow-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{selectedPattern.type}</h3>
                  <p className="text-sm text-muted-foreground">
                    {(selectedPattern.confidence * 100).toFixed(0)}% confidence
                  </p>
                </div>
                <button
                  onClick={() => setSelectedPattern(null)}
                  className="rounded-md p-2 hover:bg-muted transition-colors"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
              </div>
              <p className="mb-4">{selectedPattern.description}</p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Entities ({selectedPattern.entities.length})</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedPattern.entities.map((entity, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-muted px-2 py-1 text-xs"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedPattern.evidence.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Evidence ({selectedPattern.evidence.length})</h4>
                    <div className="space-y-2">
                      {selectedPattern.evidence.map((ev, i) => (
                        <div key={i} className="rounded-lg border p-3 text-sm">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium">{ev.source}</span>
                            <span className="text-muted-foreground text-xs">
                              {(ev.relevance * 100).toFixed(0)}% relevant
                            </span>
                          </div>
                          <p className="text-muted-foreground">{ev.content}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(ev.timestamp).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PatternsPage;
