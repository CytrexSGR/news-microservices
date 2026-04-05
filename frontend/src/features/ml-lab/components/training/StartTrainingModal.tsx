/**
 * Start Training Modal
 *
 * Modal for configuring and starting a new training job.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { trainingApi } from '../../api/mlLabApi';
import { type MLModel } from '../../types';
import { SYMBOLS, TIMEFRAMES } from '../../utils/constants';

interface StartTrainingModalProps {
  models: MLModel[];
  onClose: () => void;
  onStarted: () => void;
}

export function StartTrainingModal({ models, onClose, onStarted }: StartTrainingModalProps) {
  const [selectedModel, setSelectedModel] = useState('');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1min');
  const [nTrials, setNTrials] = useState(50);
  const [daysBack, setDaysBack] = useState(90);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel) {
      toast.error('Please select a model');
      return;
    }

    setLoading(true);
    try {
      const dateTo = new Date();
      const dateFrom = new Date();
      dateFrom.setDate(dateFrom.getDate() - daysBack);

      await trainingApi.start({
        model_id: selectedModel,
        config: {
          symbol,
          timeframe,
          date_from: dateFrom.toISOString(),
          date_to: dateTo.toISOString(),
          n_trials: nTrials,
        },
      });
      toast.success('Training started');
      onStarted();
    } catch (error) {
      toast.error('Failed to start training');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Start Training</CardTitle>
          <CardDescription>Configure and start a new training job</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Model</label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name} ({model.area})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {models.length === 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  No draft models available. Create a model first.
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Symbol</label>
                <Select value={symbol} onValueChange={setSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SYMBOLS.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium">Timeframe</label>
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEFRAMES.map((tf) => (
                      <SelectItem key={tf.value} value={tf.value}>
                        {tf.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Optuna Trials</label>
                <Input
                  type="number"
                  value={nTrials}
                  onChange={(e) => setNTrials(parseInt(e.target.value) || 50)}
                  min={10}
                  max={200}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Days of Data</label>
                <Input
                  type="number"
                  value={daysBack}
                  onChange={(e) => setDaysBack(parseInt(e.target.value) || 90)}
                  min={30}
                  max={365}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading || models.length === 0}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Start Training
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default StartTrainingModal;
