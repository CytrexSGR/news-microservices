/**
 * InstanceEditForm - Edit OSINT Instance Form
 *
 * Form for updating an existing OSINT monitoring instance
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Save, X, Plus } from 'lucide-react';
import { useUpdateOsintInstance, useOsintTemplate } from '../api';
import type { OsintInstance, OsintInstanceUpdateRequest, TemplateParameter } from '../types/osint.types';

interface InstanceEditFormProps {
  instance: OsintInstance;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function InstanceEditForm({
  instance,
  onSuccess,
  onCancel,
}: InstanceEditFormProps) {
  const { data: template, isLoading: templateLoading } = useOsintTemplate(instance.template_name);
  const updateInstance = useUpdateOsintInstance();

  const [name, setName] = useState(instance.name);
  const [description, setDescription] = useState(instance.description || '');
  const [schedule, setSchedule] = useState(instance.schedule || '');
  const [enabled, setEnabled] = useState(instance.enabled);
  const [parameters, setParameters] = useState<Record<string, unknown>>(instance.parameters);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: OsintInstanceUpdateRequest = {
      name: name !== instance.name ? name : undefined,
      description: description !== (instance.description || '') ? description || undefined : undefined,
      schedule: schedule !== (instance.schedule || '') ? schedule || undefined : undefined,
      enabled: enabled !== instance.enabled ? enabled : undefined,
      parameters: JSON.stringify(parameters) !== JSON.stringify(instance.parameters) ? parameters : undefined,
    };

    // Only send changed fields
    const hasChanges = Object.values(data).some((v) => v !== undefined);
    if (!hasChanges) {
      onCancel?.();
      return;
    }

    try {
      await updateInstance.mutateAsync({ instanceId: instance.id, data });
      onSuccess?.();
    } catch (error) {
      // Error is handled by mutation
    }
  };

  const updateParameter = (name: string, value: unknown) => {
    setParameters((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Edit Instance</CardTitle>
        <CardDescription>
          Update {instance.name} configuration
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Instance Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Monitoring Instance"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="schedule">
                Schedule (cron expression)
                <Badge variant="outline" className="ml-2 text-xs">
                  Optional
                </Badge>
              </Label>
              <Input
                id="schedule"
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
                placeholder="0 */6 * * * (every 6 hours)"
              />
              <p className="text-xs text-muted-foreground">
                Leave empty for manual execution only
              </p>
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <Label htmlFor="enabled">Enabled</Label>
                <p className="text-xs text-muted-foreground">
                  Instance will run according to schedule when enabled
                </p>
              </div>
              <Switch
                id="enabled"
                checked={enabled}
                onCheckedChange={setEnabled}
              />
            </div>
          </div>

          {/* Parameters */}
          {template && template.parameters.length > 0 && (
            <div className="space-y-4">
              <h4 className="font-medium">Parameters</h4>
              {template.parameters.map((param) => (
                <ParameterInput
                  key={param.name}
                  parameter={param}
                  value={parameters[param.name]}
                  onChange={(value) => updateParameter(param.name, value)}
                />
              ))}
            </div>
          )}

          {templateLoading && (
            <div className="text-sm text-muted-foreground">Loading template parameters...</div>
          )}

          {/* Error Display */}
          {updateInstance.isError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/5 p-4 text-red-500">
              <AlertCircle className="h-5 w-5" />
              <span>{updateInstance.error?.message || 'Failed to update instance'}</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={!name || updateInstance.isPending}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {updateInstance.isPending ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

interface ParameterInputProps {
  parameter: TemplateParameter;
  value: unknown;
  onChange: (value: unknown) => void;
}

function ParameterInput({ parameter, value, onChange }: ParameterInputProps) {
  const renderInput = () => {
    switch (parameter.type) {
      case 'boolean':
        return (
          <Switch
            checked={Boolean(value)}
            onCheckedChange={(checked) => onChange(checked)}
          />
        );

      case 'number':
        return (
          <Input
            type="number"
            value={value as number ?? ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
            min={parameter.validation?.min}
            max={parameter.validation?.max}
          />
        );

      case 'array':
        return (
          <ArrayInput
            value={(value as string[]) ?? []}
            onChange={onChange}
          />
        );

      default:
        if (parameter.validation?.enum) {
          return (
            <select
              value={String(value ?? '')}
              onChange={(e) => onChange(e.target.value)}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            >
              <option value="">Select...</option>
              {parameter.validation.enum.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          );
        }
        return (
          <Input
            value={String(value ?? '')}
            onChange={(e) => onChange(e.target.value || undefined)}
            placeholder={parameter.description}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        {parameter.name}
        {parameter.required && <span className="text-red-500">*</span>}
        <Badge variant="outline" className="text-xs">
          {parameter.type}
        </Badge>
      </Label>
      {renderInput()}
      <p className="text-xs text-muted-foreground">{parameter.description}</p>
    </div>
  );
}

interface ArrayInputProps {
  value: string[];
  onChange: (value: string[]) => void;
}

function ArrayInput({ value, onChange }: ArrayInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addItem = () => {
    if (inputValue.trim()) {
      onChange([...value, inputValue.trim()]);
      setInputValue('');
    }
  };

  const removeItem = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addItem())}
          placeholder="Add item..."
        />
        <button
          type="button"
          onClick={addItem}
          className="rounded-md border px-3 py-2 hover:bg-muted transition-colors"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {value.map((item, index) => (
            <Badge key={index} variant="secondary" className="gap-1">
              {item}
              <button
                type="button"
                onClick={() => removeItem(index)}
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

export default InstanceEditForm;
