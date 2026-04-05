/**
 * NarrativeAnalysisPage - Main analysis page for narrative detection
 *
 * Allows users to analyze text for narrative frames, bias, and propaganda.
 * Shows results with detailed breakdowns.
 */
import { useState } from 'react';
import { NarrativeAnalysisForm } from '../components/NarrativeAnalysisForm';
import { NarrativeResultView } from '../components/NarrativeResultView';
import type { NarrativeAnalysisResult } from '../types/narrative.types';

interface NarrativeAnalysisPageProps {
  className?: string;
}

export function NarrativeAnalysisPage({ className = '' }: NarrativeAnalysisPageProps) {
  const [result, setResult] = useState<NarrativeAnalysisResult | null>(null);

  const handleAnalysisComplete = (newResult: NarrativeAnalysisResult) => {
    setResult(newResult);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Narrative Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Analyze text for narrative frames, political bias, and propaganda techniques.
        </p>
      </div>

      {/* Analysis Form */}
      <NarrativeAnalysisForm onAnalysisComplete={handleAnalysisComplete} />

      {/* Results */}
      {result && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
          <NarrativeResultView result={result} showMetadata />
        </div>
      )}
    </div>
  );
}

export default NarrativeAnalysisPage;
