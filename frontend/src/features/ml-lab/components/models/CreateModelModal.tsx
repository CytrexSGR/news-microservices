/**
 * Create Model Modal
 *
 * Modal for creating new ML models.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { modelsApi } from '../../api/mlLabApi';
import { MLArea, ModelType } from '../../types';
import { AREA_ICONS, AREA_DESCRIPTIONS } from '../../utils/constants';

interface CreateModelModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export function CreateModelModal({ onClose, onCreated }: CreateModelModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [area, setArea] = useState<MLArea>(MLArea.REGIME);
  const [modelType, setModelType] = useState<ModelType>(ModelType.XGBOOST);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error('Please enter a model name');
      return;
    }

    setLoading(true);
    try {
      await modelsApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        area,
        model_type: modelType,
      });
      toast.success('Model created');
      onCreated();
    } catch (error) {
      toast.error('Failed to create model');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create New Model</CardTitle>
          <CardDescription>Define a new ML model for gate validation</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., BTC Regime Detector v1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Description (optional)</label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Model description..."
              />
            </div>

            <div>
              <label className="text-sm font-medium">Gate Area</label>
              <Select value={area} onValueChange={(v) => setArea(v as MLArea)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(MLArea).map((a) => (
                    <SelectItem key={a} value={a}>
                      <div className="flex items-center gap-2">
                        {AREA_ICONS[a]}
                        <span className="capitalize">{a}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">{AREA_DESCRIPTIONS[area]}</p>
            </div>

            <div>
              <label className="text-sm font-medium">Model Type</label>
              <Select value={modelType} onValueChange={(v) => setModelType(v as ModelType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ModelType.XGBOOST}>XGBoost</SelectItem>
                  <SelectItem value={ModelType.LIGHTGBM}>LightGBM</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Create Model
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default CreateModelModal;
