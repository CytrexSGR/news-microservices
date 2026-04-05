/**
 * BatchCanonPage - Batch processing page
 *
 * Page for batch entity canonicalization with CSV upload support.
 */
import { useState } from 'react';
import { Upload, FileText, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BatchCanonForm } from '../components/BatchCanonForm';
import { AsyncJobStatusView } from '../components/AsyncJobStatusView';
import { AsyncJobResultView } from '../components/AsyncJobResultView';
import { CanonStatsCard } from '../components/CanonStatsCard';
import type { AsyncJob } from '../types/entities.types';

interface BatchCanonPageProps {
  showBackButton?: boolean;
}

export function BatchCanonPage({ showBackButton }: BatchCanonPageProps) {
  const navigate = useNavigate();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [completedJobId, setCompletedJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'form' | 'status' | 'results'>('form');

  const handleJobStarted = (jobId: string) => {
    setActiveJobId(jobId);
    setActiveTab('status');
  };

  const handleJobCompleted = (job: AsyncJob) => {
    setCompletedJobId(job.job_id);
    setActiveTab('results');
  };

  const handleViewResults = (jobId: string) => {
    setCompletedJobId(jobId);
    setActiveTab('results');
  };

  const handleReset = () => {
    setActiveJobId(null);
    setCompletedJobId(null);
    setActiveTab('form');
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        {showBackButton && (
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
        )}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Upload className="h-8 w-8" />
            Batch Canonicalization
          </h1>
          <p className="text-muted-foreground mt-1">
            Process multiple entities at once with CSV upload or text input
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Form/Status */}
        <div className="lg:col-span-2">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
            <TabsList>
              <TabsTrigger value="form" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                New Batch
              </TabsTrigger>
              {activeJobId && (
                <TabsTrigger value="status" className="flex items-center gap-2">
                  Job Status
                </TabsTrigger>
              )}
              {completedJobId && (
                <TabsTrigger value="results" className="flex items-center gap-2">
                  Results
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="form" className="mt-4">
              <BatchCanonForm onJobStarted={handleJobStarted} />
            </TabsContent>

            {activeJobId && (
              <TabsContent value="status" className="mt-4">
                <AsyncJobStatusView
                  jobId={activeJobId}
                  onCompleted={handleJobCompleted}
                  onViewResults={handleViewResults}
                />
              </TabsContent>
            )}

            {completedJobId && (
              <TabsContent value="results" className="mt-4">
                <AsyncJobResultView jobId={completedJobId} onClose={handleReset} />
              </TabsContent>
            )}
          </Tabs>
        </div>

        {/* Right Column - Stats */}
        <div className="lg:col-span-1 space-y-6">
          <CanonStatsCard />

          {/* Instructions */}
          <div className="bg-muted rounded-lg p-4 space-y-3">
            <h3 className="font-medium">CSV Format</h3>
            <p className="text-sm text-muted-foreground">
              Upload a CSV file with one entity per line:
            </p>
            <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
              {`name, type, language
USA, LOCATION, en
Barack Obama, PERSON, en
Microsoft, ORGANIZATION, en`}
            </pre>
            <p className="text-xs text-muted-foreground">
              Type and language are optional - defaults will be applied if omitted.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
