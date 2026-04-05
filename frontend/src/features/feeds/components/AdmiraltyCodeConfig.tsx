/**
 * AdmiraltyCodeConfig Component
 *
 * Admin interface for configuring Admiralty Code thresholds (A-F ratings).
 * Allows editing min_score, label, description, and color for each rating.
 */
import { useState } from 'react';
import {
  useAdmiraltyThresholds,
  useUpdateAdmiraltyThreshold,
  useResetAdmiraltyThresholds,
} from '../api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Badge } from '@/components/ui/badge';

export function AdmiraltyCodeConfig() {
  const { data: thresholds, isLoading, error } = useAdmiraltyThresholds();
  const updateThreshold = useUpdateAdmiraltyThreshold();
  const resetThresholds = useResetAdmiraltyThresholds();
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    min_score: 0,
    label: '',
    description: '',
    color: '',
  });

  const handleEdit = (code: string) => {
    const threshold = thresholds?.find((t) => t.code === code);
    if (threshold) {
      setEditingCode(code);
      setEditForm({
        min_score: threshold.min_score,
        label: threshold.label,
        description: threshold.description,
        color: threshold.color,
      });
    }
  };

  const handleSave = async () => {
    if (!editingCode) return;

    try {
      await updateThreshold.mutateAsync({
        code: editingCode,
        updates: editForm,
      });
      setEditingCode(null);
    } catch (err) {
      // Error is handled by mutation hook
    }
  };

  const handleReset = async () => {
    if (confirm('Reset all thresholds to default values? This cannot be undone.')) {
      try {
        await resetThresholds.mutateAsync();
      } catch (err) {
        // Error is handled by mutation hook
      }
    }
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <p className="text-sm text-destructive">{(error as Error).message}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Admiralty Code Thresholds</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Configure minimum quality scores for each rating (A-F)
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={resetThresholds.isPending}
        >
          Reset to Defaults
        </Button>
      </div>

      <div className="space-y-4">
        {thresholds?.map((threshold) => (
          <div
            key={threshold.code}
            className="border rounded-lg p-4 hover:border-primary/50 transition-colors"
          >
            {editingCode === threshold.code ? (
              // Edit Mode
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`code-${threshold.code}`}>Code</Label>
                    <Input
                      id={`code-${threshold.code}`}
                      value={threshold.code}
                      disabled
                      className="bg-muted"
                    />
                  </div>
                  <div>
                    <Label htmlFor={`score-${threshold.code}`}>Min Score (0-100)</Label>
                    <Input
                      id={`score-${threshold.code}`}
                      type="number"
                      min="0"
                      max="100"
                      value={editForm.min_score}
                      onChange={(e) =>
                        setEditForm({ ...editForm, min_score: parseInt(e.target.value) })
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`label-${threshold.code}`}>Label</Label>
                    <Input
                      id={`label-${threshold.code}`}
                      value={editForm.label}
                      onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor={`color-${threshold.code}`}>Color</Label>
                    <Input
                      id={`color-${threshold.code}`}
                      value={editForm.color}
                      onChange={(e) => setEditForm({ ...editForm, color: e.target.value })}
                      placeholder="green, blue, yellow, etc."
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor={`desc-${threshold.code}`}>Description</Label>
                  <Textarea
                    id={`desc-${threshold.code}`}
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleSave}
                    disabled={updateThreshold.isPending}
                    size="sm"
                  >
                    {updateThreshold.isPending ? 'Saving...' : 'Save'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setEditingCode(null)}
                    size="sm"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              // View Mode
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Badge
                      className={`font-mono text-white ${
                        threshold.color === 'green' ? 'bg-green-500' :
                        threshold.color === 'blue' ? 'bg-blue-500' :
                        threshold.color === 'yellow' ? 'bg-yellow-500 text-gray-900' :
                        threshold.color === 'orange' ? 'bg-orange-500' :
                        threshold.color === 'red' ? 'bg-red-500' :
                        'bg-gray-500'
                      }`}
                    >
                      {threshold.code}
                    </Badge>
                    <span className="font-semibold">{threshold.label}</span>
                    <span className="text-sm text-muted-foreground">
                      (Score ≥ {threshold.min_score})
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{threshold.description}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(threshold.code)}
                >
                  Edit
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
