/**
 * BatchCanonForm - Batch upload form with CSV support
 *
 * Allows users to canonicalize multiple entities at once.
 */
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Loader2, Upload, FileText, X, Play, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useBatchCanonicalizeAsync } from '../api/useBatchCanonicalize';
import { useAsyncJobStatus } from '../api/useAsyncJobStatus';
import type { EntityType, CanonicalizeRequest, AsyncBatchCanonResponse } from '../types/entities.types';
import { ENTITY_TYPE_CONFIGS } from '../types/entities.types';

interface BatchCanonFormProps {
  onJobStarted?: (jobId: string) => void;
  className?: string;
}

interface ParsedEntity {
  name: string;
  type: EntityType;
  language: string;
}

export function BatchCanonForm({ onJobStarted, className }: BatchCanonFormProps) {
  const [entities, setEntities] = useState<ParsedEntity[]>([]);
  const [textInput, setTextInput] = useState('');
  const [defaultType, setDefaultType] = useState<EntityType>('PERSON');
  const [defaultLanguage, setDefaultLanguage] = useState('de');
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const mutation = useBatchCanonicalizeAsync({
    onSuccess: (data) => {
      const asyncData = data as AsyncBatchCanonResponse;
      setActiveJobId(asyncData.job_id);
      onJobStarted?.(asyncData.job_id);
    },
  });

  const { data: jobStatus, isProcessing, isCompleted, isFailed } = useAsyncJobStatus(activeJobId, {
    enabled: !!activeJobId,
  });

  // Parse CSV content
  const parseCSV = useCallback(
    (content: string): ParsedEntity[] => {
      const lines = content.trim().split('\n');
      const parsed: ParsedEntity[] = [];

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;

        const parts = trimmed.split(/[,;\t]/).map((p) => p.trim());
        if (parts.length === 0 || !parts[0]) continue;

        parsed.push({
          name: parts[0],
          type: (parts[1]?.toUpperCase() as EntityType) || defaultType,
          language: parts[2] || defaultLanguage,
        });
      }

      return parsed;
    },
    [defaultType, defaultLanguage]
  );

  // Handle file drop
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const parsed = parseCSV(content);
        setEntities(parsed);
      };
      reader.readAsText(file);
    },
    [parseCSV]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  });

  // Parse text input
  const handleParseText = () => {
    const parsed = parseCSV(textInput);
    setEntities(parsed);
  };

  // Remove entity from list
  const removeEntity = (index: number) => {
    setEntities((prev) => prev.filter((_, i) => i !== index));
  };

  // Submit batch
  const handleSubmit = () => {
    if (entities.length === 0) return;

    const request: CanonicalizeRequest[] = entities.map((e) => ({
      entity_name: e.name,
      entity_type: e.type,
      language: e.language,
    }));

    mutation.mutate({ entities: request });
  };

  // Reset form
  const handleReset = () => {
    setEntities([]);
    setTextInput('');
    setActiveJobId(null);
    mutation.reset();
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Batch Canonicalization
        </CardTitle>
        <CardDescription>
          Upload CSV or enter entities to canonicalize in bulk
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Default Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Default Entity Type</Label>
            <Select
              value={defaultType}
              onValueChange={(value) => setDefaultType(value as EntityType)}
            >
              <SelectTrigger>
                <SelectValue />
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
            <Label>Default Language</Label>
            <Select value={defaultLanguage} onValueChange={setDefaultLanguage}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="de">German</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Input Tabs */}
        <Tabs defaultValue="text" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="text">Text Input</TabsTrigger>
            <TabsTrigger value="file">File Upload</TabsTrigger>
          </TabsList>

          <TabsContent value="text" className="space-y-3">
            <div className="space-y-2">
              <Label>
                Entities (one per line, format: name, type, language)
              </Label>
              <Textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder={`USA, LOCATION, en
Barack Obama, PERSON, en
Microsoft, ORGANIZATION, en`}
                rows={6}
              />
            </div>
            <Button onClick={handleParseText} variant="outline" className="w-full">
              Parse Entities
            </Button>
          </TabsContent>

          <TabsContent value="file" className="space-y-3">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
            >
              <input {...getInputProps()} />
              <FileText className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
              {isDragActive ? (
                <p>Drop the CSV file here...</p>
              ) : (
                <div>
                  <p>Drag & drop a CSV file here</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or click to select a file
                  </p>
                </div>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              CSV format: name, type, language (type and language are optional)
            </p>
          </TabsContent>
        </Tabs>

        {/* Parsed Entities Preview */}
        {entities.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Parsed Entities ({entities.length})</Label>
              <Button variant="ghost" size="sm" onClick={() => setEntities([])}>
                Clear All
              </Button>
            </div>
            <ScrollArea className="h-40 border rounded-lg p-2">
              <div className="space-y-1">
                {entities.map((entity, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-muted rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{entity.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {entity.type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        ({entity.language})
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => removeEntity(idx)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Job Status */}
        {activeJobId && jobStatus && (
          <div
            className={`p-4 rounded-lg ${
              isFailed
                ? 'bg-destructive/10 border border-destructive/20'
                : isCompleted
                ? 'bg-green-500/10 border border-green-500/20'
                : 'bg-blue-500/10 border border-blue-500/20'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {isProcessing && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
              {isCompleted && <CheckCircle2 className="h-4 w-4 text-green-500" />}
              {isFailed && <AlertCircle className="h-4 w-4 text-destructive" />}
              <span className="font-medium">
                {isProcessing && 'Processing...'}
                {isCompleted && 'Completed'}
                {isFailed && 'Failed'}
              </span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Progress</span>
                <span>{jobStatus.progress_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${jobStatus.progress_percent}%` }}
                />
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>
                  {jobStatus.stats.processed_entities} / {jobStatus.stats.total_entities}
                </span>
                <span>
                  {jobStatus.stats.successful} successful, {jobStatus.stats.failed} failed
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {mutation.isError && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span className="font-medium">Error</span>
            </div>
            <p className="mt-1 text-sm text-destructive/80">
              {mutation.error?.message || 'Failed to start batch job'}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            onClick={handleSubmit}
            disabled={entities.length === 0 || mutation.isPending || isProcessing}
            className="flex-1"
          >
            {mutation.isPending || isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Batch ({entities.length})
              </>
            )}
          </Button>
          {(isCompleted || isFailed) && (
            <Button variant="outline" onClick={handleReset}>
              Reset
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
