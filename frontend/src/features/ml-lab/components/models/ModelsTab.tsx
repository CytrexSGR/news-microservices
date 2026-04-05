/**
 * ML Lab Models Tab
 *
 * List and manage ML models with filtering and actions.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Brain,
  RefreshCw,
  Plus,
  Trash2,
  Power,
  PowerOff,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { modelsApi } from '../../api/mlLabApi';
import { MLArea, ModelStatus, type MLModel } from '../../types';
import { AREA_ICONS, STATUS_COLORS } from '../../utils/constants';
import { CreateModelModal } from './CreateModelModal';

export function ModelsTab() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedArea, setSelectedArea] = useState<MLArea | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchModels = useCallback(async () => {
    try {
      const params = selectedArea !== 'all' ? { area: selectedArea } : {};
      const data = await modelsApi.list(params);
      setModels(data.models);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      toast.error('Failed to load models');
    } finally {
      setLoading(false);
    }
  }, [selectedArea]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleActivate = async (modelId: string) => {
    try {
      await modelsApi.activate(modelId);
      toast.success('Model activated');
      fetchModels();
    } catch (error) {
      toast.error('Failed to activate model');
    }
  };

  const handleDeactivate = async (modelId: string) => {
    try {
      await modelsApi.deactivate(modelId);
      toast.success('Model deactivated');
      fetchModels();
    } catch (error) {
      toast.error('Failed to deactivate model');
    }
  };

  const handleDelete = async (modelId: string) => {
    if (!confirm('Are you sure you want to delete this model?')) return;
    try {
      await modelsApi.delete(modelId);
      toast.success('Model deleted');
      fetchModels();
    } catch (error) {
      toast.error('Failed to delete model');
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Select
            value={selectedArea}
            onValueChange={(v) => setSelectedArea(v as MLArea | 'all')}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by area" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Areas</SelectItem>
              {Object.values(MLArea).map((area) => (
                <SelectItem key={area} value={area}>
                  {area.charAt(0).toUpperCase() + area.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={fetchModels}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Model
        </Button>
      </div>

      {/* Models List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No models found</p>
            <p className="text-muted-foreground">Create your first model to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {models.map((model) => (
            <Card key={model.id}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-muted rounded-lg">{AREA_ICONS[model.area]}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{model.name}</h3>
                        <Badge className={STATUS_COLORS[model.status]}>{model.status}</Badge>
                        {model.is_active && (
                          <Badge variant="outline" className="border-green-500 text-green-500">
                            Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {model.area} | {model.model_type} | v{model.version}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {model.metrics?.test_accuracy && (
                      <span className="text-sm font-medium">
                        Accuracy: {(model.metrics.test_accuracy * 100).toFixed(1)}%
                      </span>
                    )}

                    {model.status === ModelStatus.ACTIVE && !model.is_active && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleActivate(model.id)}
                      >
                        <Power className="h-4 w-4 mr-1" />
                        Activate
                      </Button>
                    )}

                    {model.is_active && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeactivate(model.id)}
                      >
                        <PowerOff className="h-4 w-4 mr-1" />
                        Deactivate
                      </Button>
                    )}

                    {!model.is_active && model.status !== ModelStatus.TRAINING && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={() => handleDelete(model.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateModelModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchModels();
          }}
        />
      )}
    </div>
  );
}

export default ModelsTab;
