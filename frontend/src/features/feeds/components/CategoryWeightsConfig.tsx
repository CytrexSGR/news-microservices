/**
 * CategoryWeightsConfig Component
 *
 * Admin interface for configuring quality score category weights.
 * Allows editing weight values for credibility, editorial, trust, and health categories.
 * Validates that weights sum to 1.00 (100%).
 */
import { useState } from 'react';
import {
  useQualityWeights,
  useUpdateQualityWeight,
  useResetQualityWeights,
  useValidateWeights,
} from '../api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export function CategoryWeightsConfig() {
  const { data: weights, isLoading, error } = useQualityWeights();
  const { data: validation } = useValidateWeights();
  const updateWeight = useUpdateQualityWeight();
  const resetWeights = useResetQualityWeights();
  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    weight: 0,
    description: '',
  });

  const handleEdit = (category: string) => {
    const weight = weights?.find((w) => w.category === category);
    if (weight) {
      setEditingCategory(category);
      setEditForm({
        weight: parseFloat(weight.weight),
        description: weight.description,
      });
    }
  };

  const handleSave = async () => {
    if (!editingCategory) return;

    try {
      await updateWeight.mutateAsync({
        category: editingCategory,
        updates: editForm,
      });
      setEditingCategory(null);
    } catch (err) {
      alert((err as any)?.response?.data?.detail || 'Failed to update weight. Weights must sum to 1.00');
    }
  };

  const handleReset = async () => {
    if (confirm('Reset all weights to default values? This cannot be undone.')) {
      try {
        await resetWeights.mutateAsync();
      } catch (err) {
        // Error is handled by mutation hook
      }
    }
  };

  // Calculate total for display
  const totalWeight = weights?.reduce((sum, w) => sum + parseFloat(w.weight), 0) || 0;
  const isValid = validation?.is_valid ?? true;

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
          <h3 className="text-lg font-semibold">Quality Score Weights</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Configure category weights for quality score calculation (must sum to 1.00)
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={resetWeights.isPending}
        >
          Reset to Defaults
        </Button>
      </div>

      {/* Validation Status */}
      <div className={`mb-6 p-4 rounded-lg border ${
        isValid
          ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
          : 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">
            {isValid ? '✓ Weights Valid' : '⚠ Weights Invalid'}
          </span>
          <span className="text-sm font-mono">
            Total: {totalWeight.toFixed(2)} {isValid ? '(100%)' : '(must be 1.00)'}
          </span>
        </div>
        <Progress value={totalWeight * 100} className="h-2" />
      </div>

      <div className="space-y-4">
        {weights?.map((weight) => (
          <div
            key={weight.category}
            className="border rounded-lg p-4 hover:border-primary/50 transition-colors"
          >
            {editingCategory === weight.category ? (
              // Edit Mode
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`cat-${weight.category}`}>Category</Label>
                    <Input
                      id={`cat-${weight.category}`}
                      value={weight.category}
                      disabled
                      className="bg-muted capitalize"
                    />
                  </div>
                  <div>
                    <Label htmlFor={`weight-${weight.category}`}>Weight (0.00 - 1.00)</Label>
                    <Input
                      id={`weight-${weight.category}`}
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={editForm.weight}
                      onChange={(e) =>
                        setEditForm({ ...editForm, weight: parseFloat(e.target.value) })
                      }
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor={`desc-${weight.category}`}>Description</Label>
                  <Textarea
                    id={`desc-${weight.category}`}
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleSave}
                    disabled={updateWeight.isPending}
                    size="sm"
                  >
                    {updateWeight.isPending ? 'Saving...' : 'Save'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setEditingCategory(null)}
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
                    <span className="font-semibold capitalize">{weight.category}</span>
                    <Badge variant="outline" className="font-mono">
                      {parseFloat(weight.weight).toFixed(2)} ({(parseFloat(weight.weight) * 100).toFixed(0)}%)
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{weight.description}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(weight.category)}
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
