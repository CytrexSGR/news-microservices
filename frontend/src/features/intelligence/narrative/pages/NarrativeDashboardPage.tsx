/**
 * NarrativeDashboardPage - Main dashboard for narrative analysis
 *
 * Provides an overview of narrative analysis statistics,
 * frame distributions, and recent analyses.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { NarrativeDashboard } from '../components/NarrativeDashboard';
import { NarrativeResultView } from '../components/NarrativeResultView';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import type { NarrativeAnalysisResult } from '../types/narrative.types';

interface NarrativeDashboardPageProps {
  className?: string;
}

export function NarrativeDashboardPage({ className = '' }: NarrativeDashboardPageProps) {
  const navigate = useNavigate();
  const [selectedResult, setSelectedResult] = useState<NarrativeAnalysisResult | null>(
    null
  );
  const [days, setDays] = useState(7);

  const handleAnalyzeClick = () => {
    navigate('/intelligence/narrative/analyze');
  };

  const handleResultClick = (result: NarrativeAnalysisResult) => {
    setSelectedResult(result);
  };

  const handleCloseDialog = () => {
    setSelectedResult(null);
  };

  return (
    <div className={className}>
      <NarrativeDashboard
        days={days}
        onAnalyzeClick={handleAnalyzeClick}
        onResultClick={handleResultClick}
      />

      {/* Result Detail Dialog */}
      <Dialog open={!!selectedResult} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Analysis Details</DialogTitle>
          </DialogHeader>
          {selectedResult && (
            <NarrativeResultView result={selectedResult} showMetadata />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default NarrativeDashboardPage;
