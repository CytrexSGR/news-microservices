/**
 * CreateInstanceForm - Create OSINT Instance Form
 *
 * Form for creating a new OSINT monitoring instance
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Plus, X } from 'lucide-react';
import { useCreateOsintInstance, useOsintTemplate } from '../api';
import type { OsintTemplate, OsintInstanceCreateRequest, TemplateParameter } from '../types/osint.types';

interface CreateInstanceFormProps {
  templateName: string;
  template?: OsintTemplate;
  onSuccess?: (instanceId: string) => void;
  onCancel?: () => void;
}

export function CreateInstanceForm({
  templateName,
  template: providedTemplate,
  onSuccess,
  onCancel,
}: CreateInstanceFormProps) {
  const { data: fetchedTemplate, isLoading: templateLoading } = useOsintTemplate(
    providedTemplate ? undefined : templateName,
    !providedTemplate
  );
  const template = providedTemplate || fetchedTemplate;

  const createInstance = useCreateOsintInstance();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [schedule, setSchedule] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [parameters, setParameters] = useState<Record<string, unknown>>({});

  // Initialize parameters with defaults when template loads
  useEffect(() => {
    if (template) {
      const defaults: Record<string, unknown> = {};
      template.parameters.forEach((param) => {
        if (param.default !== undefined) {
          defaults[param.name] = param.default;
        }
      });
      setParameters(defaults);
    }
  }, [template]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const request: OsintInstanceCreateRequest = {
      template_name: templateName,
      name,
      description: description || undefined,
      parameters,
      schedule: schedule || undefined,
      enabled,
    };

    try {
      const result = await createInstance.mutateAsync(request);
      onSuccess?.(result.id);
    } catch (error) {
      // Error is handled by mutation
    }
  };

  const updateParameter = (name: string, value: unknown) => {
    setParameters((prev) => ({ ...prev, [name]: value }));
  };

  if (templateLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="animate-pulse space-y-4">
            <div className="h-10 bg-muted rounded" />
            <div className="h-20 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!template) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Template not found: {templateName}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Instance</CardTitle>
        <CardDescription>
          Create a new monitoring instance based on the {template.name} template
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
          {template.parameters.length > 0 && (
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

          {/* Error Display */}
          {createInstance.isError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/5 p-4 text-red-500">
              <AlertCircle className="h-5 w-5" />
              <span>{createInstance.error?.message || 'Failed to create instance'}</span>
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
              disabled={!name || createInstance.isPending}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createInstance.isPending ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Create Instance
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

export default CreateInstanceForm;
