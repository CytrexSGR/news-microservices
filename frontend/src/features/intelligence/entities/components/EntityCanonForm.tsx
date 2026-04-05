/**
 * EntityCanonForm - Single entity canonicalization form
 *
 * Allows users to canonicalize a single entity by name and type.
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, CheckCircle2, AlertCircle, ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { useCanonicalizeEntity } from '../api/useCanonicalizeEntity';
import type { EntityType, CanonicalEntity } from '../types/entities.types';
import { ENTITY_TYPE_CONFIGS, getConfidenceColor } from '../types/entities.types';

const formSchema = z.object({
  entity_name: z.string().min(1, 'Entity name is required').max(255),
  entity_type: z.enum([
    'PERSON',
    'ORGANIZATION',
    'LOCATION',
    'EVENT',
    'PRODUCT',
    'OTHER',
    'MISC',
    'NOT_APPLICABLE',
  ]),
  language: z.string().default('de'),
});

type FormData = z.infer<typeof formSchema>;

interface EntityCanonFormProps {
  onSuccess?: (result: CanonicalEntity) => void;
  className?: string;
}

export function EntityCanonForm({ onSuccess, className }: EntityCanonFormProps) {
  const [result, setResult] = useState<CanonicalEntity | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      entity_name: '',
      entity_type: 'PERSON',
      language: 'de',
    },
  });

  const entityType = watch('entity_type');

  const mutation = useCanonicalizeEntity({
    onSuccess: (data) => {
      setResult(data);
      onSuccess?.(data);
    },
  });

  const onSubmit = (data: FormData) => {
    setResult(null);
    mutation.mutate({
      entity_name: data.entity_name,
      entity_type: data.entity_type as EntityType,
      language: data.language,
    });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Canonicalize Entity
        </CardTitle>
        <CardDescription>
          Resolve entity name to its canonical form with Wikidata linking
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="entity_name">Entity Name</Label>
            <Input
              id="entity_name"
              placeholder="e.g., USA, Barack Obama, Microsoft..."
              {...register('entity_name')}
            />
            {errors.entity_name && (
              <p className="text-sm text-destructive">{errors.entity_name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="entity_type">Entity Type</Label>
              <Select
                value={entityType}
                onValueChange={(value) => setValue('entity_type', value as EntityType)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {ENTITY_TYPE_CONFIGS.map((config) => (
                    <SelectItem key={config.type} value={config.type}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Select
                value={watch('language')}
                onValueChange={(value) => setValue('language', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button type="submit" disabled={mutation.isPending} className="w-full">
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Canonicalizing...
              </>
            ) : (
              <>
                Canonicalize
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        {/* Error Display */}
        {mutation.isError && (
          <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span className="font-medium">Error</span>
            </div>
            <p className="mt-1 text-sm text-destructive/80">
              {mutation.error?.message || 'Failed to canonicalize entity'}
            </p>
          </div>
        )}

        {/* Result Display */}
        {result && (
          <div className="mt-4 p-4 bg-muted rounded-lg space-y-3">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span className="font-medium">Canonicalized Successfully</span>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Canonical Name</span>
                <span className="font-medium">{result.canonical_name}</span>
              </div>

              {result.canonical_id && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Wikidata ID</span>
                  <a
                    href={`https://www.wikidata.org/wiki/${result.canonical_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    {result.canonical_id}
                  </a>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Confidence</span>
                <span className={`font-medium ${getConfidenceColor(result.confidence)}`}>
                  {(result.confidence * 100).toFixed(1)}%
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Source</span>
                <Badge variant="outline">{result.source}</Badge>
              </div>

              {result.aliases.length > 0 && (
                <div>
                  <span className="text-sm text-muted-foreground">Aliases</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {result.aliases.map((alias, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {alias}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {result.processing_time_ms && (
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Processing Time</span>
                  <span>{result.processing_time_ms.toFixed(1)}ms</span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
