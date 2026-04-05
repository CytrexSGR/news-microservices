/**
 * TemplateDetailView - Template Detail with Parameters
 *
 * Shows detailed template information and parameter documentation
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Clock,
  Settings,
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useOsintTemplate } from '../api';
import type { OsintTemplate, TemplateParameter } from '../types/osint.types';
import { getCategoryLabel } from '../types/osint.types';

interface TemplateDetailViewProps {
  templateName: string;
  template?: OsintTemplate;
  onCreateInstance?: () => void;
}

export function TemplateDetailView({
  templateName,
  template: providedTemplate,
  onCreateInstance,
}: TemplateDetailViewProps) {
  const { data: fetchedTemplate, isLoading, error } = useOsintTemplate(
    providedTemplate ? undefined : templateName,
    !providedTemplate
  );

  const template = providedTemplate || fetchedTemplate;

  if (isLoading) {
    return <TemplateDetailSkeleton />;
  }

  if (error || !template) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load template details</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{template.name}</CardTitle>
              <div className="flex items-center gap-2 mt-2">
                <Badge>{getCategoryLabel(template.category)}</Badge>
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>~{template.estimated_runtime_seconds}s runtime</span>
                </div>
              </div>
            </div>
            {onCreateInstance && (
              <button
                onClick={onCreateInstance}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                <Settings className="h-4 w-4" />
                Create Instance
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <CardDescription className="text-base">{template.description}</CardDescription>
          {template.tags && template.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-4">
              {template.tags.map((tag) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Parameters Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Settings className="h-5 w-5" />
            Parameters ({template.parameters.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {template.parameters.length === 0 ? (
            <p className="text-muted-foreground">No parameters required</p>
          ) : (
            <div className="space-y-4">
              {template.parameters.map((param) => (
                <ParameterItem key={param.name} parameter={param} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Output Schema Card */}
      {template.output_schema && Object.keys(template.output_schema).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-5 w-5" />
              Output Schema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded-lg bg-muted p-4 text-sm overflow-x-auto">
              {JSON.stringify(template.output_schema, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface ParameterItemProps {
  parameter: TemplateParameter;
}

function ParameterItem({ parameter }: ParameterItemProps) {
  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <code className="rounded bg-muted px-2 py-1 text-sm font-mono">
            {parameter.name}
          </code>
          <Badge variant="outline" className="text-xs">
            {parameter.type}
          </Badge>
          {parameter.required ? (
            <span className="flex items-center gap-1 text-xs text-red-500">
              <XCircle className="h-3 w-3" />
              required
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-green-500">
              <CheckCircle2 className="h-3 w-3" />
              optional
            </span>
          )}
        </div>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{parameter.description}</p>
      {parameter.default !== undefined && (
        <div className="mt-2 text-xs text-muted-foreground">
          Default:{' '}
          <code className="rounded bg-muted px-1 py-0.5">
            {JSON.stringify(parameter.default)}
          </code>
        </div>
      )}
      {parameter.validation && (
        <div className="mt-2 space-y-1 text-xs text-muted-foreground">
          {parameter.validation.min !== undefined && (
            <div>Min: {parameter.validation.min}</div>
          )}
          {parameter.validation.max !== undefined && (
            <div>Max: {parameter.validation.max}</div>
          )}
          {parameter.validation.pattern && (
            <div>Pattern: <code>{parameter.validation.pattern}</code></div>
          )}
          {parameter.validation.enum && (
            <div>
              Allowed: {parameter.validation.enum.map((v) => (
                <Badge key={v} variant="secondary" className="ml-1 text-xs">
                  {v}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TemplateDetailSkeleton() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <Skeleton className="h-7 w-48 mb-2" />
          <div className="flex gap-2">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-32" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-1" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-36" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-lg border p-4">
              <div className="flex gap-2 mb-2">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default TemplateDetailView;
