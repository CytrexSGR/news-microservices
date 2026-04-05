/**
 * ML Lab Training Tab
 *
 * Manage and monitor training jobs.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  RefreshCw,
  Play,
  Square,
  XCircle,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { trainingApi, modelsApi } from '../../api/mlLabApi';
import { ModelStatus, TrainingStatus, type MLModel, type TrainingJob } from '../../types';
import { TRAINING_STATUS_COLORS } from '../../utils/constants';
import { StartTrainingModal } from './StartTrainingModal';

export function TrainingTab() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showStartModal, setShowStartModal] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [jobsData, modelsData] = await Promise.all([
        trainingApi.list({ limit: 50 }),
        modelsApi.list({ limit: 100 }),
      ]);
      setJobs(jobsData.jobs);
      setModels(modelsData.models);
    } catch (error) {
      console.error('Failed to fetch training data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll for updates
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleCancel = async (jobId: string) => {
    try {
      await trainingApi.cancel(jobId);
      toast.success('Training cancelled');
      fetchData();
    } catch (error) {
      toast.error('Failed to cancel training');
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>

        <Button onClick={() => setShowStartModal(true)}>
          <Play className="h-4 w-4 mr-2" />
          Start Training
        </Button>
      </div>

      {/* Jobs List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : jobs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No training jobs</p>
            <p className="text-muted-foreground">Start a training job to train your models</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => {
            const model = models.find((m) => m.id === job.model_id);
            return (
              <Card key={job.id}>
                <CardContent className="py-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={TRAINING_STATUS_COLORS[job.status as TrainingStatus]}>
                          {job.status}
                        </Badge>
                        <span className="font-medium">{model?.name || 'Unknown Model'}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {job.symbol} | {job.timeframe}
                        </span>
                        {job.status === TrainingStatus.RUNNING && (
                          <Button size="sm" variant="ghost" onClick={() => handleCancel(job.id)}>
                            <Square className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {(job.status === TrainingStatus.RUNNING ||
                      job.status === TrainingStatus.PENDING) && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span>
                            Trial {job.current_trial} / {job.total_trials}
                          </span>
                          <span>{(job.progress * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={job.progress * 100} />
                        {job.best_score && (
                          <p className="text-sm text-muted-foreground">
                            Best Score: {(job.best_score * 100).toFixed(2)}%
                          </p>
                        )}
                      </div>
                    )}

                    {job.status === TrainingStatus.COMPLETED && job.metrics && (
                      <div className="flex items-center gap-4 text-sm">
                        <span>
                          <strong>Accuracy:</strong>{' '}
                          {((job.metrics.test_accuracy || 0) * 100).toFixed(1)}%
                        </span>
                        <span>
                          <strong>F1:</strong> {((job.metrics.test_f1 || 0) * 100).toFixed(1)}%
                        </span>
                        <span className="text-muted-foreground">
                          Completed: {new Date(job.completed_at!).toLocaleString()}
                        </span>
                      </div>
                    )}

                    {job.status === TrainingStatus.FAILED && job.error_message && (
                      <Alert variant="destructive">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription>{job.error_message}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Start Training Modal */}
      {showStartModal && (
        <StartTrainingModal
          models={models.filter((m) => m.status === ModelStatus.DRAFT)}
          onClose={() => setShowStartModal(false)}
          onStarted={() => {
            setShowStartModal(false);
            fetchData();
          }}
        />
      )}
    </div>
  );
}

export default TrainingTab;
