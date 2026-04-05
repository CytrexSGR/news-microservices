/**
 * FramesPage - Reference page for available narrative frames
 *
 * Displays all narrative frames that can be detected with
 * their descriptions, keywords, and examples.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { FramesTable } from '../components/FramesTable';
import { DetectedFrameCard } from '../components/DetectedFrameCard';
import type { NarrativeFrame, DetectedFrame } from '../types/narrative.types';

interface FramesPageProps {
  className?: string;
}

export function FramesPage({ className = '' }: FramesPageProps) {
  const [selectedFrame, setSelectedFrame] = useState<NarrativeFrame | null>(null);

  const handleFrameSelect = (frame: NarrativeFrame) => {
    setSelectedFrame(frame);
  };

  // Create a mock detected frame for preview purposes
  const createPreviewFrame = (frame: NarrativeFrame): DetectedFrame => ({
    frame,
    confidence: 0.85,
    evidence: frame.example_phrases.slice(0, 2),
  });

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Narrative Frames Reference</h1>
        <p className="text-muted-foreground mt-1">
          Browse all narrative frames that can be detected in text analysis.
          Click on a frame to see details and examples.
        </p>
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Frames Table */}
        <div className="lg:col-span-2">
          <FramesTable
            onFrameSelect={handleFrameSelect}
            selectedFrameId={selectedFrame?.id}
          />
        </div>

        {/* Selected Frame Preview */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="text-base">Frame Preview</CardTitle>
              <CardDescription>
                {selectedFrame
                  ? 'How this frame appears in analysis results'
                  : 'Select a frame to see preview'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedFrame ? (
                <DetectedFrameCard
                  frame={createPreviewFrame(selectedFrame)}
                  showEvidence
                />
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click on a frame in the table to see how it appears in analysis results.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default FramesPage;
